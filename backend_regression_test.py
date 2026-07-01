#!/usr/bin/env python3
"""
Backend Regression Test - AI Assessment Flow
Tests the end-to-end flow after backend/.env and Python dependencies were recreated.
Focus: Verify LLM integration (start assessment + chat) works correctly.
"""

import requests
import json
import sys
import uuid
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://4ad4b2b3-a136-4aa5-a519-c697503c7614.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"

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

def test_login() -> Optional[str]:
    """Test 1: POST /api/auth/login"""
    print_test("1. POST /api/auth/login - Admin Login")
    
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

def test_create_company(token: str) -> Optional[str]:
    """Test 2: POST /api/companies - Create Company"""
    print_test("2. POST /api/companies - Create Test Company")
    
    url = f"{BACKEND_URL}/companies"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Use realistic test data
    company_name = f"Nordic Manufacturing Solutions {uuid.uuid4().hex[:6]}"
    payload = {
        "name": company_name,
        "industry": "Manufacturing",
        "company_size": "Mid-market · 450 employees",
        "active_products": "28 active SKUs",
        "primary_challenge": "Process efficiency"
    }
    
    print_info(f"Creating company: {company_name}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            company_id = data.get("id") or data.get("company_id")
            if company_id:
                print_pass(f"Company created successfully (ID: {company_id})")
                return company_id
            else:
                print_fail("No company ID in response")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                return None
        else:
            print_fail(f"Create company failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_fail(f"Create company request failed: {str(e)}")
        return None

def test_create_assessment(token: str, company_id: str) -> Optional[str]:
    """Test 3: POST /api/assessments - Create Assessment"""
    print_test("3. POST /api/assessments - Create Assessment")
    
    url = f"{BACKEND_URL}/assessments"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "company_id": company_id,
        "respondent_name": "Test Manager",
        "respondent_role": "Operations Manager"
    }
    
    print_info(f"Creating assessment for company: {company_id}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            assessment_id = data.get("id") or data.get("assessment_id")
            if assessment_id:
                print_pass(f"Assessment created successfully (ID: {assessment_id})")
                return assessment_id
            else:
                print_fail("No assessment ID in response")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                return None
        else:
            print_fail(f"Create assessment failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_fail(f"Create assessment request failed: {str(e)}")
        return None

def test_start_assessment(token: str, assessment_id: str) -> bool:
    """Test 4: POST /api/assessments/{id}/start - LLM Greeting (CRITICAL)"""
    print_test("4. POST /api/assessments/{id}/start - Start Assessment (LLM Greeting)")
    
    url = f"{BACKEND_URL}/assessments/{assessment_id}/start"
    headers = {"Authorization": f"Bearer {token}"}
    
    print_info(f"Starting assessment: {assessment_id}")
    print_info("CRITICAL CHECK: This calls the LLM via EMERGENT_LLM_KEY (Claude Sonnet 4.5)")
    
    try:
        response = requests.post(url, headers=headers, timeout=30)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            message_obj = data.get("message") or data.get("greeting")
            
            if message_obj:
                # Handle both string and dict responses
                if isinstance(message_obj, dict):
                    # Extract content from message dict
                    message = message_obj.get("content", "")
                    if message:
                        message_length = len(message)
                        print_pass(f"Start assessment successful - AI greeting received (length: {message_length} chars)")
                        print_info(f"AI Greeting preview: {message[:150]}...")
                        
                        if message_length > 0:
                            print_pass("AI greeting is non-empty ✓")
                            return True
                        else:
                            print_fail("AI greeting content is empty")
                            return False
                    else:
                        print_fail("No content in message dict")
                        print_info(f"Response data: {json.dumps(data, indent=2)}")
                        return False
                elif isinstance(message_obj, str):
                    message_length = len(message_obj)
                    print_pass(f"Start assessment successful - AI greeting received (length: {message_length} chars)")
                    print_info(f"AI Greeting preview: {message_obj[:150]}...")
                    
                    if message_length > 0:
                        print_pass("AI greeting is non-empty ✓")
                        return True
                    else:
                        print_fail("AI greeting is empty")
                        return False
                else:
                    print_fail(f"AI greeting is unexpected type: {type(message_obj)}")
                    print_info(f"Response data: {json.dumps(data, indent=2)}")
                    return False
            else:
                print_fail("No message/greeting in response")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                return False
        elif response.status_code == 500:
            print_fail("❌ CRITICAL: Start assessment returned 500 (LLM integration failure)")
            print_info(f"Response: {response.text}")
            return False
        else:
            print_fail(f"Start assessment failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_fail(f"Start assessment request failed: {str(e)}")
        return False

def test_chat_message(token: str, assessment_id: str) -> bool:
    """Test 5: POST /api/assessments/{id}/chat - Send Chat Message"""
    print_test("5. POST /api/assessments/{id}/chat - Send Chat Message (AI Response)")
    
    url = f"{BACKEND_URL}/assessments/{assessment_id}/chat"
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, select language (English)
    print_info("Step 5a: Selecting language (English)")
    language_payload = {
        "message": "English"
    }
    
    try:
        response = requests.post(url, json=language_payload, headers=headers, timeout=30)
        print_info(f"Language selection - Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_fail(f"Language selection failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        print_pass("Language selection successful")
        
        # Now send the actual assessment message
        print_info("\nStep 5b: Sending assessment message")
        payload = {
            "message": "We are a mid-size manufacturing company, Standard business model, strategic priority is process efficiency."
        }
        
        print_info(f"Message: {payload['message']}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            ai_response_obj = data.get("response") or data.get("message")
            
            if ai_response_obj:
                # Handle both string and dict responses
                if isinstance(ai_response_obj, dict):
                    # Extract content from response dict
                    ai_response = ai_response_obj.get("content", "")
                    if ai_response:
                        response_length = len(ai_response)
                        print_pass(f"Chat successful - AI response received (length: {response_length} chars)")
                        print_info(f"AI Response preview: {ai_response[:150]}...")
                        
                        if response_length > 0:
                            print_pass("AI response is non-empty ✓")
                            return True
                        else:
                            print_fail("AI response content is empty")
                            return False
                    else:
                        print_fail("No content in response dict")
                        print_info(f"Response data: {json.dumps(data, indent=2)}")
                        return False
                elif isinstance(ai_response_obj, str):
                    response_length = len(ai_response_obj)
                    print_pass(f"Chat successful - AI response received (length: {response_length} chars)")
                    print_info(f"AI Response preview: {ai_response_obj[:150]}...")
                    
                    if response_length > 0:
                        print_pass("AI response is non-empty ✓")
                        return True
                    else:
                        print_fail("AI response is empty")
                        return False
                else:
                    print_fail(f"AI response is unexpected type: {type(ai_response_obj)}")
                    print_info(f"Response data: {json.dumps(data, indent=2)}")
                    return False
            else:
                print_fail("No response/message in response")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                return False
        else:
            print_fail(f"Chat failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_fail(f"Chat request failed: {str(e)}")
        return False

def test_list_assessments(token: str) -> bool:
    """Test 6: GET /api/assessments - List Assessments"""
    print_test("6. GET /api/assessments - List Assessments")
    
    url = f"{BACKEND_URL}/assessments"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print_pass(f"List assessments successful - {len(data)} assessments found")
                return True
            else:
                print_fail(f"Response is not a list (type: {type(data)})")
                return False
        else:
            print_fail(f"List assessments failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_fail(f"List assessments request failed: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Backend Regression Test - AI Assessment Flow{Colors.END}")
    print(f"{Colors.BLUE}After backend/.env and Python dependencies recreation{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Admin Email: {ADMIN_EMAIL}")
    print_info(f"Focus: LLM integration (start assessment + chat)")
    
    results = {
        "1_login": False,
        "2_create_company": False,
        "3_create_assessment": False,
        "4_start_assessment_LLM": False,
        "5_chat_AI_response": False,
        "6_list_assessments": False
    }
    
    # Test 1: Login
    token = test_login()
    if not token:
        print_fail("\n❌ Login failed - cannot proceed with other tests")
        sys.exit(1)
    results["1_login"] = True
    
    # Test 2: Create Company
    company_id = test_create_company(token)
    if not company_id:
        print_fail("\n❌ Create company failed - cannot proceed with assessment tests")
        print_summary(results)
        sys.exit(1)
    results["2_create_company"] = True
    
    # Test 3: Create Assessment
    assessment_id = test_create_assessment(token, company_id)
    if not assessment_id:
        print_fail("\n❌ Create assessment failed - cannot proceed with start/chat tests")
        print_summary(results)
        sys.exit(1)
    results["3_create_assessment"] = True
    
    # Test 4: Start Assessment (LLM Greeting) - CRITICAL
    results["4_start_assessment_LLM"] = test_start_assessment(token, assessment_id)
    
    # Test 5: Chat Message (AI Response)
    results["5_chat_AI_response"] = test_chat_message(token, assessment_id)
    
    # Test 6: List Assessments
    results["6_list_assessments"] = test_list_assessments(token)
    
    # Summary
    print_summary(results)
    
    # Exit with appropriate code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)

def print_summary(results: Dict[str, bool]):
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
    else:
        print(f"\n{Colors.RED}{'='*80}{Colors.END}")
        print(f"{Colors.RED}SOME TESTS FAILED ✗{Colors.END}")
        print(f"{Colors.RED}{'='*80}{Colors.END}")

if __name__ == "__main__":
    main()
