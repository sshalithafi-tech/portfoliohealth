#!/usr/bin/env python3
"""
PPDT Quick Assessment API Testing
Tests all Quick Assessment endpoints for functionality and integration
"""

import requests
import sys
import json
from datetime import datetime

class QuickAssessmentTester:
    def __init__(self, base_url="https://ai-assessment-check.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.quick_assessment_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, expected_status=200, data=None, description=""):
        """Make HTTP request and validate response"""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"   Request failed: {response.status_code} - {response.text}")
                return False, {}

        except Exception as e:
            print(f"   Exception: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login for authenticated endpoints"""
        success, data = self.make_request('POST', 'auth/login', data={
            "email": "admin@ppdt.com",
            "password": "Admin123!"
        }, description="Admin login")
        
        if success and isinstance(data, dict) and 'id' in data:
            return self.log_test("Admin Login", True, f"Logged in as {data.get('name', 'Unknown')}")
        return self.log_test("Admin Login", False, "Login failed")

    def test_quick_assessment_questions(self):
        """Test getting quick assessment questions (no auth required)"""
        success, data = self.make_request('GET', 'quick-assessment/questions', description="Quick assessment questions")
        
        if success and isinstance(data, dict):
            questions = data.get('questions', [])
            total = data.get('total', 0)
            
            if len(questions) == 15 and total == 15:
                # Verify question structure
                sample_q = questions[0] if questions else {}
                required_fields = ['id', 'dimension', 'question', 'options']
                missing = [f for f in required_fields if f not in sample_q]
                
                if not missing:
                    return self.log_test("Quick Assessment Questions", True, f"Found {len(questions)} well-structured questions")
                else:
                    return self.log_test("Quick Assessment Questions", False, f"Question missing fields: {missing}")
            else:
                return self.log_test("Quick Assessment Questions", False, f"Expected 15 questions, got {len(questions)}")
        
        return self.log_test("Quick Assessment Questions", False, "Request failed or invalid response")

    def test_quick_assessment_submit(self):
        """Test submitting quick assessment (no auth required)"""
        # Sample answers for all 15 questions (realistic scores)
        sample_answers = {
            "1": 3,  # Portfolio size
            "2": 4,  # Decision making
            "3": 3,  # Roles defined
            "4": 3,  # Data literacy
            "5": 4,  # PPM governance
            "6": 3,  # Product classification
            "7": 3,  # End-of-life process
            "8": 3,  # Product profitability
            "9": 3,  # Master data
            "10": 3, # IT systems
            "11": 3, # Data model
            "12": 3, # System integration
            "13": 3, # Dashboard access
            "14": 3, # Manual effort
            "15": 3  # IT architecture
        }
        
        test_data = {
            "company_name": "Test Company Ltd",
            "industry": "Technology",
            "respondent_name": "John Tester",
            "respondent_email": "john@testcompany.com",
            "answers": sample_answers
        }
        
        success, data = self.make_request('POST', 'quick-assessment/submit', data=test_data, description="Submit quick assessment")
        
        if success and isinstance(data, dict):
            required_fields = ['id', 'company_name', 'scores', 'traffic_lights', 'level_names', 'cta_message']
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                return self.log_test("Quick Assessment Submit", False, f"Missing fields: {missing}")
            
            self.quick_assessment_id = data.get('id')
            scores = data.get('scores', {})
            traffic_lights = data.get('traffic_lights', {})
            overall_score = scores.get('overall', 0)
            
            # Verify score structure
            expected_dimensions = ['people', 'process', 'data', 'technology', 'overall']
            score_dims = list(scores.keys())
            traffic_dims = list(traffic_lights.keys())
            
            if all(dim in score_dims for dim in expected_dimensions) and all(dim in traffic_dims for dim in expected_dimensions):
                return self.log_test("Quick Assessment Submit", True, f"ID: {self.quick_assessment_id}, Overall: {overall_score}")
            else:
                return self.log_test("Quick Assessment Submit", False, f"Missing score dimensions. Got: {score_dims}")
        
        return self.log_test("Quick Assessment Submit", False, "Request failed or invalid response")

    def test_get_quick_assessment(self):
        """Test getting quick assessment by ID (no auth required)"""
        if not self.quick_assessment_id:
            return self.log_test("Get Quick Assessment", False, "No quick assessment ID available")
            
        success, data = self.make_request('GET', f'quick-assessment/{self.quick_assessment_id}', description="Get quick assessment")
        
        if success and isinstance(data, dict):
            company_name = data.get('company_name', 'N/A')
            industry = data.get('industry', 'N/A')
            scores = data.get('scores', {})
            
            if company_name != 'N/A' and industry != 'N/A' and scores:
                return self.log_test("Get Quick Assessment", True, f"Company: {company_name}, Industry: {industry}")
            else:
                return self.log_test("Get Quick Assessment", False, "Missing or invalid data")
        
        return self.log_test("Get Quick Assessment", False, "Request failed")

    def test_quick_assessment_pdf(self):
        """Test PDF generation for quick assessment (no auth required)"""
        if not self.quick_assessment_id:
            return self.log_test("Quick Assessment PDF", False, "No quick assessment ID available")
            
        url = f"{self.base_url}/api/quick-assessment/{self.quick_assessment_id}/pdf"
        
        try:
            response = self.session.get(url)
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('content-type', '')
                is_pdf = response.content.startswith(b'%PDF') if response.content else False
                
                if is_pdf and 'pdf' in content_type.lower():
                    return self.log_test("Quick Assessment PDF", True, f"Valid PDF generated ({len(response.content)} bytes)")
                else:
                    return self.log_test("Quick Assessment PDF", False, f"Invalid PDF. Content-Type: {content_type}, Starts with PDF: {is_pdf}")
            else:
                return self.log_test("Quick Assessment PDF", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.log_test("Quick Assessment PDF", False, f"Exception: {str(e)}")

    def test_save_quick_assessment(self):
        """Test saving quick assessment to user account (auth required)"""
        if not self.quick_assessment_id:
            return self.log_test("Save Quick Assessment", False, "No quick assessment ID available")
            
        success, data = self.make_request('POST', f'quick-assessment/{self.quick_assessment_id}/save', description="Save quick assessment")
        
        if success and isinstance(data, dict):
            message = data.get('message', '')
            assessment_id = data.get('id', '')
            
            if 'saved' in message.lower() and assessment_id:
                return self.log_test("Save Quick Assessment", True, f"Saved with ID: {assessment_id}")
            else:
                return self.log_test("Save Quick Assessment", False, f"Unexpected response: {data}")
        
        return self.log_test("Save Quick Assessment", False, "Request failed")

    def test_get_user_quick_assessments(self):
        """Test getting user's quick assessments (auth required)"""
        success, data = self.make_request('GET', 'quick-assessments', description="Get user quick assessments")
        
        if success and isinstance(data, list):
            count = len(data)
            
            if count > 0:
                latest = data[0]
                company = latest.get('company_name', 'N/A')
                scores = latest.get('scores', {})
                overall = scores.get('overall', 0) if scores else 0
                
                return self.log_test("Get User Quick Assessments", True, f"Found {count} assessments, latest: {company} (score: {overall})")
            else:
                return self.log_test("Get User Quick Assessments", True, "No quick assessments found (expected after save)")
        
        return self.log_test("Get User Quick Assessments", False, "Request failed or invalid response")

    def test_dashboard_stats_with_quick(self):
        """Test dashboard stats includes quick assessments"""
        success, data = self.make_request('GET', 'dashboard/stats', description="Dashboard stats")
        
        if success and isinstance(data, dict):
            quick_count = data.get('total_quick_assessments', 0)
            total_assessments = data.get('total_assessments', 0)
            
            return self.log_test("Dashboard Stats (Quick)", True, f"Quick assessments: {quick_count}, Total: {total_assessments}")
        
        return self.log_test("Dashboard Stats (Quick)", False, "Request failed")

    def run_comprehensive_test(self):
        """Run all Quick Assessment tests"""
        print("🚀 Starting PPDT Quick Assessment API Tests")
        print("=" * 60)
        
        # Test sequence
        tests = [
            # Public endpoints (no auth required)
            ("Quick Assessment Questions", self.test_quick_assessment_questions),
            ("Submit Quick Assessment", self.test_quick_assessment_submit),
            ("Get Quick Assessment", self.test_get_quick_assessment),
            ("Generate PDF", self.test_quick_assessment_pdf),
            
            # Auth required endpoints
            ("Admin Login", self.test_admin_login),
            ("Save to Account", self.test_save_quick_assessment),
            ("Get User Quick Assessments", self.test_get_user_quick_assessments),
            ("Dashboard Stats", self.test_dashboard_stats_with_quick),
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")

        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Quick Assessment tests passed!")
            return 0
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed")
            return 1

def main():
    """Main test execution"""
    tester = QuickAssessmentTester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())