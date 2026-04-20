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
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.units import inch
import urllib.request

# LLM Integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

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
    
    # Add user message to history
    user_msg = {
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    chat_history = assessment.get("chat_history", [])
    chat_history.append(user_msg)
    
    # Build context for Claude
    company_context = f"""
Company: {assessment.get('company_name', 'Unknown')}
Industry: {assessment.get('company_industry', 'Unknown')}
Respondent: {assessment.get('respondent_name', 'Unknown')} ({assessment.get('respondent_role', 'Unknown')})
Current Phase: {assessment.get('current_phase', 'welcome')}
"""
    
    full_system = PPDT_SYSTEM_PROMPT + "\n\nCurrent Assessment Context:\n" + company_context
    
    # Build messages for Claude from chat history (limit to last 40 messages to stay within limits)
    claude_messages = []
    for msg in chat_history:
        if msg["role"] in ["user", "assistant"]:
            claude_messages.append({"role": msg["role"], "content": msg["content"]})
    # Keep last 40 messages to avoid token overflow
    if len(claude_messages) > 40:
        claude_messages = claude_messages[-40:]
    if not claude_messages:
        claude_messages = [{"role": "user", "content": request.message}]

    # Initialize Claude chat via Emergent integrations
    try:
        chat = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"assessment-chat-{assessment_id}",
            system_message=full_system,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        for msg in claude_messages:
            if msg["role"] == "user":
                chat.messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                chat.messages.append({"role": "assistant", "content": msg["content"]})
        response = await chat.send_message(UserMessage(text=request.message))
    except Exception as e:
        logging.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI response. Please try again.")
    
    # Add assistant response to history
    assistant_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    chat_history.append(assistant_msg)
    
    # Check if report is ready
    report_data = None
    scores = None
    status = assessment.get("status", "in_progress")
    
    if "ready_for_report" in response:
        import json as json_mod
        import re
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                report_data = json_mod.loads(json_match.group(1))
                if report_data.get("ready_for_report"):
                    scores = report_data.get("scores")
                    status = "completed"
            except json_mod.JSONDecodeError as je:
                logging.error(f"JSON parse error: {je}")
        else:
            # Try to find JSON without code block markers
            json_match2 = re.search(r'\{[\s\S]*"ready_for_report"[\s\S]*\}', response)
            if json_match2:
                try:
                    report_data = json_mod.loads(json_match2.group(0))
                    if report_data.get("ready_for_report"):
                        scores = report_data.get("scores")
                        status = "completed"
                except json_mod.JSONDecodeError:
                    pass
    
    # Update assessment
    update_data = {"chat_history": chat_history}
    if report_data:
        # Ensure weights exist with fallback to equal weights
        if not report_data.get("weights_raw"):
            report_data["weights_raw"] = {"people": 5, "process": 5, "data": 5, "technology": 5}
        if not report_data.get("weights_normalised"):
            raw = report_data["weights_raw"]
            total = sum(raw.values()) or 1
            report_data["weights_normalised"] = {k: round(v / total, 4) for k, v in raw.items()}
        update_data["report"] = report_data
        update_data["weights_raw"] = report_data.get("weights_raw")
        update_data["weights_normalised"] = report_data.get("weights_normalised")
    if scores:
        update_data["scores"] = scores
    if status == "completed":
        update_data["status"] = "completed"
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.assessments.update_one({"_id": ObjectId(assessment_id)}, {"$set": update_data})
    
    # Notify on assessment completion
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
            meta={"assessment_id": assessment_id, "company_name": company_name, "score": overall_score, "consultant": current_user.get("name", "")}
        )
    
    return {
        "message": assistant_msg,
        "report_ready": report_data is not None,
        "report": report_data
    }

