"""
E2E completion-flow test — moderately clear answers.

Goal: verify the AI emits the ```json ready_for_report=true block
immediately after the user confirms "no, please generate the report"
at the Phase 4 CONFIRM AND CLOSE prompt.

Uses direct, confident answers (Level 3-4 signals) to minimise
conversation length and LLM budget usage.
"""
import os
import sys
import time
import json
import requests

BASE = "http://localhost:8001"
ADMIN_EMAIL = "admin@ppdt.com"
ADMIN_PW = "Admin123!"

# Moderately clear answers — aligned with how the AI paces the conversation
ANSWERS = [
    # Turn 1: Phase 1 — frontload ALL required context
    ("Context: We are a mid-market industrial-equipment manufacturer, ~800 employees. "
     "Business Model: CETO (Configure-and-Engineer-to-Order). "
     "Respondent: I am the Head of Operations, with direct involvement in portfolio reviews. "
     "What prompted this assessment: leadership wants more reliable data-driven portfolio "
     "decisions ahead of the annual strategy review. "
     "Stated strategic priority: Data is our most strategically critical pillar to improve."),

    # Turn 2: People + management commitment baked in
    ("People + Management Commitment: Dedicated PPM team with three product managers and a "
     "portfolio director. Strong data literacy in engineering and portfolio; developing in "
     "sales and finance. We have a named Data Owner for product master data but not full "
     "stewardship. Executives actively participate in quarterly portfolio reviews, set "
     "targets, and have approved multi-year investment for data governance. The COO is "
     "named executive sponsor accountable for PPM. Management commitment: MEDIUM-HIGH."),

    # Turn 3: Process
    ("Process: Formal stage-gate for new-product decisions, documented and followed. "
     "Quarterly portfolio reviews use product-level financial data assembled within one "
     "working day. Discontinuation follows stage-gate with documented criteria and change "
     "control. Engineering change orders are formal with cross-functional review. However, "
     "portfolio-decision change control is NOT YET at L4 ECO-equivalent rigor — known gap."),

    # Turn 4: Data
    ("Data: Product-level profitability accessible within 2-3 hours with high confidence "
     "across active portfolio. Master data governed in SAP ERP, single authoritative source. "
     "Aras PLM feeds BOMs. Performance data refreshes weekly in Power BI. Documented data "
     "quality rules + formal arbitration path for conflicts, but SLAs between departments "
     "are still informal. Data governance operational but below L4."),

    # Turn 5: Technology + decision-vulnerability baked in
    ("Technology + Decision Vulnerability: SAP ERP, Aras PLM, Salesforce CRM, Power BI. "
     "PLM-ERP integrated with nightly BOM sync. Aras PLM is product-information backbone "
     "for engineering and partly for portfolio. Decision-makers access Power BI directly. "
     "Audit trails for engineering changes but not fully extended to portfolio decisions. "
     "Decision-type risks: discontinuation LOW, new-launch MEDIUM, product-change LOW, "
     "portfolio-investment MEDIUM."),

    # Turn 6: Phase 4 close — SHORT, direct. AI should now emit full report + ```json block.
    ("No, nothing else to add. That is a complete picture across all four pillars, "
     "management commitment, CETO business model, Data strategic priority, and decision-type "
     "vulnerabilities. Please generate the full final report now with the mandatory "
     "```json completion block at the very end (ready_for_report=true)."),

    # Safety extras if AI stalls
    "Please emit the ```json completion block now at the end of a final prose report.",
    "Proceed with final emission of the ```json ready_for_report=true block.",
]


def log(m):
    print(m, flush=True)


def chat_with_retry(s, url, payload, attempts=3, timeout=300):
    last_err = None
    for i in range(attempts):
        try:
            r = s.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last_err = f"HTTP {r.status_code}: {r.text[:300]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(4 + i * 4)
    raise RuntimeError(f"chat failed after {attempts} tries: {last_err}")


