#!/usr/bin/env python3
"""
Backend API Testing for Report/PDF Refactor Regression + Verification
Tests the seeded assessment 6b44c78c2ebdd66625059999 (Lumivex Photonics)
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://cursor-control-fix-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"
SEEDED_ASSESSMENT_ID = "6b44c78c2ebdd66625059999"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

def print_pass(msg: str):
    print(f"{Colors.GREEN}✓ PASS: {msg}{Colors.END}")

def print_fail(msg: str):
    print(f"{Colors.RED}✗ FAIL: {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.YELLOW}ℹ INFO: {msg}{Colors.END}")

def login() -> str:
    """Login and return JWT token"""
    print_test("1. POST /api/auth/login (admin credentials)")
    
    url = f"{BACKEND_URL}/auth/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_pass(f"Login successful, JWT token received (length: {len(token)})")
                return token
            else:
                print_fail("No access_token in response")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                return None
        else:
            print_fail(f"Login failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_fail(f"Login request failed: {str(e)}")
        return None

def verify_report_consistency(token: str) -> bool:
    """Verify report consistency invariants"""
    print_test(f"2. GET /api/assessments/{SEEDED_ASSESSMENT_ID} - Verify Consistency Invariants")
    
    url = f"{BACKEND_URL}/assessments/{SEEDED_ASSESSMENT_ID}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_fail(f"Expected 200, got {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        print_pass("GET request successful (200)")
        
        data = response.json()
        report = data.get("report", {})
        
        if not report:
            print_fail("No 'report' object in response")
            return False
        
        # Extract values for invariant checks
        scores = report.get("scores", {})
        overall_score = scores.get("overall")
        equal_weighted_score = report.get("equal_weighted_score")
        ninety_day = report.get("ninety_day_projection", {})
        score_current = ninety_day.get("score_current")
        score_projected = ninety_day.get("score_projected")
        bottleneck_level_current = ninety_day.get("bottleneck_level_current")
        bottleneck_level_projected = ninety_day.get("bottleneck_level_projected")
        level_names = report.get("level_names", {})
        process_level = level_names.get("process")
        
        # Check new fields
        governance_signal_summary = report.get("governance_signal_summary")
        pillar_interpretation_short = report.get("pillar_interpretation_short")
        roadmap = report.get("roadmap", {})
        
        all_passed = True
        
        # Invariant 1: overall == equal_weighted_score == score_current (all 3.6)
        print_info("\nInvariant 1: report.scores.overall == report.equal_weighted_score == report.ninety_day_projection.score_current (all 3.6)")
        print_info(f"  scores.overall: {overall_score}")
        print_info(f"  equal_weighted_score: {equal_weighted_score}")
        print_info(f"  ninety_day_projection.score_current: {score_current}")
        
        if overall_score == equal_weighted_score == score_current == 3.6:
            print_pass("Invariant 1: All three values equal 3.6 ✓")
        else:
            print_fail(f"Invariant 1: Values not equal or not 3.6")
            all_passed = False
        
        # Invariant 2: score_projected == 3.9 and > score_current
        print_info("\nInvariant 2: report.ninety_day_projection.score_projected == 3.9 and > score_current")
        print_info(f"  score_projected: {score_projected}")
        print_info(f"  score_current: {score_current}")
        
        if score_projected == 3.9:
            print_pass("Invariant 2a: score_projected == 3.9 ✓")
        else:
            print_fail(f"Invariant 2a: score_projected is {score_projected}, expected 3.9")
            all_passed = False
        
        if score_projected and score_current and score_projected > score_current:
            print_pass(f"Invariant 2b: score_projected ({score_projected}) > score_current ({score_current}) ✓")
        else:
            print_fail(f"Invariant 2b: score_projected ({score_projected}) NOT > score_current ({score_current})")
            all_passed = False
        
        # Invariant 3: bottleneck_level_current == "Defined" (matches level_names.process)
        print_info("\nInvariant 3: report.ninety_day_projection.bottleneck_level_current == 'Defined' (matches level_names.process)")
        print_info(f"  bottleneck_level_current: {bottleneck_level_current}")
        print_info(f"  level_names.process: {process_level}")
        
        if bottleneck_level_current == "Defined":
            print_pass("Invariant 3a: bottleneck_level_current == 'Defined' ✓")
        else:
            print_fail(f"Invariant 3a: bottleneck_level_current is '{bottleneck_level_current}', expected 'Defined'")
            all_passed = False
        
        if bottleneck_level_current == process_level:
            print_pass(f"Invariant 3b: bottleneck_level_current matches level_names.process ✓")
        else:
            print_fail(f"Invariant 3b: bottleneck_level_current ('{bottleneck_level_current}') does NOT match level_names.process ('{process_level}')")
            all_passed = False
        
        # Invariant 4: bottleneck_level_projected == "Managed"
        print_info("\nInvariant 4: report.ninety_day_projection.bottleneck_level_projected == 'Managed'")
        print_info(f"  bottleneck_level_projected: {bottleneck_level_projected}")
        
        if bottleneck_level_projected == "Managed":
            print_pass("Invariant 4: bottleneck_level_projected == 'Managed' ✓")
        else:
            print_fail(f"Invariant 4: bottleneck_level_projected is '{bottleneck_level_projected}', expected 'Managed'")
            all_passed = False
        
        # Check new fields
        print_info("\nNew Fields Verification:")
        
        if governance_signal_summary is not None:
            if isinstance(governance_signal_summary, list):
                print_pass(f"governance_signal_summary present (list with {len(governance_signal_summary)} items) ✓")
            else:
                print_fail(f"governance_signal_summary present but not a list (type: {type(governance_signal_summary)})")
                all_passed = False
        else:
            print_fail("governance_signal_summary NOT present")
            all_passed = False
        
        if pillar_interpretation_short is not None:
            if isinstance(pillar_interpretation_short, dict):
                print_pass(f"pillar_interpretation_short present (dict with {len(pillar_interpretation_short)} keys) ✓")
            else:
                print_fail(f"pillar_interpretation_short present but not a dict (type: {type(pillar_interpretation_short)})")
                all_passed = False
        else:
            print_fail("pillar_interpretation_short NOT present")
            all_passed = False
        
        # Check roadmap action_summary fields
        action_summary_found = False
        if roadmap:
            for phase_name, phase_data in roadmap.items():
                if isinstance(phase_data, dict) and "action_summary" in phase_data:
                    action_summary_found = True
                    print_pass(f"roadmap.{phase_name}.action_summary present ✓")
                    break
        
        if action_summary_found:
            print_pass("At least one roadmap phase has action_summary field ✓")
        else:
            print_fail("No roadmap phase has action_summary field")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False

def test_full_pdf(token: str) -> bool:
    """Test full PDF generation"""
    print_test(f"3. GET /api/assessments/{SEEDED_ASSESSMENT_ID}/pdf - Full Report (15-page)")
    
    url = f"{BACKEND_URL}/assessments/{SEEDED_ASSESSMENT_ID}/pdf"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_fail(f"Expected 200, got {response.status_code}")
            print_info(f"Response: {response.text[:500]}")
            return False
        
        print_pass("GET request successful (200)")
        
        # Check Content-Type
        content_type = response.headers.get("Content-Type", "")
        print_info(f"Content-Type: {content_type}")
        
        if "application/pdf" in content_type:
            print_pass("Content-Type is application/pdf ✓")
        else:
            print_fail(f"Content-Type is '{content_type}', expected 'application/pdf'")
            return False
        
        # Check PDF signature
        content = response.content
        pdf_length = len(content)
        print_info(f"PDF length: {pdf_length} bytes")
        
        if content[:4] == b'%PDF':
            print_pass("PDF starts with %PDF signature ✓")
        else:
            print_fail(f"PDF does NOT start with %PDF (starts with: {content[:10]})")
            return False
        
        # Check length > 5000 bytes
        if pdf_length > 5000:
            print_pass(f"PDF length ({pdf_length} bytes) > 5000 bytes ✓")
        else:
            print_fail(f"PDF length ({pdf_length} bytes) NOT > 5000 bytes")
            return False
        
        return True
        
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False

def test_summary_pdf(token: str) -> bool:
    """Test executive summary PDF generation"""
    print_test(f"4. GET /api/assessments/{SEEDED_ASSESSMENT_ID}/summary-pdf - Executive Summary (4-page)")
    
    url = f"{BACKEND_URL}/assessments/{SEEDED_ASSESSMENT_ID}/summary-pdf"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_fail(f"Expected 200, got {response.status_code}")
            print_info(f"Response: {response.text[:500]}")
            return False
        
        print_pass("GET request successful (200)")
        
        # Check Content-Type
        content_type = response.headers.get("Content-Type", "")
        print_info(f"Content-Type: {content_type}")
        
        if "application/pdf" in content_type:
            print_pass("Content-Type is application/pdf ✓")
        else:
            print_fail(f"Content-Type is '{content_type}', expected 'application/pdf'")
            return False
        
        # Check PDF signature
        content = response.content
        pdf_length = len(content)
        print_info(f"PDF length: {pdf_length} bytes")
        
        if content[:4] == b'%PDF':
            print_pass("PDF starts with %PDF signature ✓")
        else:
            print_fail(f"PDF does NOT start with %PDF (starts with: {content[:10]})")
            return False
        
        # Check length > 3000 bytes
        if pdf_length > 3000:
            print_pass(f"PDF length ({pdf_length} bytes) > 3000 bytes ✓")
        else:
            print_fail(f"PDF length ({pdf_length} bytes) NOT > 3000 bytes")
            return False
        
        return True
        
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False

def test_assessments_list(token: str) -> bool:
    """Regression test: list assessments"""
    print_test("5. GET /api/assessments - Regression Test")
    
    url = f"{BACKEND_URL}/assessments"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_fail(f"Expected 200, got {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        print_pass("GET request successful (200)")
        
        data = response.json()
        
        if isinstance(data, list):
            print_pass(f"Response is a list with {len(data)} assessments ✓")
            
            # Check if our seeded assessment is in the list
            found_seeded = False
            for assessment in data:
                if assessment.get("id") == SEEDED_ASSESSMENT_ID:
                    found_seeded = True
                    print_pass(f"Seeded assessment {SEEDED_ASSESSMENT_ID} found in list ✓")
                    break
            
            if not found_seeded:
                print_info(f"Seeded assessment {SEEDED_ASSESSMENT_ID} not found in list (may be filtered)")
            
            return True
        else:
            print_fail(f"Response is not a list (type: {type(data)})")
            return False
        
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Backend API Testing - Report/PDF Refactor Regression + Verification{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Admin Email: {ADMIN_EMAIL}")
    print_info(f"Seeded Assessment ID: {SEEDED_ASSESSMENT_ID}")
    
    results = {
        "login": False,
        "report_consistency": False,
        "full_pdf": False,
        "summary_pdf": False,
        "assessments_list": False
    }
    
    # Step 1: Login
    token = login()
    if not token:
        print_fail("\n❌ Login failed - cannot proceed with other tests")
        sys.exit(1)
    
    results["login"] = True
    
    # Step 2: Verify report consistency
    results["report_consistency"] = verify_report_consistency(token)
    
    # Step 3: Test full PDF
    results["full_pdf"] = test_full_pdf(token)
    
    # Step 4: Test summary PDF
    results["summary_pdf"] = test_summary_pdf(token)
    
    # Step 5: Regression test
    results["assessments_list"] = test_assessments_list(token)
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n{Colors.GREEN}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}ALL TESTS PASSED ✓{Colors.END}")
        print(f"{Colors.GREEN}{'='*80}{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{'='*80}{Colors.END}")
        print(f"{Colors.RED}SOME TESTS FAILED ✗{Colors.END}")
        print(f"{Colors.RED}{'='*80}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
