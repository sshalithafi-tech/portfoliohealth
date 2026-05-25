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
MODEL_NAME = "claude-sonnet-4-5-20250929"
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

# Multi-pillar / vague priorities that must NOT trigger a boost.
AMBIGUOUS_PRIORITY_TERMS = {
    "portfolio simplification",
    "profitability improvement",
    "complexity reduction",
    "digital transformation",
    "innovation",
    "growth",
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
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            system=system_message,
            messages=messages,
        )
    response = await asyncio.to_thread(_do)
    return response.content[0].text


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
        .with_model(MODEL_PROVIDER, MODEL_NAME)
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
        return await _call_anthropic_direct(system_message, history, user_message)
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
    return report_data
