"""
Parallel report-section generation (performance refactor).

Replaces the old single monolithic "emit the entire 14-section report in one
LLM call" approach with:

  1. A SEED call (unchanged conversational flow in server.py's PPDT_SYSTEM_PROMPT
     + chat_service.call_llm_with_history) that now emits only raw facts +
     pillar scores instead of the full report (fast — short prose + small JSON).
  2. Three CONCURRENT specialist calls (this module, `asyncio.gather`), each
     producing only the JSON fields for its assigned report sections:
       Call A -> Sections 1-7  (Context, Overall Maturity, Pillar Levels,
                                 Dimension Scores, Weighted Calculation,
                                 Bottleneck, Governance)
       Call B -> Sections 8-12 (Management Commitment, Assessment Reliability,
                                 Decision-Type Vulnerability, Key Findings &
                                 Critical Gaps, Improvement Roadmap)
       Call C -> Section 13    (Benchmark & Consultant's Note)
                                 Section 14 (Academic References) is already
                                 100% static in pdf_builder.py — no LLM needed.
  3. A deterministic merge back into the EXACT same report schema used before
     this refactor (no field renamed, no field dropped, no section reordered).

Does NOT touch scoring logic, DBI computation, or business-model weights —
`chat_service.normalise_report_weights` (unchanged) still runs on the merged
result, exactly as it did on the old single-call output.

Prompt caching (Anthropic `cache_control`): the static instruction blocks
below are marked as cacheable content blocks when the direct Anthropic SDK
path is available (ANTHROPIC_API_KEY configured). Only the dynamic block
(confirmed facts + transcript, different per assessment) is uncached. When
only the Emergent Universal Key is configured (no direct Anthropic key), the
calls still run fully concurrently (Fix 1 benefit) but without the caching
discount (Fix 2 is dormant on that path — emergentintegrations' generic
wrapper has no cache_control support).
"""
import asyncio
import json
import logging
import os
import re
from typing import Optional

import chat_service  # reuse the existing Anthropic/Emergent client plumbing

logger = logging.getLogger(__name__)

MODEL_NAME = "claude-sonnet-4-5-20250929"  # report-generation model — intentionally
# independent of chat_service.CHAT_MODEL_NAME so upgrading the assessment
# chat model never silently changes the report-generation model.

MAX_TOKENS_A = 4500
MAX_TOKENS_B = 6000
MAX_TOKENS_C = 1500

# ---------------------------------------------------------------------------
# Static, cacheable instruction blocks — verbatim subsets of the original
# monolithic PPDT_SYSTEM_PROMPT (server.py), reused unchanged so the model's
# grounding/wording doesn't drift from the earlier single-call version.
# ---------------------------------------------------------------------------

_SPECIALIST_PERSONA = """You are a report-writing specialist for PortfolioHealth Advisor, a PPM (product portfolio management) capability maturity assessment tool built on the PPDT framework (People, Process, Data, Technology \u2014 Hannila's doctoral research, University of Oulu).

You are given: (1) the full completed assessment conversation transcript, and (2) a set of already-confirmed facts (business model, pillar scores, bottleneck pillar, etc.) extracted from that conversation. Your ONLY job is to generate the specific JSON fields listed in the schema below \u2014 grounded in the transcript, consistent with the confirmed facts. Do not re-derive or contradict the confirmed facts provided to you. Do not emit any field that is not in the schema below.

Respond with ONLY a single fenced ```json code block containing exactly the fields in the schema. No prose before or after. No markdown outside the code block."""

