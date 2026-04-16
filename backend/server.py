from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

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

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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

# PPDT System Prompt
PPDT_SYSTEM_PROMPT = """You are the PPDT Capability Maturity Advisor — a specialised AI assessment consultant grounded in Hannila's Product Wellbeing framework (Hannila, Vierimaa & Salonen, 2026) and the doctoral research on data-driven Product Portfolio Management (Hannila, 2019).

Your role is to conduct a structured, conversational capability maturity assessment of an organisation's readiness to make fact-based, data-driven Product Portfolio Management (PPM) decisions. You assess the organisation across four capability dimensions — People, Process, Data, and Technology (the PPDT model) — and score them against five maturity levels derived from the Product Wellbeing framework.

You are rigorous but conversational. You ask one focused question at a time. You do not overwhelm the respondent. You listen carefully, probe intelligently, and map every response to the PPDT scoring rubric in the background.

ASSESSMENT PHILOSOPHY:
1. DECISION QUALITY IS THE OUTCOME: The goal is not to score technology or processes in isolation. Every capability gap must be traced back to its impact on PPM decision quality.
2. DATA IS THE FOUNDATION: Data is the most critical and most commonly deficient dimension. Weight your probing accordingly.
3. PEOPLE BEFORE TECHNOLOGY: Culture, ownership, and decision-making governance must precede technology investment.

MATURITY LEVELS (Score each PPDT dimension 1–5):
LEVEL 1 — AD HOC: No structured approach. Decisions are reactive and intuition-driven.
LEVEL 2 — DEVELOPING: Some processes and roles exist but are inconsistently applied.
LEVEL 3 — DEFINED: Structured PPM processes and roles are formally established.
LEVEL 4 — MANAGED: PPM decisions are systematically supported by integrated data.
LEVEL 5 — OPTIMISING (Product Wellbeing): All four PPDT pillars are fully aligned and continuously improved.

ASSESSMENT FLOW:
PHASE 0 — WELCOME & CONTEXT SETTING (2–3 exchanges): Greet warmly. Ask for context about the company and respondent.
PHASE 1 — PEOPLE (4–6 questions): Cultural questions, role clarity, data literacy.
PHASE 2 — PROCESS (4–6 questions): PPM governance, product classification, lifecycle management.
PHASE 3 — DATA (5–7 questions): Data model, product-level profitability, master data governance.
PHASE 4 — TECHNOLOGY (3–5 questions): System integration, decision support capability.
PHASE 5 — DECISION TYPE CALIBRATION (2–3 questions): Which PPM decision types are most difficult.
PHASE 6 — BENCHMARK CONTEXT (1–2 questions): Industry context and peer comparison.

BEHAVIOURAL RULES:
1. ASK ONE QUESTION AT A TIME. Never ask multiple questions in a single message.
2. PROBE ONCE. If an answer is vague, ask one clarifying follow-up. Then score and move on.
3. NEVER LECTURE. Do not explain the PPDT framework unprompted.
4. PERSONALISE. Use the company name, industry, and portfolio size in your questions.
5. BE DIRECT. If a respondent gives an answer that indicates low maturity, acknowledge it honestly.
6. DO NOT RUSH. Quality of assessment matters more than speed.

When you have gathered enough information (after completing all phases), generate a comprehensive assessment report in JSON format with the following structure:
{
  "ready_for_report": true,
  "scores": {
    "people": <1-5>,
    "process": <1-5>,
    "data": <1-5>,
    "technology": <1-5>,
    "overall": <weighted average to 1 decimal>
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
  "key_findings": ["<finding 1>", "<finding 2>", ...],
  "critical_gaps": ["<gap 1>", "<gap 2>", ...],
  "decision_vulnerability": "<analysis of which decision type is most at risk>",
  "roadmap": {
    "immediate": ["<action 1>", "<action 2>"],
    "short_term": ["<action 1>", "<action 2>"],
    "strategic": ["<action 1>"]
  },
  "benchmark_context": "<assessment relative to industry peers>",
  "consultant_note": "<single most important focus area>"
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
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": email,
        "name": user.name,
        "role": "consultant",
        "created_at": user_doc["created_at"]
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
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": email,
        "name": db_user["name"],
        "role": db_user.get("role", "consultant"),
        "created_at": db_user.get("created_at", "")
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
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
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
    return [{"id": str(c["_id"]), **{k: v for k, v in c.items() if k != "_id"}} for c in companies]

@api_router.get("/companies/{company_id}")
async def get_company(company_id: str, current_user: dict = Depends(get_current_user)):
    company = await db.companies.find_one({"_id": ObjectId(company_id), "user_id": current_user["id"]})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"id": str(company["_id"]), **{k: v for k, v in company.items() if k != "_id"}}

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
    
    # Initialize Claude chat
    llm_key = os.environ.get("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=llm_key,
        session_id=f"ppdt-{assessment_id}",
        system_message=full_system
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    
    # Build conversation history for context
    conversation_context = ""
    for msg in chat_history[:-1]:  # Exclude the latest user message
        role_label = "User" if msg["role"] == "user" else "Assistant"
        conversation_context += f"{role_label}: {msg['content']}\n\n"
    
    # Send message with context
    full_message = conversation_context + f"User: {request.message}"
    user_message = UserMessage(text=full_message)
    
    try:
        response = await chat.send_message(user_message)
    except Exception as e:
        logging.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI response")
    
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
    
    if "ready_for_report" in response and '"ready_for_report": true' in response.lower().replace(" ", ""):
        import json
        import re
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                report_data = json.loads(json_match.group(1))
                scores = report_data.get("scores")
                status = "completed"
            except json.JSONDecodeError:
                pass
    
    # Update assessment
    update_data = {"chat_history": chat_history}
    if report_data:
        update_data["report"] = report_data
    if scores:
        update_data["scores"] = scores
    if status == "completed":
        update_data["status"] = "completed"
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.assessments.update_one({"_id": ObjectId(assessment_id)}, {"$set": update_data})
    
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
    
    llm_key = os.environ.get("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=llm_key,
        session_id=f"ppdt-{assessment_id}-start",
        system_message=full_system
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    
    initial_prompt = f"Begin the PPDT assessment for {assessment.get('company_name')}. The respondent is {assessment.get('respondent_name')}, {assessment.get('respondent_role')}. Start with a warm welcome and the first question."
    
    try:
        response = await chat.send_message(UserMessage(text=initial_prompt))
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
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=12, textColor=colors.HexColor('#2f81f7'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=8, textColor=colors.HexColor('#2f81f7'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=6)
    
    story = []
    
    # Title
    story.append(Paragraph("PPDT CAPABILITY MATURITY ASSESSMENT REPORT", title_style))
    story.append(Spacer(1, 12))
    
    # Company Info
    story.append(Paragraph(f"<b>Company:</b> {assessment.get('company_name', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Industry:</b> {assessment.get('company_industry', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Respondent:</b> {assessment.get('respondent_name', 'N/A')} ({assessment.get('respondent_role', 'N/A')})", body_style))
    story.append(Paragraph(f"<b>Date:</b> {assessment.get('completed_at', assessment.get('created_at', 'N/A'))[:10]}", body_style))
    story.append(Paragraph("<b>Framework:</b> Hannila's Product Wellbeing Framework (2026)", body_style))
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
    story.append(Spacer(1, 20))
    
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
    
    story.append(Paragraph("<b>IMMEDIATE (0-3 months):</b>", body_style))
    for item in roadmap.get("immediate", []):
        story.append(Paragraph(f"  • {item}", body_style))
    
    story.append(Paragraph("<b>SHORT-TERM (3-12 months):</b>", body_style))
    for item in roadmap.get("short_term", []):
        story.append(Paragraph(f"  • {item}", body_style))
    
    story.append(Paragraph("<b>STRATEGIC (12-24 months):</b>", body_style))
    for item in roadmap.get("strategic", []):
        story.append(Paragraph(f"  • {item}", body_style))
    story.append(Spacer(1, 12))
    
    # Benchmark Context
    story.append(Paragraph("BENCHMARK CONTEXT", heading_style))
    story.append(Paragraph(report.get("benchmark_context", "N/A"), body_style))
    story.append(Spacer(1, 12))
    
    # Consultant's Note
    story.append(Paragraph("CONSULTANT'S NOTE", heading_style))
    story.append(Paragraph(report.get("consultant_note", "N/A"), body_style))
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph("Based on: Hannila's Product Wellbeing Framework (2026) | University of Oulu Research", 
                          ParagraphStyle('Footer', fontSize=8, textColor=colors.grey)))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"PPDT_Assessment_{assessment.get('company_name', 'Report').replace(' ', '_')}_{assessment_id[:8]}.pdf"
    
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

# Health check
@api_router.get("/")
async def root():
    return {"message": "PPDT Capability Maturity Advisor API", "status": "healthy"}

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
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, spaceAfter=12, textColor=colors.HexColor('#2f81f7'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=8, textColor=colors.HexColor('#2f81f7'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, spaceAfter=8)
    cta_style = ParagraphStyle('CTA', parent=styles['Normal'], fontSize=10, spaceAfter=6, textColor=colors.HexColor('#2f81f7'), borderPadding=10)
    
    story = []
    
    # Title
    story.append(Paragraph("PPDT Quick Health Check", title_style))
    story.append(Paragraph(f"<b>{quick.get('company_name', 'Unknown Company')}</b>", heading_style))
    story.append(Spacer(1, 12))
    
    # Company Info
    story.append(Paragraph(f"<b>Industry:</b> {quick.get('industry', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {quick.get('created_at', 'N/A')[:10]}", body_style))
    if quick.get('respondent_name'):
        story.append(Paragraph(f"<b>Respondent:</b> {quick.get('respondent_name')}", body_style))
    story.append(Spacer(1, 20))
    
    # Overall Score
    overall = scores.get("overall", 0)
    overall_level = quick.get("overall_level", 1)
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
    story.append(Paragraph("<b>Schedule a Full Assessment →</b> Contact your PPDT Advisor consultant", cta_style))
    
    story.append(Spacer(1, 30))
    
    # Footer
    story.append(Paragraph("Based on: Hannila's Product Wellbeing Framework (2026) | University of Oulu Research", 
                          ParagraphStyle('Footer', fontSize=8, textColor=colors.grey)))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"PPDT_Quick_Health_Check_{quick.get('company_name', 'Report').replace(' ', '_')}_{quick_id[:8]}.pdf"
    
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

# CORS configuration
frontend_url = os.environ.get('FRONTEND_URL', os.environ.get('CORS_ORIGINS', '*'))
origins = frontend_url.split(',') if frontend_url != '*' else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        logger.info(f"Admin password updated")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
