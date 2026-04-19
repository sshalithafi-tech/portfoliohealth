"""
PortfolioHealth Advisor - Comprehensive Backend API Tests
Tests: Auth (Bearer token), Companies CRUD with Delete, Assessments, Notifications, Admin endpoints, PDF generation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@ppdt.com"
ADMIN_PASSWORD = "Admin123!"
TEST_USER_EMAIL = f"test_user_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "Test123!"
TEST_USER_NAME = "Test User"


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "PortfolioHealth" in data["message"]
        print("✓ API health check passed")


class TestAuthentication:
    """Authentication endpoint tests - Bearer token based"""
    
    def test_login_admin_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify Bearer token is returned
        assert "access_token" in data, "access_token not in response"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        
        # Verify user data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful, token received: {data['access_token'][:20]}...")
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
        
    def test_register_new_user(self):
        """Test registering a new user"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Verify token returned
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL.lower()
        assert data["user"]["role"] == "consultant"
        print(f"✓ New user registered: {TEST_USER_EMAIL}")
        
    def test_register_duplicate_email(self):
        """Test registering with existing email fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "somepassword",
            "name": "Duplicate"
        })
        assert response.status_code == 400
        print("✓ Duplicate email registration correctly rejected")
        
    def test_auth_me_with_bearer_token(self):
        """Test /auth/me endpoint with Bearer token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Use token to get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print("✓ Bearer token authentication working correctly")
        
    def test_auth_me_without_token(self):
        """Test /auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Unauthenticated request correctly rejected")


class TestCompanies:
    """Companies CRUD tests including Delete functionality"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers with Bearer token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_company(self, auth_headers):
        """Test creating a new company"""
        company_data = {
            "name": f"TEST_Company_{int(time.time())}",
            "industry": "Technology",
            "portfolio_size": "100 products",
            "primary_challenge": "Data integration"
        }
        response = requests.post(
            f"{BASE_URL}/api/companies",
            json=company_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create company failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["name"] == company_data["name"]
        assert data["industry"] == company_data["industry"]
        print(f"✓ Company created: {data['name']} (ID: {data['id']})")
        return data
        
    def test_get_companies_with_assessment_counts(self, auth_headers):
        """Test getting companies list with assessment_count, completed_count, latest_score"""
        response = requests.get(
            f"{BASE_URL}/api/companies",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            company = data[0]
            # Verify new fields are present
            assert "assessment_count" in company
            assert "completed_count" in company
            assert "latest_score" in company or company.get("latest_score") is None
            print(f"✓ Companies list retrieved with assessment counts: {len(data)} companies")
        else:
            print("✓ Companies list retrieved (empty)")
            
    def test_delete_company(self, auth_headers):
        """Test deleting a company and its assessments"""
        # First create a company to delete
        company_data = {
            "name": f"TEST_ToDelete_{int(time.time())}",
            "industry": "Manufacturing",
            "portfolio_size": "50 products"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/companies",
            json=company_data,
            headers=auth_headers
        )
        company_id = create_response.json()["id"]
        
        # Delete the company
        delete_response = requests.delete(
            f"{BASE_URL}/api/companies/{company_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        data = delete_response.json()
        assert data["ok"] == True
        print(f"✓ Company deleted successfully: {company_id}")
        
        # Verify company no longer exists
        get_response = requests.get(
            f"{BASE_URL}/api/companies/{company_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
        print("✓ Deleted company correctly returns 404")
        
    def test_delete_nonexistent_company(self, auth_headers):
        """Test deleting a non-existent company returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/companies/000000000000000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Delete non-existent company correctly returns 404")


class TestAssessments:
    """Assessment CRUD and chat tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers with Bearer token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def test_company(self, auth_headers):
        """Create a test company for assessments"""
        company_data = {
            "name": f"TEST_AssessmentCompany_{int(time.time())}",
            "industry": "Healthcare"
        }
        response = requests.post(
            f"{BASE_URL}/api/companies",
            json=company_data,
            headers=auth_headers
        )
        return response.json()
    
    def test_create_assessment(self, auth_headers, test_company):
        """Test creating a new assessment"""
        assessment_data = {
            "company_id": test_company["id"],
            "respondent_name": "Test Respondent",
            "respondent_role": "CTO"
        }
        response = requests.post(
            f"{BASE_URL}/api/assessments",
            json=assessment_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create assessment failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["company_id"] == test_company["id"]
        assert data["status"] == "in_progress"
        print(f"✓ Assessment created: {data['id']}")
        return data
        
    def test_get_assessments(self, auth_headers):
        """Test getting assessments list"""
        response = requests.get(
            f"{BASE_URL}/api/assessments",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Assessments list retrieved: {len(data)} assessments")
        
    def test_start_assessment(self, auth_headers, test_company):
        """Test starting an assessment (get AI greeting)"""
        # Create assessment first
        assessment_data = {
            "company_id": test_company["id"],
            "respondent_name": "Test Starter",
            "respondent_role": "CEO"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/assessments",
            json=assessment_data,
            headers=auth_headers
        )
        assessment_id = create_response.json()["id"]
        
        # Start the assessment
        start_response = requests.post(
            f"{BASE_URL}/api/assessments/{assessment_id}/start",
            headers=auth_headers
        )
        assert start_response.status_code == 200, f"Start assessment failed: {start_response.text}"
        data = start_response.json()
        
        assert "message" in data
        assert data["message"]["role"] == "assistant"
        assert len(data["message"]["content"]) > 0
        print(f"✓ Assessment started, AI greeting received: {data['message']['content'][:100]}...")


class TestNotifications:
    """Notification endpoints tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers with Bearer token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_notifications(self, auth_headers):
        """Test getting notifications list"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Notifications retrieved: {len(data)} notifications")
        
    def test_get_unread_count(self, auth_headers):
        """Test getting unread notification count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        print(f"✓ Unread count: {data['count']}")
        
    def test_mark_all_read(self, auth_headers):
        """Test marking all notifications as read"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/read-all",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] == True
        print("✓ Mark all read successful")


class TestAdminEndpoints:
    """Admin-only endpoint tests"""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_admin_get_all_assessments(self, admin_headers):
        """Test admin endpoint to get all assessments"""
        response = requests.get(
            f"{BASE_URL}/api/admin/assessments",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin: All assessments retrieved: {len(data)}")
        
    def test_admin_get_all_quick_assessments(self, admin_headers):
        """Test admin endpoint to get all quick assessments"""
        response = requests.get(
            f"{BASE_URL}/api/admin/quick-assessments",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin: All quick assessments retrieved: {len(data)}")
        
    def test_admin_get_stats(self, admin_headers):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_assessments" in data
        assert "total_users" in data
        print(f"✓ Admin stats: {data['total_assessments']} assessments, {data['total_users']} users")
        
    def test_admin_export_csv(self, admin_headers):
        """Test admin CSV export endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/export/assessments",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✓ Admin CSV export working")


class TestQuickAssessment:
    """Quick assessment tests (no auth required)"""
    
    def test_get_questions(self):
        """Test getting quick assessment questions"""
        response = requests.get(f"{BASE_URL}/api/quick-assessment/questions")
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 15
        print(f"✓ Quick assessment questions retrieved: {len(data['questions'])} questions")
        
    def test_submit_quick_assessment(self):
        """Test submitting a quick assessment"""
        # Create answers for all 15 questions
        answers = {str(i): 3 for i in range(1, 16)}
        
        submit_data = {
            "company_name": f"TEST_QuickCompany_{int(time.time())}",
            "industry": "Technology",
            "respondent_name": "Quick Tester",
            "respondent_email": "quick@test.com",
            "answers": answers
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quick-assessment/submit",
            json=submit_data
        )
        assert response.status_code == 200, f"Submit failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "scores" in data
        assert "traffic_lights" in data
        assert "level_names" in data
        assert "cta_message" in data
        print(f"✓ Quick assessment submitted, overall score: {data['scores']['overall']}")
        return data
        
    def test_quick_assessment_pdf(self):
        """Test quick assessment PDF generation"""
        # First submit a quick assessment
        answers = {str(i): 3 for i in range(1, 16)}
        submit_data = {
            "company_name": f"TEST_PDFCompany_{int(time.time())}",
            "industry": "Manufacturing",
            "answers": answers
        }
        submit_response = requests.post(
            f"{BASE_URL}/api/quick-assessment/submit",
            json=submit_data
        )
        quick_id = submit_response.json()["id"]
        
        # Get PDF
        pdf_response = requests.get(f"{BASE_URL}/api/quick-assessment/{quick_id}/pdf")
        assert pdf_response.status_code == 200, f"PDF generation failed: {pdf_response.text}"
        assert "application/pdf" in pdf_response.headers.get("content-type", "")
        assert len(pdf_response.content) > 1000  # PDF should have some content
        print(f"✓ Quick assessment PDF generated: {len(pdf_response.content)} bytes")


class TestDashboard:
    """Dashboard stats tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers with Bearer token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_dashboard_stats(self, auth_headers):
        """Test dashboard stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_assessments" in data
        assert "completed_assessments" in data
        assert "total_companies" in data
        assert "average_scores" in data
        print(f"✓ Dashboard stats: {data['total_assessments']} assessments, {data['total_companies']} companies")


# Cleanup test data
class TestCleanup:
    """Cleanup test-created data"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers with Bearer token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_cleanup_test_companies(self, auth_headers):
        """Delete all TEST_ prefixed companies"""
        response = requests.get(
            f"{BASE_URL}/api/companies",
            headers=auth_headers
        )
        companies = response.json()
        
        deleted = 0
        for company in companies:
            if company["name"].startswith("TEST_"):
                delete_response = requests.delete(
                    f"{BASE_URL}/api/companies/{company['id']}",
                    headers=auth_headers
                )
                if delete_response.status_code == 200:
                    deleted += 1
        
        print(f"✓ Cleanup: Deleted {deleted} test companies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
