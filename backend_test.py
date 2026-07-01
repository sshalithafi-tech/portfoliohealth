#!/usr/bin/env python3
"""
Regression test after:
1. Reverting report_sections.py model from claude-sonnet-5 back to claude-sonnet-4-5-20250929
2. Applying 4 audit fixes to server.py (JWT_SECRET fail-fast, chat_history persisted, 
   PDF endpoints wrapped in try/except, max_length=8000 added)

Test sequence:
1. Login (POST /api/auth/login) → 200
2. Create company (POST /api/companies) → 200
3. Create assessment (POST /api/assessments) → 200
4. POST /api/assessments/{id}/start → 200 with AI greeting
5. Drive FULL conversation via repeated POST /api/assessments/{id}/chat until report_ready: true
   - TIME this final turn (should be ~70-100s, NOT ~165s)
6. Verify ALL 26 report fields are present and non-empty
7. GET /api/assessments/{id}/pdf → 200, valid PDF
8. GET /api/assessments/{id}/summary-pdf → 200, valid PDF
9. GET /api/assessments → 200, regression check
10. NEW TEST: create fresh assessment, call /start, then POST /chat with 9000-char message → expect 422
11. Verify idempotency: calling /start twice returns same greeting without error
"""

import requests
import time
import json
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://premium-report-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
EMAIL = "admin@portfoliohealth.fi"
PASSWORD = "Admin@12345"

# Required 26 report fields
REQUIRED_FIELDS = [
    "scores", "equal_weighted_score", "contextual_score", "level_names",
    "dimension_summaries", "pillar_interpretations", "pillar_interpretation_short",
    "failure_pattern_name", "failure_pattern_narrative", "financial_consequence",
    "ninety_day_projection", "governance_observations", "governance_assessment",
    "governance_signal_summary", "management_commitment", "management_commitment_assessment",
    "assessment_reliability", "decision_vulnerability_ratings", "decision_vulnerability",
    "key_findings", "critical_gaps", "roadmap", "first_action", "benchmark_context",
    "consultant_note", "closing_statement"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_login():
    """Step 1: Login"""
    log("TEST 1: POST /api/auth/login")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": EMAIL,
        "password": PASSWORD
    })
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "access_token" in data, "No access_token in response"
    log(f"✓ Login successful, token received")
    return data["access_token"]

def test_create_company(token):
    """Step 2: Create company"""
    log("TEST 2: POST /api/companies")
    resp = requests.post(f"{BASE_URL}/companies", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": f"Test Company {int(time.time())}",
            "industry": "Manufacturing",
            "portfolio_size": "50-100 products",
            "company_size": "Mid-market · 450 employees",
            "active_products": "28 active SKUs"
        }
    )
    assert resp.status_code == 200, f"Create company failed: {resp.status_code} {resp.text}"
    data = resp.json()
    company_id = data["id"]
    log(f"✓ Company created: {company_id}")
    return company_id

def test_create_assessment(token, company_id):
    """Step 3: Create assessment"""
    log("TEST 3: POST /api/assessments")
    resp = requests.post(f"{BASE_URL}/assessments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_id": company_id,
            "respondent_name": "John Smith",
            "respondent_role": "Portfolio Manager"
        }
    )
    assert resp.status_code == 200, f"Create assessment failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assessment_id = data["id"]
    log(f"✓ Assessment created: {assessment_id}")
    return assessment_id

