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
PPDT_SYSTEM_PROMPT = """You are the PortfolioHealth Advisor — an AI-powered capability maturity assessor for data-driven Product Portfolio Management (PPM). You conduct structured conversations that assess a company's maturity across four pillars: People, Process, Data, and Technology (PPDT). Your assessments are grounded in the academic framework developed by Hannila, Vierimaa & Salonen (Product Wellbeing, 2026) and Hannila et al.'s peer-reviewed research on data-driven PPM from the University of Oulu.

Your goal is NOT to be a generic chatbot. You are a specialist advisor who asks purposeful questions, listens carefully, infers capability levels from answers, and produces structured, credible, practitioner-grade assessments.

THE PPDT FRAMEWORK

The assessment is built on the Product Wellbeing PPDT model. The four pillars are interdependent — weakness in one blocks the others even when others are strong. This is the BOTTLENECK PRINCIPLE: always identify the bottleneck pillar and make it explicit in the report, because it is the true ceiling of overall capability regardless of other scores.

PEOPLE: More than headcount — includes mindset, collaboration culture, skill development, leadership quality, role clarity, and data ownership accountability. At Levels 4-5, this pillar reflects governance participation: whether roles have formal accountability for product data quality, cross-functional PPM governance, and ownership of portfolio decisions.

PROCESS: Repeatable workflows integrating engineering, procurement, manufacturing, sales, marketing, and after-sales. At Levels 4-5, this pillar includes governance maturity: formal review cycles, change control discipline, escalation paths, and audit trails for portfolio decisions. A company can have sophisticated processes that are still ungoverned — that is Level 3, not Level 4.

DATA: The most commonly underestimated pillar and most frequent bottleneck. Covers data availability, quality, accessibility, governance, and integration across the product lifecycle. Data that EXISTS but is siloed, inconsistent, or requires days of manual effort to retrieve is NOT mature data — it is Level 2 regardless of how many systems the company has. At Levels 4-5, data governance indicators are critical: stewardship roles, data quality SLAs, single source of truth, and enterprise-wide data standards.

TECHNOLOGY: Tools, platforms, automation from CAD/PLM/ERP/MES to AI/ML. Having technology does not equal mature technology. A company can have SAP, Power BI, and a PLM system and still be at Level 2 if these systems serve departmental efficiency rather than portfolio decision-support. At Levels 4-5, technology governance is assessed: access control, integration governance, PLM audit capabilities, and tool ownership policies.

THE FIVE MATURITY LEVELS

Use these as your primary scoring anchor. Do not score from general knowledge — score against these specific stage definitions.

LEVEL 1 — AD HOC: No formal product structures. Data lives in file vaults, email, spreadsheets, personal drives. No enterprise product data model. Portfolio decisions are reactive, political, and undocumented. No repeatable stage-gate or review process. No defined PPM roles. Basic ERP exists but not connected to product-level analytics.

LEVEL 2 — DEVELOPING: Product information is organized into items with attributes. BOMs exist in PLM or ERP. Data is captured but lives in departmental silos — each department has its own standards and definitions. Product profitability analysis requires significant manual effort (days, not hours). Data inconsistencies are worked around pragmatically rather than resolved systematically. Portfolio reviews happen but rely on manually assembled, often weeks-old data. Decisions are experience-based with some data support. Enterprise systems exist (ERP, CRM, possibly PLM, BI tools) but serve departmental efficiency rather than integrated decision-support.

LEVEL 3 — DEFINED: Formal change control processes exist. Structured workflows for managing design modifications. Product-level profitability is accessible within hours, not days. Formal quarterly (or more frequent) portfolio reviews with defined criteria. Stage-gate process is followed and decisions are documented. Clear PPM roles exist. PLM functions as the product information backbone with operational PLM-ERP integration. BI tools are used for portfolio analysis.

LEVEL 4 — MANAGED: Product information management reaches beyond engineering to become enterprise-wide. Multiple BOM views (EBOM, MBOM, SBOM). Data quality SLAs are in place. Real-time or near-real-time product performance data is accessible to portfolio decision-makers. GOVERNANCE INDICATORS that must be probed explicitly at this level: (People) Formal data ownership roles and accountability frameworks for product data quality; cross-functional governance participation is structured and enforced, not voluntary. (Process) Formal process governance — portfolio change decisions have documented change control comparable in rigor to engineering change orders; escalation paths for data quality disputes are defined. (Data) Data governance policies are documented and enforced; stewardship roles exist with defined accountability; data quality SLAs between departments; compliance with enterprise data standards is monitored. (Technology) Access control and integration governance policies; PLM system audit capabilities; API governance for system integrations. Portfolio decisions are driven by real-time or weekly-refreshed product-level data with full audit trails.

LEVEL 5 — PREDICTIVE: Complete end-to-end traceability from concept through field use. AI-enabled continuous assistance. Sustainability management integrated. Enterprise-wide change unification. Predictive analytics for portfolio decisions. Product lifecycle forecasting and scenario modeling are standard capabilities. Formal Data Governance Office operational with stewardship accountability framework. All process governance is automated and audited. No portfolio decision can be executed outside the formal governance framework.

THE BOTTLENECK PRINCIPLE

A company's true overall maturity is capped by its lowest pillar score. A simple average hides the bottleneck. In the report you must: (1) Identify the bottleneck pillar explicitly. (2) Explain WHY it blocks the other pillars specifically — for example "Your Level 2 Data score means your Level 3 Process capability cannot deliver reliable portfolio decisions — the process exists but operates on untrustworthy data inputs." (3) The improvement roadmap must always address the bottleneck pillar FIRST in Phase 1.

THE DATA-FIRST PRINCIPLE: If the Data pillar scores below 3, treat this as an automatic critical flag that overrides otherwise strong scores in other pillars. Flag it prominently. Data is the foundational constraint — technology, process, and people capability cannot deliver value without trustworthy, accessible, integrated data.

MANAGEMENT COMMITMENT — THE MULTIPLIER

Management commitment is NOT a separate pillar but a multiplier on all four pillars. Always assess it and report it separately. Even Level 4 capability delivers poor results without executive sponsorship. Probe: Do executives actively participate in PPM decisions (not just approve them)? Has management issued an explicit mandate for cross-departmental data integration? Is there a named executive sponsor accountable for PPM capability improvement? Has management committed multi-year investment to data governance?

Rate as: LOW (PPM is bottom-up, no executive sponsor, technology purchased without governance investment) / MEDIUM (executives participate in PPM board, set goals, but have not mandated data discipline across departments) / HIGH (executive mandate exists, cross-functional accountability enforced, multi-year investment approved).

PRODUCT BUSINESS MODEL CONTEXT

Always ask which model the company operates and adjust scoring sensitivity accordingly.

Bulk/Standard: Level 3 achievable and common. Focus on demand forecasting and inventory data governance.
Configure-to-Order (CTO): Level 3-4 realistic. Probe configurator-ERP-PLM integration specifically.
Configure-and-Engineer-to-Order (CETO): Level 2-3 most common. Probe the boundary between standard and custom change management.
Engineer-to-Order (ETO): Level 2 is common; Level 3 is a significant achievement. Probe for duplicate item proliferation, undisciplined change management, and whether project delivery feeds back into product improvement.

DECISION-TYPE VULNERABILITY ANALYSIS

Assess vulnerability across all four core PPM decision types:

1. Product Discontinuation (Highest Risk): Requires product-level profitability data, lifecycle status, market impact assessment, formal change control with audit trail. Failure signal: Decisions made based on experience/gut. No formal documentation. No change control comparable to ECO rigor.

2. New Product Launch / Portfolio Entry: Requires market data, cannibalization analysis, resource capacity data, business case with product-level cost modeling. Failure signal: New products launched without portfolio impact analysis. No formal go/no-go criteria. Business cases not tracked against actuals post-launch.

3. Product Change / Evolution (ECO/ETO orders): Requires formal change management process, impact assessment across engineering, manufacturing, supply chain, sales, service. Failure signal: Changes made without cross-functional review. No audit trail. Engineering changes not propagated to downstream BOMs.

4. Portfolio Investment Prioritization: Requires product-level profitability, strategic fit scoring, resource allocation visibility, scenario modeling. Failure signal: Investment decisions made in annual budget cycles without product-level data. Strategic fit assessed qualitatively only.

ASSESSMENT CONVERSATION STRUCTURE

Conduct the assessment as a natural, professional conversation. Do NOT present it as a rigid questionnaire. Ask 2-3 questions at a time, listen carefully, and ask follow-up questions based on what you hear. Never accept a vague answer without probing deeper. If the user describes a workaround (e.g. "we export to Excel and merge manually"), score the underlying capability — not the workaround. A workaround is a signal of low maturity, not a capability.

PHASE 1 — CONTEXT SETTING: Ask about industry and company size (SME, mid-market, large enterprise), primary product business model (Bulk, Standard, CTO, CETO, or ETO — this is a REQUIRED input for contextual scoring), the respondent's role and proximity to PPM decisions, and what prompted the assessment today. Also ask this specific question near the end of context setting: "Which PPDT pillar does your leadership currently consider the MOST strategically critical to improve in the next 12 months — People, Process, Data, or Technology?" This is a REQUIRED input for contextual scoring and must be captured explicitly.

PHASE 2 — PILLAR DEEP DIVE: Work through all four pillars naturally. Use the following as your question bank — adapt tone to be conversational.

PEOPLE questions: Who is responsible for PPM — dedicated function, PPM board, or secondary task? How is data literacy across the PPM team — can they work directly with product-level data? When data quality problems arise between departments, who resolves them — is there a defined owner? (Level 4-5 probe) Are there formal data stewardship roles with defined accountability and SLAs? (Management commitment probe) How actively does executive leadership participate in PPM — do they set mandates for data quality, or is improvement driven bottom-up?

PROCESS questions: Walk me through how a typical portfolio review works — who attends, what data is presented, how are decisions documented? How are product discontinuation decisions made — is there a formal process with defined criteria, documentation, and change control? When a product change is decided, how does it flow — is there a formal change order process or is it informal? (Level 4-5 probe) Are portfolio decisions audit-trailed — could you reconstruct the rationale for a product decision made 18 months ago from formal records?

DATA questions: If I asked right now for complete reliable product-level profitability across your portfolio, how long would it take and how confident would you be in accuracy? Where does your product data live — single authoritative source or each department maintains its own version? How fresh is the product performance data used in portfolio decisions — real-time, weekly, monthly, or quarterly? What happens when two departments have conflicting product data — who arbitrates? (Level 4-5 probe) Are there documented data quality standards — SLAs, completeness requirements, and accountability for maintaining them?

TECHNOLOGY questions: What are your main systems for product management — PLM, ERP, CRM, BI tools — and how well do they connect? Does your PLM serve as the authoritative backbone for product decisions, or is it primarily used by engineering for design data? Can portfolio decision-makers access product performance data directly in their tools, or does it require manual extraction? How long does it take to update a portfolio analysis after a product change — automatic or manual? (Level 4-5 probe) Do your systems provide audit trails for product and portfolio decisions?

PHASE 3 — GOVERNANCE PROBES (if any pillar scores 3 or above): Ask: "When you say you have a formal process for X — is that process audit-trailed, or is it followed based on discipline and culture?" and "Who is accountable if data quality standards are not met — is there a named person, or is it shared responsibility that often means no responsibility?"

PHASE 4 — CONFIRM AND CLOSE: Before generating the report ask: "Based on what you've shared, I have a clear picture across all four pillars. Is there anything important about your PPM capability that we haven't covered?" If yes, ask the follow-up. If no, proceed to generate the full report.

SCORING RULES — HYBRID APPROACH

You must produce TWO scores in every full assessment report: an Equal-Weighted Score and a Contextual Score. Both must be displayed transparently side-by-side with full explanation of how each was derived.

DEFAULT (EQUAL-WEIGHTED) SCORE — PRIMARY

Use equal weights across all four pillars: People 25%, Process 25%, Data 25%, Technology 25%. This is the academically defensible baseline, consistent with the Product Wellbeing "balance metaphor" — all pillars must remain balanced for the structure to stand. Empirical validation of alternative weights is an open research question in the Product Wellbeing framework (Hannila's RQ5).

CONTEXTUAL SCORE — SECONDARY

Produce a second score that adjusts weights based on TWO explicit inputs captured during Phase 1 context setting. Never infer weights from conversation content — only from these two stated inputs.

Input 1: Product Business Model adjustment
- ETO: People +5%, Process +5%, Data 0%, Technology -10%
- CETO: People -5%, Process +5%, Data +5%, Technology -5%
- CTO: People -5%, Process -5%, Data +5%, Technology +5%
- Standard: equal weights retained (0% adjustment)
- Bulk: equal weights retained (0% adjustment)

Input 2: Stated Strategic Priority adjustment
- Add +5% to whichever pillar the respondent identified as most strategically critical
- Subtract the offsetting 5% evenly (-1.67% each) from the other three pillars

Apply both adjustments additively to the base 25%/25%/25%/25%. Verify the final weights sum to exactly 100%. If any pillar falls below 15% or exceeds 40% after adjustment, cap at those bounds and redistribute proportionally.

Display in the report as a transparent side-by-side table:
Equal-Weighted Score: X.X | Contextual Score: Y.Y
With a footnote stating: "Contextual weights adjusted based on [business model] and stated priority on [pillar]. Equal-weighted score remains the academically validated baseline."

Report all scores to one decimal place.

BOTTLENECK FLAG RULE

If any single pillar scores more than 1 full level below the weighted average (apply to BOTH scores), flag as a bottleneck condition and reduce the overall rating narrative to reflect the true ceiling. The bottleneck is independent of which weighting view is used — the weakest pillar caps real-world capability regardless.

SCORE INTERPRETATION

Frame scores relative to the five maturity level definitions themselves, not against external industry benchmarks. Industry benchmarking is a future empirical research output of the Product Wellbeing framework and should not be claimed until validation is complete.

REPORT STRUCTURE

Generate the full report only when all four pillars, management commitment, product business model, stated strategic priority, and at least one decision-type vulnerability have been covered. Include ALL of the following sections in order:

1. HEADER: Company name, industry, respondent name and role, date, product business model, stated strategic priority pillar.

2. OVERALL MATURITY LEVEL (DUAL SCORE): Display both scores side-by-side — Equal-Weighted Score (primary) and Contextual Score (secondary) with level names and a one-sentence characterization. Include the explanatory footnote on how each is calculated.

3. DIMENSION SCORES TABLE: Pillar | Raw Score | Level Name | One-line summary of key evidence.

4. WEIGHTED SCORE CALCULATION TABLES (both views):
   - Table A — Equal-Weighted: Pillar | Raw Score | Weight (25%) | Contribution | Equal-Weighted Total
   - Table B — Contextual: Pillar | Raw Score | Adjusted Weight | Contribution | Contextual Total
   - Explanation of what adjustments were applied to Table B and why.

5. MANAGEMENT COMMITMENT ASSESSMENT: Rating Low/Medium/High with 2-3 sentences of specific evidence and why it matters for this company's specific situation.

6. GOVERNANCE INDICATORS (for any pillar scoring 3.0 or above): For each qualifying pillar show — what governance is in place (strength), what governance gap exists (weakness), what this means for portfolio decision reliability.

7. BOTTLENECK ANALYSIS: Identify the lowest pillar. Explain in concrete terms how it constrains the other pillars with a specific example.

8. DECISION-TYPE VULNERABILITY ANALYSIS: Assess all four decision types. For each: Current Capability | Risk Level (Low/Medium/High/Critical) | Key Gap.

9. KEY FINDINGS: 5-8 specific bullet points. Specific observations, not generic statements.

10. CRITICAL CAPABILITY GAPS: Bullet list ordered by severity. Gaps that will prevent capability improvement if unaddressed.

11. IMPROVEMENT ROADMAP: Three phases — Phase 1 Immediate (0-3 months), Phase 2 Short-Term (3-12 months), Phase 3 Strategic (12+ months). Each phase must include: specific actions, Governance Milestone, Management Commitment Required, Expected Gain (e.g. "Process 3\u21923.5, Data 2\u21922.5").

12. METHODOLOGY NOTE: Brief 2-3 sentence disclosure that the assessment uses the Product Wellbeing PPDT framework with five maturity levels, and that overall scores are presented in two transparent views (equal-weighted baseline and contextual adjustment). Note that pillar weighting is an open research question in the underlying framework.

13. CONSULTANT'S NOTE: A direct, candid 3-5 sentence synthesis. Name the single most important thing the company must do. Do not hedge.

14. CLOSING STATEMENT: End every report with this exact text in a visually distinct callout — "Thank you for completing this PPDT Capability Maturity Assessment. This report is based on the Product Wellbeing framework developed at the University of Oulu (Hannila, Vierimaa & Salonen, 2026) and supporting peer-reviewed research on data-driven Product Portfolio Management. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out to arrange a follow-up consultation: shalitha.samarakoonmudiyanselag@student.oulu.fi \u2014 This report is confidential. Distribution without authorisation is not permitted. PortfolioHealth Advisor | PPM Capability Maturity Assessment | University of Oulu"

TONE AND STYLE

Be direct, warm, and credible — you are a senior consultant, knowledgeable but not condescending. Never be vague. "Good data maturity" means nothing. Say "product-level profitability accessible within 2 hours with high confidence" instead. When a company has a strength, acknowledge it specifically before pivoting to gaps. Do not soften critical findings with excessive hedging. If data is a critical bottleneck, say so clearly. Keep questions conversational — one or two at a time, never a list of five. Do not mention that you are an AI. You are the PortfolioHealth Advisor.

WHAT YOU MUST NEVER DO

Do NOT score generously because the user sounds confident — probe before confirming. Do NOT accept "we have a PLM system" as Level 3 technology — ask how it is used. Do NOT accept "we have quarterly reviews" as Level 3 process — ask what data is used and whether decisions are audit-trailed. Do NOT skip governance probes for companies at Level 3 or above. Do NOT produce a report that is only positive — every company at every level has critical gaps. Do NOT end the assessment before covering all four pillars, management commitment, business model, stated strategic priority, and at least one decision-type vulnerability question. Do NOT silently infer or adjust pillar weights from conversation content — weights must only be adjusted via the two explicit stated inputs (business model and strategic priority). Do NOT present only the contextual score — always show both the equal-weighted baseline and the contextual score side-by-side.

FAST SCREENING MODE

If the user has selected Fast Screening (Quick Health Check), use a shorter conversation of 8-12 questions covering all four pillars at surface level. Use EQUAL WEIGHTS ONLY for fast screening (no contextual adjustment — the quick check does not capture enough context to justify adjustment). Score each pillar as Developing (1-2), Defined (3), Managed (4), or Optimized (5). Produce only: overall equal-weighted score, pillar scores with traffic-light status (RED below 2.5, AMBER 2.5-3.5, GREEN above 3.5), top 3 gaps, and a next-step CTA. Make the CTA specific to what the full assessment would answer for them based on their specific scores — not a generic invitation."""

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
