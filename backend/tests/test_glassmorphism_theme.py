"""
Backend API tests for PortfolioHealth Advisor - Glassmorphism Theme Update
Tests authentication, dashboard, companies, assessments, and quick assessment APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print(f"✓ API root returns 200")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@ppdt.com", "password": "Admin123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == "admin@ppdt.com"
        print(f"✓ Login successful for admin@ppdt.com")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print(f"✓ Login correctly rejects invalid credentials")
    
    def test_auth_me_without_token(self):
        """Test /auth/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print(f"✓ /auth/me correctly returns 401 without auth")


class TestDashboard:
    """Dashboard API tests"""
    
    @pytest.fixture
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@ppdt.com", "password": "Admin123!"}
        )
        assert response.status_code == 200
        return session
    
    def test_dashboard_stats(self, auth_session):
        """Test dashboard stats endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_assessments" in data
        assert "completed_assessments" in data
        assert "total_companies" in data
        print(f"✓ Dashboard stats: {data['total_assessments']} assessments, {data['total_companies']} companies")


class TestCompanies:
    """Companies API tests"""
    
    @pytest.fixture
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@ppdt.com", "password": "Admin123!"}
        )
        assert response.status_code == 200
        return session
    
    def test_get_companies(self, auth_session):
        """Test get companies list"""
        response = auth_session.get(f"{BASE_URL}/api/companies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} companies")
    
    def test_create_company(self, auth_session):
        """Test create company"""
        response = auth_session.post(
            f"{BASE_URL}/api/companies",
            json={
                "name": "TEST_API_Company",
                "industry": "Technology",
                "portfolio_size": "50 products",
                "primary_challenge": "Data integration"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "TEST_API_Company"
        print(f"✓ Created company: {data['name']}")
        return data


class TestAssessments:
    """Assessments API tests"""
    
    @pytest.fixture
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@ppdt.com", "password": "Admin123!"}
        )
        assert response.status_code == 200
        return session
    
    def test_get_assessments(self, auth_session):
        """Test get assessments list"""
        response = auth_session.get(f"{BASE_URL}/api/assessments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} assessments")


class TestQuickAssessment:
    """Quick Assessment API tests"""
    
    def test_get_questions(self):
        """Test get quick assessment questions"""
        response = requests.get(f"{BASE_URL}/api/quick-assessment/questions")
        assert response.status_code == 200
        data = response.json()
        # API returns {"questions": [...], "total": 15}
        assert "questions" in data
        assert "total" in data
        assert data["total"] == 15  # Should have 15 questions
        print(f"✓ Got {data['total']} quick assessment questions")
    
    def test_submit_quick_assessment(self):
        """Test submit quick assessment"""
        # First get questions to know the IDs
        questions_response = requests.get(f"{BASE_URL}/api/quick-assessment/questions")
        questions_data = questions_response.json()
        questions = questions_data["questions"]
        
        # Create answers for all questions (select first option value)
        answers = {}
        for q in questions:
            answers[str(q["id"])] = q["options"][0]["value"]
        
        response = requests.post(
            f"{BASE_URL}/api/quick-assessment/submit",
            json={
                "company_name": "TEST_Quick_Company",
                "industry": "Technology",
                "respondent_name": "Test User",
                "respondent_email": "test@example.com",
                "answers": answers
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert "scores" in data
        assert "overall" in data["scores"]
        print(f"✓ Quick assessment submitted, overall score: {data['scores']['overall']}")
    
    def test_get_quick_assessment_result(self):
        """Test get quick assessment result"""
        # First submit an assessment
        questions_response = requests.get(f"{BASE_URL}/api/quick-assessment/questions")
        questions_data = questions_response.json()
        questions = questions_data["questions"]
        
        answers = {}
        for q in questions:
            answers[str(q["id"])] = q["options"][0]["value"]
        
        submit_response = requests.post(
            f"{BASE_URL}/api/quick-assessment/submit",
            json={
                "company_name": "TEST_Result_Company",
                "industry": "Manufacturing",
                "answers": answers
            }
        )
        assessment_id = submit_response.json()["id"]
        
        # Get the result
        response = requests.get(f"{BASE_URL}/api/quick-assessment/{assessment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "TEST_Result_Company"
        print(f"✓ Retrieved quick assessment result for {data['company_name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