def test_start_assessment(token, assessment_id):
    """Step 4: Start assessment (AI greeting)"""
    log("TEST 4: POST /api/assessments/{id}/start")
    resp = requests.post(f"{BASE_URL}/assessments/{assessment_id}/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Start assessment failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "message" in data, "No message in response"
    greeting = data["message"]["content"]
    assert len(greeting) > 0, "Empty greeting"
    assert "Welcome" in greeting or "Tervetuloa" in greeting or "Välkommen" in greeting, \
        f"Unexpected greeting format: {greeting[:100]}"
    log(f"✓ AI greeting received ({len(greeting)} chars)")
    return greeting

def test_full_conversation(token, assessment_id):
    """Step 5: Drive FULL conversation until report_ready: true"""
    log("TEST 5: Drive FULL conversation via POST /api/assessments/{id}/chat")
    
    # Conversation flow: language → context → anchor questions → pillar assessment → governance → close
    messages = [
        # Language selection
        "English",
        
        # Context questions
        "We're a mid-market manufacturing company with about 450 employees. We make industrial automation equipment.",
        
        # Business model
        "We're primarily configure-to-order (CTO). We have standard modules that we configure based on customer requirements.",
        
        # What prompted assessment
        "We're struggling with portfolio complexity and want to understand our capability gaps.",
        
        # Primary performance metric
        "Our leadership focuses primarily on gross margin and on-time delivery rate.",
        
        # R&D budget
        "Our annual R&D spend is around 8 million euros.",
        
        # Recent portfolio decision
        "We discontinued a legacy product line last year, but it turned out some customers still needed it. We learned that we didn't have good visibility into actual customer demand across our portfolio.",
        
        # Active products
        "We have about 28 active SKUs, but different departments count them differently. Sales sees them one way, engineering another.",
        
        # People pillar - roles and responsibilities
        "Our portfolio decisions are made by a cross-functional team led by our VP of Product Management. But when data is wrong, it's not always clear who should fix it. We've lost some critical knowledge when key people left.",
        
        # Process pillar - review cycles
        "We have quarterly portfolio reviews, but they're not always well-documented. We use email and meetings to make changes. It's hard to reconstruct why we made certain decisions 18 months ago.",
        
        # Data pillar - profitability and quality
        "It takes us about 2-3 weeks to pull together product-level profitability, and honestly we're not 100% confident in the numbers. Different departments often disagree on costs and margins. Our data is spread across SAP, Salesforce, and various spreadsheets.",
        
        # Technology pillar - tools
        "We have SAP for ERP and Salesforce for CRM, but they don't really talk to each other. People manually bridge the gaps with Excel. We've invested in these systems, but I'm not sure they've improved decision quality much.",
        
        # Governance probe
        "Our processes are somewhat documented, but they depend a lot on having the right people in the room. Data quality ownership between departments is informal - we don't have named owners.",
        
        # Management commitment
        "Leadership talks about portfolio management, but it's not really enforced consistently. We have some executive sponsorship from our VP of Product, but follow-through is inconsistent. I'd say it's medium commitment.",
        
        # Anything else
        "No, I think we've covered everything important."
    ]
    
    report_data = None
    final_turn_time = None
    
    for i, msg in enumerate(messages, 1):
        log(f"  Turn {i}/{len(messages)}: Sending message ({len(msg)} chars)")
        
        start_time = time.time()
        resp = requests.post(f"{BASE_URL}/assessments/{assessment_id}/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": msg}
        )
        elapsed = time.time() - start_time
        
        assert resp.status_code == 200, f"Chat turn {i} failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        assert "message" in data, f"No message in turn {i} response"
        ai_response = data["message"]["content"]
        log(f"  Turn {i} completed in {elapsed:.1f}s, AI response: {len(ai_response)} chars")
        
        if data.get("report_ready"):
            log(f"  ✓ Report ready after turn {i}!")
            final_turn_time = elapsed
            report_data = data.get("report")
            break
    
    assert report_data is not None, "Report was not generated after full conversation"
    assert final_turn_time is not None, "Final turn time not captured"
    
    log(f"✓ FULL conversation completed, report generated")
    log(f"✓ TIMING: Final turn took {final_turn_time:.1f} seconds")
    
    # Check timing expectation: should be ~70-100s with Sonnet 4.5, NOT ~165s with Sonnet 5
    if final_turn_time > 120:
        log(f"⚠ WARNING: Final turn took {final_turn_time:.1f}s (expected ~70-100s)")
    else:
        log(f"✓ Timing acceptable: {final_turn_time:.1f}s (target: 70-100s)")
    
    return report_data, final_turn_time

