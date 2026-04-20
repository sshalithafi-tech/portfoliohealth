"""
E2E completion-flow smoke test.

Drives the chat endpoint through a full assessment using deliberately
ambiguous answers, then verifies:
  1. JSON emits at end of conversation (report_ready=true).
  2. Assessment status flips to 'completed' in the DB.
  3. PDF generates and starts with %PDF.
  4. scores.overall == equal_weighted_score (primary view).
"""
import os
import sys
import json
import time
import requests

BASE = os.environ.get("API_URL", "http://localhost:8001")
ADMIN_EMAIL = "admin@ppdt.com"
ADMIN_PW = "Admin123!"
MAX_TURNS = 45

# Deliberately ambiguous / vague answers — test the AI's probing + scoring discipline
ANSWERS = [
    # Phase 1 — context: frontload all required inputs in the first message
    ("We're a mid-market industrial-equipment manufacturer, ~800 employees. "
     "Business model: Configure-and-Engineer-to-Order (CETO). I'm the Head of Operations. "
     "What prompted this assessment: leadership wants more reliable product-level portfolio "
     "decisions before the next annual strategic review — they feel decisions today rely "
     "too much on gut and weeks-old spreadsheets. Stated strategic priority: Data."),
    # Phase 2 — People
    "Portfolio management is a secondary task for our product managers — no dedicated PPM board.",
    "Data literacy is mixed: engineering is fine, sales and finance struggle with product-level data.",
    "Cross-departmental data conflicts are resolved via email chains; there's no named arbitrator or steward.",
    "No formal data stewardship roles or accountability framework. Responsibility is shared, so effectively unassigned.",
    "Executives approve PPM decisions but don't mandate data discipline — improvement is bottom-up. Management commitment is LOW to MEDIUM at best.",
    # Process
    "Quarterly portfolio reviews exist but data prep takes ~2 weeks of manual effort.",
    "Discontinuation decisions happen in leadership meetings without a formal stage-gate or documented criteria.",
    "Change orders are informal for minor changes and only semi-formal for larger ones.",
    "We cannot reconstruct the rationale for a portfolio decision from 18 months ago — no audit trail.",
    # Data
    "Getting reliable product-level profitability across the portfolio takes 3-4 days and we're only moderately confident in the numbers.",
    "Product data is mostly in SAP ERP but each department maintains its own spreadsheet views.",
    "Portfolio-review performance data is typically 4-6 weeks old.",
    "When two departments have conflicting product data there's no arbitrator — the loudest voice wins.",
    "No documented data quality standards, SLAs, or completeness requirements.",
    # Technology
    "Main systems: SAP ERP, Aras PLM, Salesforce CRM, Power BI. PLM-ERP are only partially integrated.",
    "Aras PLM is used by engineering for design data — it is NOT the portfolio decision backbone.",
    "Portfolio decision-makers cannot access product performance data directly; IT must extract it.",
    "Updating a portfolio analysis after a product change takes days of manual work; no automatic propagation.",
    "Our systems do not provide audit trails for portfolio or product-change decisions.",
    # Governance probes (we're mostly below L3, but answer if asked)
    "Processes are followed based on discipline and culture — not audit trail.",
    "Data quality accountability is shared, so effectively no one is accountable.",
    # Decision-type vulnerability
    "Product discontinuation is the highest-risk decision type — we keep SKUs alive because no one wants to make the call.",
    "New product launches happen without formal portfolio-impact analysis; business cases are not tracked against actuals.",
    "ECO/ETO change orders are not propagated consistently across downstream BOMs; no cross-functional review for minor ones.",
    "Portfolio investment prioritisation happens in annual budget cycles without product-level data; strategic fit is assessed qualitatively.",
    # Confirm & close
    "No, that's a full picture across all four pillars. Please produce the final report.",
    # Explicit JSON emission triggers
    "Please deliver the full prose report and then emit the mandatory completion JSON block (```json fenced, ready_for_report=true) at the very end.",
    "Please emit the final report now with the completion JSON — equal_weighted_score as primary, contextual_score as secondary, and all schema fields populated.",
    "Proceed with the final report emission right now — include the ```json ready_for_report=true block at the end.",
    "Final emission: output the full prose report then the ```json``` completion block at the very end in one message.",
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def chat_with_retry(s, url, payload, attempts=4):
    import requests as rq
    last_err = None
    for i in range(attempts):
        try:
            r = s.post(url, json=payload, timeout=180)
            if r.status_code == 200:
                return r.json()
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except (rq.exceptions.RequestException, ValueError) as e:
            last_err = str(e)
        time.sleep(2 + i * 2)
    raise RuntimeError(f"chat failed after {attempts} tries: {last_err}")


def main():
    s = requests.Session()

    # 1. Login
    r = s.post(f"{BASE}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=60)
    r.raise_for_status()
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}"})
    log(f"Logged in. token_len={len(token)}")

    # 2. Create company + assessment
    co = s.post(f"{BASE}/api/companies",
                json={"name": "CompletionFlowTest Oy", "industry": "Industrial Equipment"}, timeout=15).json()
    cid = co["id"]
    log(f"Created company {cid}")

    a = s.post(f"{BASE}/api/assessments",
               json={"company_id": cid, "respondent_name": "Jane Ambiguous",
                     "respondent_role": "Head of Operations"}, timeout=15).json()
    aid = a["id"]
    log(f"Created assessment {aid}")

    # 3. Start (with retry — LLM can be slow)
    start = None
    for attempt in range(4):
        try:
            r = s.post(f"{BASE}/api/assessments/{aid}/start", timeout=180)
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            if r.status_code == 200 and body.get("message"):
                start = body
                break
            log(f"start attempt {attempt+1} failed: HTTP={r.status_code} body_keys={list(body.keys())}")
        except Exception as e:
            log(f"start attempt {attempt+1} exception: {e}")
        time.sleep(3 + attempt * 2)
    if start is None:
        log("❌ could not start assessment")
        sys.exit(2)
    greeting = start["message"]["content"]
    log(f"GREETING ({len(greeting)} chars): {greeting[:140]!r}")

    # 4. Drive the conversation
    report_data = None
    turn = 0
    ans_idx = 0
    last_assistant = greeting
    while turn < MAX_TURNS:
        if ans_idx >= len(ANSWERS):
            user_msg = "Please emit the final report and completion JSON now."
        else:
            user_msg = ANSWERS[ans_idx]
        ans_idx += 1
        turn += 1

        log(f"--- Turn {turn} ---")
        log(f"USER: {user_msg}")

        resp = chat_with_retry(s, f"{BASE}/api/assessments/{aid}/chat",
                                {"message": user_msg})
        assistant = resp["message"]["content"]
        last_assistant = assistant
        # show short preview
        log(f"AI ({len(assistant)} chars): {assistant[:240]!r}")

        if resp.get("report_ready") and resp.get("report"):
            report_data = resp["report"]
            log(f"🎉 report_ready=true at turn {turn}")
            break

    if report_data is None:
        log("❌ FAILED: conversation exhausted without report_ready=true")
        log("Last assistant message (tail):")
        log(last_assistant[-800:])
        sys.exit(1)

    # 5. Verify DB status flip
    fetched = s.get(f"{BASE}/api/assessments/{aid}", timeout=15).json()
    status = fetched.get("status")
    log(f"DB status = {status!r}")
    assert status == "completed", f"Expected status 'completed', got {status!r}"

    # 6. Verify primary-score invariant (scores.overall == equal_weighted_score)
    scores = report_data.get("scores", {}) or {}
    overall = scores.get("overall")
    eq = report_data.get("equal_weighted_score")
    ctx = report_data.get("contextual_score")
    log(f"scores.overall={overall}  equal_weighted_score={eq}  contextual_score={ctx}")
    issues = []
    if overall is None:
        issues.append("scores.overall is missing")
    if eq is None:
        issues.append("equal_weighted_score is missing")
    if overall is not None and eq is not None and round(float(overall), 2) != round(float(eq), 2):
        issues.append(f"scores.overall ({overall}) != equal_weighted_score ({eq})")

    # Additional schema checks (things the Report Page + PDF need)
    required_fields = [
        "ready_for_report", "level_names", "weights_raw", "weights_normalised",
        "dimension_summaries", "pillar_interpretations", "governance_observations",
        "governance_assessment", "management_commitment_assessment",
        "key_findings", "critical_gaps", "decision_vulnerability", "roadmap",
        "benchmark_context", "consultant_note", "closing_statement",
        # New fields
        "business_model", "strategic_priority", "bottleneck_pillar",
        "management_commitment", "contextual_weights", "decision_vulnerability_ratings",
    ]
    for f in required_fields:
        if f not in report_data:
            issues.append(f"missing field: {f}")

    # Roadmap shape
    roadmap = report_data.get("roadmap", {}) or {}
    for phase_key in ("immediate", "short_term", "strategic"):
        phase = roadmap.get(phase_key)
        if not isinstance(phase, dict):
            issues.append(f"roadmap.{phase_key} must be an object")
        else:
            for k in ("actions", "pillar_focus", "governance_milestone",
                      "management_commitment", "expected_gain"):
                if k not in phase:
                    issues.append(f"roadmap.{phase_key}.{k} missing")

    # weights_normalised should sum to ~1
    w = report_data.get("weights_normalised", {}) or {}
    if w:
        s_sum = round(sum(float(v) for v in w.values()), 2)
        if abs(s_sum - 1.0) > 0.02:
            issues.append(f"weights_normalised sum = {s_sum}, expected 1.0")

    # 7. Download PDF
    pdf_resp = s.get(f"{BASE}/api/assessments/{aid}/pdf", timeout=60)
    log(f"PDF HTTP={pdf_resp.status_code}  size={len(pdf_resp.content)}")
    if pdf_resp.status_code != 200:
        issues.append(f"PDF download HTTP {pdf_resp.status_code}")
    elif not pdf_resp.content.startswith(b"%PDF"):
        issues.append(f"PDF magic wrong: {pdf_resp.content[:8]!r}")
    else:
        # save for inspection
        path = "/tmp/completion_flow.pdf"
        open(path, "wb").write(pdf_resp.content)
        log(f"Saved PDF → {path}")

    # 8. Print the full report JSON for inspection
    log("========== REPORT JSON ==========")
    print(json.dumps(report_data, indent=2)[:4000])
    log("=================================")

    # 9. Cleanup
    s.delete(f"{BASE}/api/companies/{cid}", timeout=15)
    log("Cleanup OK")

    # 10. Summary
    if issues:
        log(f"❌ {len(issues)} ISSUE(S):")
        for i in issues:
            log(f"  - {i}")
        sys.exit(1)
    log("✅ ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
