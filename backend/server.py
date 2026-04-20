from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import bcrypt
import jwt
import secrets
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
import asyncio

# PDF generation (delegated to pdf_builder)
from pdf_builder import build_full_assessment_pdf, build_quick_assessment_pdf

# Chat / LLM service helpers
from chat_service import (
    build_system_prompt,
    call_llm_with_history,
    call_llm_greeting,
    extract_report_json,
    normalise_report_weights,
)

import re
import json as json_mod

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ.get("JWT_SECRET", "default-secret-change-me")

# Password Hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# JWT Token Management
def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

# Auth Dependency
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        del user["_id"]
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Admin dependency
async def require_admin(request: Request) -> dict:
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============================================
# NOTIFICATION HELPER
# ============================================

async def create_notification(
    notif_type: str,
    title: str,
    message: str,
    user_id: str = None,
    admin_only: bool = False,
    meta: dict = None
):
    """Create a notification. If user_id is set, it's for that user. If admin_only, only admins see it."""
    doc = {
        "type": notif_type,
        "title": title,
        "message": message,
        "user_id": user_id,
        "admin_only": admin_only,
        "read_by": [],
        "meta": meta or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(doc)

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str

class CompanyCreate(BaseModel):
    name: str
    industry: str
    portfolio_size: Optional[str] = None
    primary_challenge: Optional[str] = None

class CompanyResponse(BaseModel):
    id: str
    name: str
    industry: str
    portfolio_size: Optional[str] = None
    primary_challenge: Optional[str] = None
    created_at: str
    user_id: str

class AssessmentCreate(BaseModel):
    company_id: str
    respondent_name: str
    respondent_role: str

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str

class AssessmentUpdate(BaseModel):
    chat_history: Optional[List[Dict[str, Any]]] = None
    current_phase: Optional[str] = None
    scores: Optional[Dict[str, int]] = None
    status: Optional[str] = None
    report: Optional[Dict[str, Any]] = None

class SendMessageRequest(BaseModel):
    message: str

# Contact email for closing statement
CONTACT_EMAIL = "shalitha.samarakoonmudiyanselage@student.oulu.fi"

# PPDT System Prompt
PPDT_SYSTEM_PROMPT = """You are the PortfolioHealth Advisor — a specialised AI assessment consultant grounded in peer-reviewed PPM research from the University of Oulu.

Your role is to conduct a structured, conversational capability maturity assessment of an organisation's readiness to make fact-based, data-driven Product Portfolio Management (PPM) decisions. You assess the organisation across four capability dimensions — People, Process, Data, and Technology (the PPDT model) — and score them against five maturity levels derived from the PPM Capability Maturity Framework.

You are rigorous but conversational. You ask one focused question at a time. You do not overwhelm the respondent. You listen carefully, probe intelligently, and map every response to the PPDT scoring rubric in the background.

ASSESSMENT PHILOSOPHY:
1. DECISION QUALITY IS THE OUTCOME: The goal is not to score technology or processes in isolation. Every capability gap must be traced back to its impact on PPM decision quality.
2. DATA IS THE FOUNDATION: Data is the most critical and most commonly deficient dimension. Weight your probing accordingly.
3. PEOPLE BEFORE TECHNOLOGY: Culture, ownership, and decision-making governance must precede technology investment.

MATURITY LEVELS (Score each PPDT dimension 1–5):
LEVEL 1 — AD HOC: No structured approach. Decisions are reactive and intuition-driven.
LEVEL 2 — DEVELOPING: Some processes and roles exist but are inconsistently applied.
LEVEL 3 — DEFINED: Structured PPM processes and roles are formally established.
LEVEL 4 — MANAGED: PPM decisions are systematically supported by integrated data. Governance structures are embedded.
LEVEL 5 — OPTIMISING: All four PPDT pillars are fully aligned and continuously improved. Governance is proactive and adaptive.

GOVERNANCE INDICATORS (Levels 4–5 ONLY):
When a pillar appears to score at Level 4 or 5, you MUST ask governance-related questions within that pillar. Frame them naturally.

- PEOPLE (Governance at L4-L5): Probe role-based data ownership, accountability frameworks, cross-functional governance participation. E.g. "At higher maturity levels, governance becomes critical. Who owns the product performance data and how is accountability structured?"
- PROCESS (Governance at L4-L5): Probe formal review cycles, change control, escalation paths, audit trails for portfolio decisions. E.g. "How are portfolio decisions audited? Is there a formal escalation path when criteria are not met?"
- DATA (Governance at L4-L5): Probe data governance policies, stewardship roles, data quality SLAs, compliance with data standards. E.g. "Do you have formal data stewardship roles? How do you enforce data quality standards across the product lifecycle?"
- TECHNOLOGY (Governance at L4-L5): Probe system governance, access control, integration governance, PLM audit capabilities, tool ownership policies. E.g. "Who governs access to your PLM/PPM systems? Are there audit logs for critical portfolio decisions?"

ASSESSMENT FLOW:
PHASE 0 — WELCOME & CONTEXT SETTING (2–3 exchanges): Greet warmly. Ask for context about the company and respondent.
PHASE 1 — PEOPLE (4–6 questions): Cultural questions, role clarity, data literacy. If answers suggest L4+, ask governance questions.
PHASE 2 — PROCESS (4–6 questions): PPM governance, product classification, lifecycle management. If answers suggest L4+, ask governance questions.
PHASE 3 — DATA (5–7 questions): Data model, product-level profitability, master data governance. If answers suggest L4+, ask governance questions.
PHASE 4 — TECHNOLOGY (3–5 questions): System integration, decision support capability. If answers suggest L4+, ask governance questions.
PHASE 5 — STRATEGIC WEIGHTING (1 question): Ask the respondent to assign a strategic importance weight (1–10) to each of the four pillars. E.g. "Now I need to understand your strategic priorities. On a scale of 1 to 10, how important is each dimension to your organisation's PPM goals? Please give me a number for People, Process, Data, and Technology."
PHASE 6 — DECISION TYPE CALIBRATION (2–3 questions): Which PPM decision types are most difficult.
PHASE 7 — BENCHMARK CONTEXT (1–2 questions): Industry context and peer comparison.

BEHAVIOURAL RULES:
1. ASK ONE QUESTION AT A TIME. Never ask multiple questions in a single message.
2. PROBE ONCE. If an answer is vague, ask one clarifying follow-up. Then score and move on.
3. NEVER LECTURE. Do not explain the PPDT framework unprompted.
4. PERSONALISE. Use the company name, industry, and portfolio size in your questions.
5. BE DIRECT. If a respondent gives an answer that indicates low maturity, acknowledge it honestly.
6. DO NOT RUSH. Quality of assessment matters more than speed.
7. COMPLETE ALL PHASES. You must complete all phases before generating the report. Do not skip any phase.
8. SIGNAL COMPLETION CLEARLY. When you have completed ALL phases, generate your final summary message that includes the report JSON. Start your final message with "Thank you for completing this assessment." and include the structured report.

When you have gathered enough information (after completing ALL phases including strategic weighting), generate a comprehensive assessment report in JSON format. Calculate the overall score using the WEIGHTED SUM: M = w_pe * S_pe + w_pr * S_pr + w_d * S_d + w_t * S_t, where the weights are normalised from the respondent's 1-10 ratings so they sum to 1.

JSON structure:
{
  "ready_for_report": true,
  "scores": {
    "people": <1-5>,
    "process": <1-5>,
    "data": <1-5>,
    "technology": <1-5>,
    "overall": <weighted sum to 2 decimals>
  },
  "weights_raw": {
    "people": <1-10 from respondent>,
    "process": <1-10>,
    "data": <1-10>,
    "technology": <1-10>
  },
  "weights_normalised": {
    "people": <0-1 normalised>,
    "process": <0-1>,
    "data": <0-1>,
    "technology": <0-1>
  },
  "level_names": {
    "people": "<level name>",
    "process": "<level name>",
    "data": "<level name>",
    "technology": "<level name>",
    "overall": "<level name>"
  },
  "dimension_summaries": {
    "people": "<1-sentence summary>",
    "process": "<1-sentence summary>",
    "data": "<1-sentence summary>",
    "technology": "<1-sentence summary>"
  },
  "pillar_interpretations": {
    "people": "<1-sentence interpretation of what their score means in practice>",
    "process": "<1-sentence interpretation>",
    "data": "<1-sentence interpretation>",
    "technology": "<1-sentence interpretation>"
  },
  "governance_observations": {
    "people": "<governance observation or 'N/A - below Level 4'>",
    "process": "<governance observation or 'N/A - below Level 4'>",
    "data": "<governance observation or 'N/A - below Level 4'>",
    "technology": "<governance observation or 'N/A - below Level 4'>"
  },
  "governance_assessment": "<2-3 sentence dynamic paragraph about current governance state based on responses about roles, reviews, and decision authority>",
  "management_commitment_assessment": "<2-3 sentence dynamic paragraph about management commitment based on responses about executive involvement and top-management support>",
  "key_findings": ["<finding 1>", "<finding 2>", ...],
  "critical_gaps": ["<gap 1>", "<gap 2>", ...],
  "decision_vulnerability": "<analysis of which decision type is most at risk>",
  "roadmap": {
    "immediate": {
      "actions": ["<action 1>", "<action 2>"],
      "pillar_focus": "<which pillars>",
      "governance_milestone": "<milestone>",
      "management_commitment": "<requirement>",
      "expected_gain": "<expected maturity movement>"
    },
    "short_term": {
      "actions": ["<action 1>", "<action 2>"],
      "pillar_focus": "<which pillars>",
      "governance_milestone": "<milestone>",
      "management_commitment": "<requirement>",
      "expected_gain": "<expected maturity movement>"
    },
    "strategic": {
      "actions": ["<action 1>", "<action 2>"],
      "pillar_focus": "<which pillars>",
      "governance_milestone": "<milestone>",
      "management_commitment": "<requirement>",
      "expected_gain": "<expected maturity movement>"
    }
  },
  "benchmark_context": "<assessment relative to industry peers>",
  "consultant_note": "<single most important focus area>",
  "closing_statement": "Thank you for completing this capability maturity assessment. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out via email to arrange a follow-up consultation: """ + CONTACT_EMAIL + """"
}

Include this JSON block at the END of your final message when the assessment is complete, wrapped in ```json``` code blocks."""

# Auth Routes
@api_router.post("/auth/register")
async def register(user: UserRegister, response: Response):
    email = user.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "email": email,
        "password_hash": hash_password(user.password),
        "name": user.name,
        "role": "consultant",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Notify admins about new registration
    await create_notification(
        notif_type="new_user",
        title="New User Registered",
        message=f"{user.name} ({email}) has created an account.",
        admin_only=True,
        meta={"user_name": user.name, "user_email": email}
    )
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    
    return {
        "access_token": access_token,
        "user": {
            "id": user_id,
            "email": email,
            "name": user.name,
            "role": "consultant",
            "created_at": user_doc["created_at"]
        }
    }

@api_router.post("/auth/login")
async def login(user: UserLogin, response: Response, request: Request):
    email = user.email.lower()
    
    # Check brute force
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"{client_ip}:{email}"
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    
    if attempts and attempts.get("count", 0) >= 5:
        lockout_time = attempts.get("last_attempt")
        if lockout_time:
            lockout_dt = datetime.fromisoformat(lockout_time) if isinstance(lockout_time, str) else lockout_time
            if datetime.now(timezone.utc) - lockout_dt < timedelta(minutes=15):
                raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")
    
    db_user = await db.users.find_one({"email": email})
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        # Record failed attempt
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {
                "$inc": {"count": 1},
                "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}
            },
            upsert=True
    )
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Clear failed attempts on success
    await db.login_attempts.delete_one({"identifier": identifier})
    
    user_id = str(db_user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    
    return {
        "access_token": access_token,
        "user": {
            "id": user_id,
            "email": email,
            "name": db_user["name"],
            "role": db_user.get("role", "consultant"),
            "created_at": db_user.get("created_at", "")
        }
    }

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(refresh_token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        access_token = create_access_token(str(user["_id"]), user["email"])
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# Company Routes
@api_router.post("/companies")
async def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_user)):
    company_doc = {
        "name": company.name,
        "industry": company.industry,
        "portfolio_size": company.portfolio_size,
        "primary_challenge": company.primary_challenge,
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.companies.insert_one(company_doc)
    return {
        "id": str(result.inserted_id),
        **{k: v for k, v in company_doc.items() if k != "_id"}
    }

@api_router.get("/companies")
async def get_companies(current_user: dict = Depends(get_current_user)):
    companies = await db.companies.find({"user_id": current_user["id"]}, {"_id": 1, "name": 1, "industry": 1, "portfolio_size": 1, "primary_challenge": 1, "created_at": 1, "user_id": 1}).to_list(1000)
    result = []
    for c in companies:
        cid = str(c["_id"])
        total = await db.assessments.count_documents({"company_id": cid})
        completed = await db.assessments.count_documents({"company_id": cid, "status": "completed"})
        # Get latest assessment score
        latest = await db.assessments.find_one({"company_id": cid, "status": "completed"}, sort=[("completed_at", -1)])
        latest_score = latest.get("scores", {}).get("overall") if latest else None
        result.append({
            "id": cid,
            **{k: v for k, v in c.items() if k != "_id"},
            "assessment_count": total,
            "completed_count": completed,
            "latest_score": latest_score,
        })
    return result

@api_router.get("/companies/{company_id}")
async def get_company(company_id: str, current_user: dict = Depends(get_current_user)):
    company = await db.companies.find_one({"_id": ObjectId(company_id), "user_id": current_user["id"]})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"id": str(company["_id"]), **{k: v for k, v in company.items() if k != "_id"}}

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a company and all its associated assessments"""
    company = await db.companies.find_one({"_id": ObjectId(company_id), "user_id": current_user["id"]})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Delete all assessments for this company
    await db.assessments.delete_many({"company_id": company_id})
    # Delete the company
    await db.companies.delete_one({"_id": ObjectId(company_id)})
    return {"ok": True, "message": f"Company '{company.get('name', '')}' and all associated assessments deleted."}


@api_router.get("/companies/{company_id}/assessments")
async def get_company_assessments(company_id: str, current_user: dict = Depends(get_current_user)):
    # Verify company belongs to user
    company = await db.companies.find_one({"_id": ObjectId(company_id), "user_id": current_user["id"]})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    assessments = await db.assessments.find(
        {"company_id": company_id},
        {"_id": 1, "respondent_name": 1, "respondent_role": 1, "status": 1, "scores": 1, "created_at": 1, "completed_at": 1}
    ).sort("created_at", -1).to_list(100)
    
    return [{"id": str(a["_id"]), **{k: v for k, v in a.items() if k != "_id"}} for a in assessments]

# Assessment Routes
@api_router.post("/assessments")
async def create_assessment(assessment: AssessmentCreate, current_user: dict = Depends(get_current_user)):
    # Verify company belongs to user
    company = await db.companies.find_one({"_id": ObjectId(assessment.company_id), "user_id": current_user["id"]})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    assessment_doc = {
        "company_id": assessment.company_id,
        "company_name": company["name"],
        "company_industry": company["industry"],
        "respondent_name": assessment.respondent_name,
        "respondent_role": assessment.respondent_role,
        "user_id": current_user["id"],
        "chat_history": [],
        "current_phase": "welcome",
        "scores": None,
        "status": "in_progress",
        "report": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    result = await db.assessments.insert_one(assessment_doc)
    return {
        "id": str(result.inserted_id),
        **{k: v for k, v in assessment_doc.items() if k != "_id"}
    }

@api_router.get("/assessments")
async def get_assessments(current_user: dict = Depends(get_current_user)):
    assessments = await db.assessments.find(
        {"user_id": current_user["id"]},
        {"_id": 1, "company_id": 1, "company_name": 1, "company_industry": 1, "respondent_name": 1, "respondent_role": 1, "status": 1, "scores": 1, "created_at": 1, "completed_at": 1}
    ).sort("created_at", -1).to_list(1000)
    return [{"id": str(a["_id"]), **{k: v for k, v in a.items() if k != "_id"}} for a in assessments]

@api_router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"id": str(assessment["_id"]), **{k: v for k, v in assessment.items() if k != "_id"}}

@api_router.patch("/assessments/{assessment_id}")
async def update_assessment(assessment_id: str, update: AssessmentUpdate, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        if update_data.get("status") == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        await db.assessments.update_one({"_id": ObjectId(assessment_id)}, {"$set": update_data})
    
    updated = await db.assessments.find_one({"_id": ObjectId(assessment_id)})
    return {"id": str(updated["_id"]), **{k: v for k, v in updated.items() if k != "_id"}}

# Chat Route
@api_router.post("/assessments/{assessment_id}/chat")
async def send_chat_message(assessment_id: str, request: SendMessageRequest, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Record user turn
    chat_history = assessment.get("chat_history", [])
    chat_history.append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Ask Claude
    try:
        response_text = await call_llm_with_history(
            session_id=f"assessment-chat-{assessment_id}",
            system_message=build_system_prompt(PPDT_SYSTEM_PROMPT, assessment),
            history=chat_history[:-1],
            user_message=request.message,
        )
    except Exception as exc:
        logging.error(f"LLM error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to get AI response. Please try again.")

    assistant_msg = {
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    chat_history.append(assistant_msg)

    # Try to extract report JSON from the assistant message
    report_data = extract_report_json(response_text)
    scores = None
    status = assessment.get("status", "in_progress")
    if report_data and report_data.get("ready_for_report"):
        report_data = normalise_report_weights(report_data)
        scores = report_data.get("scores")
        status = "completed"

    # Persist
    update_data = {"chat_history": chat_history}
    if report_data:
        update_data["report"] = report_data
        update_data["weights_raw"] = report_data.get("weights_raw")
        update_data["weights_normalised"] = report_data.get("weights_normalised")
    if scores:
        update_data["scores"] = scores
    if status == "completed":
        update_data["status"] = "completed"
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()

    await db.assessments.update_one({"_id": ObjectId(assessment_id)}, {"$set": update_data})

    # Notifications on completion
    if status == "completed":
        company_name = assessment.get("company_name", "Unknown")
        overall_score = scores.get("overall", "N/A") if scores else "N/A"
        await create_notification(
            notif_type="assessment_completed",
            title="Assessment Completed",
            message=f"Your assessment for {company_name} is complete. Overall score: {overall_score}/5.",
            user_id=current_user["id"],
            meta={"assessment_id": assessment_id, "company_name": company_name, "score": overall_score}
        )
        await create_notification(
            notif_type="assessment_completed",
            title="Assessment Completed",
            message=f"{current_user.get('name', 'A consultant')} completed an assessment for {company_name}. Score: {overall_score}/5.",
            admin_only=True,
            meta={"assessment_id": assessment_id, "company_name": company_name,
                  "score": overall_score, "consultant": current_user.get("name", "")}
        )

    return {
        "message": assistant_msg,
        "report_ready": report_data is not None,
        "report": report_data,
    }

# Start Assessment (generate initial greeting)
@api_router.post("/assessments/{assessment_id}/start")
async def start_assessment(assessment_id: str, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.get("chat_history") and len(assessment["chat_history"]) > 0:
        first = assessment["chat_history"][0]
        return {"message": {"role": "assistant", "content": first["content"], "timestamp": first["timestamp"]}}

    try:
        response_text = await call_llm_greeting(
            session_id=f"assessment-start-{assessment_id}",
            system_message=build_system_prompt(PPDT_SYSTEM_PROMPT, assessment),
        )
    except Exception as exc:
        logging.error(f"LLM error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to start assessment")

    greeting_msg = {
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.assessments.update_one(
        {"_id": ObjectId(assessment_id)},
        {"$set": {"chat_history": [greeting_msg]}}
    )
    return {"message": greeting_msg}

# PDF Report Generation
@api_router.get("/assessments/{assessment_id}/pdf")
async def generate_pdf_report(assessment_id: str, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.get("report"):
        raise HTTPException(status_code=400, detail="Assessment report not yet generated")

    buffer = build_full_assessment_pdf(assessment)
    filename = (
        f"PortfolioHealth_Assessment_"
        f"{assessment.get('company_name', 'Report').replace(' ', '_')}_"
        f"{assessment_id[:8]}.pdf"
    )
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    total_assessments = await db.assessments.count_documents({"user_id": current_user["id"]})
    completed_assessments = await db.assessments.count_documents({"user_id": current_user["id"], "status": "completed"})
    total_companies = await db.companies.count_documents({"user_id": current_user["id"]})
    total_quick_assessments = await db.quick_assessments.count_documents({"user_id": current_user["id"]})
    
    # Average scores from completed assessments
    completed = await db.assessments.find(
        {"user_id": current_user["id"], "status": "completed", "scores": {"$ne": None}}
    ).to_list(1000)
    
    avg_scores = {"people": 0, "process": 0, "data": 0, "technology": 0, "overall": 0}
    if completed:
        for a in completed:
            scores = a.get("scores", {})
            for dim in avg_scores.keys():
                avg_scores[dim] += scores.get(dim, 0)
        for dim in avg_scores.keys():
            avg_scores[dim] = round(avg_scores[dim] / len(completed), 1)
    
    return {
        "total_assessments": total_assessments,
        "completed_assessments": completed_assessments,
        "in_progress_assessments": total_assessments - completed_assessments,
        "total_companies": total_companies,
        "total_quick_assessments": total_quick_assessments,
        "average_scores": avg_scores
    }


# ============================================
# NOTIFICATION ENDPOINTS
# ============================================

@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Get notifications for the current user"""
    user_id = current_user["id"]
    is_admin = current_user.get("role") == "admin"

    query = {"$or": [{"user_id": user_id}]}
    if is_admin:
        query["$or"].append({"admin_only": True})
        query["$or"].append({"user_id": None, "admin_only": False})

    notifications = await db.notifications.find(
        query, {"_id": 1, "type": 1, "title": 1, "message": 1, "read_by": 1, "created_at": 1, "meta": 1}
    ).sort("created_at", -1).limit(50).to_list(50)

    return [{
        "id": str(n["_id"]),
        "type": n.get("type", ""),
        "title": n.get("title", ""),
        "message": n.get("message", ""),
        "read": user_id in n.get("read_by", []),
        "created_at": n.get("created_at", ""),
        "meta": n.get("meta", {}),
    } for n in notifications]

