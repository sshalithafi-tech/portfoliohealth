"""Detailed report inspection script."""
import requests
import json
import re

BASE_URL = "https://premium-report-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"
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

data = response.json()
report = data.get("report", {})

print("="*80)
print("REPORT FIELD COMPLETENESS CHECK")
print("="*80)

# All required fields
required_fields = {
    "scores": dict,
    "equal_weighted_score": (int, float),
    "contextual_score": (int, float),
    "level_names": dict,
    "dimension_summaries": dict,
    "pillar_interpretations": dict,
    "pillar_interpretation_short": dict,
    "failure_pattern_name": str,
    "failure_pattern_narrative": str,
    "financial_consequence": dict,
    "ninety_day_projection": dict,
    "governance_observations": dict,
    "governance_assessment": str,
    "governance_signal_summary": list,
    "management_commitment": str,
    "management_commitment_assessment": str,
    "assessment_reliability": dict,
    "decision_vulnerability_ratings": dict,
    "decision_vulnerability": str,
    "key_findings": list,
    "critical_gaps": list,
    "roadmap": dict,
    "first_action": dict,
    "benchmark_context": str,
    "consultant_note": str,
    "closing_statement": str,
}

missing = []
empty = []
present = []

for field, expected_type in required_fields.items():
    if field not in report:
        missing.append(field)
    else:
        value = report[field]
        if value is None or value == "" or value == [] or value == {}:
            empty.append(field)
        elif expected_type == (int, float) and value == 0 and field == "contextual_score":
            # contextual_score of 0 is suspicious
            empty.append(field)
        else:
            present.append(field)

print(f"\n✓ PRESENT AND NON-EMPTY: {len(present)}/{len(required_fields)}")
for f in present:
    value = report[f]
    if isinstance(value, str):
        print(f"  {f}: {len(value)} chars")
    elif isinstance(value, list):
        print(f"  {f}: {len(value)} items")
    elif isinstance(value, dict):
        print(f"  {f}: {len(value)} keys")
    else:
        print(f"  {f}: {value}")

if missing:
    print(f"\n✗ MISSING: {len(missing)}")
    for f in missing:
        print(f"  - {f}")

if empty:
    print(f"\n⚠ EMPTY: {len(empty)}")
    for f in empty:
        print(f"  - {f}")

# Check specific fields
print("\n" + "="*80)
print("KEY FIELD VALUES")
print("="*80)

scores = report.get("scores", {})
print(f"\nScores:")
print(f"  people: {scores.get('people')}")
print(f"  process: {scores.get('process')}")
print(f"  data: {scores.get('data')}")
print(f"  technology: {scores.get('technology')}")
print(f"  overall: {scores.get('overall')}")

print(f"\nDual Scores:")
print(f"  equal_weighted_score: {report.get('equal_weighted_score')}")
print(f"  contextual_score: {report.get('contextual_score')}")

print(f"\nFailure Pattern:")
print(f"  name: {report.get('failure_pattern_name')}")
narrative = report.get('failure_pattern_narrative', '')
if narrative:
    sentences = re.split(r'[.!?]+', narrative)
    print(f"  narrative: {len(sentences)} sentences, {len(narrative)} chars")
else:
    print(f"  narrative: EMPTY")

print(f"\nGovernance:")
print(f"  assessment: {len(report.get('governance_assessment', ''))} chars")
print(f"  signal_summary: {len(report.get('governance_signal_summary', []))} items")

print(f"\nManagement:")
print(f"  commitment: {report.get('management_commitment')}")
print(f"  assessment: {len(report.get('management_commitment_assessment', ''))} chars")

print(f"\nKey Findings & Gaps:")
print(f"  key_findings: {len(report.get('key_findings', []))} items")
critical_gaps = report.get('critical_gaps', [])
print(f"  critical_gaps: {len(critical_gaps)} items")
if critical_gaps:
    with_labels = [g for g in critical_gaps if 'Precondition' in str(g)]
    print(f"    with Precondition labels: {len(with_labels)}/{len(critical_gaps)}")

print(f"\nRoadmap:")
roadmap = report.get('roadmap', {})
for phase in ['immediate', 'short_term', 'strategic']:
    phase_data = roadmap.get(phase, {})
    expected_gain = phase_data.get('expected_gain', '')
    print(f"  {phase}:")
    print(f"    expected_gain: {expected_gain}")
    print(f"    action_summary: {len(phase_data.get('action_summary', ''))} chars")

print(f"\nConsultant Note:")
consultant_note = report.get('consultant_note', '')
if consultant_note:
    word_count = len(consultant_note.split())
    print(f"  {len(consultant_note)} chars, ~{word_count} words")
    if word_count > 250:
        print(f"  ⚠ EXCEEDS 250-word cap")
else:
    print(f"  EMPTY")

print(f"\nBenchmark Context:")
benchmark = report.get('benchmark_context', '')
print(f"  {len(benchmark)} chars")

# Check roadmap continuity
print("\n" + "="*80)
print("ROADMAP CONTINUITY CHECK")
print("="*80)

immediate = roadmap.get('immediate', {})
expected_gain = immediate.get('expected_gain', '')
if expected_gain:
    pattern = r"(People|Process|Data|Technology):\s*([\d.]+)\s*[→\-]\s*([\d.]+)"
    matches = re.findall(pattern, expected_gain)
    
    if len(matches) == 4:
        print("\n✓ All 4 pillars found in expected_gain")
        mismatches = []
        for pillar_name, start_str, end_str in matches:
            pillar_key = pillar_name.lower()
            start_value = float(start_str)
            score_value = float(scores.get(pillar_key, 0))
            
            if abs(start_value - score_value) > 0.01:
                mismatches.append(f"{pillar_name}: starts at {start_value} but score is {score_value}")
            else:
                print(f"  {pillar_name}: {start_value} → {end_str} (matches score {score_value})")
        
        if mismatches:
            print(f"\n✗ CONTINUITY ERRORS:")
            for m in mismatches:
                print(f"  - {m}")
        else:
            print(f"\n✓ CONTINUITY VERIFIED: All starting values match pillar scores")
    else:
        print(f"\n✗ Expected 4 pillars, found {len(matches)}")
else:
    print("\n✗ expected_gain is empty")

# Test PDFs
print("\n" + "="*80)
print("PDF GENERATION TEST")
print("="*80)

response = requests.get(f"{BASE_URL}/assessments/{ASSESSMENT_ID}/pdf", headers=headers, timeout=60)
if response.status_code == 200:
    pdf_bytes = response.content
    is_pdf = pdf_bytes[:4] == b"%PDF"
    print(f"\n✓ Full PDF: {len(pdf_bytes)} bytes, valid signature: {is_pdf}")
else:
    print(f"\n✗ Full PDF: HTTP {response.status_code}")

response = requests.get(f"{BASE_URL}/assessments/{ASSESSMENT_ID}/summary-pdf", headers=headers, timeout=60)
if response.status_code == 200:
    pdf_bytes = response.content
    is_pdf = pdf_bytes[:4] == b"%PDF"
    print(f"✓ Summary PDF: {len(pdf_bytes)} bytes, valid signature: {is_pdf}")
else:
    print(f"✗ Summary PDF: HTTP {response.status_code}")

print("\n" + "="*80)
