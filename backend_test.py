#!/usr/bin/env python3
"""
Backend API Test Suite for PortfolioHealth Advisor
Tests the complete AI assessment flow end-to-end
"""

import requests
import json
import sys
from datetime import datetime

# Base URL from frontend/.env
BASE_URL = "https://f0f12400-45cd-4941-b54c-279e9345466b.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def log_error(message):
    print(f"{RED}✗ {message}{RESET}")

def log_info(message):
    print(f"{BLUE}ℹ {message}{RESET}")

def log_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")

class TestSession:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.company_id = None
        self.assessment_id = None
        self.errors = []
        self.warnings = []

    def test_login(self):
        """Test 1: Login with admin credentials"""
        log_info("Test 1: POST /api/auth/login")
        
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                
                if self.token and self.user_id:
                    log_success(f"Login successful. User ID: {self.user_id}")
                    log_info(f"Token received: {self.token[:20]}...")
                    return True
                else:
                    log_error("Login response missing token or user_id")
                    self.errors.append("Login: Missing token or user_id in response")
                    return False
            else:
                log_error(f"Login failed with status {response.status_code}")
                log_error(f"Response: {response.text}")
                self.errors.append(f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Login request failed: {str(e)}")
            self.errors.append(f"Login exception: {str(e)}")
            return False

    def test_create_company(self):
        """Test 2: Create a company"""
        log_info("Test 2: POST /api/companies")
        
        if not self.token:
            log_error("Skipping - no auth token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.post(
                f"{BASE_URL}/companies",
                json={
                    "name": "Nordic Manufacturing Solutions",
                    "industry": "Industrial Manufacturing",
                    "portfolio_size": "Large portfolio",
                    "company_size": "Mid-market · 450 employees",
                    "active_products": "28 active SKUs",
                    "primary_challenge": "Portfolio complexity and profitability visibility"
                },
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.company_id = data.get("id")
                
                if self.company_id:
                    log_success(f"Company created. ID: {self.company_id}")
                    log_info(f"Company name: {data.get('name')}")
                    return True
                else:
                    log_error("Company response missing ID")
                    self.errors.append("Create company: Missing ID in response")
                    return False
            else:
                log_error(f"Create company failed with status {response.status_code}")
                log_error(f"Response: {response.text}")
                self.errors.append(f"Create company failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Create company request failed: {str(e)}")
            self.errors.append(f"Create company exception: {str(e)}")
            return False

    def test_create_assessment(self):
        """Test 3: Create an assessment"""
        log_info("Test 3: POST /api/assessments")
        
        if not self.token or not self.company_id:
            log_error("Skipping - missing token or company_id")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.post(
                f"{BASE_URL}/assessments",
                json={
                    "company_id": self.company_id,
                    "respondent_name": "Maria Virtanen",
                    "respondent_role": "Head of Product Portfolio"
                },
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.assessment_id = data.get("id")
                
                if self.assessment_id:
                    log_success(f"Assessment created. ID: {self.assessment_id}")
                    log_info(f"Respondent: {data.get('respondent_name')} ({data.get('respondent_role')})")
                    log_info(f"Status: {data.get('status')}")
                    return True
                else:
                    log_error("Assessment response missing ID")
                    self.errors.append("Create assessment: Missing ID in response")
                    return False
            else:
                log_error(f"Create assessment failed with status {response.status_code}")
                log_error(f"Response: {response.text}")
                self.errors.append(f"Create assessment failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Create assessment request failed: {str(e)}")
            self.errors.append(f"Create assessment exception: {str(e)}")
            return False

    def test_start_assessment(self):
        """Test 4: CRITICAL - Start assessment (triggers LLM greeting)"""
        log_info("Test 4: POST /api/assessments/{assessment_id}/start (CRITICAL - LLM greeting)")
        
        if not self.token or not self.assessment_id:
            log_error("Skipping - missing token or assessment_id")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.post(
                f"{BASE_URL}/assessments/{self.assessment_id}/start",
                headers=headers,
                timeout=30  # LLM call may take longer
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                
                if content and len(content) > 0:
                    log_success("AI assessment started successfully!")
                    log_info(f"AI greeting received ({len(content)} characters)")
                    log_info(f"First 200 chars: {content[:200]}...")
                    
                    # Check if it's the expected multilingual greeting
                    if "Welcome" in content or "Tervetuloa" in content or "Välkommen" in content:
                        log_success("AI greeting contains expected multilingual welcome")
                    else:
                        log_warning("AI greeting doesn't contain expected welcome message")
                        self.warnings.append("Start assessment: Unexpected greeting format")
                    
                    return True
                else:
                    log_error("AI greeting is empty!")
                    self.errors.append("Start assessment: Empty AI greeting content")
                    return False
            elif response.status_code == 500:
                log_error("CRITICAL: Assessment start returned 500 - Failed to start assessment")
                log_error(f"Response: {response.text}")
                self.errors.append(f"Start assessment FAILED: 500 - {response.text}")
                return False
            else:
                log_error(f"Start assessment failed with status {response.status_code}")
                log_error(f"Response: {response.text}")
                self.errors.append(f"Start assessment failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Start assessment request failed: {str(e)}")
            self.errors.append(f"Start assessment exception: {str(e)}")
            return False

    def test_chat_message(self):
        """Test 5: Send a chat message and verify AI responds"""
        log_info("Test 5: POST /api/assessments/{assessment_id}/chat")
        
        if not self.token or not self.assessment_id:
            log_error("Skipping - no token or assessment_id")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.post(
                f"{BASE_URL}/assessments/{self.assessment_id}/chat",
                json={
                    "message": "English"
                },
                headers=headers,
                timeout=30  # LLM call may take longer
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                
                if content and len(content) > 0:
                    log_success("AI responded to chat message!")
                    log_info(f"AI response received ({len(content)} characters)")
                    log_info(f"First 200 chars: {content[:200]}...")
                    
                    # Check if report is ready (shouldn't be after just one message)
                    report_ready = data.get("report_ready", False)
                    if report_ready:
                        log_warning("Report marked as ready after only one message (unexpected)")
                        self.warnings.append("Chat: Report ready too early")
                    
                    return True
                else:
                    log_error("AI response is empty!")
                    self.errors.append("Chat: Empty AI response content")
                    return False
            else:
                log_error(f"Chat message failed with status {response.status_code}")
                log_error(f"Response: {response.text}")
                self.errors.append(f"Chat failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Chat message request failed: {str(e)}")
            self.errors.append(f"Chat exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print("PortfolioHealth Advisor - Backend API Test Suite")
        print("Testing AI Assessment Flow End-to-End")
        print("="*80 + "\n")
        
        results = {
            "Login": self.test_login(),
            "Create Company": self.test_create_company(),
            "Create Assessment": self.test_create_assessment(),
            "Start Assessment (LLM)": self.test_start_assessment(),
            "Chat Message (LLM)": self.test_chat_message()
        }
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
            print(f"{test_name:30} {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if self.errors:
            print(f"\n{RED}CRITICAL ERRORS:{RESET}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n{YELLOW}WARNINGS:{RESET}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print("\n" + "="*80 + "\n")
        
        return passed == total

def main():
    test_session = TestSession()
    success = test_session.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