_PILLAR_THEORY = """PILLAR DEFINITIONS & SCORING SIGNALS

PEOPLE \u2014 Covers roles, responsibilities, skills, and governance ownership.
- Level 1: No defined PPM roles; decisions made ad hoc by whoever is available
- Level 2: Informal ownership; individuals carry knowledge not captured in systems
- Level 3: Defined roles with some cross-functional accountability
- Level 4: Formal data ownership per domain; governance participation is structured
- Level 5: Accountability is embedded in KPIs; succession-proof governance

PROCESS \u2014 Covers formal review cycles, change control, decision traceability.
- Level 1: No formal review cycles; changes made verbally or via email
- Level 2: Some recurring meetings, but no audit trail or structured agenda
- Level 3: Formal change control exists; PLM-ERP integration underway or active
- Level 4: Portfolio reviews are scheduled, minuted, and traceable; stage-gate enforced
- Level 5: Fully automated workflow triggers; decisions reconstructable end-to-end

DATA \u2014 The most common bottleneck. Covers data quality, accessibility, consistency.
- Level 1: Data lives in personal spreadsheets and email threads
- Level 2: Departmental data exists but is siloed; no single product-level view
- Level 3: Centralised data repository; product-level profitability retrievable
- Level 4: Data quality SLAs defined; master data governance enforced
- Level 5: Real-time, trusted, automated data feeds into portfolio decisions

TECHNOLOGY \u2014 Covers tools used for portfolio decisions \u2014 not just tool ownership.
- Level 1: Excel only; no integrated tools
- Level 2: Departmental tools (CRM, ERP) used in isolation
- Level 3: Some integration between systems; PLM or ERP used for portfolio views
- Level 4: Enterprise-wide integrated platform supports portfolio decision-making
- Level 5: AI-assisted analytics; scenario modelling; automated lifecycle alerts

EXACT MATURITY LEVEL NAMES (use these identically \u2014 no paraphrasing):
- LEVEL 1 \u2014 AD HOC
- LEVEL 2 \u2014 DEVELOPING
- LEVEL 3 \u2014 DEFINED
- LEVEL 4 \u2014 MANAGED
- LEVEL 5 \u2014 PREDICTIVE

DATA-FIRST RULE: If Data scores below 3.0, flag this as a critical blocker regardless of other pillar scores. Data at Level 1\u20132 means portfolio decisions are based on incomplete or unreliable information \u2014 this overrides any technology investment already made.

BOTTLENECK PRINCIPLE: The four pillars are interdependent. A weakness in any one pillar acts as a ceiling on overall portfolio capability. You cannot compensate for a weak Data pillar with a strong Technology pillar.

BOTTLENECK CAPPING RULE: If the lowest pillar score is 1.0 or more below the calculated overall average, the narrative interpretation must be capped at the bottleneck pillar's level \u2014 not the average. Example: Overall = 3.3, but Data = 2.0 \u2192 narrative is capped at DEVELOPING, not DEFINED. Name this explicitly."""

_SCORING_WEIGHTS = """CONTEXTUAL SCORING \u2014 BUSINESS MODEL WEIGHTS (for reference only; the final weighted numbers are recomputed deterministically by the backend \u2014 you may narrate them but do not need to compute exact figures)

  Business Model  | People | Process | Data | Technology
  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  ETO             |  35%   |  30%    | 20%  |   15%
  CETO            |  25%   |  30%    | 25%  |   20%
  CTO             |  20%   |  25%    | 30%  |   25%
  Standard        |  15%   |  30%    | 35%  |   20%
  Bulk            |  10%   |  35%    | 20%  |   35%

These weights are derived from the CODP (Customer Order Decoupling Point) framework (Haug, Ladeby & Edwards, 2009; Wikner & Rudberg, 2004) and corroborated by Hannila, Salonen & Vierimaa (2024), Tolonen et al. (2014, 2015), Trentin et al. (2022), and Hannila et al. (2020) \u2014 a peer-reviewed, thesis-grounded design choice, not a heuristic."""

_MANDATORY_RULE_4 = """MANDATORY RULE \u2014 FAILURE PATTERN SELECTION

`failure_pattern_name` MUST be selected based on the confirmed bottleneck pillar:

  \u2022 People bottleneck    \u2192 "Silent Knowledge Risk"
  \u2022 Process bottleneck   \u2192 "Salami Effect"
  \u2022 Data bottleneck      \u2192 use judgment:
      - If Process \u2265 Level 3 AND the data gap is in the predictive/foresight layer (forward-looking KPIs, portfolio scenarios, renewal signals) \u2192 "Business Case Validity Risk"
      - If Process < Level 3 OR Technology < Level 3, AND the gap is in the visibility layer (product profitability, master data, integrated dashboards) \u2192 "Hidden Maintenance Cost"
  \u2022 Technology bottleneck \u2192 "Technology Misattribution Risk"

`failure_pattern_narrative` MUST be exactly 3 sentences, no academic language, following this order:
  Sentence 1 \u2014 what is operationally happening NOW as a result of the bottleneck.
  Sentence 2 \u2014 which portfolio decision type is most at risk and why.
  Sentence 3 \u2014 what capability the organisation is MISSING as a result.

Do NOT exceed 3 sentences under any circumstance.

CLIENT-SPECIFIC EVIDENCE (non-optional): the pattern NAME and 3-sentence structure come from the library above, but the supporting detail MUST incorporate at least one specific fact drawn from THIS respondent's own answers in the transcript \u2014 a named system, a named decision, or a named event (e.g. "the Windchill-to-SAP handoff"). Never rely solely on the generic library description."""

