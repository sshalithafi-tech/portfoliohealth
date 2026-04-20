"""
E2E test for trimmed prompt — 5 turns, auto-emission after pillar 4.

The new prompt skips Phase 4 confirmation; after the 4th pillar answer,
the AI should immediately emit the full report + ```json block.
"""
import os
import sys
import time
import json
import requests

BASE = "http://localhost:8001"

ANSWERS = [
    # Turn 1: Phase 1 context
    ("Industrial-equipment manufacturer, ~800 employees (mid-market). "
     "Business model: CETO. I'm the Head of Operations. Strategic priority: Data."),
    # Turn 2: People
    ("Dedicated PPM team: three product managers + portfolio director. Data literacy strong "
     "in engineering/portfolio, developing in sales/finance. Named Data Owner for master data "
     "(not full stewardship). COO is executive sponsor; executives actively participate in "
     "quarterly portfolio board; multi-year investment approved. Management commitment: MEDIUM-HIGH."),
    # Turn 3: Process
    ("Formal stage-gate for portfolio decisions, documented and followed. Quarterly reviews "
     "use product-level financials assembled in one working day. Discontinuation follows "
     "stage-gate with documented criteria + change control. ECOs are formal cross-functional. "
     "Gap: portfolio-decision audit trails not yet at L4 ECO-equivalent rigor."),
    # Turn 4: Data
    ("Product-level profitability accessible in 2-3 hours with high confidence. Single source "
     "of truth in SAP ERP; Aras PLM feeds BOMs. Data refreshes weekly in Power BI. Documented "
     "quality rules + arbitration path exist. SLAs between departments still informal — gap."),
    # Turn 5: Technology (last pillar — AI should auto-emit after this)
    ("SAP ERP + Aras PLM + Salesforce CRM + Power BI. Nightly PLM-ERP BOM sync. Aras is the "
     "engineering product backbone + partly portfolio. Decision-makers access Power BI directly "
     "(no IT extraction). Audit trails exist for engineering changes, not yet for all "
     "portfolio decisions. Decision vulnerabilities: discontinuation LOW, new-launch MEDIUM, "
     "product-change LOW, portfolio-investment MEDIUM."),
    # Safety net if AI stalls
    "Please emit the full report and ```json completion block now.",
]


def log(m):
    print(m, flush=True)


def post_with_retry(s, url, payload, attempts=3, timeout=300):
    last = None
    for i in range(attempts):
        try:
            r = s.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:300]}"
        except Exception as e:
            last = str(e)
        time.sleep(4 + i * 4)
    raise RuntimeError(f"failed: {last}")


def main():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login",
               json={"email": "admin@ppdt.com", "password": "Admin123!"}, timeout=60)
    r.raise_for_status()
    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})

    co = s.post(f"{BASE}/api/companies",
                json={"name": "TrimmedPromptTest Oy", "industry": "Industrial Equipment"},
                timeout=20).json()
    cid = co["id"]
    a = s.post(f"{BASE}/api/assessments",
               json={"company_id": cid, "respondent_name": "Mira Clear",
                     "respondent_role": "Head of Operations"},
               timeout=20).json()
    aid = a["id"]
    log(f"Assessment {aid}")

    # Start
    start = None
    for i in range(3):
        try:
            r = s.post(f"{BASE}/api/assessments/{aid}/start", timeout=180)
            if r.status_code == 200 and r.json().get("message"):
                start = r.json()
                break
        except Exception as e:
            log(f"start exc: {e}")
        time.sleep(4)
    if not start:
        s.delete(f"{BASE}/api/companies/{cid}", timeout=15)
        sys.exit(2)
    log("started")

    final = None
    report_data = None
    for turn, ans in enumerate(ANSWERS, 1):
        log(f"\n=== Turn {turn} ===")
        log(f"USER: {ans[:180]}...")
        try:
            resp = post_with_retry(s, f"{BASE}/api/assessments/{aid}/chat",
                                    {"message": ans})
        except RuntimeError as e:
            log(f"❌ {e}")
            break
        final = resp["message"]["content"]
        log(f"AI ({len(final)} chars, report_ready={resp.get('report_ready')}):")
        # Show first 400 + last 300 to see start AND whether JSON fence appears at end
        log(final[:400])
        if len(final) > 700:
            log("  ... [middle truncated] ...")
            log(final[-300:])
        if resp.get("report_ready") and resp.get("report"):
            report_data = resp["report"]
            log(f"\n🎉 report_ready=True at turn {turn}")
            break

    # Save full final message
    if final:
        open("/tmp/trimmed_final.txt", "w").write(final)
        log(f"\nSaved: /tmp/trimmed_final.txt ({len(final)} chars)")

    # Verify
    fetched = s.get(f"{BASE}/api/assessments/{aid}", timeout=15).json()
    log(f"DB status: {fetched.get('status')}")
    log(f"Report stored: {bool(fetched.get('report'))}")

    issues = []
    if report_data is None:
        issues.append("report_ready never True — check /tmp/trimmed_final.txt for JSON fence")
    else:
        scores = report_data.get("scores") or {}
        overall = scores.get("overall")
        eq = report_data.get("equal_weighted_score")
        ctx = report_data.get("contextual_score")
        log(f"\nscores.overall={overall}  equal={eq}  contextual={ctx}")
        if overall is None or eq is None:
            issues.append("missing scores.overall or equal_weighted_score")
        elif round(float(overall), 2) != round(float(eq), 2):
            issues.append(f"scores.overall ({overall}) != equal_weighted_score ({eq})")

        pdf = s.get(f"{BASE}/api/assessments/{aid}/pdf", timeout=60)
        log(f"PDF HTTP={pdf.status_code} size={len(pdf.content)}")
        if pdf.status_code == 200 and pdf.content.startswith(b"%PDF"):
            open("/tmp/trimmed_e2e.pdf", "wb").write(pdf.content)
            log("✅ PDF ok")
        else:
            issues.append(f"PDF failed {pdf.status_code}")

    # Cleanup
    s.delete(f"{BASE}/api/companies/{cid}", timeout=15)

    if issues:
        log(f"\n❌ {len(issues)} issues:")
        for i in issues: log(f"  - {i}")
        sys.exit(1)
    log("\n✅ E2E TRIMMED TEST PASSED")


if __name__ == "__main__":
    main()
