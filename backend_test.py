#!/usr/bin/env python3
"""
PPDT Capability Maturity Advisor - Backend API Testing
Tests all API endpoints for functionality and integration
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class PPDTAPITester:
    def __init__(self, base_url: str = "https://section-search.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.user_token = None
        self.admin_user = None
        self.test_company_id = None
        self.test_assessment_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method: str, endpoint: str, expected_status: int = 200, 
                    description: str = "", data: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Make HTTP request and validate response"""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}

            if not success:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response_data}"
            else:
                details = f"Status: {response.status_code}"
                
            return self.log_test(description or f"{method} {endpoint}", success, details), response_data

        except Exception as e:
            return self.log_test(description or f"{method} {endpoint}", False, f"Exception: {str(e)}"), {}

    def test_health_check(self) -> bool:
        """Test API health check"""
        success, data = self.make_request("GET", "/", 200, "API Health Check")
        if success and "PPDT" in str(data.get("message", "")):
            print(f"   API message: {data.get('message')}")
            return True
        return success

    def test_admin_login(self) -> bool:
        """Test admin login with provided credentials"""
        login_data = {
            "email": "admin@ppdt.com",
            "password": "Admin123!"
        }
        
        success, data = self.make_request("POST", "/auth/login", 200, "Admin Login", login_data)
        
        if success and "id" in data:
            self.admin_user = data
            # Extract cookies for session management
            print(f"   Admin user logged in: {data.get('name')} ({data.get('role')})")
            return True
        return False

    def test_user_registration(self) -> bool:
        """Test user registration flow"""
        timestamp = datetime.now().strftime("%H%M%S")
        register_data = {
            "email": f"test_{timestamp}@example.com",
            "password": "Test123!",
            "name": f"Test User {timestamp}"
        }
        
        success, data = self.make_request("POST", "/auth/register", 200, "User Registration", register_data)
        
        if success and "id" in data:
            print(f"   Registered user: {data.get('name')} ({data.get('email')})")
            return True
        return False

    def test_auth_me(self) -> bool:
        """Test getting current user info"""
        success, data = self.make_request("GET", "/auth/me", 200, "Get Current User")
        return success and "id" in data

    def test_dashboard_stats(self) -> bool:
        """Test dashboard statistics endpoint"""
        success, data = self.make_request("GET", "/dashboard/stats", 200, "Dashboard Stats")
        
        if success:
            required_fields = ["total_assessments", "completed_assessments", "total_companies"]
            has_all_fields = all(field in data for field in required_fields)
            return self.log_test("Dashboard Stats - Required Fields", has_all_fields, 
                               f"Fields: {list(data.keys())}")
        return False

    def test_create_company(self) -> bool:
        """Test creating a new company"""
        company_data = {
            "name": f"Test Company {datetime.now().strftime('%H%M%S')}",
            "industry": "Technology",
            "portfolio_size": "100-500 products",
            "primary_challenge": "Data integration and decision-making processes"
        }
        
        success, data = self.make_request("POST", "/companies", 200, "Create Company", company_data)
        
        if success and "id" in data:
            self.test_company_id = data["id"]
            print(f"   Created company: {data.get('name')} (ID: {self.test_company_id})")
            return True
        return False

    def test_get_companies(self) -> bool:
        """Test retrieving companies list"""
        success, data = self.make_request("GET", "/companies", 200, "Get Companies")
        
        if success and isinstance(data, list):
            print(f"   Found {len(data)} companies")
            return True
        return False

    def test_create_assessment(self) -> bool:
        """Test creating a new assessment"""
        if not self.test_company_id:
            return self.log_test("Create Assessment", False, "No test company available")
        
        assessment_data = {
            "company_id": self.test_company_id,
            "respondent_name": "John Smith",
            "respondent_role": "Product Manager"
        }
        
        success, data = self.make_request("POST", "/assessments", 200, "Create Assessment", assessment_data)
        
        if success and "id" in data:
            self.test_assessment_id = data["id"]
            print(f"   Created assessment: {data.get('respondent_name')} (ID: {self.test_assessment_id})")
            return True
        return False

    def test_get_assessments(self) -> bool:
        """Test retrieving assessments list"""
        success, data = self.make_request("GET", "/assessments", 200, "Get Assessments")
        
        if success and isinstance(data, list):
            print(f"   Found {len(data)} assessments")
            return True
        return False

    def test_start_assessment(self) -> bool:
        """Test starting an assessment (AI greeting)"""
        if not self.test_assessment_id:
            return self.log_test("Start Assessment", False, "No test assessment available")
        
        success, data = self.make_request("POST", f"/assessments/{self.test_assessment_id}/start", 
                                        200, "Start Assessment")
        
        if success and "message" in data:
            message = data["message"]
            if "content" in message and len(message["content"]) > 0:
                print(f"   AI greeting received: {message['content'][:100]}...")
                return True
        return False

    def test_chat_message(self) -> bool:
        """Test sending a chat message to assessment"""
        if not self.test_assessment_id:
            return self.log_test("Send Chat Message", False, "No test assessment available")
        
        chat_data = {
            "message": "Hello, I'm ready to begin the PPDT assessment for our company."
        }
        
        success, data = self.make_request("POST", f"/assessments/{self.test_assessment_id}/chat", 
                                        200, "Send Chat Message", chat_data)
        
        if success and "message" in data:
            message = data["message"]
            if "content" in message and len(message["content"]) > 0:
                print(f"   AI response received: {message['content'][:100]}...")
                return True
        return False

    def test_get_assessment_details(self) -> bool:
        """Test retrieving specific assessment details"""
        if not self.test_assessment_id:
            return self.log_test("Get Assessment Details", False, "No test assessment available")
        
        success, data = self.make_request("GET", f"/assessments/{self.test_assessment_id}", 
                                        200, "Get Assessment Details")
        
        if success and "id" in data:
            print(f"   Assessment status: {data.get('status')}, Chat history: {len(data.get('chat_history', []))} messages")
            return True
        return False

    def test_logout(self) -> bool:
        """Test user logout"""
        success, data = self.make_request("POST", "/auth/logout", 200, "User Logout")
        return success

    def run_comprehensive_test(self) -> int:
        """Run all tests in sequence"""
        print("🚀 Starting PPDT Capability Maturity Advisor API Tests")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API health check failed - stopping tests")
            return 1
        
        # Authentication tests
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return 1
        
        self.test_user_registration()
        self.test_auth_me()
        
        # Core functionality tests
        self.test_dashboard_stats()
        
        # Company management
        self.test_create_company()
        self.test_get_companies()
        
        # Assessment workflow
        self.test_create_assessment()
        self.test_get_assessments()
        self.test_start_assessment()
        self.test_chat_message()
        self.test_get_assessment_details()
        
        # Cleanup
        self.test_logout()
        
        # Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed")
            return 1

def main():
    """Main test execution"""
    tester = PPDTAPITester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())