@api_router.get("/notifications/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get unread notification count"""
    user_id = current_user["id"]
    is_admin = current_user.get("role") == "admin"

    query = {"read_by": {"$ne": user_id}, "$or": [{"user_id": user_id}]}
    if is_admin:
        query["$or"].append({"admin_only": True})
        query["$or"].append({"user_id": None, "admin_only": False})

    count = await db.notifications.count_documents(query)
    return {"count": count}

@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a single notification as read"""
    await db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$addToSet": {"read_by": current_user["id"]}}
    )
    return {"ok": True}

@api_router.post("/notifications/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the current user"""
    user_id = current_user["id"]
    is_admin = current_user.get("role") == "admin"

    query = {"read_by": {"$ne": user_id}, "$or": [{"user_id": user_id}]}
    if is_admin:
        query["$or"].append({"admin_only": True})
        query["$or"].append({"user_id": None, "admin_only": False})

    await db.notifications.update_many(query, {"$addToSet": {"read_by": user_id}})
    return {"ok": True}


# Health check
@api_router.get("/")
async def root():
    return {"message": "PortfolioHealth Advisor API", "status": "healthy"}

# ============================================
# ADMIN ENDPOINTS - View all assessments
# ============================================

@api_router.get("/admin/assessments")
async def admin_get_all_assessments(current_user: dict = Depends(require_admin)):
    """Get ALL assessments across all users (admin only)"""
    assessments = await db.assessments.find(
        {},
        {"_id": 1, "company_id": 1, "company_name": 1, "company_industry": 1,
         "respondent_name": 1, "respondent_role": 1, "status": 1, "scores": 1,
         "created_at": 1, "completed_at": 1, "user_id": 1}
    ).sort("created_at", -1).to_list(5000)

    # Enrich with user info
    user_ids = list(set(a.get("user_id") for a in assessments if a.get("user_id")))
    users_map = {}
    for uid in user_ids:
        try:
            u = await db.users.find_one({"_id": ObjectId(uid)}, {"_id": 0, "name": 1, "email": 1})
            if u:
                users_map[uid] = u
        except Exception:
            pass

    result = []
    for a in assessments:
        user_info = users_map.get(a.get("user_id"), {})
        result.append({
            "id": str(a["_id"]),
            "company_name": a.get("company_name", ""),
            "company_industry": a.get("company_industry", ""),
            "respondent_name": a.get("respondent_name", ""),
            "respondent_role": a.get("respondent_role", ""),
            "status": a.get("status", ""),
            "scores": a.get("scores"),
            "created_at": a.get("created_at", ""),
            "completed_at": a.get("completed_at"),
            "consultant_name": user_info.get("name", "Unknown"),
            "consultant_email": user_info.get("email", ""),
        })
    return result

@api_router.get("/admin/quick-assessments")
async def admin_get_all_quick_assessments(current_user: dict = Depends(require_admin)):
    """Get ALL quick assessments (admin only)"""
    quick = await db.quick_assessments.find(
        {},
        {"_id": 1, "company_name": 1, "industry": 1, "respondent_name": 1,
         "respondent_email": 1, "scores": 1, "traffic_lights": 1, "level_names": 1,
         "created_at": 1, "user_id": 1}
    ).sort("created_at", -1).to_list(5000)

    return [{
        "id": str(q["_id"]),
        "company_name": q.get("company_name", ""),
        "industry": q.get("industry", ""),
        "respondent_name": q.get("respondent_name", ""),
        "respondent_email": q.get("respondent_email", ""),
        "scores": q.get("scores"),
        "traffic_lights": q.get("traffic_lights"),
        "level_names": q.get("level_names"),
        "created_at": q.get("created_at", ""),
        "saved_by_user": bool(q.get("user_id")),
    } for q in quick]

@api_router.get("/admin/stats")
async def admin_get_stats(current_user: dict = Depends(require_admin)):
    """Get global stats across all users (admin only)"""
    total_assessments = await db.assessments.count_documents({})
    completed_assessments = await db.assessments.count_documents({"status": "completed"})
    total_quick = await db.quick_assessments.count_documents({})
    total_companies = await db.companies.count_documents({})
    total_users = await db.users.count_documents({})

    return {
        "total_assessments": total_assessments,
        "completed_assessments": completed_assessments,
        "in_progress_assessments": total_assessments - completed_assessments,
        "total_quick_assessments": total_quick,
        "total_companies": total_companies,
        "total_users": total_users,
    }

@api_router.get("/admin/export/assessments")
async def admin_export_assessments_csv(current_user: dict = Depends(require_admin)):
    """Export all assessments as CSV (admin only)"""
    import csv
    import io

    assessments = await db.assessments.find(
        {},
        {"_id": 1, "company_name": 1, "company_industry": 1, "respondent_name": 1,
         "respondent_role": 1, "status": 1, "scores": 1, "created_at": 1, "completed_at": 1}
    ).sort("created_at", -1).to_list(10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Company", "Industry", "Respondent", "Role", "Status",
                     "People", "Process", "Data", "Technology", "Overall", "Date", "Completed"])

    for a in assessments:
        scores = a.get("scores") or {}
        writer.writerow([
            a.get("company_name", ""),
            a.get("company_industry", ""),
            a.get("respondent_name", ""),
            a.get("respondent_role", ""),
            a.get("status", ""),
            scores.get("people", ""),
            scores.get("process", ""),
            scores.get("data", ""),
            scores.get("technology", ""),
            scores.get("overall", ""),
            a.get("created_at", ""),
            a.get("completed_at", ""),
        ])

    csv_content = output.getvalue()
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assessments_export.csv"}
    )

