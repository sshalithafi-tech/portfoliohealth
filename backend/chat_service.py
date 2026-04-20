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
    if not report_data.get("weights_raw"):
        report_data["weights_raw"] = {"people": 5, "process": 5, "data": 5, "technology": 5}
    if not report_data.get("weights_normalised"):
        raw = report_data["weights_raw"]
        total = sum(raw.values()) or 1
        report_data["weights_normalised"] = {k: round(v / total, 4) for k, v in raw.items()}
    normalise_business_model(report_data)
    recompute_dual_scores(report_data)
    return report_data
