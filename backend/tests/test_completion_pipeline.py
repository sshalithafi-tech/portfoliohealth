"""
Completion-flow pipeline test — synthetic path.

Verifies the backend completion pipeline end-to-end WITHOUT consuming
LLM budget, by:
  1. Constructing a synthetic assistant message that matches the JSON
     emission contract we gave the prompt (```json + ready_for_report=true).
  2. Running it through chat_service.extract_report_json and
     normalise_report_weights — same functions the chat handler uses.
  3. Using a direct DB write to simulate the chat handler persisting the
     report + flipping status to completed.
  4. Calling GET /api/assessments/{id}/pdf to confirm the PDF generates
     with the new schema and starts with %PDF.
  5. Asserting scores.overall == equal_weighted_score (primary view).

If this passes, we know the JSON parsing, DB write, and PDF builder all
handle the new schema correctly. The only thing that requires real LLM
budget to verify is whether the model itself emits the block at the
right moment — which is prompt-driven and can be re-tested once budget
is available.
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import requests
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Load env the same way server.py does
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

sys.path.insert(0, "/app/backend")
from chat_service import extract_report_json, normalise_report_weights  # noqa: E402

BASE = "http://localhost:8001"
ADMIN_EMAIL = "admin@ppdt.com"
ADMIN_PW = "Admin123!"


SYNTHETIC_REPORT = {
    "ready_for_report": True,
    "business_model": "CETO",
    "strategic_priority": "data",
    "bottleneck_pillar": "data",
    "management_commitment": "Low",
    "equal_weighted_score": 1.8,
    "contextual_score": 1.7,
    "contextual_weights": {
        "people": 0.233,
        "process": 0.283,
        "data": 0.333,
        "technology": 0.151,
    },
    "scores": {
        "people": 2,
        "process": 2,
        "data": 2,
        "technology": 1,
        "overall": 1.8,
    },
    "weights_raw": {"people": 5, "process": 5, "data": 5, "technology": 5},
    "weights_normalised": {"people": 0.25, "process": 0.25, "data": 0.25, "technology": 0.25},
    "level_names": {
        "people": "Developing",
        "process": "Developing",
        "data": "Developing",
        "technology": "Ad Hoc",
        "overall": "Developing",
    },
    "dimension_summaries": {
        "people": "PPM is a secondary task; mixed data literacy; no data stewardship roles.",
        "process": "Quarterly reviews exist but data prep takes two weeks; no formal stage-gate; no audit trail.",
        "data": "Product-level profitability takes 3-4 days; departmental silos; 4-6 week stale data.",
        "technology": "SAP, Aras PLM, Salesforce, Power BI — fragmented; PLM not decision backbone; no audit trails.",
    },
    "pillar_interpretations": {
        "people": "Your People score of 2 places you at Developing — roles exist informally but lack accountability.",
        "process": "Your Process score of 2 reflects periodic reviews but without formal stage-gates or audit trails.",
        "data": "Your Data score of 2 is the primary bottleneck — data exists but is fragmented and slow to retrieve.",
        "technology": "Your Technology score of 1 reflects that systems serve departmental efficiency, not portfolio decisions.",
    },
    "governance_observations": {
        "people": "N/A - below Level 4",
        "process": "N/A - below Level 4",
        "data": "N/A - below Level 4",
        "technology": "N/A - below Level 4",
    },
    "governance_assessment": (
        "Governance is effectively absent — processes are followed by discipline, not audit trail, and "
        "data quality accountability is shared so no one is accountable. This blocks every pillar from "
        "rising above Level 2 regardless of other investment."
    ),
    "management_commitment_assessment": (
        "Management commitment is LOW. Executives approve PPM decisions but have not mandated cross-"
        "departmental data discipline, and improvement is driven bottom-up. Without an executive "
        "sponsor and explicit mandate, capability investments will not stick."
    ),
    "decision_vulnerability_ratings": {
        "discontinuation": "Critical",
        "new_launch": "High",
        "product_change": "High",
        "portfolio_investment": "High",
    },
    "decision_vulnerability": (
        "Product discontinuation is the highest-risk decision type — SKUs are kept alive because no one "
        "wants to make the call, no formal change control exists, and no audit trail supports the rationale. "
        "New launches and product changes are also highly vulnerable due to the absence of formal go/no-go "
        "criteria and cross-functional review, with portfolio investment prioritisation operating on "
        "annual budget cycles without product-level data."
    ),
    "key_findings": [
        "Portfolio management is a secondary task — no dedicated PPM function or board.",
        "Data prep for portfolio reviews takes 2 weeks of manual effort.",
        "Product-level profitability requires 3-4 days to assemble reliably.",
        "No single source of truth — departmental silos with conflicting spreadsheets.",
        "Aras PLM is used only by engineering, not as portfolio decision backbone.",
        "No audit trails for portfolio or product-change decisions.",
        "Management commitment is LOW — executives approve but do not mandate.",
        "Product discontinuation has Critical decision-type risk due to absent stage-gates.",
    ],
    "critical_gaps": [
        "No data stewardship roles or accountability framework — Data is the bottleneck.",
        "No formal change control for portfolio decisions comparable to ECO rigor.",
        "No single source of truth for product master data across SAP/Aras/Salesforce.",
        "No executive mandate for cross-departmental data discipline.",
        "Performance data is 4-6 weeks stale at point of decision.",
    ],
    "roadmap": {
        "immediate": {
            "actions": [
                "Appoint a named data steward accountable for product master data quality.",
                "Publish product master-data ownership matrix across Engineering, Finance, Sales.",
                "Instrument a single product-level profitability view refreshed weekly.",
            ],
            "pillar_focus": "Data (bottleneck pillar) + People (accountability).",
            "governance_milestone": "Data stewardship role formally established with SLA-backed quality targets.",
            "management_commitment": "Executive sponsor named; quarterly PPM review added to exec calendar.",
            "expected_gain": "Data 2→2.5, People 2→2.5",
        },
        "short_term": {
            "actions": [
                "Roll out formal stage-gate process for discontinuation and launch decisions with audit trail.",
                "Integrate Aras PLM with SAP ERP at the BOM level.",
                "Train Sales and Finance on product-level data literacy.",
            ],
            "pillar_focus": "Process + Technology + People.",
            "governance_milestone": "Portfolio decisions audit-trailed and reconstructable 18 months later.",
            "management_commitment": "Multi-year investment approved for data integration programme.",
            "expected_gain": "Process 2→3, Technology 1→2.5",
        },
        "strategic": {
            "actions": [
                "Deploy enterprise product information backbone with real-time portfolio dashboards.",
                "Establish Data Governance Office with formal SLAs between departments.",
                "Embed AI-assisted scenario modelling for portfolio investment prioritisation.",
            ],
            "pillar_focus": "All four pillars — optimisation phase.",
            "governance_milestone": "Every portfolio decision flows through formal governance framework.",
            "management_commitment": "Executive board reviews PPM performance monthly with KPI dashboards.",
            "expected_gain": "Overall 1.8→3.5+",
        },
    },
    "benchmark_context": (
        "Relative to the five PPDT maturity level definitions, CompletionFlowTest Oy sits solidly at "
        "Level 2 (Developing). Industry benchmarking against peers is an open research question in the "
        "Product Wellbeing framework and is not claimed here."
    ),
    "consultant_note": (
        "The single most important thing this company must do is appoint a named Data Steward with "
        "executive backing in the next 90 days. Every other capability investment — Process, Technology, "
        "or People — will underperform until the data foundation is trustworthy and accountable. Start "
        "there. Do not wait for a broader transformation programme."
    ),
    "closing_statement": (
        "Thank you for completing this PPDT Capability Maturity Assessment. "
        "This report is based on the Product Wellbeing framework developed at the University of Oulu "
        "(Hannila, Vierimaa & Salonen, 2026). Contact: shalitha.samarakoonmudiyanselage@student.oulu.fi"
    ),
}


def synthesise_assistant_message(report: dict) -> str:
    """Build what the model WOULD emit — prose report + fenced JSON block at the end."""
    prose = (
        "# Full PPDT Capability Maturity Assessment Report\n\n"
        "## 1. Header\n"
        "Company: CompletionFlowTest Oy | Industrial Equipment | Jane Ambiguous (Head of Operations)\n"
        f"Business Model: {report['business_model']} | Stated Priority: {report['strategic_priority']}\n\n"
        "## 2. Overall Maturity\n"
        f"Equal-Weighted: {report['equal_weighted_score']:.1f} · Contextual: {report['contextual_score']:.1f}\n\n"
        "## 13. Consultant's Note\n"
        f"{report['consultant_note']}\n\n"
        "---\n\n"
        "```json\n" + json.dumps(report, indent=2) + "\n```\n"
    )
    return prose


def log(m):
    print(m, flush=True)


async def write_report_to_db(assessment_id: str, report_data: dict):
    """Simulate what the chat handler does after parsing JSON."""
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    normalised = normalise_report_weights(report_data)
    await db.assessments.update_one(
        {"_id": ObjectId(assessment_id)},
        {"$set": {
            "report": normalised,
            "scores": normalised.get("scores"),
            "weights_raw": normalised.get("weights_raw"),
            "weights_normalised": normalised.get("weights_normalised"),
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    client.close()


def main():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=30)
    r.raise_for_status()
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}"})

    # Create company + assessment
    co = s.post(f"{BASE}/api/companies",
                json={"name": "SyntheticCompletion Oy", "industry": "Industrial Equipment"},
                timeout=20).json()
    cid = co["id"]
    a = s.post(f"{BASE}/api/assessments",
               json={"company_id": cid, "respondent_name": "Jane Synthetic",
                     "respondent_role": "Head of Operations"},
               timeout=20).json()
    aid = a["id"]
    log(f"Created assessment {aid}")

    # Build the synthetic emission + run it through the production parser
    emission = synthesise_assistant_message(SYNTHETIC_REPORT)
    parsed = extract_report_json(emission)
    issues = []

    if parsed is None:
        issues.append("extract_report_json returned None on a well-formed emission")
        log("❌ parser rejected synthetic emission")
        log(emission[-600:])
        sys.exit(1)
    log("✅ extract_report_json parsed the emission")

    if parsed.get("ready_for_report") is not True:
        issues.append("parsed dict missing ready_for_report=true")

    # Simulate the chat handler's persist step
    asyncio.run(write_report_to_db(aid, parsed))
    log("✅ DB write simulated (status → completed)")

    # Verify via API
    fetched = s.get(f"{BASE}/api/assessments/{aid}", timeout=15).json()
    if fetched.get("status") != "completed":
        issues.append(f"status != completed (got {fetched.get('status')!r})")
    else:
        log("✅ status is 'completed'")

    report = fetched.get("report") or {}
    overall = (report.get("scores") or {}).get("overall")
    eq = report.get("equal_weighted_score")
    ctx = report.get("contextual_score")
    log(f"scores.overall={overall}  equal_weighted_score={eq}  contextual_score={ctx}")
    if overall is None or eq is None:
        issues.append("scores.overall or equal_weighted_score missing in stored report")
    elif round(float(overall), 2) != round(float(eq), 2):
        issues.append(f"scores.overall ({overall}) != equal_weighted_score ({eq})")
    else:
        log("✅ scores.overall matches equal_weighted_score (primary view)")

    # weights_normalised sums to 1
    w = report.get("weights_normalised", {})
    w_sum = round(sum(float(v) for v in w.values()), 3)
    if abs(w_sum - 1.0) > 0.02:
        issues.append(f"weights_normalised sum = {w_sum}")
    else:
        log(f"✅ weights_normalised sums to {w_sum}")

    # Schema completeness
    required = [
        "level_names", "weights_raw", "weights_normalised",
        "dimension_summaries", "pillar_interpretations", "governance_observations",
        "governance_assessment", "management_commitment_assessment",
        "key_findings", "critical_gaps", "decision_vulnerability", "roadmap",
        "benchmark_context", "consultant_note", "closing_statement",
        "business_model", "strategic_priority", "bottleneck_pillar",
        "management_commitment", "contextual_weights", "decision_vulnerability_ratings",
    ]
    missing = [f for f in required if f not in report]
    if missing:
        issues.append(f"missing fields: {missing}")
    else:
        log(f"✅ all {len(required)} required fields present")

    # Roadmap structure
    for p in ("immediate", "short_term", "strategic"):
        phase = report.get("roadmap", {}).get(p, {})
        for k in ("actions", "pillar_focus", "governance_milestone",
                  "management_commitment", "expected_gain"):
            if k not in phase:
                issues.append(f"roadmap.{p}.{k} missing")
    if not any("roadmap" in i for i in issues):
        log("✅ roadmap has all three phases with all rich fields")

    # PDF generation
    pdf_resp = s.get(f"{BASE}/api/assessments/{aid}/pdf", timeout=60)
    log(f"PDF HTTP={pdf_resp.status_code}  size={len(pdf_resp.content)}")
    if pdf_resp.status_code != 200:
        issues.append(f"PDF HTTP {pdf_resp.status_code}")
    elif not pdf_resp.content.startswith(b"%PDF"):
        issues.append(f"PDF magic wrong: {pdf_resp.content[:8]!r}")
    else:
        open("/tmp/synthetic_completion.pdf", "wb").write(pdf_resp.content)
        log(f"✅ PDF generated and starts with %PDF → /tmp/synthetic_completion.pdf ({len(pdf_resp.content)} bytes)")

    # Cleanup
    s.delete(f"{BASE}/api/companies/{cid}", timeout=15)

    if issues:
        log(f"\n❌ {len(issues)} ISSUE(S):")
        for i in issues:
            log(f"  - {i}")
        sys.exit(1)
    log("\n✅ ALL PIPELINE CHECKS PASSED")


if __name__ == "__main__":
    main()
