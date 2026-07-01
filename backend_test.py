"""
Backend test for AI assessment start + chat flow after environment reset recovery.
Tests the critical LLM integration using the user's ANTHROPIC_API_KEY.

This test follows the exact sequence requested:
1. Login with admin credentials
2. Create a test company
3. Create an assessment
4. Start assessment (POST /start) - CRITICAL CHECK: must return 200 with AI greeting, NOT 500
5. Send one chat message (language selection) - must return 200 with AI response
6. Regression check (GET /assessments)
"""
import requests
import json
import time

# Backend URL from frontend/.env
BACKEND_URL = "https://3b9051c6-d242-4cb5-8c23-c2efa7f58051.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"

class AIAssessmentTester:
    def __init__(self):
        self.token = None
        self.company_id = None
        self.assessment_id = None
        
    def test_1_login(self) -> bool:
        """Test 1: POST /api/auth/login with admin credentials"""
        print("\n" + "="*80)
        print("TEST 1: Login with admin credentials")
        print("="*80)
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    print(f"✓ PASSED: Login successful, JWT token received")
                    print(f"Token preview: {self.token[:20]}...")
                    return True
                else:
                    print(f"✗ FAILED: No access_token in response")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print(f"✗ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ FAILED: Exception occurred: {str(e)}")
            return False
    
    def test_2_create_company(self) -> bool:
        """Test 2: POST /api/companies - create a test company"""
        print("\n" + "="*80)
        print("TEST 2: Create a test company")
        print("="*80)
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/companies",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": "Arctic Innovations Oy",
                    "industry": "Industrial Automation & Robotics",
                    "company_size": "Mid-market",
                    "active_products": "25 active products",
                    "primary_challenge": "Portfolio complexity and resource allocation"
                },
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.company_id = data.get("id")
                if self.company_id:
                    print(f"✓ PASSED: Company created successfully")
                    print(f"Company ID: {self.company_id}")
                    print(f"Company Name: {data.get('name')}")
                    return True
                else:
                    print(f"✗ FAILED: No company ID in response")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print(f"✗ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ FAILED: Exception occurred: {str(e)}")
            return False
    
    def test_3_create_assessment(self) -> bool:
        """Test 3: POST /api/assessments - create an assessment"""
        print("\n" + "="*80)
        print("TEST 3: Create an assessment")
        print("="*80)
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/assessments",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "company_id": self.company_id,
                    "respondent_name": "Antti Korhonen",
                    "respondent_role": "Chief Product Officer"
                },
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.assessment_id = data.get("id")
                if self.assessment_id:
                    print(f"✓ PASSED: Assessment created successfully")
                    print(f"Assessment ID: {self.assessment_id}")
                    print(f"Respondent: {data.get('respondent_name')} ({data.get('respondent_role')})")
                    return True
                else:
                    print(f"✗ FAILED: No assessment ID in response")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print(f"✗ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ FAILED: Exception occurred: {str(e)}")
            return False
    
    def test_4_start_assessment(self) -> bool:
        """Test 4: POST /api/assessments/{id}/start - CRITICAL CHECK for AI greeting"""
        print("\n" + "="*80)
        print("TEST 4: Start assessment (CRITICAL CHECK - AI greeting via LLM)")
        print("="*80)
        print("This test verifies the LLM integration using ANTHROPIC_API_KEY")
        print("Expected: HTTP 200 with non-empty AI-generated greeting message")
        print("Must NOT return HTTP 500")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BACKEND_URL}/assessments/{self.assessment_id}/start",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            elapsed = time.time() - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {elapsed:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                
                if content and len(content) > 0:
                    print(f"✓ PASSED: AI greeting received successfully")
                    print(f"Greeting length: {len(content)} characters")
                    print(f"Greeting preview: {content[:150]}...")
                    print(f"Full greeting: {content}")
                    return True
                else:
                    print(f"✗ FAILED: Empty greeting message")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print(f"✗ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                
                # Check backend logs for error details
                print("\n--- Checking backend logs for errors ---")
                import subprocess
                try:
                    log_output = subprocess.check_output(
                        ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    print(log_output)
                except Exception as log_err:
                    print(f"Could not read backend logs: {log_err}")
                
                return False
                
        except Exception as e:
            print(f"✗ FAILED: Exception occurred: {str(e)}")
            return False
    
    def test_5_chat_message(self) -> bool:
        """Test 5: POST /api/assessments/{id}/chat - send a simple reply message"""
        print("\n" + "="*80)
        print("TEST 5: Send chat message (language selection)")
        print("="*80)
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BACKEND_URL}/assessments/{self.assessment_id}/chat",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"message": "English"},
                timeout=30
            )
            elapsed = time.time() - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {elapsed:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                
                if content and len(content) > 0:
                    print(f"✓ PASSED: AI response received successfully")
                    print(f"Response length: {len(content)} characters")
                    print(f"Response preview: {content[:150]}...")
                    return True
                else:
                    print(f"✗ FAILED: Empty AI response")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print(f"✗ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                
                # Check backend logs for error details
                print("\n--- Checking backend logs for errors ---")
                import subprocess
                try:
                    log_output = subprocess.check_output(
                        ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    print(log_output)
                except Exception as log_err:
                    print(f"Could not read backend logs: {log_err}")
                
                return False
                
        except Exception as e:
            print(f"✗ FAILED: Exception occurred: {str(e)}")
            return False
    
    def test_6_regression_check(self) -> bool:
        """Test 6: GET /api/assessments - regression check"""
        print("\n" + "="*80)
        print("TEST 6: Regression check (GET /api/assessments)")
        print("="*80)
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/assessments",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✓ PASSED: Assessments list retrieved successfully")
                    print(f"Total assessments: {len(data)}")
                    
                    # Check if our new assessment is in the list
                    found = False
                    for assessment in data:
                        if assessment.get("id") == self.assessment_id:
                            found = True
                            print(f"✓ New assessment found in list (ID: {self.assessment_id})")
                            break
                    
                    if not found:
                        print(f"⚠ WARNING: New assessment not found in list")
                    
                    return True
                else:
                    print(f"✗ FAILED: Expected list, got {type(data)}")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print(f"✗ FAILED: Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ FAILED: Exception occurred: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print("AI ASSESSMENT START + CHAT FLOW TEST")
        print("Testing after environment reset recovery")
        print("="*80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        
        results = []
        
        # Test 1: Login
        test1_passed = self.test_1_login()
        results.append(("Test 1: Login", test1_passed))
        if not test1_passed:
            print("\n✗ STOPPING: Cannot proceed without authentication")
            self.print_summary(results)
            return False
        
        # Test 2: Create company
        test2_passed = self.test_2_create_company()
        results.append(("Test 2: Create Company", test2_passed))
        if not test2_passed:
            print("\n✗ STOPPING: Cannot proceed without company")
            self.print_summary(results)
            return False
        
        # Test 3: Create assessment
        test3_passed = self.test_3_create_assessment()
        results.append(("Test 3: Create Assessment", test3_passed))
        if not test3_passed:
            print("\n✗ STOPPING: Cannot proceed without assessment")
            self.print_summary(results)
            return False
        
        # Test 4: Start assessment (CRITICAL CHECK)
        test4_passed = self.test_4_start_assessment()
        results.append(("Test 4: Start Assessment (AI Greeting) - CRITICAL", test4_passed))
        if not test4_passed:
            print("\n✗ CRITICAL TEST FAILED: AI greeting not working")
            # Continue with remaining tests for completeness
        
        # Test 5: Chat message
        test5_passed = self.test_5_chat_message()
        results.append(("Test 5: Chat Message (AI Response)", test5_passed))
        
        # Test 6: Regression check
        test6_passed = self.test_6_regression_check()
        results.append(("Test 6: Regression Check (GET /assessments)", test6_passed))
        
        # Print summary
        self.print_summary(results)
        
        # Return overall success
        return all(passed for _, passed in results)
    
    def print_summary(self, results):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        passed_count = sum(1 for _, passed in results if passed)
        total_count = len(results)
        
        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")
        
        print("\n" + "-"*80)
        print(f"TOTAL: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            print("✓ ALL TESTS PASSED - AI assessment flow is working correctly")
        else:
            print("✗ SOME TESTS FAILED - See details above")
        
        print("="*80)


if __name__ == "__main__":
    tester = AIAssessmentTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
