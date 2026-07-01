"""
Comprehensive backend test for report generation with Claude Sonnet 5.

Tests the FULL report-generation flow after upgrading report_sections.py's model
from claude-sonnet-4-5-20250929 to claude-sonnet-5.

Test Steps:
1. Login (POST /api/auth/login)
2. Create a company (POST /api/companies)
3. Create an assessment (POST /api/assessments)
4. POST /api/assessments/{id}/start to get the AI greeting
5. Drive a FULL conversation via repeated POST /api/assessments/{id}/chat calls:
   - Select language (e.g. "English")
   - Answer context/anchor questions
   - Answer People/Process/Data/Technology pillar questions
   - Answer governance probe
   - Confirm/close (e.g. "no, that's all")
   - Continue until response includes report_ready: true and populated report object
6. TIME the final report-generating turn
7. Verify the returned report object has ALL required fields present and non-empty
8. Verify roadmap continuity
9. GET /api/assessments/{id}/pdf — confirm 200, application/pdf, valid %PDF bytes
10. GET /api/assessments/{id}/summary-pdf — confirm 200, application/pdf, valid %PDF bytes
11. Regression: GET /api/assessments — confirm 200, list includes this assessment
"""
import asyncio
import json
import time
from datetime import datetime
import requests

# Backend URL from frontend/.env
BASE_URL = "https://3b9051c6-d242-4cb5-8c23-c2efa7f58051.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"

# Required fields in the report object (26 fields total)
REQUIRED_FIELDS = [
    "scores",
    "equal_weighted_score",
    "contextual_score",
    "level_names",
    "dimension_summaries",
    "pillar_interpretations",
    "pillar_interpretation_short",
    "failure_pattern_name",
    "failure_pattern_narrative",
    "financial_consequence",
    "ninety_day_projection",
    "governance_observations",
    "governance_assessment",
    "governance_signal_summary",
    "management_commitment",
    "management_commitment_assessment",
    "assessment_reliability",
    "decision_vulnerability_ratings",
    "decision_vulnerability",
    "key_findings",
    "critical_gaps",
    "roadmap",
    "first_action",
    "benchmark_context",
    "consultant_note",
    "closing_statement",
]

# Conversation flow for a realistic assessment
CONVERSATION_TURNS = [
    # Turn 1: Language selection
    "English",
    
    # Turn 2: Company context
    "We are TechFlow Solutions, a mid-sized software company in the B2B SaaS space. We have about 45 active products and around 200 employees.",
    
    # Turn 3: Business model
    "We operate primarily as a Standard business model - we have configurable software products that we customize for different customer segments.",
    
    # Turn 4: Strategic priority
    "Our main strategic priority is improving data quality and analytics capabilities to make better portfolio decisions.",
    
    # Turn 5: Anchor decision
    "Our most challenging decision recently was whether to discontinue three legacy products that still had some revenue but were consuming significant maintenance resources.",
    
    # Turn 6: People pillar
    "We have a product management team of 5 people, but roles are not clearly defined. Product decisions often depend on who is available. We don't have formal data ownership or governance roles.",
    
    # Turn 7: Process pillar
    "We have quarterly business reviews, but they're not well structured. We don't have formal stage-gate processes. Product changes are often approved via email or Slack conversations.",
    
    # Turn 8: Data pillar
    "Our product data is scattered across Salesforce, Jira, and various Excel spreadsheets. We don't have a single source of truth for product profitability. Financial data comes from our ERP but it's not integrated with product data.",
    
    # Turn 9: Technology pillar
    "We use Salesforce for CRM, Jira for development tracking, and QuickBooks for financials. These systems don't talk to each other. Most portfolio analysis is done manually in Excel.",
    
    # Turn 10: Governance
    "Portfolio decisions are made by the executive team in monthly meetings, but there's no formal governance structure. We don't have documented decision criteria or audit trails.",
    
    # Turn 11: Anything else / close
    "No, that covers everything. I think we've discussed all the key areas.",
]


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_result(test_name, passed, details=""):
    """Print test result with formatting."""
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"{status} - {test_name}")
    if details:
        print(f"  {details}")


def verify_field_present_and_non_empty(report, field_path):
    """
    Verify a field exists and is non-empty in the report.
    field_path can be a simple string like "scores" or a dot-separated path like "roadmap.immediate"
    """
    parts = field_path.split(".")
    current = report
    
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, f"Field '{field_path}' not found"
        current = current[part]
    
    # Check if non-empty
    if current is None:
        return False, f"Field '{field_path}' is None"
    
    if isinstance(current, (str, list, dict)):
        if not current:
            return False, f"Field '{field_path}' is empty"
    
    return True, ""