def main():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=60)
    r.raise_for_status()
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}"})

    co = s.post(f"{BASE}/api/companies",
                json={"name": "ClearAnswers Oy", "industry": "Industrial Equipment"},
                timeout=20).json()
    cid = co["id"]
    a = s.post(f"{BASE}/api/assessments",
               json={"company_id": cid, "respondent_name": "Mira Clear",
                     "respondent_role": "Head of Operations"},
               timeout=20).json()
    aid = a["id"]
    log(f"Created assessment {aid}")

    # Start
    start_body = None
    for attempt in range(3):
        try:
            r = s.post(f"{BASE}/api/assessments/{aid}/start", timeout=180)
            if r.status_code == 200 and r.json().get("message"):
                start_body = r.json()
                break
            log(f"start attempt {attempt+1} HTTP={r.status_code}")
        except Exception as e:
            log(f"start attempt {attempt+1} exc: {e}")
        time.sleep(4)
    if start_body is None:
        log("❌ could not start")
        s.delete(f"{BASE}/api/companies/{cid}", timeout=15)
        sys.exit(2)
    log("✅ started")

    final_msg = None
    report_data = None
    ans_idx = 0
    for turn in range(1, 16):
        if ans_idx >= len(ANSWERS):
            user_msg = "Please emit the final report with ```json completion block."
        else:
            user_msg = ANSWERS[ans_idx]
        ans_idx += 1
        log(f"\n=== Turn {turn} ===")
        log(f"USER ({len(user_msg)} chars): {user_msg[:200]}...")
        try:
            resp = chat_with_retry(s, f"{BASE}/api/assessments/{aid}/chat",
                                   {"message": user_msg})
        except RuntimeError as e:
            log(f"❌ {e}")
            # fetch current state + bail
            break
        assistant = resp["message"]["content"]
        final_msg = assistant
        log(f"AI ({len(assistant)} chars, report_ready={resp.get('report_ready')}):")
        log(assistant[:400] + ("\n...[truncated]..." if len(assistant) > 400 else ""))

        if resp.get("report_ready") and resp.get("report"):
            report_data = resp["report"]
            log(f"\n🎉 report_ready=True at turn {turn}")
            break

    # Save final assistant message for inspection
    if final_msg:
        with open("/tmp/final_assistant_message.txt", "w") as f:
            f.write(final_msg)
        log(f"\nSaved full final assistant message → /tmp/final_assistant_message.txt "
            f"({len(final_msg)} chars)")

    # Verify
    fetched = s.get(f"{BASE}/api/assessments/{aid}", timeout=15).json()
    log(f"\nDB status: {fetched.get('status')}")
    log(f"Report stored: {bool(fetched.get('report'))}")

    issues = []
    if report_data is None:
        issues.append("report_ready never became true")
    else:
        scores = report_data.get("scores", {})
        overall = scores.get("overall")
        eq = report_data.get("equal_weighted_score")
        ctx = report_data.get("contextual_score")
        log(f"\nscores.overall={overall}  equal_weighted_score={eq}  contextual_score={ctx}")
        if overall is None or eq is None:
            issues.append("missing overall or equal_weighted_score")
        elif round(float(overall), 2) != round(float(eq), 2):
            issues.append(f"scores.overall ({overall}) != equal_weighted_score ({eq})")

        # PDF
        pdf = s.get(f"{BASE}/api/assessments/{aid}/pdf", timeout=60)
        log(f"PDF HTTP={pdf.status_code} size={len(pdf.content)}")
        if pdf.status_code != 200 or not pdf.content.startswith(b"%PDF"):
            issues.append(f"PDF failed: HTTP={pdf.status_code} magic={pdf.content[:8]!r}")
        else:
            open("/tmp/clear_e2e.pdf", "wb").write(pdf.content)
            log(f"✅ PDF saved /tmp/clear_e2e.pdf")

    # Cleanup
    s.delete(f"{BASE}/api/companies/{cid}", timeout=15)

    if issues:
        log(f"\n❌ {len(issues)} issue(s):")
        for i in issues:
            log(f"  - {i}")
        sys.exit(1)
    log("\n✅ CLEAR-ANSWER E2E TEST PASSED")


if __name__ == "__main__":
    main()