@api_router.get("/admin/export/quick-assessments")
async def admin_export_quick_csv(current_user: dict = Depends(require_admin)):
    """Export all quick assessments as CSV (admin only)"""
    import csv
    import io

    quick = await db.quick_assessments.find(
        {},
        {"_id": 1, "company_name": 1, "industry": 1, "respondent_name": 1,
         "respondent_email": 1, "scores": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Company", "Industry", "Respondent", "Email",
                     "People", "Process", "Data", "Technology", "Overall", "Date"])

    for q in quick:
        scores = q.get("scores") or {}
        writer.writerow([
            q.get("company_name", ""),
            q.get("industry", ""),
            q.get("respondent_name", ""),
            q.get("respondent_email", ""),
            scores.get("people", ""),
            scores.get("process", ""),
            scores.get("data", ""),
            scores.get("technology", ""),
            scores.get("overall", ""),
            q.get("created_at", ""),
        ])

    csv_content = output.getvalue()
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=quick_assessments_export.csv"}
    )



# ============================================
# QUICK ASSESSMENT ENDPOINTS
# ============================================

# Quick Assessment Questions - Hardcoded
QUICK_ASSESSMENT_QUESTIONS = [
    {
        "id": 1,
        "dimension": "qualifier",
        "question": "How many products are in your active portfolio?",
        "options": [
            {"label": "<50", "value": 1},
            {"label": "50–200", "value": 2},
            {"label": "200–500", "value": 3},
            {"label": "500+", "value": 4}
        ]
    },
    {
        "id": 2,
        "dimension": "people",
        "question": "How are portfolio decisions typically made?",
        "options": [
            {"label": "Intuition & seniority", "value": 1},
            {"label": "Mixed approach", "value": 2},
            {"label": "Structured analysis", "value": 4},
            {"label": "Fully data-driven", "value": 5}
        ]
    },
    {
        "id": 3,
        "dimension": "people",
        "question": "Are roles and ownership for product data clearly defined?",
        "options": [
            {"label": "No defined roles", "value": 1},
            {"label": "Some roles exist", "value": 2},
            {"label": "Roles defined", "value": 4},
            {"label": "Fully governed", "value": 5}
        ]
    },
    {
        "id": 4,
        "dimension": "people",
        "question": "How would you rate your team's data literacy for PPM?",
        "options": [
            {"label": "Very low", "value": 1},
            {"label": "Developing", "value": 2},
            {"label": "Moderate", "value": 3},
            {"label": "High", "value": 5}
        ]
    },
    {
        "id": 5,
        "dimension": "process",
        "question": "Does a formal PPM governance process with decision gates exist?",
        "options": [
            {"label": "No process", "value": 1},
            {"label": "Informal", "value": 2},
            {"label": "Defined but inconsistent", "value": 3},
            {"label": "Fully operational", "value": 5}
        ]
    },
    {
        "id": 6,
        "dimension": "process",
        "question": "Can you classify products as strategic, supportive, or non-strategic?",
        "options": [
            {"label": "No classification", "value": 1},
            {"label": "Partial", "value": 2},
            {"label": "Defined criteria", "value": 4},
            {"label": "Systematically applied", "value": 5}
        ]
    },
    {
        "id": 7,
        "dimension": "process",
        "question": "Is there a formal product end-of-life and rationalisation process?",
        "options": [
            {"label": "No", "value": 1},
            {"label": "Ad hoc", "value": 2},
            {"label": "Defined", "value": 4},
            {"label": "Consistently enforced", "value": 5}
        ]
    },
    {
        "id": 8,
        "dimension": "data",
        "question": "Can you calculate product-level profitability reliably?",
        "options": [
            {"label": "No", "value": 1},
            {"label": "Only estimate", "value": 2},
            {"label": "With manual effort", "value": 3},
            {"label": "Automated & trusted", "value": 5}
        ]
    },
    {
        "id": 9,
        "dimension": "data",
        "question": "Is product master data standardised and governed across business units?",
        "options": [
            {"label": "No", "value": 1},
            {"label": "Partially", "value": 2},
            {"label": "Mostly", "value": 4},
            {"label": "Fully", "value": 5}
        ]
    },
    {
        "id": 10,
        "dimension": "data",
        "question": "How many IT systems must be manually combined to analyse portfolio performance?",
        "options": [
            {"label": "5+", "value": 1},
            {"label": "3–4", "value": 2},
            {"label": "2", "value": 4},
            {"label": "Single integrated source", "value": 5}
        ]
    },
    {
        "id": 11,
        "dimension": "data",
        "question": "Is there a corporate-level data model connecting product, financial & customer data?",
        "options": [
            {"label": "No", "value": 1},
            {"label": "In progress", "value": 2},
            {"label": "Partially deployed", "value": 4},
            {"label": "Fully operational", "value": 5}
        ]
    },
    {
        "id": 12,
        "dimension": "technology",
        "question": "Are PLM, ERP, and CRM systems integrated for PPM decision support?",
        "options": [
            {"label": "Not integrated", "value": 1},
            {"label": "Minimal integration", "value": 2},
            {"label": "Partial", "value": 3},
            {"label": "Fully integrated", "value": 5}
        ]
    },
    {
        "id": 13,
        "dimension": "technology",
        "question": "Can leadership access product performance dashboards without IT support?",
        "options": [
            {"label": "No", "value": 1},
            {"label": "Rarely", "value": 2},
            {"label": "Sometimes", "value": 3},
            {"label": "Always", "value": 5}
        ]
    },
    {
        "id": 14,
        "dimension": "technology",
        "question": "How much manual effort is required to produce a portfolio performance report?",
        "options": [
            {"label": "Days of work", "value": 1},
            {"label": "Half a day", "value": 2},
            {"label": "Hours", "value": 4},
            {"label": "Near real-time", "value": 5}
        ]
    },
    {
        "id": 15,
        "dimension": "technology",
        "question": "Does your business IT architecture reflect your data model (data-first approach)?",
        "options": [
            {"label": "No", "value": 1},
            {"label": "Not sure", "value": 2},
            {"label": "Partially", "value": 3},
            {"label": "Fully aligned", "value": 5}
        ]
    }
]

