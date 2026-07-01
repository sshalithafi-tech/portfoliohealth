#!/usr/bin/env python3
"""
Backend API test for Executive Summary PDF redesign verification.
Tests only the PDF/report endpoints after visual-only changes to executive_summary_builder.py.
"""

import requests
import sys

# Backend URL from frontend/.env
BACKEND_URL = "https://e4765877-f239-4dfd-a6c2-2ccddf64c5ba.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"

# Seeded completed assessment ID
ASSESSMENT_ID = "6b44c78c2ebdd66625059999"

def test_login():
    """Test 1: POST /api/auth/login with admin credentials"""
    print("\n" + "="*80)
    print("TEST 1: POST /api/auth/login")
    print("="*80)
    
    url = f"{BACKEND_URL}/auth/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print(f"✓ PASSED: Login successful, JWT token received (length: {len(data['access_token'])})")
                return data["access_token"]
            elif "token" in data:
                print(f"✓ PASSED: Login successful, JWT token received (length: {len(data['token'])})")
                return data["token"]
            else:
                print(f"✗ FAILED: Login returned 200 but no token in response: {data}")
                return None
        else:
            print(f"✗ FAILED: Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ FAILED: Exception during login: {e}")
        return None

def test_summary_pdf(token):
    """Test 2: GET /api/assessments/{id}/summary-pdf - Executive Summary PDF (redesigned)"""
    print("\n" + "="*80)
    print("TEST 2: GET /api/assessments/{id}/summary-pdf (Executive Summary PDF)")
    print("="*80)
    
    url = f"{BACKEND_URL}/assessments/{ASSESSMENT_ID}/summary-pdf"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            pdf_bytes = response.content
            pdf_size = len(pdf_bytes)
            
            print(f"PDF Size: {pdf_size} bytes ({pdf_size / 1024:.2f} KB)")
            
            # Check if bytes start with %PDF
            starts_with_pdf = pdf_bytes[:4] == b'%PDF'
            print(f"Starts with %PDF: {starts_with_pdf}")
            
            # Check Content-Type
            is_pdf_content_type = 'application/pdf' in content_type
            print(f"Content-Type is application/pdf: {is_pdf_content_type}")
            
            # Check size is meaningfully larger than before (~8.6KB previously, should be ~13-14KB now)
            # Previous size was ~8651 bytes, new should be roughly 13000-14000 bytes
            size_increased = pdf_size > 10000  # At least 10KB to be safe
            print(f"Size increased from ~8.6KB: {size_increased} (target: ~13-14KB)")
            
            if is_pdf_content_type and starts_with_pdf and size_increased:
                print(f"✓ PASSED: Executive Summary PDF generated successfully")
                print(f"  - Valid PDF signature (%PDF)")
                print(f"  - Correct Content-Type (application/pdf)")
                print(f"  - Size increased from ~8.6KB to {pdf_size / 1024:.2f}KB (reflects new charts/cards)")
                return True
            else:
                print(f"✗ FAILED: Executive Summary PDF validation failed")
                if not is_pdf_content_type:
                    print(f"  - Wrong Content-Type: {content_type}")
                if not starts_with_pdf:
                    print(f"  - Invalid PDF signature: {pdf_bytes[:10]}")
                if not size_increased:
                    print(f"  - Size not increased enough: {pdf_size} bytes (expected >10KB)")
                return False
        else:
            print(f"✗ FAILED: Summary PDF request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"✗ FAILED: Exception during summary PDF request: {e}")
        return False

def test_full_pdf(token):
    """Test 3: GET /api/assessments/{id}/pdf - Full 15-page report (regression test)"""
    print("\n" + "="*80)
    print("TEST 3: GET /api/assessments/{id}/pdf (Full 15-page report - REGRESSION)")
    print("="*80)
    
    url = f"{BACKEND_URL}/assessments/{ASSESSMENT_ID}/pdf"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            pdf_bytes = response.content
            pdf_size = len(pdf_bytes)
            
            print(f"PDF Size: {pdf_size} bytes ({pdf_size / 1024:.2f} KB)")
            
            # Check if bytes start with %PDF
            starts_with_pdf = pdf_bytes[:4] == b'%PDF'
            print(f"Starts with %PDF: {starts_with_pdf}")
            
            # Check Content-Type
            is_pdf_content_type = 'application/pdf' in content_type
            print(f"Content-Type is application/pdf: {is_pdf_content_type}")
            
            # Full report should be larger (previously ~22KB)
            size_reasonable = pdf_size > 5000  # At least 5KB
            print(f"Size reasonable for full report: {size_reasonable}")
            
            if is_pdf_content_type and starts_with_pdf and size_reasonable:
                print(f"✓ PASSED: Full report PDF generated successfully (regression test passed)")
                print(f"  - Valid PDF signature (%PDF)")
                print(f"  - Correct Content-Type (application/pdf)")
                print(f"  - Size: {pdf_size / 1024:.2f}KB")
                return True
            else:
                print(f"✗ FAILED: Full report PDF validation failed")
                if not is_pdf_content_type:
                    print(f"  - Wrong Content-Type: {content_type}")
                if not starts_with_pdf:
                    print(f"  - Invalid PDF signature: {pdf_bytes[:10]}")
                if not size_reasonable:
                    print(f"  - Size too small: {pdf_size} bytes")
                return False
        else:
            print(f"✗ FAILED: Full PDF request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"✗ FAILED: Exception during full PDF request: {e}")
        return False

def test_assessments_list(token):
    """Test 4: GET /api/assessments - List assessments (regression test)"""
    print("\n" + "="*80)
    print("TEST 4: GET /api/assessments (List assessments - REGRESSION)")
    print("="*80)
    
    url = f"{BACKEND_URL}/assessments"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            
            if isinstance(data, list):
                print(f"Number of assessments: {len(data)}")
                
                # Check if seeded assessment is in the list
                seeded_found = any(a.get('id') == ASSESSMENT_ID for a in data)
                print(f"Seeded assessment {ASSESSMENT_ID} found: {seeded_found}")
                
                if seeded_found:
                    print(f"✓ PASSED: Assessments list retrieved successfully, seeded assessment found")
                    return True
                else:
                    print(f"✗ FAILED: Seeded assessment {ASSESSMENT_ID} not found in list")
                    print(f"Available assessment IDs: {[a.get('id') for a in data]}")
                    return False
            else:
                print(f"✗ FAILED: Response is not a list: {data}")
                return False
        else:
            print(f"✗ FAILED: Assessments list request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"✗ FAILED: Exception during assessments list request: {e}")
        return False

def main():
    """Run all backend tests"""
    print("\n" + "="*80)
    print("BACKEND API TEST: Executive Summary PDF Redesign Verification")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    print(f"Assessment ID: {ASSESSMENT_ID}")
    
    results = {
        "test_1_login": False,
        "test_2_summary_pdf": False,
        "test_3_full_pdf": False,
        "test_4_assessments_list": False
    }
    
    # Test 1: Login
    token = test_login()
    if token:
        results["test_1_login"] = True
    else:
        print("\n✗ CRITICAL: Login failed, cannot proceed with other tests")
        print_summary(results)
        sys.exit(1)
    
    # Test 2: Executive Summary PDF (the redesigned one)
    results["test_2_summary_pdf"] = test_summary_pdf(token)
    
    # Test 3: Full PDF (regression)
    results["test_3_full_pdf"] = test_full_pdf(token)
    
    # Test 4: Assessments list (regression)
    results["test_4_assessments_list"] = test_assessments_list(token)
    
    # Print summary
    print_summary(results)
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✓ PASSED" if passed_flag else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if all(results.values()):
        print("\n✓ ALL TESTS PASSED - Executive Summary PDF redesign verified successfully")
    else:
        print("\n✗ SOME TESTS FAILED - See details above")

if __name__ == "__main__":
    main()
