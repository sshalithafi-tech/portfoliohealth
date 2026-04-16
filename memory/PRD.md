# PortfolioHealth Advisor - Product Requirements Document

## Original Problem Statement
Build a PortfolioHealth Advisor — a specialized AI assessment consultant grounded in peer-reviewed PPM research from the University of Oulu. The app conducts structured, conversational capability maturity assessments across four dimensions: People, Process, Data, and Technology (PPDT model), scoring organizations against five maturity levels.

## Branding
- **App Name**: PortfolioHealth Advisor
- **Tagline**: Academically grounded in published PPM research · University of Oulu
- **Framework Name**: PPM Capability Maturity Framework
- **Attribution**: This tool is an independent academic research output developed as part of a Master's thesis at the University of Oulu (IEM–IPIC, 2026). Assessment methodology is grounded in peer-reviewed PPM research. Not affiliated with or endorsed by any commercial framework.

## User Personas
1. **Consultants** - Primary users who conduct assessments for client companies
2. **Company Representatives** - Respondents who answer assessment questions
3. **Administrators** - Manage platform and user access

## Core Requirements (Static)
- Conversational AI assessment using Claude Sonnet 4.5
- PPDT scoring framework (People, Process, Data, Technology)
- Five maturity levels (Ad Hoc → Developing → Defined → Managed → Optimising)
- Company management for longitudinal tracking
- Assessment history and reporting
- PDF export for client deliverables
- User authentication for consultants
- Dark professional theme (navy/charcoal, blue accent #2f81f7)

## Technology Stack
- **Frontend**: React 19, Tailwind CSS, Recharts, Lucide React
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
- **AI**: Claude Sonnet 4.5 via emergentintegrations library
- **Auth**: JWT with httpOnly cookies
- **PDF**: ReportLab

## What's Been Implemented (April 16, 2026)

### Authentication System
- ✅ User registration with email/password
- ✅ Login with JWT tokens (httpOnly cookies)
- ✅ Session management with refresh tokens
- ✅ Brute force protection (5 attempts → 15 min lockout)
- ✅ Admin user seeding

### Company Management
- ✅ Create companies with industry, portfolio size, challenges
- ✅ List and search companies
- ✅ Link assessments to companies for longitudinal tracking

### Full Assessment System
- ✅ Create assessments linked to companies
- ✅ AI-powered conversational assessment chat
- ✅ Claude Sonnet 4.5 integration via Emergent LLM key
- ✅ Phase tracking (Welcome → People → Process → Data → Technology → Decision → Benchmark → Report)
- ✅ Chat history persistence
- ✅ Automatic report generation with scores

### Quick Assessment (10-Minute Rapid Screening) - NEW
- ✅ Landing page with "Quick Check" and "Full Assessment" options
- ✅ 15 fixed multiple-choice questions (3-4 per PPDT dimension)
- ✅ Progress bar and question navigation
- ✅ No login required to take assessment
- ✅ Instant results with radar chart visualization
- ✅ Traffic light indicators (Red/Amber/Green) per dimension
- ✅ Weighted scoring (Data ×0.35, Process ×0.25, People ×0.25, Technology ×0.15)
- ✅ One-page PDF export "PPDT Quick Health Check"
- ✅ Save to account functionality
- ✅ CTA conversion hook to Full Assessment

### Reporting
- ✅ PPDT scores display with radar/bar charts
- ✅ Key findings and critical gaps
- ✅ Improvement roadmap (immediate/short-term/strategic)
- ✅ Benchmark context and consultant notes
- ✅ PDF export functionality

### Dashboard
- ✅ Assessment statistics (total, completed, in progress)
- ✅ Company count
- ✅ Quick assessment count
- ✅ Average PPDT scores across completed assessments
- ✅ Recent assessments table
- ✅ Quick actions for Quick Check, Companies, Assessments

### UI/UX
- ✅ Dark professional theme matching McKinsey Digital aesthetic
- ✅ Responsive sidebar navigation
- ✅ Phase indicator in assessment chat
- ✅ Toast notifications
- ✅ Loading states and animations
- ✅ University of Oulu research reference in footer

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token

### Dashboard & Companies
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET/POST /api/companies` - Companies CRUD
- `GET /api/companies/{id}` - Get company details
- `GET /api/companies/{id}/assessments` - Company assessments

### Full Assessment
- `GET/POST /api/assessments` - Assessments CRUD
- `GET /api/assessments/{id}` - Get assessment details
- `PATCH /api/assessments/{id}` - Update assessment
- `POST /api/assessments/{id}/start` - Start assessment
- `POST /api/assessments/{id}/chat` - Send chat message
- `GET /api/assessments/{id}/pdf` - Download PDF report

### Quick Assessment (NEW)
- `GET /api/quick-assessment/questions` - Get all 15 questions
- `POST /api/quick-assessment/submit` - Submit answers, get results
- `GET /api/quick-assessment/{id}` - Get assessment by ID
- `GET /api/quick-assessment/{id}/pdf` - Download PDF report
- `POST /api/quick-assessment/{id}/save` - Save to user account
- `GET /api/quick-assessments` - Get user's quick assessments

## Quick Assessment Questions
| # | Dimension | Question |
|---|-----------|----------|
| 1 | Qualifier | How many products are in your active portfolio? |
| 2-4 | People | Decision-making, roles/ownership, data literacy |
| 5-7 | Process | PPM governance, product classification, end-of-life |
| 8-11 | Data | Profitability, master data, system integration, data model |
| 12-15 | Technology | System integration, dashboards, reporting effort, architecture |

## Prioritized Backlog

### P0 - Critical (Completed)
- ✅ Core full assessment flow
- ✅ AI integration (Claude Sonnet 4.5)
- ✅ User authentication
- ✅ Company management
- ✅ Report generation
- ✅ PDF export
- ✅ Quick Assessment (10-min screening)

### P1 - High Priority (Future)
- [ ] Email notifications for completed assessments
- [ ] Team/organization accounts
- [ ] Assessment templates
- [ ] Custom branding for PDF reports

### P2 - Medium Priority (Future)
- [ ] Assessment comparison view
- [ ] Longitudinal tracking charts (6-12 month trends)
- [ ] Export to Excel/CSV
- [ ] Assessment sharing links

### P3 - Nice to Have (Future)
- [ ] Multi-language support
- [ ] Custom assessment dimensions
- [ ] Integration with CRM systems
- [ ] Mobile app

## Next Tasks
1. Add longitudinal tracking visualization for repeat assessments
2. Implement assessment comparison features
3. Add email notifications for completed assessments