LEVEL_NAMES = {
    1: "Ad Hoc",
    2: "Developing", 
    3: "Defined",
    4: "Managed",
    5: "Optimising"
}

LEVEL_GAPS = {
    1: "critical gaps in all PPDT dimensions, with decisions driven by intuition rather than data",
    2: "foundational gaps in data governance and process maturity that limit fact-based decision making",
    3: "defined processes but incomplete integration between systems and inconsistent data quality",
    4: "good operational capability but opportunities to optimize data-driven portfolio decisions",
    5: "strong PPDT maturity with continuous improvement opportunities"
}

class QuickAssessmentSubmit(BaseModel):
    company_name: str
    industry: str
    respondent_name: Optional[str] = None
    respondent_email: Optional[str] = None
    answers: Dict[str, int]  # question_id -> selected_value

class QuickAssessmentSave(BaseModel):
    quick_assessment_id: str

def calculate_quick_scores(answers: Dict[str, int]) -> Dict[str, Any]:
    """Calculate PPDT scores from quick assessment answers"""
    dimension_scores = {
        "people": [],
        "process": [],
        "data": [],
        "technology": []
    }
    
    for q in QUICK_ASSESSMENT_QUESTIONS:
        q_id = str(q["id"])
        if q_id in answers and q["dimension"] != "qualifier":
            dimension_scores[q["dimension"]].append(answers[q_id])
    
    scores = {}
    for dim, values in dimension_scores.items():
        if values:
            scores[dim] = round(sum(values) / len(values), 1)
        else:
            scores[dim] = 0
    
    # Weighted overall: Data ×0.35, Process ×0.25, People ×0.25, Technology ×0.15
    overall = round(
        scores.get("data", 0) * 0.35 +
        scores.get("process", 0) * 0.25 +
        scores.get("people", 0) * 0.25 +
        scores.get("technology", 0) * 0.15,
        1
    )
    scores["overall"] = overall
    
    return scores

