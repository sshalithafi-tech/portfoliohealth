"""
Helpers for assessment chat (LLM calls, JSON report parsing).
Keeps the route handler in `server.py` focused on orchestration.
"""
import json
import logging
import os
import re
from typing import Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-5-20250929"

VALID_BUSINESS_MODELS = {"Bulk", "Standard", "CTO", "CETO", "ETO"}
MODEL_COMPLEXITY_ORDER = ["ETO", "CETO", "CTO", "Standard", "Bulk"]


def build_system_prompt(base_prompt: str, assessment: dict) -> str:
    """Append per-assessment context to the base PPDT system prompt."""
    ctx = (
        f"\n\nCurrent Assessment Context:\n"
        f"Company: {assessment.get('company_name', 'Unknown')}\n"
        f"Industry: {assessment.get('company_industry', 'Unknown')}\n"
        f"Respondent: {assessment.get('respondent_name', 'Unknown')} "
        f"({assessment.get('respondent_role', 'Unknown')})\n"
        f"Current Phase: {assessment.get('current_phase', 'welcome')}\n"
    )
    return base_prompt + ctx


def _build_llm_chat(session_id: str, system_message: str) -> LlmChat:
    return LlmChat(
        api_key=os.environ.get("EMERGENT_LLM_KEY"),
        session_id=session_id,
        system_message=system_message,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)


async def call_llm_with_history(
    *, session_id: str, system_message: str, history: list, user_message: str
) -> str:
    """Send a user message to Claude, seeding the chat with prior history."""
    chat = _build_llm_chat(session_id, system_message)
    trimmed = [m for m in history if m.get("role") in ("user", "assistant")][-40:]
    for msg in trimmed:
        chat.messages.append({"role": msg["role"], "content": msg["content"]})
    return await chat.send_message(UserMessage(text=user_message))


async def call_llm_greeting(*, session_id: str, system_message: str) -> str:
    """Kick off an assessment — ask the LLM to introduce itself and ask Q1."""
    chat = _build_llm_chat(session_id, system_message)
    return await chat.send_message(UserMessage(
        text="Please begin the assessment by introducing yourself and asking the first question."
    ))


def extract_report_json(response_text: str) -> Optional[dict]:
    """Try to pull a structured PPDT report JSON out of an assistant response."""
    if "ready_for_report" not in response_text:
        return None
    fenced = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError as err:
            logger.error("JSON parse error in fenced block: %s", err)
    fallback = re.search(r'\{[\s\S]*"ready_for_report"[\s\S]*\}', response_text)
    if fallback:
        try:
            return json.loads(fallback.group(0))
        except json.JSONDecodeError:
            return None
    return None


def normalise_business_model(report_data: dict) -> dict:
    """If business_model is missing or a 'mixed' value, pick the highest-complexity
    model found in the string and annotate the original."""
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
    """Ensure equal_weighted_score is the plain mean of the four pillar scores."""
    scores = report_data.get("scores") or {}
    pillars = ["people", "process", "data", "technology"]
    try:
        pillar_scores = [float(scores.get(p, 0) or 0) for p in pillars]
    except (TypeError, ValueError):
        return report_data

    mean = round(sum(pillar_scores) / 4.0, 1)
    eq = report_data.get("equal_weighted_score")
    ctx = report_data.get("contextual_score")

    bm = report_data.get("business_model")
    strategic = (report_data.get("strategic_priority") or "").strip().lower()
    adjustment_present = (bm not in (None, "Bulk", "Standard")) or bool(strategic)

    try:
        if eq is not None and ctx is not None:
            if round(float(eq), 2) == round(float(ctx), 2) and adjustment_present:
                report_data["equal_weighted_score"] = mean
    except (TypeError, ValueError):
        pass

    final_eq = report_data.get("equal_weighted_score")
    if final_eq is None or not isinstance(final_eq, (int, float)):
        report_data["equal_weighted_score"] = mean
        final_eq = mean
    scores["overall"] = float(final_eq)
    report_data["scores"] = scores
    return report_data


def normalise_report_weights(report_data: dict) -> dict:
    """Ensure weights_raw / weights_normalised are present and sum to 1.
    Also normalise business_model and recompute dual scores."""
    if not report_data.get("weights_raw"):
        report_data["weights_raw"] = {"people": 5, "process": 5, "data": 5, "technology": 5}
    if not report_data.get("weights_normalised"):
        raw = report_data["weights_raw"]
        total = sum(raw.values()) or 1
        report_data["weights_normalised"] = {k: round(v / total, 4) for k, v in raw.items()}
    normalise_business_model(report_data)
    recompute_dual_scores(report_data)
    return report_data