def test_report_fields(report_data):
    """Step 6: Verify ALL 26 report fields are present and non-empty"""
    log("TEST 6: Verify ALL 26 report fields present and non-empty")
    
    missing_fields = []
    empty_fields = []
    
    for field in REQUIRED_FIELDS:
        if field not in report_data:
            missing_fields.append(field)
        else:
            value = report_data[field]
            # Check if empty (None, empty string, empty list, empty dict, or 0 for contextual_score)
            if value is None:
                empty_fields.append(f"{field} (None)")
            elif isinstance(value, str) and not value.strip():
                empty_fields.append(f"{field} (empty string)")
            elif isinstance(value, list) and len(value) == 0:
                empty_fields.append(f"{field} (empty list)")
            elif isinstance(value, dict) and len(value) == 0:
                empty_fields.append(f"{field} (empty dict)")
            elif field == "contextual_score" and value == 0.0:
                empty_fields.append(f"{field} (0.0 - should be non-zero)")
    
    if missing_fields:
        log(f"✗ MISSING FIELDS ({len(missing_fields)}): {', '.join(missing_fields)}")
    
    if empty_fields:
        log(f"✗ EMPTY FIELDS ({len(empty_fields)}): {', '.join(empty_fields)}")
    
    if not missing_fields and not empty_fields:
        log(f"✓ ALL 26 fields present and non-empty")
    
    # Specific checks for fields that failed with Sonnet 5
    critical_fields = [
        "contextual_score",
        "failure_pattern_name",
        "failure_pattern_narrative",
        "governance_assessment",
        "governance_signal_summary"
    ]
    
    log("  Checking critical fields that failed with Sonnet 5:")
    for field in critical_fields:
        value = report_data.get(field)
        if field == "contextual_score":
            if value and value != 0.0:
                log(f"  ✓ {field}: {value} (non-zero)")
            else:
                log(f"  ✗ {field}: {value} (should be non-zero)")
        elif field == "governance_signal_summary":
            if value and isinstance(value, list) and len(value) > 0:
                log(f"  ✓ {field}: {len(value)} items")
            else:
                log(f"  ✗ {field}: empty or missing")
        else:
            if value and (not isinstance(value, str) or value.strip()):
                log(f"  ✓ {field}: present ({len(str(value))} chars)")
            else:
                log(f"  ✗ {field}: empty or missing")
    
    # Check roadmap continuity
    roadmap = report_data.get("roadmap", {})
    scores = report_data.get("scores", {})
    if roadmap and scores:
        immediate = roadmap.get("immediate", {})
        expected_gain = immediate.get("expected_gain", "")
        if expected_gain:
            log(f"  Checking roadmap continuity:")
            log(f"    Pillar scores: People={scores.get('people')}, Process={scores.get('process')}, Data={scores.get('data')}, Technology={scores.get('technology')}")
            log(f"    Immediate phase expected_gain: {expected_gain}")
    
    return len(missing_fields) == 0 and len(empty_fields) == 0