def verify_roadmap_continuity(report):
    """
    Verify roadmap continuity:
    - roadmap.immediate's expected_gain starting values match the confirmed pillar scores
    """
    scores = report.get("scores", {})
    roadmap = report.get("roadmap", {})
    immediate = roadmap.get("immediate", {})
    expected_gain = immediate.get("expected_gain", "")
    
    if not expected_gain:
        return False, "roadmap.immediate.expected_gain is empty"
    
    # Parse expected_gain format: "People: X.X → X.X | Process: X.X → X.X | Data: X.X → X.X | Technology: X.X → X.X"
    import re
    pattern = r"(People|Process|Data|Technology):\s*([\d.]+)\s*[→->]\s*([\d.]+)"
    matches = re.findall(pattern, expected_gain)
    
    if len(matches) != 4:
        return False, f"expected_gain format incorrect: {expected_gain}"
    
    mismatches = []
    for pillar_name, start_str, end_str in matches:
        pillar_key = pillar_name.lower()
        try:
            start_value = float(start_str)
            score_value = float(scores.get(pillar_key, 0))
            
            # Allow small floating point differences
            if abs(start_value - score_value) > 0.01:
                mismatches.append(
                    f"{pillar_name}: expected_gain starts at {start_value} but score is {score_value}"
                )
        except (ValueError, TypeError) as e:
            return False, f"Error parsing values for {pillar_name}: {e}"
    
    if mismatches:
        return False, "; ".join(mismatches)
    
    return True, "All starting values match pillar scores"


