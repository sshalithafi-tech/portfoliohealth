"""
Helpers for assessment chat (LLM calls, JSON report parsing).

Dual-path LLM client:
  - If ANTHROPIC_API_KEY is set (production / Render), use the Anthropic SDK
    directly with the user's own key.
  - Otherwise fall back to Emergent Universal Key via `emergentintegrations`
    so the preview environment keeps working out of the box.

Keeps the route handler in `server.py` focused on orchestration.
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

MODEL_PROVIDER = "anthropic"
# Assessment chat / interview model (the live PPDT conversational engine —
# /api/assessments/{id}/start and the conversational turns of
# /api/assessments/{id}/chat). Upgraded to Claude Sonnet 5.
# NOTE: this constant is intentionally NOT shared with report_sections.py —
# report generation keeps its own independent model constant so upgrading
# the chat model never silently changes the report-generation model.
CHAT_MODEL_NAME = "claude-sonnet-5"
MAX_TOKENS = 16000

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

VALID_BUSINESS_MODELS = {"Bulk", "Standard", "CTO", "CETO", "ETO"}
MODEL_COMPLEXITY_ORDER = ["ETO", "CETO", "CTO", "Standard", "Bulk"]

# Business model → pillar weight table (CODP-derived, see system prompt in
# server.py). Each row sums to 1.0. Used both for the LLM prompt (documented
# in server.py) and for deterministic recomputation of the contextual score
# when the LLM omits it or duplicates the equal-weighted value into it.
BUSINESS_MODEL_WEIGHTS = {
    "ETO":      {"people": 0.35, "process": 0.30, "data": 0.20, "technology": 0.15},
    "CETO":     {"people": 0.25, "process": 0.30, "data": 0.25, "technology": 0.20},
    "CTO":      {"people": 0.20, "process": 0.25, "data": 0.30, "technology": 0.25},
    "Standard": {"people": 0.15, "process": 0.30, "data": 0.35, "technology": 0.20},
    "Bulk":     {"people": 0.10, "process": 0.35, "data": 0.20, "technology": 0.35},
}

# Strategic-priority → pillar mapping for the +5% boost (Step 2 in the prompt).
# Only applied when the priority maps UNAMBIGUOUSLY to a single pillar.
PRIORITY_PILLAR_MAP = {
    "people":     ["people", "talent", "culture", "training", "leadership", "hr"],
    "process":    ["process", "governance", "workflow", "review", "cadence"],
    "data":       ["data", "master data", "analytics", "reporting", "bi", "insight"],
    "technology": ["technology", "systems", "erp", "plm", "it ", "digital tool"],
}

# Ambiguous / multi-pillar priorities that must NOT trigger a boost.
# Source: PPDT Scoring Logic & Business-Model-Contextual Weighting thesis (Table 2):
# "Portfolio simplification, profitability, complexity" and
# "Digital transformation, innovation" → No boost.
AMBIGUOUS_PRIORITY_TERMS = {
    "portfolio simplification",
    "profitability",
    "complexity",
    "digital transformation",
    "innovation",
}


def compute_pillar_contextual_gaps(scores: dict, weights: dict) -> dict:
    """Per-pillar contribution to the divergence between contextual and
    equal-weighted scores.

    Per the thesis (Section: Dual-Score Architecture):
        per_pillar_gap_i = (w_i − 0.25) × pillar_score_i

    The sum of these four gaps equals (contextual_score − equal_weighted_score).
    A POSITIVE gap means the company is strong in a pillar the business model
    weights heavily — alignment. A NEGATIVE gap means the business model
    demands more from this pillar than the company currently has — the
    misalignment direction the DBI flags.
    """
    pillars = ("people", "process", "data", "technology")
    out = {}
    for p in pillars:
        try:
            s = float(scores.get(p, 0) or 0)
            w = float(weights.get(p, 0.25) or 0.25)
        except (TypeError, ValueError):
            s, w = 0.0, 0.25
        out[p] = round((w - 0.25) * s, 4)
    return out


def compute_decision_bottleneck_index(scores: dict, weights: dict) -> Optional[dict]:
    """Decision Bottleneck Index (DBI) — per the thesis.

    "The pillar with the largest gap between contextual score and
     equal-weighted score — identifies the dimension most misaligned
     relative to business model demands."

    The per-pillar contribution to (contextual − equal) is:

        gap_i = (w_i − 0.25) × score_i

    and  ∑ gap_i  ==  contextual_score − equal_weighted_score.

    The DBI is the pillar with the largest ABSOLUTE such gap. The signed
    `gap` field is exposed so the UI can describe direction:
      • gap > 0  → pillar contributes MORE to contextual than to equal
                   (the business model rewards this pillar and the company
                    has capability here — alignment-positive).
      • gap < 0  → pillar contributes LESS to contextual than to equal
                   (the business model de-emphasises this pillar, OR the
                    company has capability in a pillar that doesn't earn
                    full credit under the contextual weighting).
    """
    pillars = ("people", "process", "data", "technology")
    gaps = compute_pillar_contextual_gaps(scores, weights)
    if not any(abs(v) > 1e-9 for v in gaps.values()):
        return None  # equal weights — DBI is meaningless
    pillar = max(pillars, key=lambda p: abs(gaps[p]))
    g = gaps[pillar]
    return {
        "pillar": pillar,
        "gap": round(g, 4),
        "direction": "above-baseline" if g > 0 else "below-baseline",
        "gaps_by_pillar": gaps,
    }


def derive_contextual_weights(report_data: dict) -> Optional[dict]:
    """Return the final normalised pillar weights for the contextual score.

    Order of preference:
      1. Business-model lookup (+ optional unambiguous priority boost).
      2. LLM-supplied `contextual_weights` (or `weights_normalised` as legacy
         fallback).
    Returns ``None`` when no usable weight source is available — the caller
    then keeps the equal-weighted baseline as the contextual value.
    """
    pillars = ("people", "process", "data", "technology")
    bm = report_data.get("business_model")
    base = BUSINESS_MODEL_WEIGHTS.get(bm)

    if base is None:
        # Fall back to weights the LLM may have produced.
        for key in ("contextual_weights", "weights_normalised"):
            w = report_data.get(key)
            if isinstance(w, dict) and all(p in w for p in pillars):
                try:
                    total = sum(float(w[p]) for p in pillars)
                except (TypeError, ValueError):
                    continue
                if total > 0:
                    return {p: float(w[p]) / total for p in pillars}
        return None

    weights = dict(base)
    priority = (report_data.get("strategic_priority") or "").strip().lower()
    if priority and priority not in AMBIGUOUS_PRIORITY_TERMS:
        target = None
        for pillar, keywords in PRIORITY_PILLAR_MAP.items():
            if any(kw in priority for kw in keywords):
                target = pillar
                break
        if target:
            weights[target] += 0.05
            others = [p for p in weights if p != target]
            decrement = 0.05 / len(others) if others else 0
            for p in others:
                weights[p] -= decrement
            total = sum(weights.values()) or 1
            weights = {p: weights[p] / total for p in weights}
    return weights


# ---------------------------------------------------------------------------
# Client selection
# ---------------------------------------------------------------------------
_anthropic_client = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic  # type: ignore
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("chat_service: using direct Anthropic SDK (production mode)")
    except Exception as exc:  # pragma: no cover
        logger.warning("chat_service: anthropic SDK unavailable (%s), falling back to Emergent", exc)
        _anthropic_client = None


def _trim_history(history: list) -> list:
    return [
        {"role": m["role"], "content": m["content"]}
        for m in (history or [])
        if m.get("role") in ("user", "assistant") and m.get("content")
    ][-40:]


async def _call_anthropic_direct(system_message: str, history: list, user_message: str) -> str:
    messages = _trim_history(history)
    messages.append({"role": "user", "content": user_message})
    # anthropic SDK is sync; run in thread to keep the event loop unblocked.
    import asyncio
    def _do():
        return _anthropic_client.messages.create(
            model=CHAT_MODEL_NAME,
            max_tokens=MAX_TOKENS,
            system=system_message,
            messages=messages,
        )
    response = await asyncio.to_thread(_do)
    # Claude Sonnet 5 supports Extended Thinking and may return multiple content blocks:
    # - type="text" blocks contain the actual response text
    # - type="thinking" blocks contain reasoning (should be ignored for final output)
    # - type="redacted_thinking" blocks are safety-filtered (should be ignored)
    # Extract and join all text blocks, ignoring thinking blocks.
    text_blocks = [block.text for block in response.content if block.type == "text"]
    return "".join(text_blocks) if text_blocks else ""


async def _call_emergent(session_id: str, system_message: str, history: list, user_message: str) -> str:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    initial = [{"role": "system", "content": system_message}]
    initial.extend(_trim_history(history))
    chat = (
        LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message,
            initial_messages=initial,
        )
        .with_model(MODEL_PROVIDER, CHAT_MODEL_NAME)
        .with_params(max_tokens=MAX_TOKENS)
    )
    return await chat.send_message(UserMessage(text=user_message))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_system_prompt(base_prompt: str, assessment: dict) -> str:
    ctx = (
        f"\n\nCurrent Assessment Context:\n"
        f"Company: {assessment.get('company_name', 'Unknown')}\n"
        f"Industry: {assessment.get('company_industry', 'Unknown')}\n"
        f"Respondent: {assessment.get('respondent_name', 'Unknown')} "
        f"({assessment.get('respondent_role', 'Unknown')})\n"
        f"Current Phase: {assessment.get('current_phase', 'welcome')}\n"
    )
    return base_prompt + ctx


async def call_llm_with_history(
    *, session_id: str, system_message: str, history: list, user_message: str
) -> str:
    if _anthropic_client is not None:
        try:
            return await _call_anthropic_direct(system_message, history, user_message)
        except Exception as exc:
            # The user's own Claude key is primary. If it transiently fails
            # (rate limit, credit exhaustion, network) and an Emergent key is
            # available (preview env), fall back so the assessment still starts.
            if EMERGENT_LLM_KEY:
                logger.warning(
                    "chat_service: direct Anthropic call failed (%s); "
                    "falling back to Emergent Universal Key", exc,
                )
                return await _call_emergent(session_id, system_message, history, user_message)
            raise
    return await _call_emergent(session_id, system_message, history, user_message)


async def call_llm_greeting(*, session_id: str, system_message: str) -> str:
    greeting_prompt = "Please begin the assessment by introducing yourself and asking the first question."
    return await call_llm_with_history(
        session_id=session_id,
        system_message=system_message,
        history=[],
        user_message=greeting_prompt,
    )


# ---------------------------------------------------------------------------
# Report JSON extraction
# ---------------------------------------------------------------------------
def extract_report_json(response_text: str) -> Optional[dict]:
    """
    Pull the `ready_for_report: true` JSON block out of the assistant response.

    Tolerant of:
      - fenced ```json blocks (with or without trailing whitespace)
      - any-language fenced blocks
      - un-fenced JSON object after the closing prose
      - minor trailing chatter after the closing brace
    """
    if not response_text or "ready_for_report" not in response_text:
        return None

    # 1) fenced ```json ... ```
    fenced = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response_text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError as err:
            logger.error("JSON parse error in fenced json block: %s", err)

    # 2) any fenced block (no language tag)
    any_fenced = re.search(r"```\s*(\{[\s\S]*?\})\s*```", response_text, re.DOTALL)
    if any_fenced and "ready_for_report" in any_fenced.group(1):
        try:
            return json.loads(any_fenced.group(1))
        except json.JSONDecodeError as err:
            logger.error("JSON parse error in untagged fenced block: %s", err)

    # 3) un-fenced — find first '{' preceding 'ready_for_report' and balance braces.
    idx = response_text.find("ready_for_report")
    if idx == -1:
        return None
    start = response_text.rfind("{", 0, idx)
    if start == -1:
        return None
    depth = 0
    end = None
    in_str = False
    escape = False
    for i in range(start, len(response_text)):
        ch = response_text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError as err:
            logger.error("JSON parse error in unfenced block: %s", err)
    return None


def normalise_business_model(report_data: dict) -> dict:
    raw = (report_data.get("business_model") or "").strip()
    if raw in VALID_BUSINESS_MODELS:
        return report_data
    upper = raw.upper()
    picked = None
    for m in MODEL_COMPLEXITY_ORDER:
        if m.upper() in upper:
            picked = m
            break
    if picked is None:
        return report_data
    report_data["business_model_raw"] = raw or None
    report_data["business_model"] = picked
    report_data["business_model_note"] = (
        f"Primary business model: {picked} (respondent indicated: {raw or 'unspecified'})"
    )
    return report_data


def recompute_dual_scores(report_data: dict) -> dict:
    """Make the dual-score invariants hold regardless of what the LLM emitted.

    Invariants enforced here (and asserted by tests):
      • equal_weighted_score  ==  simple average of the 4 pillar scores
                                  (academically validated 25%/25%/25%/25%
                                  baseline — never overridden by the LLM).
      • scores.overall        ==  equal_weighted_score
                                  (this is the primary score surfaced on
                                  the cover page and in dashboard rows).
      • contextual_score      ==  weighted sum using the business-model
                                  weight table (+ optional unambiguous
                                  priority boost). Recomputed deterministically
                                  if the LLM omitted it; otherwise the LLM
                                  value is retained (it captures the priority
                                  boost nuance).

    The contextual score is intentionally left distinct from the equal
    baseline: they may be numerically equal (unknown business model, or
    rare coincidence) but the LABELS must always remain separate. UI and
    PDF code both follow this contract.
    """
    scores = report_data.get("scores") or {}
    pillars = ["people", "process", "data", "technology"]
    try:
        pillar_scores = {p: float(scores.get(p, 0) or 0) for p in pillars}
    except (TypeError, ValueError):
        return report_data

    # ── Equal-weighted score: simple average, ALWAYS recomputed.
    eq_mean = round(sum(pillar_scores.values()) / 4.0, 1)
    report_data["equal_weighted_score"] = eq_mean

    # scores.overall mirrors the equal-weighted baseline (primary view).
    scores["overall"] = eq_mean
    report_data["scores"] = scores

    # ── Contextual score: prefer LLM-emitted value, else recompute from
    # business-model weight table. If the LLM duplicated the equal-weighted
    # value into the contextual slot for a known business model, treat it as
    # missing and recompute.
    try:
        ctx_raw = report_data.get("contextual_score")
        ctx_value = float(ctx_raw) if ctx_raw is not None else None
    except (TypeError, ValueError):
        ctx_value = None

    bm = report_data.get("business_model")
    weights = derive_contextual_weights(report_data)

    # Detect the "LLM lazily copied the equal-weighted value" case for known
    # business models and force a recomputation.
    if (
        ctx_value is not None
        and weights is not None
        and bm in BUSINESS_MODEL_WEIGHTS
        and round(ctx_value, 1) == round(eq_mean, 1)
    ):
        ctx_value = None

    if ctx_value is None and weights is not None:
        ctx_value = sum(pillar_scores[p] * weights[p] for p in pillars)

    if ctx_value is not None:
        report_data["contextual_score"] = round(float(ctx_value), 2)

    # Expose the final normalised contextual weights so the dashboard/PDF can
    # show the row used for the calculation.
    if weights is not None:
        report_data["contextual_weights"] = {
            p: round(weights[p], 4) for p in pillars
        }
        # Decision Bottleneck Index — per thesis (Section: DBI).
        # Per-pillar contribution gaps + the pillar with the largest absolute
        # gap. These are deterministic functions of `scores` + `weights`, so
        # we always recompute them rather than trusting an LLM-supplied value.
        gaps = compute_pillar_contextual_gaps(pillar_scores, weights)
        report_data["pillar_contextual_gaps"] = gaps
        dbi = compute_decision_bottleneck_index(pillar_scores, weights)
        if dbi is not None:
            report_data["decision_bottleneck_index"] = dbi

    return report_data


# ---------------------------------------------------------------------------
# 90-day projection — deterministic recomputation (Part 1C)
# ---------------------------------------------------------------------------
# The projection MUST derive from the SAME Phase-1 ("immediate") expected_gain
# values used in the roadmap, and score_current MUST equal the overall
# equal-weighted score shown on page 1. We recompute both here so the two
# sections can never drift apart, regardless of what the LLM emitted.

_MATURITY_LEVELS = ["Ad Hoc", "Developing", "Defined", "Managed", "Predictive"]


def _band_from_score(score: float) -> int:
    """Map a maturity score to its 0-4 level band (mirrors pdf_builder)."""
    try:
        n = float(score)
    except (TypeError, ValueError):
        return 0
    if n < 1.5:
        return 0
    if n < 2.5:
        return 1
    if n < 3.5:
        return 2
    if n < 4.5:
        return 3
    return 4


def _shift_level(current_level: str, delta_bands: int) -> str:
    """Move a level label up/down by `delta_bands`, keeping the authoritative
    current label as the anchor so it always matches the rest of the report."""
    cur = (current_level or "").strip().lower()
    idx = next(
        (i for i, lvl in enumerate(_MATURITY_LEVELS) if lvl.lower() == cur),
        None,
    )
    if idx is None:
        return current_level or ""
    new_idx = max(0, min(len(_MATURITY_LEVELS) - 1, idx + delta_bands))
    return _MATURITY_LEVELS[new_idx]


def _parse_expected_gain(text: str) -> dict:
    """Parse 'People: 2.0 -> 2.5 | Process: 1.5 -> 2.5 | ...' into
    {pillar: (start, end)}. Tolerant of '->', '→' and 'to' separators."""
    result: dict = {}
    if not text or not isinstance(text, str):
        return result
    pattern = re.compile(
        r"(people|process|data|technology)\s*:\s*([\d.]+)\s*(?:->|\u2192|to)\s*([\d.]+)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        try:
            result[m.group(1).lower()] = (float(m.group(2)), float(m.group(3)))
        except (TypeError, ValueError):
            continue
    return result


def recompute_ninety_day_projection(report_data: dict) -> dict:
    """Force the 90-day projection to agree with page-1 overall + Phase-1 roadmap.

    Invariants:
      • score_current            == equal_weighted_score (page-1 overall).
      • score_projected          == equal-weighted average of the Phase-1
                                    ("immediate") expected_gain END values,
                                    capped at +0.8 (Mandatory Rule 5).
      • score_delta              == score_projected - score_current.
      • bottleneck_level_current == level_names[bottleneck_pillar] (authoritative).
      • bottleneck_level_projected derived from the Phase-1 END score of the
        bottleneck pillar, shifted from the authoritative current level.
    """
    pillars = ["people", "process", "data", "technology"]
    scores = report_data.get("scores") or {}
    eq = report_data.get("equal_weighted_score")
    if eq is None:
        eq = scores.get("overall")
    if eq is None:
        return report_data

    proj = report_data.get("ninety_day_projection")
    if not isinstance(proj, dict):
        proj = {}
        report_data["ninety_day_projection"] = proj

    try:
        current = round(float(eq), 1)
    except (TypeError, ValueError):
        return report_data
    proj["score_current"] = current

    roadmap = report_data.get("roadmap") or {}
    immediate = roadmap.get("immediate") if isinstance(roadmap, dict) else None
    gains = {}
    if isinstance(immediate, dict):
        gains = _parse_expected_gain(immediate.get("expected_gain", ""))

    end_scores = {}
    for p in pillars:
        try:
            cur_p = float(scores.get(p, 0) or 0)
        except (TypeError, ValueError):
            cur_p = 0.0
        end_scores[p] = gains[p][1] if p in gains else cur_p

    projected = round(sum(end_scores.values()) / 4.0, 1)
    if projected - current > 0.8:
        projected = round(current + 0.8, 1)
    if projected < current:
        projected = current
    proj["score_projected"] = projected
    proj["score_delta"] = round(projected - current, 1)

    bottleneck = (report_data.get("bottleneck_pillar") or "").strip().lower()
    level_names = report_data.get("level_names") or {}
    if bottleneck in pillars:
        cur_level = level_names.get(bottleneck) or proj.get("bottleneck_level_current") or ""
        proj["bottleneck_level_current"] = cur_level
        try:
            cur_pillar_score = float(scores.get(bottleneck, 0) or 0)
        except (TypeError, ValueError):
            cur_pillar_score = 0.0
        end_pillar_score = end_scores.get(bottleneck, cur_pillar_score)
        delta_bands = _band_from_score(end_pillar_score) - _band_from_score(cur_pillar_score)
        proj["bottleneck_level_projected"] = _shift_level(cur_level, delta_bands)

    return report_data


def normalise_report_weights(report_data: dict) -> dict:
    if not report_data.get("weights_raw"):
        report_data["weights_raw"] = {"people": 5, "process": 5, "data": 5, "technology": 5}
    if not report_data.get("weights_normalised"):
        raw = report_data["weights_raw"]
        total = sum(raw.values()) or 1
        report_data["weights_normalised"] = {k: round(v / total, 4) for k, v in raw.items()}
    normalise_business_model(report_data)
    recompute_dual_scores(report_data)
    recompute_ninety_day_projection(report_data)
    return report_data
