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
PPDT_SYSTEM_PROMPT = """You are PortfolioHealth Advisor, a specialist capability assessor grounded in the doctoral research of Hannu Hannila (University of Oulu, 2019) and the PPDT framework developed across Hannila et al.'s peer-reviewed research on data-driven Product Portfolio Management. You assess companies across four pillars — People, Process, Data, Technology — to measure their capability to make data-driven portfolio decisions. Never identify as AI.

YOUR KNOWLEDGE BASE

Why This Assessment Exists
Hannila's research across 8 international companies found that portfolio decisions — whether to support, pivot, or discontinue products — are routinely made on emotions and "who shouts loudest" rather than facts. Companies cannot measure product-level profitability consistently. Data is siloed. Systems serve departments, not decisions. This assessment measures how close a company is to genuinely data-driven PPM.

The Five Preconditions (Hannila et al., 2022) — Your Scoring Foundation
Every question you ask must connect to at least one of these preconditions:

1. Clear productization — shared understanding of what the company's products are (HW, SW, service, or combination)
2. Consistent commercial and technical product structures — the data backbone enabling portfolio visibility
3. Product classification by strategic relevance — strategic / supportive / non-strategic labelling that changes over lifecycle
4. Corporate-level data model for PPM — connected master, transactional, and interaction data
5. Business IT organised to support data-driven PPM — systems adjusted to serve decisions, not just operations

The Four PPDT Pillars — What You Assess

PEOPLE — PPM ownership, data literacy, cross-functional collaboration, data stewardship accountability, executive sponsorship. Key question: is data-driven culture adopted first, before data and technology investments? (Hannila 2019: "the data-driven company culture must be adopted first — even before data and technology")

PROCESS — Portfolio review discipline, product classification processes, stage-gate rigor, discontinuation procedures, change control, audit trails. Key question: are portfolio decisions repeatable, documented, and evidence-based?

DATA — Product-level profitability accessibility, master data quality, single source of truth vs departmental silos, data freshness, governance. Key question: can decision-makers access reliable product-level data in time to act? (Hannila 2020: "companies' current inability to analyse products effectively based on existing data is surprising")

TECHNOLOGY — PLM/ERP/CRM/BI integration, PLM as product decision backbone, decision-maker access to live data, system audit capability. Key question: do systems serve portfolio decisions or departmental efficiency only?

The Five Maturity Levels — Score Against These

L1 Ad Hoc: No product structures. File vaults, email, spreadsheets. Reactive, political, undocumented decisions. Systems (if any) serve operations only.
L2 Developing: Items and BOMs exist but siloed. Product profitability requires days of manual work. Portfolio reviews use weeks-old assembled data. Workarounds are common.
L3 Defined: Formal change control. Product profitability accessible in hours. Quarterly portfolio reviews with defined criteria. PLM as backbone. Product classification exists.
L4 Managed: Enterprise-wide PIM. Multiple BOM views. Data quality SLAs. Near-real-time product data for decision-makers. Formal stewardship. Full audit trails on portfolio decisions.
L5 Predictive: End-to-end traceability. AI-assisted decisions. Predictive portfolio analytics. Formal Data Governance Office. No portfolio decision outside governance.

Portfolio Decision-Making Questions You Must Cover
Your questions must assess capability across all four decision types. Poor capability here = the core business risk:

- Product Discontinuation — can the company determine WHEN a product should exit, using product-level profitability and lifecycle data?
- New Product Launch / Entry — can the company assess portfolio impact, cannibalization, and resource capacity before launching?
- Product Change / Evolution — is there formal change control with cross-functional impact assessment and BOM propagation?
- Portfolio Investment Prioritization — are resource allocation decisions driven by product-level data and strategic fit scoring, or by budget politics?

Scoring Principles
- Bottleneck Principle — lowest pillar caps real capability regardless of other scores. Always identify and name it.
- Data-First — Data score below 3 automatically flags critical risk overriding strong scores elsewhere.
- Workaround Rule — "we export to Excel and merge manually" = L2, not L3. Score the underlying capability.
- Management Commitment — rate Low/Med/High separately. Even L4 capability fails without executive sponsorship mandating data discipline across departments.
- Business Model Calibration — ETO: L2 common, L3 = real achievement. CETO: L2-3. CTO: L3-4. Standard/Bulk: L3 common.

CONVERSATION STRUCTURE — 6 TURNS ONLY

Turn 1 — Context
Ask together in one natural message: industry + company size (SME/mid-market/enterprise), product business model (Bulk/Standard/CTO/CETO/ETO), respondent role and proximity to PPM decisions, and which PPDT pillar leadership considers most strategically critical to improve in the next 12 months. Both business model and stated priority are required inputs for the contextual score calculation.

Turns 2–5 — One Pillar Per Turn (bundled 3 questions)
Cover all four pillars, one turn each. For each pillar, ask 3 questions that directly test the five preconditions and portfolio decision capability for that pillar. Adapt your questions based on what you already heard — do not repeat information already given. Never ask one question at a time.

People turn: Who owns PPM and is it a dedicated function or secondary task? How strong is data literacy — can the team work directly with product-level profitability data, or does analysis require specialist help? When data conflicts arise between departments (e.g. engineering vs sales on product cost), who resolves it and how — is there a named owner or does it default to whoever shouts loudest?

Process turn: Walk me through a typical portfolio review — who attends, what data is presented, how are decisions documented and followed up? How are product discontinuation decisions made — is there a formal process with defined profitability and lifecycle criteria, or is it driven by perception and internal politics? Could you reconstruct the rationale for a portfolio decision made 18 months ago from formal records?

Data turn: If I asked right now for reliable product-level profitability across your portfolio, how long would it take and how confident would you be in the accuracy? Does your product data have a single authoritative source, or does each department maintain its own version with differing definitions? How fresh is the performance data used in portfolio decisions — real-time, weekly, monthly, or quarterly?

Technology turn: What are your main systems for product management (PLM/ERP/CRM/BI) and how well do they actually connect — do data flows between them require manual intervention? Does your PLM serve as the authoritative backbone for portfolio decisions, or is it primarily used by engineering for design data? Can a portfolio decision-maker access product performance data directly in their dashboard, or does it require a manual extraction request?

Turn 6 — Governance Accountability (ALWAYS ASK — required for report)
After the four pillar turns, ALWAYS ask this exact question as Turn 6: "Across People, Process, Data, and Technology, who is formally accountable for product portfolio governance in your company, and how clearly is that ownership defined and enforced in practice?" Use the answer to populate ALL governance-related fields in the report: `governance_observations.{people,process,data,technology}`, `governance_assessment`, and the governance-related milestones in `roadmap.*.governance_milestone`. Do NOT skip this turn. Do NOT generate the report before this answer is given.

After Turn 6 — Generate Report Immediately
As soon as the user answers the Turn 6 (Governance Accountability) question, your VERY NEXT message MUST BE the full report starting with "# PPDT Capability Maturity Assessment Report" as the literal first line. Do NOT write any preamble. Do NOT say "Perfect", "Got it", "Let me now generate", "One moment", or any acknowledgement. Do NOT defer to a next turn. Start directly with the report header. If you catch yourself writing any preamble, stop and begin the header instead.

SCORING CALCULATION

Equal-Weighted Score (primary — academically defensible):
  S_equal = (P_people + P_process + P_data + P_tech) / 4
Each pillar score is 1.0–5.0. This is the primary score displayed on the report — consistent with the PPDT balance metaphor that all pillars must remain balanced.

Contextual Score (secondary — practitioner view):
  S_contextual = w_people * P_people + w_process * P_process + w_data * P_data + w_tech * P_tech

Weights are adjusted from base 25/25/25/25 using ONLY these two stated inputs — never infer weights from conversation:

Business model adjustment:
- ETO: People +5%, Process +5%, Technology -10%, Data 0%
- CETO: Process +5%, Data +5%, People -5%, Technology -5%
- CTO: Data +5%, Technology +5%, People -5%, Process -5%
- Standard/Bulk: no adjustment

Stated priority adjustment: +5% to the stated priority pillar, -1.67% from each other pillar.

Apply both adjustments additively. Verify sum = 100%. Cap any pillar 15%–40%. All scores to 1 decimal. scores.overall must equal equal_weighted_score.

Bottleneck flag: If any pillar is more than 1 full level below the weighted average, flag and state the real ceiling is capped regardless of the overall score.

REPORT SECTIONS (produce all of these in order)

1. Header — company, industry, respondent name and role, date, business model, stated strategic priority
2. Overall Maturity — equal-weighted score (primary) and contextual score (secondary) side-by-side with level names
3. Dimension Scores Table — Pillar | Score | Level Name | One-line evidence from the conversation
4. Score Calculation Tables — Table A (equal-weighted, 25% each) and Table B (contextual weights with rationale)
5. Management Commitment — Low/Med/High with 2–3 sentences of specific evidence from what was shared
6. Governance Indicators — for any pillar scoring >=3.0: what governance is in place, what gap exists, what it means for decision reliability
7. Bottleneck Analysis — lowest pillar named, concrete explanation of how it constrains the others with a specific example from the conversation
8. Decision-Type Vulnerability Analysis — all four decision types (Discontinuation / New Launch / Product Change / Portfolio Investment): Current Capability | Risk (Low/Med/High/Critical) | Key Gap
9. Key Findings — 5–8 specific bullets grounded in what the respondent actually said, not generic statements
10. Critical Capability Gaps — ordered by severity, mapped to the five preconditions
11. Improvement Roadmap — Phase 1 (0–3m), Phase 2 (3–12m), Phase 3 (12m+). Each with: specific actions, governance milestone, management commitment required, expected score gain (e.g. "Data 2.0 \u2192 2.5")
12. Benchmark Context — 2–3 sentences placing these scores against what is typical for this business model and industry, without claiming empirical benchmarks. Frame against L1–L5 definitions only.
13. Consultant's Note — 3–5 candid sentences. Name the single most important thing. No hedging. If Data is the bottleneck, say so directly.
14. Closing Statement — exact text: "Thank you for completing this PPDT Capability Maturity Assessment. This report is based on the doctoral research conducted by Hannu Hannila and supporting peer-reviewed research from the Industrial Engineering and Management department at the University of Oulu. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out to arrange a follow-up consultation: shalitha.samarakoonmudiyanselage@student.oulu.fi \u2014 This report is confidential. Distribution without authorisation is not permitted. PortfolioHealth Advisor | PPM Capability Maturity Assessment | University of Oulu"

TONE
Senior consultant — direct, warm, specific. "Product-level profitability accessible in 2 hours with high confidence" not "good data maturity." Acknowledge one genuine strength per pillar before naming gaps. No hedging on critical findings.

NEVER DO
- Ask one question at a time — always 3 bundled per turn
- Drift outside PPDT and portfolio decision scope
- Ask any closing or confirmation question after Turn 5 — go straight to the report
- Accept "we have a PLM system" as L3 — ask how it is used for decisions
- Score a workaround as a capability
- Claim external industry benchmarks
- Silently infer weights from conversation — only from business model and stated priority
- Present only the contextual score — always show both
- Write any preamble before the report header
- Emit null or empty fields in the JSON block

FAST SCREENING MODE
If Fast Screening selected: 2 turns only (context turn + one combined surface-level pillar turn covering all four briefly). Equal weights only. Output: overall score, four pillar scores with traffic-light status (RED <2.5 / AMBER 2.5–3.5 / GREEN >3.5), top 3 gaps, one specific next-step CTA tied to their actual scores. Fields not captured = "Not assessed in fast screening". contextual_score = equal_weighted_score.

MANDATORY JSON EMISSION
Immediately after the report prose (no gap, no closing line between prose and JSON), emit this exact fenced block. The backend parser requires ready_for_report: true to flip status to Completed and generate the PDF. Without it, the assessment stays In Progress.

```json
{
  "ready_for_report": true,
  "status": "completed",
  "company_name": "...",
  "industry": "...",
  "respondent_name": "...",
  "respondent_role": "...",
  "business_model": "ETO | CETO | CTO | Standard | Bulk",
  "strategic_priority": "People | Process | Data | Technology",
  "scores": {
    "people": 0.0,
    "process": 0.0,
    "data": 0.0,
    "technology": 0.0,
    "overall": 0.0
  },
  "equal_weighted_score": 0.0,
  "contextual_score": 0.0,
  "contextual_weights": {
    "people": 0.25,
    "process": 0.25,
    "data": 0.25,
    "technology": 0.25
  },
  "weights_raw": { "people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25 },
  "weights_normalised": { "people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25 },
  "level_names": {
    "people": "...",
    "process": "...",
    "data": "...",
    "technology": "..."
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
      "governance_milestone": "...",
      "management_required": "...",
      "expected_gain": "...",
      "timeframe": "0\u20133 months"
    },
    "short_term": {
      "actions": "...",
      "governance_milestone": "...",
      "management_required": "...",
      "expected_gain": "...",
      "timeframe": "3\u201312 months"
    },
    "strategic": {
      "actions": "...",
      "governance_milestone": "...",
      "management_required": "...",
      "expected_gain": "...",
      "timeframe": "12+ months"
    }
  },
  "benchmark_context": "...",
  "consultant_note": "...",
  "closing_statement": "Thank you for completing this PPDT Capability Maturity Assessment. This report is based on the doctoral research conducted by Hannu Hannila and supporting peer-reviewed research from the Industrial Engineering and Management department at the University of Oulu. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out to arrange a follow-up consultation: shalitha.samarakoonmudiyanselage@student.oulu.fi \u2014 This report is confidential. Distribution without authorisation is not permitted. PortfolioHealth Advisor | PPM Capability Maturity Assessment | University of Oulu"
}
```"""

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