_MANDATORY_RULE_5 = """MANDATORY RULE \u2014 90-DAY PROJECTION

`ninety_day_projection.what_becomes_possible` MUST be framed in the client's stated `primary_performance_metric` (supplied to you as a confirmed fact). If none was stated, default to portfolio-margin framing.

`ninety_day_projection.score_projected` MUST NEVER exceed a 0.8-point gain over `score_current` (the confirmed overall score) within the 90-day window. If your best-case realistic projection is smaller, use the smaller number \u2014 do not inflate.

`ninety_day_projection.comparable_outcome` MUST reference a named outcome type sourced to interview evidence or published literature. NEVER invent a percentage or timeframe without a source."""

_WRITING_STYLE_A = """WRITING STYLE (applies to all fields you emit)

- Default sentence length is 15-20 words. Break any sentence exceeding 30 words into two sentences.
- `pillar_interpretations` (long form): cap at 5 sentences per pillar. Structure as 3 short labelled clauses: (1) what's working, (2) what's the gap, (3) why this score.
- `pillar_interpretation_short`: max 2 short sentences per pillar (<= 40 words total), generated independently \u2014 do NOT truncate or copy `pillar_interpretations`. Zero citations, zero precondition numbers.
- `governance_signal_summary`: 3-4 plain-language bullets, each under 15 words, zero citations, zero precondition numbers.
- CITATIONS: remove ALL inline citation parentheticals (e.g. "(Precondition 3: ...)", "(Hannila et al., 2020)") from `failure_pattern_narrative`, `pillar_interpretation_short`, `governance_signal_summary`, `financial_consequence`, `ninety_day_projection`. Citations are not permitted in any field you generate."""

_PRECONDITIONS_LIST = """THE FIVE PRECONDITIONS (Hannila et al. 2020, Hannila 2019) \u2014 use only these, numbered exactly:

  Precondition 1: Mutual understanding of products and a consistent commercial and technical product structure
  Precondition 2: Product classification into strategic, supportive, and non-strategic categories
  Precondition 3: A holistic, corporate-level data model that connects master data to key business processes
  Precondition 4: Data governance practices ensuring data quality, data ownership, and data accessibility
  Precondition 5: Business IT systems adapted to support real-time visualisation and analysis of the product portfolio

Precondition keys for `first_action.preconditions_met`:
  p1_product_structure       \u2014 mutual understanding of company products
  p2_product_classification  \u2014 commercial + technical product structure and strategic classification
  p3_data_model              \u2014 holistic corporate-level data model
  p4_data_governance          \u2014 data governance and business IT ownership
  p5_business_it             \u2014 business IT support (systems able to surface a live portfolio view)"""

_MANDATORY_RULE_1 = """MANDATORY RULE \u2014 PRECONDITION LABELLING IN critical_gaps

Every item in the `critical_gaps` array MUST end with a precondition label in this exact format:
  (Precondition N: [name])

If a single gap spans two preconditions, cite both, e.g. `(Precondition 3 & 4: holistic data model and data governance)`. No gap may be written without this label.

Example: "Product master data is fragmented across SAP, Salesforce and spreadsheets; no single source of truth for portfolio decisions (Precondition 3: holistic, corporate-level data model)." """

_MANDATORY_RULE_2 = """MANDATORY RULE \u2014 SCORE TRAJECTORY IN ROADMAP PHASES

Each of the three roadmap phases (`roadmap.immediate`, `roadmap.short_term`, `roadmap.strategic`) MUST include an `expected_gain` field showing score deltas for all four pillars in this exact format:

  People: X.X \u2192 X.X | Process: X.X \u2192 X.X | Data: X.X \u2192 X.X | Technology: X.X \u2192 X.X

Rules of continuity:
- Phase 1 (`immediate`) starting values MUST equal the confirmed assessed pillar scores supplied to you.
- Each phase's end value MUST equal the next phase's start value (no gaps, no resets).
- All four pillars MUST appear in every phase, even with no movement (write "3.0 \u2192 3.0").
- Use one decimal place. Use the arrow character "\u2192" (not "->" or "to")."""