def get_traffic_light(score: float) -> str:
    """Return traffic light status based on score"""
    if score >= 4:
        return "green"
    elif score >= 3:
        return "amber"
    return "red"

@api_router.get("/quick-assessment/questions")
async def get_quick_assessment_questions():
    """Get all quick assessment questions"""
    return {"questions": QUICK_ASSESSMENT_QUESTIONS, "total": len(QUICK_ASSESSMENT_QUESTIONS)}

@api_router.post("/quick-assessment/submit")
async def submit_quick_assessment(data: QuickAssessmentSubmit):
    """Submit quick assessment answers and get results (no auth required)"""
    scores = calculate_quick_scores(data.answers)
    
    overall_level = max(1, min(5, round(scores["overall"])))
    level_name = LEVEL_NAMES.get(overall_level, "Unknown")
    gap_description = LEVEL_GAPS.get(overall_level, "")
    
    traffic_lights = {
        "people": get_traffic_light(scores.get("people", 0)),
        "process": get_traffic_light(scores.get("process", 0)),
        "data": get_traffic_light(scores.get("data", 0)),
        "technology": get_traffic_light(scores.get("technology", 0)),
        "overall": get_traffic_light(scores.get("overall", 0))
    }
    
    level_names = {
        "people": LEVEL_NAMES.get(max(1, min(5, round(scores.get("people", 0)))), "Unknown"),
        "process": LEVEL_NAMES.get(max(1, min(5, round(scores.get("process", 0)))), "Unknown"),
        "data": LEVEL_NAMES.get(max(1, min(5, round(scores.get("data", 0)))), "Unknown"),
        "technology": LEVEL_NAMES.get(max(1, min(5, round(scores.get("technology", 0)))), "Unknown"),
        "overall": level_name
    }
    
    # Store in database for potential later save
    quick_doc = {
        "company_name": data.company_name,
        "industry": data.industry,
        "respondent_name": data.respondent_name,
        "respondent_email": data.respondent_email,
        "answers": data.answers,
        "scores": scores,
        "traffic_lights": traffic_lights,
        "level_names": level_names,
        "overall_level": overall_level,
        "gap_description": gap_description,
        "assessment_type": "screening",
        "user_id": None,  # Not linked to user yet
        "created_at": datetime.now(timezone.utc).isoformat(),
        "saved": False
    }
    
    result = await db.quick_assessments.insert_one(quick_doc)
    
    # Notify admins about new quick assessment
    await create_notification(
        notif_type="quick_assessment",
        title="Quick Assessment Completed",
        message=f"{data.company_name} ({data.industry}) completed a Quick Check. Overall: {scores.get('overall', 0):.1f}/5.",
        admin_only=True,
        meta={"quick_id": str(result.inserted_id), "company_name": data.company_name, "score": scores.get("overall", 0)}
    )
    
    return {
        "id": str(result.inserted_id),
        "company_name": data.company_name,
        "industry": data.industry,
        "scores": scores,
        "traffic_lights": traffic_lights,
        "level_names": level_names,
        "overall_level": overall_level,
        "level_name": level_name,
        "gap_description": gap_description,
        "cta_message": f"Based on your score of {scores['overall']}/5, your organisation is at the {level_name} stage. Companies at this level typically have {gap_description}. A full PPDT assessment takes 60–90 minutes and produces a prioritised improvement roadmap."
    }