# Start Assessment (generate initial greeting)
@api_router.post("/assessments/{assessment_id}/start")
async def start_assessment(assessment_id: str, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if assessment.get("chat_history") and len(assessment["chat_history"]) > 0:
        return {"message": {"role": "assistant", "content": assessment["chat_history"][0]["content"], "timestamp": assessment["chat_history"][0]["timestamp"]}}
    
    # Generate initial greeting
    company_context = f"""
Company: {assessment.get('company_name', 'Unknown')}
Industry: {assessment.get('company_industry', 'Unknown')}
Respondent: {assessment.get('respondent_name', 'Unknown')} ({assessment.get('respondent_role', 'Unknown')})
"""
    
    full_system = PPDT_SYSTEM_PROMPT + "\n\nCurrent Assessment Context:\n" + company_context
    
    try:
        chat = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"assessment-start-{assessment_id}",
            system_message=full_system,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        response = await chat.send_message(UserMessage(text="Please begin the assessment by introducing yourself and asking the first question."))
    except Exception as e:
        logging.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start assessment")
    
    greeting_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.assessments.update_one(
        {"_id": ObjectId(assessment_id)},
        {"$set": {"chat_history": [greeting_msg]}}
    )
    
    return {"message": greeting_msg}

# PDF Report Generation
LOGO_URL = "https://static.prod-images.emergentagent.com/jobs/ad26f002-f220-4b9d-b343-979dba7f2367/images/6407f98124d827501f865028cbbf81566506fd19a8f17f5fd5b271241d491414.png"

def get_pdf_logo():
    """Download logo and return as BytesIO for reportlab"""
    try:
        logo_data = BytesIO()
        req = urllib.request.urlopen(LOGO_URL, timeout=5)
        logo_data.write(req.read())
        logo_data.seek(0)
        return logo_data
    except Exception:
        return None

def build_pdf_header(story, styles, title_text=""):
    """Professional PDF header for management-level reports"""
    # Brand colors
    brand_dark = colors.HexColor('#1A1A2E')
    brand_blue = colors.HexColor('#2f81f7')
    brand_cyan = colors.HexColor('#00B4D8')
    
    # Header bar - dark navy background
    header_data = [[""]]
    header_table = Table(header_data, colWidths=[490], rowHeights=[60])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), brand_dark),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    # Brand text on dark header
    brand_style = ParagraphStyle('BrandName', fontSize=20, fontName='Helvetica-Bold', textColor=colors.white, leading=24)
    sub_style = ParagraphStyle('BrandSub', fontSize=8, textColor=colors.HexColor('#8899AA'), leading=10)
    
    brand_content = Table([
        [Paragraph("PortfolioHealth Advisor", brand_style)],
        [Paragraph("PPM Capability Maturity Assessment  |  University of Oulu", sub_style)]
    ], colWidths=[450])
    brand_content.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (0, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    # Wrap in the dark header
    header_data2 = [[brand_content]]
    header_bar = Table(header_data2, colWidths=[490], rowHeights=[56])
    header_bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), brand_dark),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_bar)
    
    # Thin accent line
    accent_line = Table([[""]],colWidths=[490], rowHeights=[3])
    accent_line.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), brand_cyan),
    ]))
    story.append(accent_line)
    story.append(Spacer(1, 20))
    
    if title_text:
        title_style = ParagraphStyle('ReportTitle', fontName='Helvetica-Bold', fontSize=16, spaceAfter=8, textColor=brand_dark)
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 6))

def build_pdf_closing(story, styles):
    """Add closing statement CTA to PDF"""
    closing_style = ParagraphStyle('Closing', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#333333'),
                                   borderPadding=12, backColor=colors.HexColor('#FFF8E1'), borderColor=colors.HexColor('#FFB300'),
                                   borderWidth=1, borderRadius=4, spaceAfter=8, leading=14)
    footer_style = ParagraphStyle('Footer', fontSize=8, textColor=colors.grey, alignment=1)
    
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Thank you for completing this capability maturity assessment. If you would like further analysis, "
        f"expert input, or tailored recommendations based on your results, please reach out via email to arrange "
        f"a follow-up consultation: <b>{CONTACT_EMAIL}</b>",
        closing_style
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph("© 2026 PortfolioHealth Advisor · Based on PPM Capability Maturity Research · University of Oulu", footer_style))