_MANDATORY_RULE_3 = """MANDATORY RULE \u2014 COOPER STAGE-GATE REFERENCE (conditional)

  (3a) When `decision_vulnerability_ratings.new_launch` is rated "High" or "Critical", the `decision_vulnerability` prose field MUST include this exact sentence, verbatim, once:
       "Where new product launch governance is absent or immature, a formal Stage-Gate intake process (Cooper, Edgett & Kleinschmidt, 2001) provides structured go/kill criteria at each development gate, directly addressing Process pillar gaps."

  (3b) When the confirmed Process pillar score is below 3.0, the `roadmap.short_term.actions` field MUST include this exact sentence, verbatim, once:
       "Introduce a lightweight Stage-Gate intake process for new launches (Cooper et al., 2001), applying strategic fit, value maximisation, and portfolio balance as the three gate criteria to anchor new launch decisions to portfolio strategy."

If a trigger condition does not apply, do NOT insert that sentence."""

_MANDATORY_RULE_6 = """MANDATORY RULE \u2014 PRECONDITIONS STATUS

`first_action.preconditions_met` MUST be populated for all five preconditions based on conversational evidence:
  \u2022 "met"      \u2014 clear evidence the precondition is functioning today.
  \u2022 "partial"  \u2014 some evidence exists but with gaps, inconsistencies, or manual workarounds.
  \u2022 "not met"  \u2014 clear evidence the precondition is absent.

If evidence is insufficient, default to "partial" AND note the evidence gap in `critical_gaps` using the Rule 1 labelling format."""

_MANAGEMENT_COMMITMENT_DEF = """MANAGEMENT COMMITMENT \u2014 assessed separately as Low / Medium / High.
- Low: PPM is discussed but not resourced or enforced from leadership
- Medium: Some executive sponsorship; inconsistent follow-through
- High: PPM has board-level visibility; dedicated budget and accountability

Management Commitment acts as a multiplier. High capability scores with Low commitment signal capability that exists on paper but not in practice."""

_WRITING_STYLE_B = """WRITING STYLE (applies to all fields you emit)

- Default sentence length is 15-20 words. Break any sentence exceeding 30 words into two sentences.
- Each roadmap `action_summary`: ONE sentence (<= 25 words), no citations \u2014 distinct from the detailed `actions` field.
- CITATIONS: `critical_gaps`, `decision_vulnerability`, and `roadmap.*.actions` MAY include citations/precondition labels (these map to the Academic Framework & References section). `key_findings` and each roadmap `action_summary` must NOT include citations."""

_WRITING_STYLE_C = """WRITING STYLE (applies to all fields you emit)

- `consultant_note`: the flagship long-form section \u2014 rich and narrative, but capped at 250 words maximum. Stay premium, not sprawling. May include citations (e.g. "(Hannila et al., 2020)", "(Cooper et al., 2001)") \u2014 this maps to the Academic Framework & References section.
- `benchmark_context`: 1-2 sentences, may include citations."""


def _facts_block(seed: dict) -> str:
    """Render the confirmed seed facts as a compact block for the dynamic
    (non-cached) part of each specialist prompt."""
    scores = seed.get("scores") or {}
    lines = [
        f"Company: {seed.get('company_name', 'Unknown')}",
        f"Industry: {seed.get('industry', 'Unknown')}",
        f"Business model: {seed.get('business_model', 'Unknown')}",
        f"Strategic priority: {seed.get('strategic_priority', 'Unknown')}",
        f"Company size: {seed.get('company_size', 'Unknown')}",
        f"Active products: {seed.get('active_products', 'Unknown')}",
        f"Primary performance metric: {seed.get('primary_performance_metric', '')}",
        f"R&D budget band: {seed.get('rd_budget_band', 'not stated')}",
        f"Anchor decision type: {seed.get('anchor_decision_type', 'none stated')}",
        f"Anchor decision note: {seed.get('anchor_decision_note', '')}",
        f"Active product definition clarity: {seed.get('active_product_definition_clarity', 'not stated')}",
        f"CONFIRMED SCORES \u2014 People: {scores.get('people')}, Process: {scores.get('process')}, "
        f"Data: {scores.get('data')}, Technology: {scores.get('technology')}, Overall: {scores.get('overall')}",
        f"CONFIRMED bottleneck pillar: {seed.get('bottleneck_pillar', 'Unknown')}",
    ]
    return "\n".join(lines)


