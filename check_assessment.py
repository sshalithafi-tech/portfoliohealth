"""Quick script to check if the assessment report was generated."""
import requests
import json

BASE_URL = "https://premium-report-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"

# Assessment ID from the test run
ASSESSMENT_ID = "6a4517fb57a67e8071a4d766"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    timeout=30
)
token = response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get assessment
response = requests.get(
    f"{BASE_URL}/assessments/{ASSESSMENT_ID}",
    headers=headers,
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    report = data.get("report")
    
    if report:
        print("✓ Report exists!")
        print(f"  equal_weighted_score: {report.get('equal_weighted_score')}")
        print(f"  contextual_score: {report.get('contextual_score')}")
        print(f"  failure_pattern_name: {report.get('failure_pattern_name')}")
        print(f"  management_commitment: {report.get('management_commitment')}")
        
        # Check field completeness
        required_fields = [
            "scores", "equal_weighted_score", "contextual_score", "level_names",
            "dimension_summaries", "pillar_interpretations", "pillar_interpretation_short",
            "failure_pattern_name", "failure_pattern_narrative", "financial_consequence",
            "ninety_day_projection", "governance_observations", "governance_assessment",
            "governance_signal_summary", "management_commitment", "management_commitment_assessment",
            "assessment_reliability", "decision_vulnerability_ratings", "decision_vulnerability",
            "key_findings", "critical_gaps", "roadmap", "first_action",
            "benchmark_context", "consultant_note", "closing_statement"
        ]
        
        missing = [f for f in required_fields if f not in report or not report[f]]
        print(f"\n  Fields present: {len(required_fields) - len(missing)}/{len(required_fields)}")
        if missing:
            print(f"  Missing/empty: {missing}")
    else:
        print("✗ No report in assessment")
        print(f"  Status: {data.get('status')}")
        print(f"  Chat history length: {len(data.get('chat_history', []))}")
else:
    print(f"✗ Failed to get assessment: HTTP {response.status_code}")