def main():
    print_section("BACKEND TEST: Full Report Generation Flow (Claude Sonnet 5)")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    token = None
    company_id = None
    assessment_id = None
    
    try:
        # ===================================================================
        # TEST 1: Login
        # ===================================================================
        print_section("TEST 1: Login")
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                print_result("Login", True, f"Token received: {token[:20]}...")
            else:
                print_result("Login", False, f"No token in response: {data}")
                return
        else:
            print_result("Login", False, f"HTTP {response.status_code}: {response.text}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # ===================================================================
        # TEST 2: Create Company
        # ===================================================================
        print_section("TEST 2: Create Company")
        response = requests.post(
            f"{BASE_URL}/companies",
            headers=headers,
            json={
                "name": f"Test Company {int(time.time())}",
                "industry": "Software & Technology"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            company_id = data.get("id")
            print_result("Create Company", True, f"Company ID: {company_id}")
        else:
            print_result("Create Company", False, f"HTTP {response.status_code}: {response.text}")
            return
        
        # ===================================================================
        # TEST 3: Create Assessment
        # ===================================================================
        print_section("TEST 3: Create Assessment")
        response = requests.post(
            f"{BASE_URL}/assessments",
            headers=headers,
            json={
                "company_id": company_id,
                "respondent_name": "Test User",
                "respondent_role": "Product Manager"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            assessment_id = data.get("id")
            print_result("Create Assessment", True, f"Assessment ID: {assessment_id}")
        else:
            print_result("Create Assessment", False, f"HTTP {response.status_code}: {response.text}")
            return
        
        # ===================================================================
        # TEST 4: Start Assessment (AI Greeting)
        # ===================================================================
        print_section("TEST 4: Start Assessment (AI Greeting)")
        response = requests.post(
            f"{BASE_URL}/assessments/{assessment_id}/start",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            # Response structure: {"message": {"role": "assistant", "content": "...", "timestamp": "..."}}
            message_obj = data.get("message", {})
            if isinstance(message_obj, dict):
                greeting = message_obj.get("content", "")
            else:
                greeting = message_obj if isinstance(message_obj, str) else ""
            
            if isinstance(greeting, str) and greeting:
                print_result("Start Assessment", True, f"Greeting received ({len(greeting)} chars)")
                if len(greeting) > 100:
                    print(f"  Greeting preview: {greeting[:100]}...")
                else:
                    print(f"  Greeting: {greeting}")
            else:
                print_result("Start Assessment", False, f"Unexpected response structure: {data}")
                return
        else:
            print_result("Start Assessment", False, f"HTTP {response.status_code}: {response.text}")
            return
        
        # ===================================================================
        # TEST 5: Drive Full Conversation Until Report Ready
        # ===================================================================
        print_section("TEST 5: Drive Full Conversation")
        
        report_ready = False
        report_data = None
        final_turn_time = None
        turn_number = 0
        
        for user_message in CONVERSATION_TURNS:
            turn_number += 1
            print(f"\n--- Turn {turn_number} ---")
            print(f"User: {user_message[:80]}{'...' if len(user_message) > 80 else ''}")
            
            # Time this turn
            turn_start = time.time()
            
            response = requests.post(
                f"{BASE_URL}/assessments/{assessment_id}/chat",
                headers=headers,
                json={"message": user_message},
                timeout=180  # 3 minutes timeout for report generation
            )
            
            turn_end = time.time()
            turn_duration = turn_end - turn_start
            
            if response.status_code != 200:
                print_result(f"Chat Turn {turn_number}", False, 
                           f"HTTP {response.status_code}: {response.text[:200]}")
                return
            
            data = response.json()
            # Response structure: {"message": "...", "report_ready": false/true, "report": {...}}
            ai_message = data.get("message", "")
            if isinstance(ai_message, dict):
                ai_message = ai_message.get("content", "")
            
            report_ready = data.get("report_ready", False)
            
            if isinstance(ai_message, str):
                if len(ai_message) > 100:
                    print(f"AI: {ai_message[:100]}...")
                else:
                    print(f"AI: {ai_message}")
            else:
                print(f"AI: [Unexpected message type: {type(ai_message)}]")
            
            print(f"Turn duration: {turn_duration:.1f}s")
            
            if report_ready:
                report_data = data.get("report")
                final_turn_time = turn_duration
                print(f"\n🎉 REPORT READY after {turn_number} turns!")
                print(f"⏱️  FINAL TURN TIME: {final_turn_time:.1f} seconds")
                break
        
        if not report_ready:
            print_result("Full Conversation", False, 
                       f"Report not ready after {turn_number} turns")
            return
        
        print_result("Full Conversation", True, 
                   f"Report generated in {final_turn_time:.1f}s after {turn_number} turns")
        
        # ===================================================================
        # TEST 6: Verify Report Field Completeness
        # ===================================================================
        print_section("TEST 6: Verify Report Field Completeness")
        
        missing_fields = []
        empty_fields = []
        
        for field in REQUIRED_FIELDS:
            present, error = verify_field_present_and_non_empty(report_data, field)
            if not present:
                if "not found" in error:
                    missing_fields.append(field)
                else:
                    empty_fields.append(field)
        
        # Special checks for nested fields
        nested_checks = [
            "roadmap.immediate",
            "roadmap.short_term",
            "roadmap.strategic",
            "roadmap.immediate.expected_gain",
            "roadmap.short_term.expected_gain",
            "roadmap.strategic.expected_gain",
        ]
        
        for field_path in nested_checks:
            present, error = verify_field_present_and_non_empty(report_data, field_path)
            if not present:
                if "not found" in error:
                    missing_fields.append(field_path)
                else:
                    empty_fields.append(field_path)
        
        total_fields = len(REQUIRED_FIELDS) + len(nested_checks)
        present_count = total_fields - len(missing_fields) - len(empty_fields)
        
        print(f"Field completeness: {present_count}/{total_fields} fields present and non-empty")
        
        if missing_fields:
            print(f"\n❌ MISSING FIELDS ({len(missing_fields)}):")
            for field in missing_fields:
                print(f"  - {field}")
        
        if empty_fields:
            print(f"\n⚠️  EMPTY FIELDS ({len(empty_fields)}):")
            for field in empty_fields:
                print(f"  - {field}")
        
        # Print some key field values for verification
        print(f"\n📊 Key Report Values:")
        print(f"  equal_weighted_score: {report_data.get('equal_weighted_score')}")
        print(f"  contextual_score: {report_data.get('contextual_score')}")
        print(f"  scores.overall: {report_data.get('scores', {}).get('overall')}")
        print(f"  scores.people: {report_data.get('scores', {}).get('people')}")
        print(f"  scores.process: {report_data.get('scores', {}).get('process')}")
        print(f"  scores.data: {report_data.get('scores', {}).get('data')}")
        print(f"  scores.technology: {report_data.get('scores', {}).get('technology')}")
        print(f"  failure_pattern_name: {report_data.get('failure_pattern_name')}")
        print(f"  management_commitment: {report_data.get('management_commitment')}")
        
        # Check critical_gaps for Precondition labels
        critical_gaps = report_data.get("critical_gaps", [])
        print(f"\n  critical_gaps count: {len(critical_gaps)}")
        if critical_gaps:
            gaps_with_labels = [g for g in critical_gaps if "Precondition" in str(g)]
            print(f"  critical_gaps with Precondition labels: {len(gaps_with_labels)}/{len(critical_gaps)}")
            if gaps_with_labels:
                print(f"  Example: {gaps_with_labels[0][:100]}...")
        
        # Check consultant_note length
        consultant_note = report_data.get("consultant_note", "")
        if consultant_note:
            word_count = len(consultant_note.split())
            print(f"\n  consultant_note: {len(consultant_note)} chars, ~{word_count} words")
            if word_count > 250:
                print(f"    ⚠️  WARNING: Exceeds 250-word cap")
        
        # Check benchmark_context
        benchmark_context = report_data.get("benchmark_context", "")
        if benchmark_context:
            print(f"  benchmark_context: {len(benchmark_context)} chars")
        
        all_fields_ok = len(missing_fields) == 0 and len(empty_fields) == 0
        print_result("Field Completeness", all_fields_ok, 
                   f"{present_count}/{total_fields} fields verified")
        
        # ===================================================================
        # TEST 7: Verify Roadmap Continuity
        # ===================================================================
        print_section("TEST 7: Verify Roadmap Continuity")
        
        continuity_ok, continuity_msg = verify_roadmap_continuity(report_data)
        print_result("Roadmap Continuity", continuity_ok, continuity_msg)
        
        if continuity_ok:
            immediate = report_data.get("roadmap", {}).get("immediate", {})
            print(f"  expected_gain: {immediate.get('expected_gain')}")
        
        # ===================================================================
        # TEST 8: GET Full PDF
        # ===================================================================
        print_section("TEST 8: GET Full PDF")
        
        response = requests.get(
            f"{BASE_URL}/assessments/{assessment_id}/pdf",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            pdf_bytes = response.content
            is_pdf = pdf_bytes[:4] == b"%PDF"
            
            print_result("Full PDF", is_pdf and "application/pdf" in content_type,
                       f"{len(pdf_bytes)} bytes, Content-Type: {content_type}, "
                       f"Valid PDF signature: {is_pdf}")
        else:
            print_result("Full PDF", False, f"HTTP {response.status_code}")
        
        # ===================================================================
        # TEST 9: GET Summary PDF
        # ===================================================================
        print_section("TEST 9: GET Summary PDF")
        
        response = requests.get(
            f"{BASE_URL}/assessments/{assessment_id}/summary-pdf",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            pdf_bytes = response.content
            is_pdf = pdf_bytes[:4] == b"%PDF"
            
            print_result("Summary PDF", is_pdf and "application/pdf" in content_type,
                       f"{len(pdf_bytes)} bytes, Content-Type: {content_type}, "
                       f"Valid PDF signature: {is_pdf}")
        else:
            print_result("Summary PDF", False, f"HTTP {response.status_code}")
        
        # ===================================================================
        # TEST 10: Regression - GET Assessments List
        # ===================================================================
        print_section("TEST 10: Regression - GET Assessments List")
        
        response = requests.get(
            f"{BASE_URL}/assessments",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            assessments = response.json()
            found = any(a.get("id") == assessment_id for a in assessments)
            print_result("Assessments List", found,
                       f"List contains {len(assessments)} assessments, "
                       f"test assessment {'found' if found else 'NOT FOUND'}")
        else:
            print_result("Assessments List", False, f"HTTP {response.status_code}")
        
        # ===================================================================
        # FINAL SUMMARY
        # ===================================================================
        print_section("TEST SUMMARY")
        print(f"✅ All core tests completed")
        print(f"⏱️  Report generation time: {final_turn_time:.1f} seconds")
        print(f"📊 Field completeness: {present_count}/{total_fields}")
        print(f"🔗 Roadmap continuity: {'✓ PASSED' if continuity_ok else '✗ FAILED'}")
        
        if missing_fields or empty_fields:
            print(f"\n⚠️  Issues found:")
            if missing_fields:
                print(f"   - {len(missing_fields)} missing fields")
            if empty_fields:
                print(f"   - {len(empty_fields)} empty fields")
        else:
            print(f"\n✅ All required fields present and non-empty")
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
