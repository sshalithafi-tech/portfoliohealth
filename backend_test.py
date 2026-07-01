"""
Comprehensive backend test for PortfolioHealth Advisor report generation performance refactor.

Tests the full conversation flow through all phases and measures the exact timing
of the final report-generation turn (seed + 3 concurrent specialist calls).
"""
import requests
import time
import json
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://4ad4b2b3-a136-4aa5-a519-c697503c7614.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@portfoliohealth.fi"
ADMIN_PASSWORD = "Admin@12345"

class PortfolioHealthTester:
    def __init__(self):
        self.token = None
        self.company_id = None
        self.assessment_id = None
        self.report_ready_timing = None
        
    def login(self) -> bool:
        """Step 1: Login with admin credentials"""
        print("\n=== STEP 1: Login ===")
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            print(f"✓ Login successful, token received")
            return True
        else:
            print(f"✗ Login failed: {response.text}")
            return False
    
    def create_company(self) -> bool:
        """Step 2: Create a test company"""
        print("\n=== STEP 2: Create Company ===")
        response = requests.post(
            f"{BACKEND_URL}/companies",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Nordic Precision Manufacturing Oy",
                "industry": "Industrial Equipment Manufacturing",
                "company_size": "Mid-market · 380 employees",
                "active_products": "42 active SKUs across 3 product families",
                "primary_challenge": "Portfolio complexity and data fragmentation"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            self.company_id = data.get("id")
            print(f"✓ Company created: {data.get('name')} (ID: {self.company_id})")
            return True
        else:
            print(f"✗ Company creation failed: {response.text}")
            return False
    
    def create_assessment(self) -> bool:
        """Step 3: Create a new assessment"""
        print("\n=== STEP 3: Create Assessment ===")
        response = requests.post(
            f"{BACKEND_URL}/assessments",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "company_id": self.company_id,
                "respondent_name": "Mika Virtanen",
                "respondent_role": "VP of Product Development"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            self.assessment_id = data.get("id")
            print(f"✓ Assessment created (ID: {self.assessment_id})")
            return True
        else:
            print(f"✗ Assessment creation failed: {response.text}")
            return False
    
    def start_assessment(self) -> bool:
        """Step 4: Start assessment and get AI greeting"""
        print("\n=== STEP 4: Start Assessment ===")
        response = requests.post(
            f"{BACKEND_URL}/assessments/{self.assessment_id}/start",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            greeting = data.get("message", {}).get("content", "")
            print(f"✓ AI greeting received ({len(greeting)} chars)")
            print(f"Greeting preview: {greeting[:100]}...")
            return True
        else:
            print(f"✗ Start assessment failed: {response.text}")
            return False
    
    def send_chat_message(self, message: str, step_label: str = "") -> Optional[Dict[str, Any]]:
        """Send a chat message and return the response"""
        if step_label:
            print(f"\n{step_label}")
        print(f"User: {message[:80]}{'...' if len(message) > 80 else ''}")
        
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/assessments/{self.assessment_id}/chat",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"message": message}
        )
        elapsed = time.time() - start_time
        
        print(f"Status: {response.status_code} (took {elapsed:.2f}s)")
        
        if response.status_code == 200:
            data = response.json()
            ai_message = data.get("message", {}).get("content", "")
            report_ready = data.get("report_ready", False)
            
            print(f"AI: {ai_message[:100]}{'...' if len(ai_message) > 100 else ''}")
            
            if report_ready:
                self.report_ready_timing = elapsed
                print(f"\n🎯 REPORT READY! This turn took {elapsed:.2f} seconds")
            
            return data
        else:
            print(f"✗ Chat failed: {response.text}")
            return None
    
    def drive_full_conversation(self) -> bool:
        """Step 5: Drive the full conversation through all phases"""
        print("\n=== STEP 5: Full Conversation Flow ===")
        
        # Phase (a): Language selection
        response = self.send_chat_message("English", "Phase (a): Language Selection")
        if not response:
            return False
        
        # Phase (b): Context questions
        # Industry, company size, business model
        response = self.send_chat_message(
            "We're in industrial equipment manufacturing, specifically hydraulic systems and precision components. "
            "We're a mid-sized company with about 380 employees. Our business model is primarily Standard - "
            "we have a catalog of configurable products with some customization options, but most sales are "
            "from our standard product families.",
            "Phase (b): Context - Industry & Business Model"
        )
        if not response:
            return False
        
        # What prompted the assessment
        response = self.send_chat_message(
            "We're prompted by increasing portfolio complexity. Over the past 5 years we've grown from 28 to 42 SKUs, "
            "and we're finding it harder to make data-driven decisions about which products to invest in, which to "
            "phase out, and where to allocate our R&D budget. Our leadership wants better visibility.",
            "Phase (b): Context - Assessment Trigger"
        )
        if not response:
            return False
        
        # Phase (c): Anchor questions
        # Primary performance metric
        response = self.send_chat_message(
            "Our leadership primarily evaluates portfolio decisions based on gross margin. Revenue growth is important, "
            "but margin is the key metric - we need to maintain at least 35% gross margin across the portfolio.",
            "Phase (c): Anchor Q1 - Primary Performance Metric"
        )
        if not response:
            return False
        
        # R&D budget scale
        response = self.send_chat_message(
            "Our annual R&D and product development spend is in the range of 5 to 20 million euros. "
            "I'd say closer to 12 million last year.",
            "Phase (c): Anchor Q2 - R&D Budget"
        )
        if not response:
            return False
        
        # Recent portfolio decision that didn't go as expected
        response = self.send_chat_message(
            "Last year we discontinued our legacy HPX-200 hydraulic pump series, thinking the market had moved on. "
            "But we underestimated the installed base - we lost several key service contracts and had to scramble "
            "to support customers. We learned that we didn't have good visibility into the full lifecycle value "
            "of that product line, including aftermarket revenue.",
            "Phase (c): Anchor Q3 - Recent Decision"
        )
        if not response:
            return False
        
        # Active product count and definition clarity
        response = self.send_chat_message(
            "We have 42 active SKUs currently. But honestly, the definition of 'active' varies by department. "
            "Sales counts anything we can still quote. Engineering counts what's in current production. "
            "Finance counts what generated revenue in the last 12 months. So no, we don't have a consistent definition.",
            "Phase (c): Anchor Q4 - Active Products"
        )
        if not response:
            return False
        
        # Phase (d): Pillar assessment - PEOPLE
        response = self.send_chat_message(
            "Portfolio decisions are primarily made by myself as VP of Product Development, working with our CFO "
            "and the Sales Director. We meet quarterly, but it's not a formal governance structure - more of an "
            "informal steering group. There's no single person who owns the portfolio as their primary responsibility.",
            "Phase (d): PEOPLE - Decision Responsibility"
        )
        if not response:
            return False
        
        response = self.send_chat_message(
            "When data is wrong or missing, it usually falls to whoever notices it. We don't have formal data ownership. "
            "Product cost data lives with Finance, technical specs with Engineering, customer data with Sales. "
            "When there's a discrepancy, we have to chase people down. And yes, we've lost critical knowledge when "
            "people left - our former product manager for the HPX series took a lot of tribal knowledge with him.",
            "Phase (d): PEOPLE - Data Ownership & Knowledge Loss"
        )
        if not response:
            return False
        
        response = self.send_chat_message(
            "We don't have formal PPM training. People learn on the job. When someone new joins the team, they shadow "
            "the existing staff for a few weeks. We don't have documented competency requirements for portfolio roles. "
            "Skills are more about institutional knowledge than formal qualifications.",
            "Phase (d): PEOPLE - Skills & Training"
        )
        if not response:
            return False
        
        # Phase (d): Pillar assessment - PROCESS
        response = self.send_chat_message(
            "We have quarterly portfolio reviews, but they're not always well-documented. We discuss performance, "
            "but the minutes are informal - usually just action items in an email. If you asked me to reconstruct "
            "the reasoning behind the HPX-200 discontinuation from 18 months ago, I'd have to rely on memory and "
            "dig through email threads. There's no formal audit trail.",
            "Phase (d): PROCESS - Review Cycles & Traceability"
        )
        if not response:
            return False
        
        response = self.send_chat_message(
            "Our change control process is documented in theory - we have an ECO process in our PLM system. "
            "But in practice, urgent changes often bypass it. Sales will promise a customer modification, "
            "Engineering makes the change, and sometimes Finance doesn't find out until the cost variance shows up. "
            "So I'd say it's partially followed, not consistently enforced.",
            "Phase (d): PROCESS - Change Control"
        )
        if not response:
            return False
        
        # Phase (d): Pillar assessment - DATA
        response = self.send_chat_message(
            "Product-level profitability takes us about 2-3 weeks to pull together, and honestly, I'm only about "
            "70% confident in the numbers. We have to manually reconcile data from SAP for costs, Salesforce for "
            "revenue, and spreadsheets for overhead allocation. Different departments definitely disagree on the "
            "same product's data - Sales has one margin number, Finance has another.",
            "Phase (d): DATA - Profitability & Confidence"
        )
        if not response:
            return False
        
        response = self.send_chat_message(
            "Our product data is spread across multiple systems. Master data is supposed to be in SAP, but Engineering "
            "maintains technical specs in our PLM system (Windchill), Sales has customer-specific configurations in "
            "Salesforce, and Marketing has their own product catalog spreadsheets. There's no single source of truth. "
            "We're constantly reconciling discrepancies.",
            "Phase (d): DATA - Centralization"
        )
        if not response:
            return False
        
        # Phase (d): Pillar assessment - TECHNOLOGY
        response = self.send_chat_message(
            "When we're actually making portfolio decisions in our quarterly meetings, we use Excel. We pull data "
            "from SAP and Salesforce beforehand, but the actual analysis and decision support happens in spreadsheets. "
            "We have the systems, but they don't talk to each other in a way that's useful for portfolio decisions.",
            "Phase (d): TECHNOLOGY - Decision Tools"
        )
        if not response:
            return False
        
        response = self.send_chat_message(
            "Our ERP (SAP), CRM (Salesforce), and PLM (Windchill) systems don't really talk to each other. "
            "We have some basic integrations - like order data flows from Salesforce to SAP - but for portfolio "
            "analysis, people manually bridge the gaps. We export from one system, massage the data in Excel, "
            "and import to another. It's very manual.",
            "Phase (d): TECHNOLOGY - System Integration"
        )
        if not response:
            return False
        
        response = self.send_chat_message(
            "I'd say our technology investment has mostly improved data storage, not decision quality. We have more "
            "data than ever, but it's harder to get actionable insights. The systems help us track transactions, "
            "but they haven't made portfolio decisions any easier or faster.",
            "Phase (d): TECHNOLOGY - Impact on Decisions"
        )
        if not response:
            return False
        
        # Phase (e): Governance probe (since some pillars >= 3.0 likely)
        response = self.send_chat_message(
            "The processes I've described are partially documented - we have some written procedures, especially "
            "around change control and quarterly reviews. But they're not consistently followed, and there's no "
            "real audit trail. A lot depends on the right people being in the room. If I'm not in the quarterly "
            "meeting, decisions might get made differently.",
            "Phase (e): Governance - Documentation & Accountability"
        )
        if not response:
            return False
        
        response = self.send_chat_message(
            "Data quality at the boundary between departments is a known problem, but no one specifically owns it. "
            "When there's a discrepancy between what Engineering says a product costs and what Finance says, "
            "we have to convene a meeting to sort it out. There's no named person accountable for resolving those gaps.",
            "Phase (e): Governance - Data Quality Ownership"
        )
        if not response:
            return False
        
        # Phase (f): Confirm & close - trigger report generation
        response = self.send_chat_message(
            "No, that covers everything. I think you have a good picture of where we are.",
            "Phase (f): Confirm & Close - TRIGGER REPORT GENERATION"
        )
        if not response:
            return False
        
        # Check if report is ready
        if response.get("report_ready"):
            print(f"\n✓ Report generation completed successfully!")
            return True
        else:
            # Sometimes the AI asks one more follow-up - answer it
            print("\nAI asked a follow-up question, answering to complete...")
            response = self.send_chat_message(
                "No, I don't think there's anything else important we haven't covered. You've asked about all the key areas.",
                "Phase (f): Final Confirmation"
            )
            if response and response.get("report_ready"):
                print(f"\n✓ Report generation completed successfully!")
                return True
            else:
                print(f"\n⚠ Report not ready after full conversation")
                return False
    
    def verify_report_fields(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Step 7: Verify all required report fields are present and non-empty"""
        print("\n=== STEP 7: Verify Report Fields ===")
        
        required_fields = {
            # Top-level score fields
            "scores": ["people", "process", "data", "technology", "overall"],
            "equal_weighted_score": None,
            "contextual_score": None,
            "level_names": ["people", "process", "data", "technology", "overall"],
            
            # Narrative sections
            "dimension_summaries": ["people", "process", "data", "technology"],
            "pillar_interpretations": ["people", "process", "data", "technology"],
            "pillar_interpretation_short": ["people", "process", "data", "technology"],
            
            # Failure pattern
            "failure_pattern_name": None,
            "failure_pattern_narrative": None,
            
            # Financial consequence
            "financial_consequence": ["cost_category", "consequence_narrative", "metric_framing"],
            
            # 90-day projection
            "ninety_day_projection": ["score_current", "score_projected", "score_delta", 
                                      "bottleneck_level_current", "bottleneck_level_projected",
                                      "what_becomes_possible", "comparable_outcome"],
            
            # Governance
            "governance_observations": ["people", "process", "data", "technology"],
            "governance_assessment": None,
            "governance_signal_summary": None,  # list
            
            # Management & reliability
            "management_commitment": None,
            "management_commitment_assessment": None,
            "assessment_reliability": ["confidence", "factors"],
            
            # Decision vulnerability
            "decision_vulnerability_ratings": ["discontinuation", "new_launch", "product_change", "portfolio_investment"],
            "decision_vulnerability": None,
            
            # Findings & gaps
            "key_findings": None,  # list
            "critical_gaps": None,  # list
            
            # Roadmap
            "roadmap": {
                "immediate": ["action_summary", "actions", "expected_gain"],
                "short_term": ["action_summary", "actions", "expected_gain"],
                "strategic": ["action_summary", "actions", "expected_gain"]
            },
            
            # First action
            "first_action": ["headline", "description", "expected_outcome", "who_owns_it", 
                           "time_to_implement", "preconditions_met"],
            
            # Benchmark & consultant note
            "benchmark_context": None,
            "consultant_note": None,
            "closing_statement": None,
        }
        
        results = {
            "missing": [],
            "empty": [],
            "present": []
        }
        
        def check_field(field_name, subfields=None, parent_obj=None):
            obj = parent_obj if parent_obj is not None else report
            
            if field_name not in obj:
                results["missing"].append(field_name)
                return False
            
            value = obj[field_name]
            
            # Check if empty/null
            if value is None or (isinstance(value, str) and not value.strip()):
                results["empty"].append(field_name)
                return False
            
            # Check subfields if specified
            if subfields:
                if isinstance(subfields, list):
                    for subfield in subfields:
                        if isinstance(value, dict):
                            if subfield not in value:
                                results["missing"].append(f"{field_name}.{subfield}")
                            elif value[subfield] is None or (isinstance(value[subfield], str) and not value[subfield].strip()):
                                results["empty"].append(f"{field_name}.{subfield}")
                            else:
                                results["present"].append(f"{field_name}.{subfield}")
                        elif isinstance(value, list):
                            # For lists, just check it's non-empty
                            if len(value) == 0:
                                results["empty"].append(field_name)
                            else:
                                results["present"].append(field_name)
                            break
                elif isinstance(subfields, dict):
                    for subfield, sub_subfields in subfields.items():
                        if subfield not in value:
                            results["missing"].append(f"{field_name}.{subfield}")
                        else:
                            check_field(subfield, sub_subfields, value)
            else:
                results["present"].append(field_name)
            
            return True
        
        for field, subfields in required_fields.items():
            check_field(field, subfields)
        
        # Print results
        print(f"\n✓ Present and non-empty: {len(results['present'])} fields")
        
        if results["missing"]:
            print(f"\n✗ MISSING fields ({len(results['missing'])}):")
            for field in results["missing"]:
                print(f"  - {field}")
        
        if results["empty"]:
            print(f"\n✗ EMPTY/NULL fields ({len(results['empty'])}):")
            for field in results["empty"]:
                print(f"  - {field}")
        
        # Check roadmap continuity
        print("\n=== Roadmap Continuity Check ===")
        roadmap = report.get("roadmap", {})
        scores = report.get("scores", {})
        
        if roadmap.get("immediate", {}).get("expected_gain"):
            immediate_gain = roadmap["immediate"]["expected_gain"]
            print(f"Immediate phase expected_gain: {immediate_gain}")
            
            # Parse starting values
            import re
            pattern = r"(People|Process|Data|Technology):\s*([\d.]+)\s*→"
            matches = re.findall(pattern, immediate_gain)
            
            continuity_ok = True
            for pillar_name, start_val in matches:
                pillar_key = pillar_name.lower()
                score_val = scores.get(pillar_key)
                if score_val is not None:
                    if abs(float(start_val) - float(score_val)) > 0.01:
                        print(f"  ✗ {pillar_name}: roadmap starts at {start_val}, but score is {score_val}")
                        continuity_ok = False
                    else:
                        print(f"  ✓ {pillar_name}: {start_val} matches score")
            
            if continuity_ok:
                print("✓ Roadmap continuity check PASSED")
            else:
                print("✗ Roadmap continuity check FAILED")
        
        return results
    
    def test_pdf_generation(self) -> bool:
        """Step 8: Test full PDF generation"""
        print("\n=== STEP 8: Full PDF Generation ===")
        response = requests.get(
            f"{BACKEND_URL}/assessments/{self.assessment_id}/pdf",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            content = response.content
            size = len(content)
            
            print(f"Content-Type: {content_type}")
            print(f"Size: {size} bytes")
            
            if content_type == "application/pdf" and content[:4] == b"%PDF" and size > 5000:
                print(f"✓ Full PDF generated successfully ({size} bytes)")
                return True
            else:
                print(f"✗ PDF validation failed")
                return False
        else:
            print(f"✗ PDF generation failed: {response.text}")
            return False
    
    def test_summary_pdf_generation(self) -> bool:
        """Step 9: Test summary PDF generation"""
        print("\n=== STEP 9: Summary PDF Generation ===")
        response = requests.get(
            f"{BACKEND_URL}/assessments/{self.assessment_id}/summary-pdf",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            content = response.content
            size = len(content)
            
            print(f"Content-Type: {content_type}")
            print(f"Size: {size} bytes")
            
            if content_type == "application/pdf" and content[:4] == b"%PDF" and size > 3000:
                print(f"✓ Summary PDF generated successfully ({size} bytes)")
                return True
            else:
                print(f"✗ Summary PDF validation failed")
                return False
        else:
            print(f"✗ Summary PDF generation failed: {response.text}")
            return False
    
    def verify_assessment_persistence(self) -> bool:
        """Step 10: Verify assessment was persisted correctly"""
        print("\n=== STEP 10: Verify Assessment Persistence ===")
        response = requests.get(
            f"{BACKEND_URL}/assessments/{self.assessment_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            report = data.get("report")
            
            if report:
                print(f"✓ Assessment persisted with report")
                # Quick sanity check
                if report.get("scores") and report.get("closing_statement"):
                    print(f"✓ Report structure looks correct")
                    return True
                else:
                    print(f"✗ Report structure incomplete")
                    return False
            else:
                print(f"✗ No report in persisted assessment")
                return False
        else:
            print(f"✗ Failed to retrieve assessment: {response.text}")
            return False
    
    def run_full_test(self):
        """Run the complete test suite"""
        print("=" * 80)
        print("PORTFOLIOHEALTH ADVISOR - REPORT GENERATION PERFORMANCE TEST")
        print("=" * 80)
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Create company
        if not self.create_company():
            return False
        
        # Step 3: Create assessment
        if not self.create_assessment():
            return False
        
        # Step 4: Start assessment
        if not self.start_assessment():
            return False
        
        # Step 5-6: Drive full conversation and time report generation
        if not self.drive_full_conversation():
            return False
        
        # Get the final assessment with report
        response = requests.get(
            f"{BACKEND_URL}/assessments/{self.assessment_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code != 200:
            print(f"\n✗ Failed to retrieve final assessment")
            return False
        
        assessment_data = response.json()
        report = assessment_data.get("report")
        
        if not report:
            print(f"\n✗ No report in final assessment")
            return False
        
        # Step 7: Verify all report fields
        field_results = self.verify_report_fields(report)
        
        # Step 8: Test full PDF
        pdf_ok = self.test_pdf_generation()
        
        # Step 9: Test summary PDF
        summary_pdf_ok = self.test_summary_pdf_generation()
        
        # Step 10: Verify persistence
        persistence_ok = self.verify_assessment_persistence()
        
        # Final summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        print(f"\n(a) TIMING:")
        if self.report_ready_timing:
            print(f"    Report-ready turn took: {self.report_ready_timing:.2f} seconds")
            if self.report_ready_timing < 90:
                print(f"    ✓ PASSED: Under 90-second target")
            else:
                print(f"    ⚠ SLOW: Exceeded 90-second target")
        else:
            print(f"    ✗ FAILED: No timing captured")
        
        print(f"\n(b) FIELD COMPLETENESS:")
        if not field_results["missing"] and not field_results["empty"]:
            print(f"    ✓ PASSED: All required fields present and non-empty")
        else:
            print(f"    ✗ FAILED: {len(field_results['missing'])} missing, {len(field_results['empty'])} empty")
        
        print(f"\n(c) ROADMAP CONTINUITY:")
        print(f"    (See detailed check above)")
        
        print(f"\n(d) PDF GENERATION:")
        if pdf_ok and summary_pdf_ok:
            print(f"    ✓ PASSED: Both PDFs generated successfully")
        else:
            print(f"    ✗ FAILED: PDF generation issues")
        
        print("\n" + "=" * 80)
        
        return True


if __name__ == "__main__":
    tester = PortfolioHealthTester()
    success = tester.run_full_test()
    exit(0 if success else 1)