@api_router.post("/quick-assessment/{quick_id}/save")
async def save_quick_assessment(quick_id: str, current_user: dict = Depends(get_current_user)):
    """Save a quick assessment to user's account"""
    quick = await db.quick_assessments.find_one({"_id": ObjectId(quick_id)})
    if not quick:
        raise HTTPException(status_code=404, detail="Quick assessment not found")
    
    # Update with user_id
    await db.quick_assessments.update_one(
        {"_id": ObjectId(quick_id)},
        {"$set": {"user_id": current_user["id"], "saved": True}}
    )
    
    return {"message": "Quick assessment saved to your account", "id": quick_id}

@api_router.get("/quick-assessment/{quick_id}")
async def get_quick_assessment(quick_id: str):
    """Get a quick assessment by ID (for PDF generation)"""
    quick = await db.quick_assessments.find_one({"_id": ObjectId(quick_id)})
    if not quick:
        raise HTTPException(status_code=404, detail="Quick assessment not found")
    
    return {
        "id": str(quick["_id"]),
        **{k: v for k, v in quick.items() if k != "_id"}
    }

@api_router.get("/quick-assessment/{quick_id}/pdf")
async def generate_quick_assessment_pdf(quick_id: str):
    """Generate PDF for quick assessment"""
    quick = await db.quick_assessments.find_one({"_id": ObjectId(quick_id)})
    if not quick:
        raise HTTPException(status_code=404, detail="Quick assessment not found")

    buffer = build_quick_assessment_pdf(quick)
    filename = (
        f"PortfolioHealth_Quick_Assessment_"
        f"{quick.get('company_name', 'Report').replace(' ', '_')}_{quick_id[:8]}.pdf"
    )
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/quick-assessments")
async def get_user_quick_assessments(current_user: dict = Depends(get_current_user)):
    """Get all quick assessments for current user"""
    quick_assessments = await db.quick_assessments.find(
        {"user_id": current_user["id"]},
        {"_id": 1, "company_name": 1, "industry": 1, "scores": 1, "traffic_lights": 1, "level_names": 1, "created_at": 1, "assessment_type": 1}
    ).sort("created_at", -1).to_list(100)
    
    return [{"id": str(q["_id"]), **{k: v for k, v in q.items() if k != "_id"}} for q in quick_assessments]

