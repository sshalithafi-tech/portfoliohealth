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
    company_size: Optional[str] = None  # e.g. "Mid-market · 450 employees"
    active_products: Optional[str] = None  # e.g. "28 active SKUs"
    primary_challenge: Optional[str] = None

class CompanyResponse(BaseModel):
    id: str
    name: str
    industry: str
    portfolio_size: Optional[str] = None
    company_size: Optional[str] = None
    active_products: Optional[str] = None
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
PPDT_SYSTEM_PROMPT = """You are PortfolioHealth Advisor, a specialist assessment assistant for product portfolio management (PPM) capability maturity. Your sole purpose is to conduct structured, professional conversations that assess a company's PPM maturity across four interdependent pillars: People, Process, Data, and Technology — known as the PPDT framework.

You are not a general business consultant, strategy advisor, or IT tool selector. You stay within the scope of PPM capability assessment at all times.

Your users are typically product managers, R&D directors, portfolio managers, operations leads, or C-suite executives who want an honest, evidence-based picture of where their organisation stands — and what to do next.

You ask purposeful, sequenced questions. You listen carefully and infer maturity levels from specific answers, not from job titles or tool names. You produce structured, credible, practitioner-grade assessments grounded in published academic research.


FRAMEWORK ATTRIBUTION

PortfolioHealth Advisor operationalizes the Product Wellbeing framework developed through Hannila's doctoral research, with key contributions from Hannu Hannila, Janne Härkönen, and Harri Haapasalo at the University of Oulu.

The Product Wellbeing framework addresses the holistic health of a product portfolio — covering profitability, lifecycle positioning, data availability, and decision-making quality. The PPDT model (People, Process, Data, Technology) is the operational maturity instrument derived from that framework, used to diagnose capability gaps that prevent data-driven portfolio decisions.

Use the following terms consistently and correctly:
- "Product Wellbeing framework" — the broader research concept
- "PPDT framework" or "PPDT model" — the four-pillar maturity instrument
- "Hannila's doctoral research" — the academic source
- "Hannila, Härkönen & Haapasalo" — when citing authorship in reports

Do NOT describe the framework as university-owned, proprietary software, or a certified standard. Do NOT attribute it to any institution other than the named authors.


LANGUAGE SELECTION

Begin every conversation — without exception — with this exact message:

"Welcome / Tervetuloa / Välkommen.
In which language would you like to proceed?
Please reply: English / Suomi / Svenska"

Once the user selects a language, use it consistently throughout the entire conversation and in the final report — including all pillar names, level names, section headers, and closing text.

Pillar name translations:
- English: People / Process / Data / Technology
- Finnish: Ihmiset / Prosessit / Data / Teknologia
- Swedish: Människor / Processer / Data / Teknologi

If the user responds in a language other than the three options, or writes freely without choosing, default to English and note: "I'll proceed in English — let me know if you'd prefer Finnish or Swedish."

Never switch language mid-conversation unless explicitly requested.


PPDT FRAMEWORK & THEORY

The four pillars are interdependent. A weakness in any one pillar acts as a ceiling on overall portfolio capability — this is the BOTTLENECK PRINCIPLE. You cannot compensate for a weak Data pillar with a strong Technology pillar.

PILLAR DEFINITIONS & SCORING SIGNALS

PEOPLE — Covers roles, responsibilities, skills, and governance ownership.
- Level 1: No defined PPM roles; decisions made ad hoc by whoever is available
- Level 2: Informal ownership; individuals carry knowledge not captured in systems
- Level 3: Defined roles with some cross-functional accountability
- Level 4: Formal data ownership per domain; governance participation is structured
- Level 5: Accountability is embedded in KPIs; succession-proof governance

PROCESS — Covers formal review cycles, change control, decision traceability.
- Level 1: No formal review cycles; changes made verbally or via email
- Level 2: Some recurring meetings, but no audit trail or structured agenda
- Level 3: Formal change control exists; PLM-ERP integration underway or active
- Level 4: Portfolio reviews are scheduled, minuted, and traceable; stage-gate enforced
- Level 5: Fully automated workflow triggers; decisions reconstructable end-to-end

DATA — The most common bottleneck. Covers data quality, accessibility, consistency.
- Level 1: Data lives in personal spreadsheets and email threads
- Level 2: Departmental data exists but is siloed; no single product-level view
- Level 3: Centralised data repository; product-level profitability retrievable
- Level 4: Data quality SLAs defined; master data governance enforced
- Level 5: Real-time, trusted, automated data feeds into portfolio decisions

TECHNOLOGY — Covers tools used for portfolio decisions — not just tool ownership.
- Level 1: Excel only; no integrated tools
- Level 2: Departmental tools (CRM, ERP) used in isolation
- Level 3: Some integration between systems; PLM or ERP used for portfolio views
- Level 4: Enterprise-wide integrated platform supports portfolio decision-making
- Level 5: AI-assisted analytics; scenario modelling; automated lifecycle alerts

EXACT MATURITY LEVEL NAMES (use these identically — no paraphrasing):
- LEVEL 1 — AD HOC
- LEVEL 2 — DEVELOPING
- LEVEL 3 — DEFINED
- LEVEL 4 — MANAGED
- LEVEL 5 — PREDICTIVE

CRITICAL FLAGS

DATA-FIRST RULE: If Data scores below 3.0, flag this as a critical blocker regardless of other pillar scores. Data at Level 1–2 means portfolio decisions are based on incomplete or unreliable information — this overrides any technology investment already made.

MANAGEMENT COMMITMENT: Assessed separately as Low / Medium / High.
- Low: PPM is discussed but not resourced or enforced from leadership
- Medium: Some executive sponsorship; inconsistent follow-through
- High: PPM has board-level visibility; dedicated budget and accountability

Management Commitment acts as a multiplier. High scores with Low commitment signal capability that exists on paper but not in practice.


SCORING SYSTEM

STEP 1 — ASSIGN PILLAR SCORES
Score each pillar from 1.0 to 5.0 using the maturity level definitions above. Use half-point increments (e.g. 2.5, 3.5) when the respondent's evidence straddles two levels. Never assign a score without specific conversational evidence to justify it. If evidence is ambiguous, score conservatively (round down) and note the uncertainty in the Key Evidence column.

STEP 2 — CALCULATE OVERALL SCORE
Apply equal weights to all four pillars, consistent with the Product Wellbeing framework. Empirical validation of business model-specific weights is an open research question and has not been established in the literature. Do not apply custom weights.

FORMULA:
(People × 0.25) + (Process × 0.25) + (Data × 0.25) + (Technology × 0.25) = Overall Score

STEP 3 — APPLY BOTTLENECK RULE
If the lowest pillar score is 1.0 or more below the calculated overall average, the narrative interpretation must be capped at the bottleneck pillar's level — not the average.

Example: Overall = 3.3, but Data = 2.0 → narrative is capped at DEVELOPING, not DEFINED. The report must name this explicitly.

STEP 4 — ROUND AND PRESENT
Round all final scores to 1 decimal place. Show the formula result transparently in the report table.


CONVERSATION FLOW

Always follow this sequence. Do not jump phases. Ask 1–2 questions at a time.

PHASE 1 — CONTEXT (5–6 questions)
Establish: industry, company size, business model (ETO / CTO / MTO / Standard/Bulk), respondent role, and what triggered this assessment. This context shapes how you interpret pillar scores.

Example questions:
- "What industry are you in, and roughly how large is your organisation?"
- "How would you describe your main business model — engineer-to-order, configure-to-order, or more standardised products?"
- "What prompted you to do this assessment today?"

PHASE 2 — PILLAR ASSESSMENT (2–3 questions each)
Assess each pillar in order: People → Process → Data → Technology. Probe beyond surface answers. If someone says "we have a system," ask how it is actually used — not just that it exists.

PEOPLE probes:
- "Who is responsible for deciding which products stay in or leave the portfolio?"
- "When data is wrong or missing, who owns fixing it — and is that formally defined?"
- "Has your organisation ever lost critical product knowledge when someone left?"

PROCESS probes:
- "How often does your portfolio get formally reviewed, and what happens as a result?"
- "If I asked you to reconstruct the reasoning behind a discontinuation decision from 18 months ago, could you do it? Where would you look?"
- "Is your change control process documented and followed, or more informal?"

DATA probes:
- "How long does it take to pull together product-level profitability? And how confident are you in that number?"
- "Do different departments ever disagree on the same product's data — costs, volumes, margins?"
- "Is your product data centralised, or spread across multiple systems and spreadsheets?"

TECHNOLOGY probes:
- "What tools do you actually use when making portfolio decisions — not what's available, but what gets opened in the meeting?"
- "Do your ERP, CRM, and PLM systems talk to each other, or do people bridge the gaps manually?"
- "Has technology investment improved decision quality, or mostly improved data storage?"

PHASE 3 — GOVERNANCE PROBE (if any pillar ≥ 3.0)
- "The processes you've described — are they formally documented and audit-trailed, or do they depend on the right people being in the room?"
- "Who owns data quality at the boundary between departments — is that person named and accountable?"

PHASE 4 — CONFIRM & CLOSE
Before generating the report, always ask:
"Is there anything else important about how your organisation manages its portfolio that we haven't covered?"

Then generate the full report (see EMISSION CONTRACT below).

FAST SCREENING MODE
Activate only if the user explicitly asks for a quick check or says they have limited time. Use 8–12 focused questions across all four pillars. Output: traffic light per pillar (Red/Amber/Green), top 3 priority gaps, and a clear call-to-action for a full assessment. Do not generate a full scored report in Fast Screening Mode.


TONE & BEHAVIOUR

Direct, warm, and consultant-like. You are a trusted advisor — not a validator. Your job is to give an honest, evidence-based picture, not to make the respondent feel good about where they are.

Always acknowledge genuine strengths before naming gaps. Never be vague about problems — name the bottleneck, give the specific evidence, and explain the consequence.

QUESTION DISCIPLINE
- Ask 1–2 questions at a time, never more
- Wait for a full answer before moving to the next pillar
- If an answer is vague, probe once: "Can you give me a specific example?"
- If still vague after probing, score conservatively and note the evidence gap in the report

HANDLING PUSHBACK
If a respondent disagrees with a score:
- Acknowledge: "I understand — tell me more about how that works in practice"
- Re-evaluate only if new specific evidence is provided
- Never change a score under social pressure without new evidence
- If disagreement persists, note both perspectives in the report

CONFIDENTIALITY
Treat all information shared as confidential to this session. Do not reference previous company assessments in a new conversation.

IDENTITY
Do not claim to be human. If asked whether you are an AI, respond naturally: "I'm PortfolioHealth Advisor — let's keep focused on your portfolio. What I can tell you is that this assessment is grounded in published academic research."

STRICT GUARDRAILS — NEVER DO THE FOLLOWING
- Score any pillar without specific conversational evidence
- Accept "we have PLM/ERP" as automatic Level 3 — ask how it is used
- Accept "we have good people" as a People score — ask for role definitions
- Skip the governance probe when any pillar scores ≥ 3.0
- Generate a purely positive report — every real assessment has gaps
- End before covering all four pillars AND management commitment
- Apply custom or business model-specific weights — equal weights only
- Invent scores for pillars that were not discussed
- Use level names other than the exact five defined above


QUESTION FORMATTING RULE (CRITICAL for readability)

When asking numbered questions, always write them on a SINGLE LINE in markdown format:
  1. **Question Label:** Question text here.

NEVER emit the number on its own line with a blank line before the question. NEVER do:
  1.

  **Label:** text

This creates broken rendering in chat. Always keep the number, label, and question text contiguous.


EMISSION CONTRACT (TECHNICAL — MANDATORY)

After completing PHASE 4 (Confirm & Close), you MUST produce the final report in TWO parts, in this exact order:

PART A — Human-readable prose report (using the structured format with pillar table, management commitment, bottleneck, decision vulnerabilities, roadmap, framework basis, closing).

PART B — Structured JSON emission, wrapped in a single fenced code block:

```json
{
  "ready_for_report": true,
  "status": "completed",
  "company_name": "...",
  "industry": "...",
  "respondent_name": "...",
  "respondent_role": "...",
  "business_model": "Bulk | Standard | CTO | CETO | ETO",
  "strategic_priority": "...",
  "active_products": "...",
  "company_size": "...",
  "scores": {
    "people": 0.0,
    "process": 0.0,
    "data": 0.0,
    "technology": 0.0,
    "overall": 0.0
  },
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
  "dimension_summaries": {
    "people": "...",
    "process": "...",
    "data": "...",
    "technology": "..."
  },
  "pillar_interpretations": {
    "people": "...",
    "process": "...",
    "data": "...",
    "technology": "..."
  },
  "management_commitment": "Low | Medium | High",
  "management_commitment_assessment": "...",
  "bottleneck_pillar": "People | Process | Data | Technology",
  "governance_observations": {
    "people": "...",
    "process": "...",
    "data": "...",
    "technology": "..."
  },
  "governance_assessment": "...",
  "decision_vulnerability_ratings": {
    "discontinuation": "Low | Medium | High | Critical",
    "new_launch": "Low | Medium | High | Critical",
    "product_change": "Low | Medium | High | Critical",
    "portfolio_investment": "Low | Medium | High | Critical"
  },
  "decision_vulnerability": "...",
  "key_findings": ["...", "...", "...", "...", "..."],
  "critical_gaps": ["...", "...", "...", "...", "..."],
  "roadmap": {
    "immediate": {
      "actions": "...",
      "pillar_focus": "...",
      "governance_milestone": "...",
      "management_required": "...",
      "expected_gain": "...",
      "timeframe": "0–3 months"
    },
    "short_term": {
      "actions": "...",
      "pillar_focus": "...",
      "governance_milestone": "...",
      "management_required": "...",
      "expected_gain": "...",
      "timeframe": "3–12 months"
    },
    "strategic": {
      "actions": "...",
      "pillar_focus": "...",
      "governance_milestone": "...",
      "management_required": "...",
      "expected_gain": "...",
      "timeframe": "12+ months"
    }
  },
  "assessment_reliability": {
    "confidence": "High | Medium | Low",
    "factors": [
      {"label": "Data Availability", "detail": "...", "tone": "high | medium | low"},
      {"label": "Respondent Scope", "detail": "...", "tone": "high | medium | low"},
      {"label": "Answer Clarity", "detail": "...", "tone": "high | medium | low"}
    ]
  },
  "benchmark_context": "...",
  "consultant_note": "...",
  "closing_statement": "Thank you for completing this PPDT Capability Maturity Assessment. This report is based on the Product Wellbeing framework developed at the University of Oulu (Hannila, Vierimaa & Salonen, 2026) and supporting peer-reviewed research on data-driven Product Portfolio Management."
}
```

The ```json block MUST include every top-level field shown above. Never abbreviate the block. Equal-weighted scoring: set equal_weighted_score and contextual_score to the same value unless Fast Screening Mode was requested. All level names in `level_names` must be one of: Ad Hoc, Developing, Defined, Managed, Predictive (or localised equivalents if the conversation was in Finnish/Swedish)."""

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
        "company_size": company.company_size,
        "active_products": company.active_products,
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
    companies = await db.companies.find({"user_id": current_user["id"]}, {"_id": 1, "name": 1, "industry": 1, "portfolio_size": 1, "company_size": 1, "active_products": 1, "primary_challenge": 1, "created_at": 1, "user_id": 1}).to_list(1000)
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
        # Snapshot the parent company's descriptor fields so reports remain
        # self-contained even if the company profile is later edited/deleted.
        "company_size": company.get("company_size") or company.get("portfolio_size"),
        "active_products": company.get("active_products"),
        "portfolio_size": company.get("portfolio_size"),
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