def test_pdf_generation(token, assessment_id):
    """Step 7: GET /api/assessments/{id}/pdf → 200, valid PDF"""
    log("TEST 7: GET /api/assessments/{id}/pdf")
    resp = requests.get(f"{BASE_URL}/assessments/{assessment_id}/pdf",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"PDF generation failed: {resp.status_code}"
    assert resp.headers.get("content-type") == "application/pdf", \
        f"Wrong content type: {resp.headers.get('content-type')}"
    pdf_bytes = resp.content
    assert pdf_bytes.startswith(b"%PDF"), "Invalid PDF signature"
    assert len(pdf_bytes) > 5000, f"PDF too small: {len(pdf_bytes)} bytes"
    log(f"✓ Full PDF generated: {len(pdf_bytes)} bytes, valid %PDF signature")
    return len(pdf_bytes)

def test_summary_pdf_generation(token, assessment_id):
    """Step 8: GET /api/assessments/{id}/summary-pdf → 200, valid PDF"""
    log("TEST 8: GET /api/assessments/{id}/summary-pdf")
    resp = requests.get(f"{BASE_URL}/assessments/{assessment_id}/summary-pdf",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Summary PDF generation failed: {resp.status_code}"
    assert resp.headers.get("content-type") == "application/pdf", \
        f"Wrong content type: {resp.headers.get('content-type')}"
    pdf_bytes = resp.content
    assert pdf_bytes.startswith(b"%PDF"), "Invalid PDF signature"
    assert len(pdf_bytes) > 3000, f"Summary PDF too small: {len(pdf_bytes)} bytes"
    log(f"✓ Summary PDF generated: {len(pdf_bytes)} bytes, valid %PDF signature")
    return len(pdf_bytes)

def test_assessments_list(token):
    """Step 9: GET /api/assessments → 200, regression check"""
    log("TEST 9: GET /api/assessments (regression check)")
    resp = requests.get(f"{BASE_URL}/assessments",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Get assessments failed: {resp.status_code}"
    data = resp.json()
    assert isinstance(data, list), "Response is not a list"
    log(f"✓ Assessments list retrieved: {len(data)} assessments")
    return len(data)

def test_max_length_validation(token, company_id):
    """Step 10: NEW TEST - create fresh assessment, call /start, then POST /chat with 9000-char message → expect 422"""
    log("TEST 10: NEW TEST - max_length=8000 validation on chat message")
    
    # Create fresh assessment
    resp = requests.post(f"{BASE_URL}/assessments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_id": company_id,
            "respondent_name": "Test User",
            "respondent_role": "Test Role"
        }
    )
    assert resp.status_code == 200, f"Create assessment failed: {resp.status_code}"
    assessment_id = resp.json()["id"]
    log(f"  Created fresh assessment: {assessment_id}")
    
    # Start assessment
    resp = requests.post(f"{BASE_URL}/assessments/{assessment_id}/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Start assessment failed: {resp.status_code}"
    log(f"  Started assessment")
    
    # Send 9000-char message (over 8000 limit)
    long_message = "A" * 9000
    log(f"  Sending {len(long_message)}-char message (over 8000 limit)")
    resp = requests.post(f"{BASE_URL}/assessments/{assessment_id}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": long_message}
    )
    
    assert resp.status_code == 422, \
        f"Expected 422 (validation error), got {resp.status_code}. Response: {resp.text}"
    
    log(f"✓ Validation working: 9000-char message correctly rejected with HTTP 422")
    return assessment_id

def test_idempotency(token, assessment_id):
    """Step 11: Verify idempotency - calling /start twice returns same greeting without error"""
    log("TEST 11: Verify idempotency - calling /start twice")
    
    # First call
    resp1 = requests.post(f"{BASE_URL}/assessments/{assessment_id}/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp1.status_code == 200, f"First /start call failed: {resp1.status_code}"
    greeting1 = resp1.json()["message"]["content"]
    
    # Second call
    resp2 = requests.post(f"{BASE_URL}/assessments/{assessment_id}/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 200, f"Second /start call failed: {resp2.status_code}"
    greeting2 = resp2.json()["message"]["content"]
    
    assert greeting1 == greeting2, "Greetings differ between calls"
    log(f"✓ Idempotency verified: both calls returned same greeting ({len(greeting1)} chars)")

def main():
    log("=" * 80)
    log("REGRESSION TEST: Model revert + 4 audit fixes")
    log("=" * 80)
    
    try:
        # Step 1: Login
        token = test_login()
        
        # Step 2: Create company
        company_id = test_create_company(token)
        
        # Step 3: Create assessment
        assessment_id = test_create_assessment(token, company_id)
        
        # Step 4: Start assessment
        greeting = test_start_assessment(token, assessment_id)
        
        # Step 5: Drive full conversation
        report_data, final_turn_time = test_full_conversation(token, assessment_id)
        
        # Step 6: Verify all 26 fields
        all_fields_ok = test_report_fields(report_data)
        
        # Step 7: Generate full PDF
        pdf_size = test_pdf_generation(token, assessment_id)
        
        # Step 8: Generate summary PDF
        summary_pdf_size = test_summary_pdf_generation(token, assessment_id)
        
        # Step 9: Regression check
        assessment_count = test_assessments_list(token)
        
        # Step 10: Max length validation
        validation_assessment_id = test_max_length_validation(token, company_id)
        
        # Step 11: Idempotency check
        test_idempotency(token, validation_assessment_id)
        
        log("=" * 80)
        log("SUMMARY")
        log("=" * 80)
        log(f"✓ Test 1: Login successful")
        log(f"✓ Test 2: Company created")
        log(f"✓ Test 3: Assessment created")
        log(f"✓ Test 4: AI greeting received")
        log(f"✓ Test 5: Full conversation completed, report generated in {final_turn_time:.1f}s")
        log(f"{'✓' if all_fields_ok else '✗'} Test 6: All 26 fields {'present and non-empty' if all_fields_ok else 'FAILED'}")
        log(f"✓ Test 7: Full PDF generated ({pdf_size} bytes)")
        log(f"✓ Test 8: Summary PDF generated ({summary_pdf_size} bytes)")
        log(f"✓ Test 9: Assessments list retrieved ({assessment_count} assessments)")
        log(f"✓ Test 10: Max length validation working (422 for 9000-char message)")
        log(f"✓ Test 11: Idempotency verified")
        log("=" * 80)
        
        if all_fields_ok and final_turn_time < 120:
            log("✓✓✓ ALL TESTS PASSED ✓✓✓")
            log(f"Report generation model (claude-sonnet-4-5-20250929) is working correctly.")
            log(f"Timing: {final_turn_time:.1f}s (target: 70-100s, acceptable: <120s)")
            return 0
        else:
            if not all_fields_ok:
                log("✗✗✗ FIELD COMPLETENESS FAILED ✗✗✗")
            if final_turn_time >= 120:
                log(f"⚠ WARNING: Timing slower than expected ({final_turn_time:.1f}s)")
            return 1
            
    except AssertionError as e:
        log(f"✗✗✗ TEST FAILED ✗✗✗")
        log(f"Error: {e}")
        return 1
    except Exception as e:
        log(f"✗✗✗ UNEXPECTED ERROR ✗✗✗")
        log(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