# Include the router in the main app
app.include_router(api_router)

# SPA catch-all: serve React index.html for all non-API routes (fixes page refresh 404)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve React SPA for any non-API route (handles browser refresh)"""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    index_path = "/app/frontend/build/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # In dev, the frontend dev server handles this
    raise HTTPException(status_code=404, detail="Not found")

# CORS configuration — dynamically allow the request origin for cookie-based auth
class DynamicCORSMiddleware:
    """Allow any origin while supporting credentials by echoing the request Origin header."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        from starlette.requests import Request as StarletteRequest
        request = StarletteRequest(scope, receive)
        origin = request.headers.get("origin", "")

        if request.method == "OPTIONS":
            response = Response(status_code=200)
            response.headers["access-control-allow-origin"] = origin or "*"
            response.headers["access-control-allow-credentials"] = "true"
            response.headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
            response.headers["access-control-allow-headers"] = "content-type, authorization, cookie"
            response.headers["access-control-max-age"] = "600"
            await response(scope, receive, send)
            return

        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                raw_headers = list(message.get("headers", []))
                # Remove any existing CORS headers
                raw_headers = [(k, v) for k, v in raw_headers if k.lower() not in [
                    b"access-control-allow-origin",
                    b"access-control-allow-credentials",
                    b"access-control-allow-methods",
                    b"access-control-allow-headers",
                ]]
                raw_headers.append((b"access-control-allow-origin", (origin or "*").encode()))
                raw_headers.append((b"access-control-allow-credentials", b"true"))
                message["headers"] = raw_headers
            await send(message)

        await self.app(scope, receive, send_with_cors)

app.add_middleware(DynamicCORSMiddleware)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup event - create indexes and seed admin
@app.on_event("startup")
async def startup_event():
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.assessments.create_index("user_id")
    await db.assessments.create_index("company_id")
    await db.companies.create_index("user_id")
    await db.notifications.create_index("user_id")
    await db.notifications.create_index("created_at")
    
    # Seed admin user
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