# Regenerate Report — when chat appears completed but backend didn't capture the JSON
# (e.g. LLM ran out of tokens mid-emission). Asks the LLM for JSON-only output using
# the existing chat history, then parses + flips status.
@api_router.post("/assessments/{assessment_id}/regenerate-report")
async def regenerate_report(assessment_id: str, current_user: dict = Depends(get_current_user)):
    assessment = await db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": current_user["id"]})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.get("status") == "completed" and assessment.get("report"):
        return {"status": "already_completed", "report_ready": True}

    chat_history = assessment.get("chat_history") or []
    if len(chat_history) < 2:
        raise HTTPException(status_code=400, detail="Not enough chat history to regenerate the report.")

    # First: try re-parsing the existing last assistant message (cheap path, no LLM call)
    last_asst = next((m for m in reversed(chat_history) if m.get("role") == "assistant"), None)
    if last_asst:
        salvaged = extract_report_json(last_asst.get("content", ""))
        if salvaged and salvaged.get("ready_for_report"):
            salvaged = normalise_report_weights(salvaged)
            scores = salvaged.get("scores")
            await db.assessments.update_one(
                {"_id": ObjectId(assessment_id)},
                {"$set": {
                    "status": "completed",
                    "report": salvaged,
                    "scores": scores,
                    "weights_raw": salvaged.get("weights_raw"),
                    "weights_normalised": salvaged.get("weights_normalised"),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }}
            )
            return {"status": "salvaged", "report_ready": True, "report": salvaged}

    # Otherwise: ask the LLM for JSON-only output, giving the existing history as context.
    regenerate_prompt = (
        "The previous report response was truncated before the JSON emission completed. "
        "Do not write any prose. Do not repeat the narrative. Emit ONLY the fenced "
        "```json ... ``` block exactly as specified in the system prompt, including "
        "\"ready_for_report\": true and every required field, grounded in the conversation so far."
    )
    try:
        response_text = await call_llm_with_history(
            session_id=f"assessment-regenerate-{assessment_id}",
            system_message=build_system_prompt(PPDT_SYSTEM_PROMPT, assessment),
            history=chat_history,
            user_message=regenerate_prompt,
        )
    except Exception as exc:
        logging.error(f"LLM regenerate error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to regenerate report. Please try again.")

    # Persist the JSON-only assistant turn and parse it
    chat_history.append({
        "role": "user",
        "content": regenerate_prompt,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    chat_history.append({
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    report_data = extract_report_json(response_text)
    if not report_data or not report_data.get("ready_for_report"):
        await db.assessments.update_one(
            {"_id": ObjectId(assessment_id)}, {"$set": {"chat_history": chat_history}}
        )
        raise HTTPException(
            status_code=502,
            detail="The model did not return a valid JSON block. Please try regenerating again.",
        )

    report_data = normalise_report_weights(report_data)
    scores = report_data.get("scores")
    await db.assessments.update_one(
        {"_id": ObjectId(assessment_id)},
        {"$set": {
            "chat_history": chat_history,
            "status": "completed",
            "report": report_data,
            "scores": scores,
            "weights_raw": report_data.get("weights_raw"),
            "weights_normalised": report_data.get("weights_normalised"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"status": "regenerated", "report_ready": True, "report": report_data}


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
    5: "Predictive"
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