def _transcript_text(chat_history: list) -> str:
    lines = []
    for m in (chat_history or []):
        role = "Respondent" if m.get("role") == "user" else "PortfolioHealth Advisor"
        content = (m.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n\n".join(lines)


async def _call_specialist(*, static_block: str, dynamic_block: str, schema_block: str, max_tokens: int) -> str:
    """Call the LLM for one specialist section.

    Uses the direct Anthropic SDK with prompt caching (`cache_control`) on the
    static block when ANTHROPIC_API_KEY is configured (production path).
    Falls back to the Emergent Universal Key (no caching, still concurrent)
    when it is not.
    """
    user_content = (
        f"{dynamic_block}\n\n"
        f"JSON SCHEMA \u2014 emit ONLY these fields, wrapped in a single fenced ```json code block:\n\n"
        f"```json\n{schema_block}\n```"
    )

    if chat_service._anthropic_client is not None:
        def _do():
            return chat_service._anthropic_client.messages.create(
                model=MODEL_NAME,
                max_tokens=max_tokens,
                system=[
                    {"type": "text", "text": static_block, "cache_control": {"type": "ephemeral"}},
                ],
                messages=[{"role": "user", "content": user_content}],
            )
        response = await asyncio.to_thread(_do)
        # Defensive: extract only text blocks (some Claude models may return
        # additional non-text content blocks, e.g. thinking blocks).
        text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "".join(text_blocks) if text_blocks else ""

    # Emergent fallback \u2014 no cache_control support, still runs concurrently.
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    session_id = f"report-section-{os.urandom(6).hex()}"
    chat = (
        LlmChat(
            api_key=chat_service.EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=static_block,
        )
        .with_model("anthropic", MODEL_NAME)
        .with_params(max_tokens=max_tokens)
    )
    return await chat.send_message(UserMessage(text=user_content))


def _extract_json_block(text: str) -> Optional[dict]:
    if not text:
        return None
    fenced = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if not candidate:
        any_fenced = re.search(r"```\s*(\{[\s\S]*?\})\s*```", text, re.DOTALL)
        candidate = any_fenced.group(1) if any_fenced else None
    if not candidate:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        logger.error("report_sections: JSON parse error: %s", exc)
        return None


async def _call_specialist_with_retry(*, label: str, static_block: str, dynamic_block: str,
                                       schema_block: str, max_tokens: int, attempts: int = 2) -> Optional[dict]:
    """Call one specialist section, retrying once (fresh call, no cache of
    the failure) if the response isn't parseable JSON \u2014 LLM output is
    occasionally malformed (stray comma, unescaped quote). Cheap to retry
    since each specialist call is small/fast relative to the old monolithic
    call. Returns None only if every attempt fails.
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            text = await _call_specialist(static_block=static_block, dynamic_block=dynamic_block,
                                           schema_block=schema_block, max_tokens=max_tokens)
        except Exception as exc:
            last_error = exc
            logger.error("report_sections: call %s attempt %d/%d raised: %s", label, attempt, attempts, exc)
            continue
        parsed = _extract_json_block(text)
        if parsed:
            if attempt > 1:
                logger.info("report_sections: call %s succeeded on retry attempt %d", label, attempt)
            return parsed
        last_error = "no parseable JSON in response"
        logger.warning("report_sections: call %s attempt %d/%d returned unparseable JSON", label, attempt, attempts)
    logger.error("report_sections: call %s failed after %d attempts (last error: %s)", label, attempts, last_error)
    return None


# ---------------------------------------------------------------------------
# Schema fragments for each concurrent call (verbatim field shapes from the
# original monolithic schema \u2014 no field renamed, no field dropped).
# ---------------------------------------------------------------------------

_SCHEMA_A = """{
  "equal_weighted_score": 0.0,
  "contextual_score": 0.0,
  "contextual_weights": { "people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25 },
  "weights_raw": { "people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25 },
  "weights_normalised": { "people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25 },
  "level_names": {
    "people": "Ad Hoc | Developing | Defined | Managed | Predictive",
    "process": "...",
    "data": "...",
    "technology": "...",
    "overall": "..."
  },
  "dimension_summaries": { "people": "...", "process": "...", "data": "...", "technology": "..." },
  "pillar_interpretations": { "people": "...", "process": "...", "data": "...", "technology": "..." },
  "pillar_interpretation_short": { "people": "...", "process": "...", "data": "...", "technology": "..." },
  "failure_pattern_name": "Silent Knowledge Risk | Salami Effect | Business Case Validity Risk | Hidden Maintenance Cost | Technology Misattribution Risk",
  "failure_pattern_narrative": "Exactly 3 sentences.",
  "financial_consequence": {
    "cost_category": "Named cost category tied to the bottleneck AND business model. Never invent a monetary figure.",
    "consequence_narrative": "2-3 sentences. No fabricated numbers or percentages.",
    "metric_framing": "One sentence mapping to primary_performance_metric."
  },
  "ninety_day_projection": {
    "score_current": 0.0,
    "score_projected": 0.0,
    "score_delta": 0.0,
    "bottleneck_level_current": "Ad Hoc | Developing | Defined | Managed | Predictive",
    "bottleneck_level_projected": "Ad Hoc | Developing | Defined | Managed | Predictive",
    "what_becomes_possible": "Exactly 2 sentences.",
    "comparable_outcome": "Named outcome type sourced to interview evidence or published literature."
  },
  "governance_observations": { "people": "...", "process": "...", "data": "...", "technology": "..." },
  "governance_assessment": "...",
  "governance_signal_summary": ["...", "...", "..."]
}"""

_SCHEMA_B = """{
  "management_commitment": "Low | Medium | High",
  "management_commitment_assessment": "...",
  "assessment_reliability": {
    "confidence": "High | Medium | Low",
    "factors": [
      {"label": "Data Availability", "detail": "...", "tone": "high | medium | low"},
      {"label": "Respondent Scope", "detail": "...", "tone": "high | medium | low"},
      {"label": "Answer Clarity", "detail": "...", "tone": "high | medium | low"}
    ]
  },
  "decision_vulnerability_ratings": {
    "discontinuation": "Low | Medium | High | Critical",
    "new_launch": "Low | Medium | High | Critical",
    "product_change": "Low | Medium | High | Critical",
    "portfolio_investment": "Low | Medium | High | Critical"
  },
  "decision_vulnerability": "...",
  "key_findings": ["...", "...", "...", "...", "..."],
  "critical_gaps": ["... (Precondition N: name)", "... (Precondition N: name)", "... (Precondition N: name)"],
  "roadmap": {
    "immediate": {
      "action_summary": "...", "actions": "...", "pillar_focus": "...",
      "governance_milestone": "...", "management_required": "...",
      "expected_gain": "People: X.X \u2192 X.X | Process: X.X \u2192 X.X | Data: X.X \u2192 X.X | Technology: X.X \u2192 X.X",
      "timeframe": "0\u20133 months"
    },
    "short_term": {
      "action_summary": "...", "actions": "...", "pillar_focus": "...",
      "governance_milestone": "...", "management_required": "...",
      "expected_gain": "People: X.X \u2192 X.X | Process: X.X \u2192 X.X | Data: X.X \u2192 X.X | Technology: X.X \u2192 X.X",
      "timeframe": "3\u201312 months"
    },
    "strategic": {
      "action_summary": "...", "actions": "...", "pillar_focus": "...",
      "governance_milestone": "...", "management_required": "...",
      "expected_gain": "People: X.X \u2192 X.X | Process: X.X \u2192 X.X | Data: X.X \u2192 X.X | Technology: X.X \u2192 X.X",
      "timeframe": "12+ months"
    }
  },
  "first_action": {
    "headline": "6\u201310 word imperative",
    "description": "2\u20133 sentences.",
    "expected_outcome": "One sentence.",
    "who_owns_it": "Role titles only. No named individuals.",
    "time_to_implement": "e.g. 2\u20134 weeks",
    "preconditions_met": {
      "p1_product_structure": "met | partial | not met",
      "p2_product_classification": "met | partial | not met",
      "p3_data_model": "met | partial | not met",
      "p4_data_governance": "met | partial | not met",
      "p5_business_it": "met | partial | not met"
    }
  }
}"""

_SCHEMA_C = """{
  "benchmark_context": "...",
  "consultant_note": "..."
}"""

_ALLOWED_KEYS_A = {
    "equal_weighted_score", "contextual_score", "contextual_weights", "weights_raw", "weights_normalised",
    "level_names", "dimension_summaries", "pillar_interpretations", "pillar_interpretation_short",
    "failure_pattern_name", "failure_pattern_narrative", "financial_consequence",
    "ninety_day_projection", "governance_observations", "governance_assessment", "governance_signal_summary",
}
_ALLOWED_KEYS_B = {
    "management_commitment", "management_commitment_assessment", "assessment_reliability",
    "decision_vulnerability_ratings", "decision_vulnerability", "key_findings", "critical_gaps",
    "roadmap", "first_action",
}
_ALLOWED_KEYS_C = {"benchmark_context", "consultant_note"}

# Fallback defaults so the merged report ALWAYS has every field from the
# original schema, even if a specialist call fails every retry (network
# error, persistently malformed JSON, etc). Keeps the schema contract intact
# for pdf_builder.py / normalise_report_weights / the frontend.
_FIELD_DEFAULTS = {
    "equal_weighted_score": 0.0,
    "contextual_score": 0.0,
    "contextual_weights": {"people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25},
    "weights_raw": {"people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25},
    "weights_normalised": {"people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25},
    "level_names": {"people": "", "process": "", "data": "", "technology": "", "overall": ""},
    "dimension_summaries": {"people": "", "process": "", "data": "", "technology": ""},
    "pillar_interpretations": {"people": "", "process": "", "data": "", "technology": ""},
    "pillar_interpretation_short": {"people": "", "process": "", "data": "", "technology": ""},
    "failure_pattern_name": "",
    "failure_pattern_narrative": "",
    "financial_consequence": {"cost_category": "", "consequence_narrative": "", "metric_framing": ""},
    "ninety_day_projection": {
        "score_current": 0.0, "score_projected": 0.0, "score_delta": 0.0,
        "bottleneck_level_current": "", "bottleneck_level_projected": "",
        "what_becomes_possible": "", "comparable_outcome": "",
    },
    "governance_observations": {"people": "", "process": "", "data": "", "technology": ""},
    "governance_assessment": "",
    "governance_signal_summary": [],
    "management_commitment": "Medium",
    "management_commitment_assessment": "",
    "assessment_reliability": {"confidence": "Medium", "factors": []},
    "decision_vulnerability_ratings": {"discontinuation": "Medium", "new_launch": "Medium",
                                       "product_change": "Medium", "portfolio_investment": "Medium"},
    "decision_vulnerability": "",
    "key_findings": [],
    "critical_gaps": [],
    "roadmap": {
        "immediate": {"action_summary": "", "actions": "", "pillar_focus": "", "governance_milestone": "",
                      "management_required": "", "expected_gain": "", "timeframe": "0\u20133 months"},
        "short_term": {"action_summary": "", "actions": "", "pillar_focus": "", "governance_milestone": "",
                       "management_required": "", "expected_gain": "", "timeframe": "3\u201312 months"},
        "strategic": {"action_summary": "", "actions": "", "pillar_focus": "", "governance_milestone": "",
                      "management_required": "", "expected_gain": "", "timeframe": "12+ months"},
    },
    "first_action": {
        "headline": "", "description": "", "expected_outcome": "", "who_owns_it": "",
        "time_to_implement": "",
        "preconditions_met": {"p1_product_structure": "partial", "p2_product_classification": "partial",
                               "p3_data_model": "partial", "p4_data_governance": "partial",
                               "p5_business_it": "partial"},
    },
    "benchmark_context": "",
    "consultant_note": "",
}

STATIC_CLOSING_STATEMENT = (
    "Thank you for completing this PPDT Capability Maturity Assessment. This report is based on "
    "the Product Wellbeing framework developed at the University of Oulu (Hannila, Salonen & "
    "Vierimaa, 2024) and supporting peer-reviewed research on data-driven Product Portfolio "
    "Management."
)


def _reconcile_roadmap_continuity(report_data: dict) -> dict:
    """MANDATORY RULE 2 safety net: force the `immediate` phase's expected_gain
    starting values to exactly match the confirmed pillar scores, and force
    each phase's end value to equal the next phase's start value. Purely
    mechanical string-level fix \u2014 does not touch scoring/DBI logic.
    """
    scores = report_data.get("scores") or {}
    roadmap = report_data.get("roadmap") or {}
    pillars = ["people", "process", "data", "technology"]
    phase_order = ["immediate", "short_term", "strategic"]
    label_map = {"people": "People", "process": "Process", "data": "Data", "technology": "Technology"}

    parsed = {}
    for phase in phase_order:
        phase_data = roadmap.get(phase)
        gain_text = phase_data.get("expected_gain", "") if isinstance(phase_data, dict) else ""
        parsed[phase] = chat_service._parse_expected_gain(gain_text) if gain_text else {}

    if not any(parsed.values()):
        return report_data

    try:
        prev_end = {p: float(scores.get(p, 0) or 0) for p in pillars}
    except (TypeError, ValueError):
        return report_data

    for phase in phase_order:
        phase_data = roadmap.get(phase)
        if not isinstance(phase_data, dict):
            continue
        pairs = parsed.get(phase) or {}
        rebuilt = []
        for p in pillars:
            start = prev_end[p]
            end = pairs[p][1] if p in pairs else start
            rebuilt.append(f"{label_map[p]}: {start:.1f} \u2192 {end:.1f}")
            prev_end[p] = end
        phase_data["expected_gain"] = " | ".join(rebuilt)

    return report_data


def enforce_verbosity_caps(report_data: dict) -> dict:
    """Mechanical backstop for the caps already instructed in the prompt
    (failure_pattern_narrative <= 3 sentences, pillar_interpretations <= 5
    sentences, consultant_note <= 250 words), in case the model doesn't fully
    comply. Pure text trimming \u2014 does not touch scoring/DBI/schema.
    """
    def _cap_sentences(text, max_sentences: int):
        if not isinstance(text, str) or not text.strip():
            return text
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return " ".join(sentences[:max_sentences]) if len(sentences) > max_sentences else text

    def _cap_words(text, max_words: int):
        if not isinstance(text, str) or not text.strip():
            return text
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "\u2026"

    fpn = report_data.get("failure_pattern_narrative")
    if fpn:
        report_data["failure_pattern_narrative"] = _cap_sentences(fpn, 3)

    pi = report_data.get("pillar_interpretations")
    if isinstance(pi, dict):
        report_data["pillar_interpretations"] = {k: _cap_sentences(v, 5) for k, v in pi.items()}

    pis = report_data.get("pillar_interpretation_short")
    if isinstance(pis, dict):
        report_data["pillar_interpretation_short"] = {k: _cap_words(v, 40) for k, v in pis.items()}

    note = report_data.get("consultant_note")
    if note:
        report_data["consultant_note"] = _cap_words(note, 250)

    gss = report_data.get("governance_signal_summary")
    if isinstance(gss, list):
        report_data["governance_signal_summary"] = [_cap_words(b, 15) for b in gss][:4]

    return report_data


async def generate_report_sections(seed: dict, chat_history: list) -> dict:
    """Fire the 3 concurrent specialist calls and merge with the seed into
    the exact same report schema used before this refactor.
    """
    facts = _facts_block(seed)
    transcript = _transcript_text(chat_history)
    dynamic_common = f"CONFIRMED FACTS:\n{facts}\n\nFULL ASSESSMENT TRANSCRIPT:\n{transcript}"

    static_a = "\n\n".join([_SPECIALIST_PERSONA, _PILLAR_THEORY, _SCORING_WEIGHTS,
                            _MANDATORY_RULE_4, _MANDATORY_RULE_5, _WRITING_STYLE_A])
    static_b = "\n\n".join([_SPECIALIST_PERSONA, _MANAGEMENT_COMMITMENT_DEF, _PRECONDITIONS_LIST,
                            _MANDATORY_RULE_1, _MANDATORY_RULE_2, _MANDATORY_RULE_3,
                            _MANDATORY_RULE_6, _WRITING_STYLE_B])
    static_c = "\n\n".join([_SPECIALIST_PERSONA, _WRITING_STYLE_C])

    results = await asyncio.gather(
        _call_specialist_with_retry(label="A (sections 1-7)", static_block=static_a, dynamic_block=dynamic_common,
                                     schema_block=_SCHEMA_A, max_tokens=MAX_TOKENS_A),
        _call_specialist_with_retry(label="B (sections 8-12)", static_block=static_b, dynamic_block=dynamic_common,
                                     schema_block=_SCHEMA_B, max_tokens=MAX_TOKENS_B),
        _call_specialist_with_retry(label="C (section 13)", static_block=static_c, dynamic_block=dynamic_common,
                                     schema_block=_SCHEMA_C, max_tokens=MAX_TOKENS_C),
    )

    merged = dict(seed)
    call_specs = [("A (sections 1-7)", _ALLOWED_KEYS_A), ("B (sections 8-12)", _ALLOWED_KEYS_B),
                  ("C (section 13)", _ALLOWED_KEYS_C)]
    for (label, allowed_keys), parsed in zip(call_specs, results):
        if parsed:
            merged.update({k: v for k, v in parsed.items() if k in allowed_keys})
        else:
            logger.error("report_sections: specialist call %s produced no usable fields "
                         "(defaults will be used for its section)", label)

    merged["closing_statement"] = STATIC_CLOSING_STATEMENT
    merged.setdefault("ready_for_report", True)
    merged.setdefault("status", "completed")

    # Guarantee every field from the original schema exists, even if a call
    # permanently failed after retries \u2014 keeps the schema contract intact.
    for key, default in _FIELD_DEFAULTS.items():
        merged.setdefault(key, default)

    merged = _reconcile_roadmap_continuity(merged)
    merged = enforce_verbosity_caps(merged)

    return merged