@api_router.get("/assessments/{assessment_id}/pdf")
async def generate_pdf_report(assessment_id: str, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if not assessment.get("report"):
        raise HTTPException(status_code=400, detail="Assessment report not yet generated")
    
    report = assessment["report"]
    scores = report.get("scores", {})
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=8, textColor=colors.HexColor('#2f81f7'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=6)
    gov_style = ParagraphStyle('Governance', parent=styles['Normal'], fontSize=9, spaceAfter=4, textColor=colors.HexColor('#6B4C00'),
                               backColor=colors.HexColor('#FFFDE7'), borderPadding=6, borderColor=colors.HexColor('#FFD54F'),
                               borderWidth=0.5, leading=12)
    
    story = []
    
    # Logo Header
    build_pdf_header(story, styles, "PPDT CAPABILITY MATURITY ASSESSMENT REPORT")
    
    # Company Info
    story.append(Paragraph(f"<b>Company:</b> {assessment.get('company_name', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Industry:</b> {assessment.get('company_industry', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Respondent:</b> {assessment.get('respondent_name', 'N/A')} ({assessment.get('respondent_role', 'N/A')})", body_style))
    story.append(Paragraph(f"<b>Date:</b> {assessment.get('completed_at', assessment.get('created_at', 'N/A'))[:10]}", body_style))
    story.append(Spacer(1, 20))
    
    # Overall Score
    overall = scores.get("overall", "N/A")
    level_names = report.get("level_names", {})
    story.append(Paragraph(f"<b>OVERALL MATURITY LEVEL:</b> {overall} / 5.0 — {level_names.get('overall', 'N/A')}", heading_style))
    story.append(Spacer(1, 12))
    
    # Dimension Scores Table
    story.append(Paragraph("DIMENSION SCORES", heading_style))
    dim_summaries = report.get("dimension_summaries", {})
    
    table_data = [["Dimension", "Score", "Level", "Summary"]]
    for dim in ["people", "process", "data", "technology"]:
        table_data.append([
            dim.capitalize(),
            str(scores.get(dim, "N/A")),
            level_names.get(dim, "N/A"),
            dim_summaries.get(dim, "N/A")[:60] + "..." if len(dim_summaries.get(dim, "")) > 60 else dim_summaries.get(dim, "N/A")
        ])
    
    table = Table(table_data, colWidths=[80, 50, 80, 280])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2f81f7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))
    
    # Weighted Score Breakdown
    weights_raw = report.get("weights_raw", {"people": 5, "process": 5, "data": 5, "technology": 5})
    raw_total = sum(weights_raw.values()) or 1
    weights_norm = report.get("weights_normalised", {d: weights_raw.get(d, 5) / raw_total for d in ["people", "process", "data", "technology"]})
    
    story.append(Paragraph("WEIGHTED SCORE CALCULATION", heading_style))
    weight_data = [["Pillar", "Raw Score", "Weight (1-10)", "Normalised", "Contribution"]]
    for dim in ["people", "process", "data", "technology"]:
        s = scores.get(dim, 0)
        w_raw = weights_raw.get(dim, 5)
        w_norm = weights_norm.get(dim, 0.25)
        contrib = s * w_norm
        weight_data.append([dim.capitalize(), str(s), str(w_raw), f"{w_norm:.2f}", f"{contrib:.2f}"])
    weight_data.append(["", "", "", "Overall:", f"{scores.get('overall', 0):.2f}"])
    
    wt = Table(weight_data, colWidths=[80, 60, 70, 70, 80])
    wt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A1A2E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f0f0f0')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    story.append(wt)
    story.append(Spacer(1, 16))
    
    # Governance Observations (Levels 4-5 only)
    gov_obs = report.get("governance_observations", {})
    has_gov = any(v and "N/A" not in str(v) and "below" not in str(v).lower() for v in gov_obs.values())
    if has_gov:
        story.append(Paragraph("GOVERNANCE INDICATORS (Levels 4–5)", heading_style))
        for dim in ["people", "process", "data", "technology"]:
            obs = gov_obs.get(dim, "")
            if obs and "N/A" not in str(obs) and "below" not in str(obs).lower():
                story.append(Paragraph(f"<b>{dim.capitalize()} — Governance:</b> {obs}", gov_style))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 12))
    
    # Governance & Ownership
    story.append(Paragraph("GOVERNANCE & OWNERSHIP", heading_style))
    story.append(Paragraph("Governance is the connective tissue between all four PPDT dimensions. Without clear ownership and accountability, even high capability produces unreliable portfolio decisions.", body_style))
    if report.get("governance_assessment"):
        story.append(Paragraph(f"<i>{report['governance_assessment']}</i>", body_style))
    story.append(Spacer(1, 8))
    
    # Management Commitment
    story.append(Paragraph("MANAGEMENT COMMITMENT", heading_style))
    story.append(Paragraph("Management commitment acts as a multiplier on all capability investments. Without leadership buy-in, PPM improvements produce limited, short-lived change.", body_style))
    if report.get("management_commitment_assessment"):
        story.append(Paragraph(f"<i>{report['management_commitment_assessment']}</i>", body_style))
    story.append(Spacer(1, 12))
    
    # Key Findings
    story.append(Paragraph("KEY FINDINGS", heading_style))
    for finding in report.get("key_findings", []):
        story.append(Paragraph(f"• {finding}", body_style))
    story.append(Spacer(1, 12))
    
    # Critical Gaps
    story.append(Paragraph("CRITICAL CAPABILITY GAPS", heading_style))
    for gap in report.get("critical_gaps", []):
        story.append(Paragraph(f"• {gap}", body_style))
    story.append(Spacer(1, 12))
    
    # Decision Vulnerability
    story.append(Paragraph("DECISION-TYPE VULNERABILITY ANALYSIS", heading_style))
    story.append(Paragraph(report.get("decision_vulnerability", "N/A"), body_style))
    story.append(Spacer(1, 12))
    
    # Roadmap
    story.append(Paragraph("IMPROVEMENT ROADMAP", heading_style))
    roadmap = report.get("roadmap", {})
    
    for phase_key, phase_title in [("immediate", "PHASE 1 — IMMEDIATE (0–3 months)"), ("short_term", "PHASE 2 — SHORT-TERM (3–12 months)"), ("strategic", "PHASE 3 — STRATEGIC (12+ months)")]:
        phase_data = roadmap.get(phase_key, [])
        story.append(Paragraph(f"<b>{phase_title}</b>", body_style))
        actions = phase_data.get("actions", phase_data) if isinstance(phase_data, dict) else phase_data
        if isinstance(actions, list):
            for item in actions:
                story.append(Paragraph(f"  • {item}", body_style))
        if isinstance(phase_data, dict):
            if phase_data.get("governance_milestone"):
                story.append(Paragraph(f"  <i>Governance Milestone:</i> {phase_data['governance_milestone']}", body_style))
            if phase_data.get("management_commitment"):
                story.append(Paragraph(f"  <i>Management Commitment:</i> {phase_data['management_commitment']}", body_style))
            if phase_data.get("expected_gain"):
                story.append(Paragraph(f"  <i>Expected Gain:</i> {phase_data['expected_gain']}", body_style))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 12))
    
    # Benchmark Context
    story.append(Paragraph("BENCHMARK CONTEXT", heading_style))
    story.append(Paragraph(report.get("benchmark_context", "N/A"), body_style))
    story.append(Spacer(1, 12))
    
    # Consultant's Note
    story.append(Paragraph("CONSULTANT'S NOTE", heading_style))
    story.append(Paragraph(report.get("consultant_note", "N/A"), body_style))
    
    # Closing Statement
    build_pdf_closing(story, styles)
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"PortfolioHealth_Assessment_{assessment.get('company_name', 'Report').replace(' ', '_')}_{assessment_id[:8]}.pdf"
    
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
    
    scores = quick.get("scores", {})
    traffic_lights = quick.get("traffic_lights", {})
    level_names = quick.get("level_names", {})
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=8, textColor=colors.HexColor('#2f81f7'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, spaceAfter=8)
    cta_style = ParagraphStyle('CTA', parent=styles['Normal'], fontSize=10, spaceAfter=6, textColor=colors.HexColor('#2f81f7'), borderPadding=10)
    
    story = []
    
    # Logo Header
    build_pdf_header(story, styles, "PPDT QUICK HEALTH CHECK REPORT")
    
    # Company Info
    story.append(Paragraph(f"<b>Industry:</b> {quick.get('industry', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {quick.get('created_at', 'N/A')[:10]}", body_style))
    if quick.get('respondent_name'):
        story.append(Paragraph(f"<b>Respondent:</b> {quick.get('respondent_name')}", body_style))
    story.append(Spacer(1, 20))
    
    # Overall Score
    overall = scores.get("overall", 0)
    level_name = quick.get("level_names", {}).get("overall", "Unknown")
    
    story.append(Paragraph(f"<b>OVERALL MATURITY LEVEL: {overall} / 5.0 — {level_name}</b>", heading_style))
    story.append(Spacer(1, 16))
    
    # Dimension Scores Table with Traffic Lights
    def get_traffic_color(status):
        if status == "green":
            return colors.HexColor('#238636')
        elif status == "amber":
            return colors.HexColor('#D29922')
        return colors.HexColor('#F85149')
    
    table_data = [["Dimension", "Score", "Level", "Status"]]
    for dim in ["people", "process", "data", "technology"]:
        score = scores.get(dim, 0)
        level = level_names.get(dim, "N/A")
        status = traffic_lights.get(dim, "red").upper()
        table_data.append([dim.capitalize(), str(score), level, status])
    
    table = Table(table_data, colWidths=[100, 60, 100, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2f81f7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    story.append(table)
    story.append(Spacer(1, 24))
    
    # Key Insights
    story.append(Paragraph("KEY INSIGHTS", heading_style))
    
    # Find weakest dimension
    dim_scores = [(dim, scores.get(dim, 0)) for dim in ["people", "process", "data", "technology"]]
    dim_scores.sort(key=lambda x: x[1])
    weakest = dim_scores[0]
    strongest = dim_scores[-1]
    
    story.append(Paragraph(f"• <b>Weakest Area:</b> {weakest[0].capitalize()} ({weakest[1]}/5) — This dimension requires immediate attention.", body_style))
    story.append(Paragraph(f"• <b>Strongest Area:</b> {strongest[0].capitalize()} ({strongest[1]}/5) — Build on this foundation.", body_style))
    
    if scores.get("data", 0) < 3:
        story.append(Paragraph("• <b>Data Gap Alert:</b> Data capability is the most critical bottleneck in PPM maturity. Prioritise data governance.", body_style))
    
    story.append(Spacer(1, 24))
    
    # CTA Box
    story.append(Paragraph("NEXT STEPS", heading_style))
    gap_desc = quick.get("gap_description", "")
    cta_text = f"Based on your score of {overall}/5, your organisation is at the <b>{level_name}</b> stage. Companies at this level typically have {gap_desc}. A full PPDT assessment takes 60–90 minutes and produces a prioritised improvement roadmap with specific, actionable recommendations."
    story.append(Paragraph(cta_text, body_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Schedule a Full Assessment →</b> Contact your PortfolioHealth Advisor consultant", cta_style))
    
    # Closing Statement
    build_pdf_closing(story, styles)
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"PortfolioHealth_Quick_Assessment_{quick.get('company_name', 'Report').replace(' ', '_')}_{quick_id[:8]}.pdf"
    
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
