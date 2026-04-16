# PPDT Capability Maturity Advisor - Product Requirements Document

## Original Problem Statement
Build a PPDT Capability Maturity Advisor — a specialized AI assessment consultant grounded in Hannila's Product Wellbeing framework (2026) and doctoral research on data-driven Product Portfolio Management (Hannila, 2019). The app conducts structured, conversational capability maturity assessments across four dimensions: People, Process, Data, and Technology (PPDT model), scoring organizations against five maturity levels.

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

### Assessment System
- ✅ Create assessments linked to companies
- ✅ AI-powered conversational assessment chat
- ✅ Claude Sonnet 4.5 integration via Emergent LLM key
- ✅ Phase tracking (Welcome → People → Process → Data → Technology → Decision → Benchmark → Report)
- ✅ Chat history persistence
- ✅ Automatic report generation with scores

### Reporting
- ✅ PPDT scores display with radar/bar charts
- ✅ Key findings and critical gaps
- ✅ Improvement roadmap (immediate/short-term/strategic)
- ✅ Benchmark context and consultant notes
- ✅ PDF export functionality

### Dashboard
- ✅ Assessment statistics (total, completed, in progress)
- ✅ Company count
- ✅ Average PPDT scores across completed assessments
- ✅ Recent assessments table

### UI/UX
- ✅ Dark professional theme matching McKinsey Digital aesthetic
- ✅ Responsive sidebar navigation
- ✅ Phase indicator in assessment chat
- ✅ Toast notifications
- ✅ Loading states and animations
- ✅ University of Oulu research reference in footer

## API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET/POST /api/companies` - Companies CRUD
- `GET /api/companies/{id}` - Get company details
- `GET /api/companies/{id}/assessments` - Company assessments
- `GET/POST /api/assessments` - Assessments CRUD
- `GET /api/assessments/{id}` - Get assessment details
- `PATCH /api/assessments/{id}` - Update assessment
- `POST /api/assessments/{id}/start` - Start assessment
- `POST /api/assessments/{id}/chat` - Send chat message
- `GET /api/assessments/{id}/pdf` - Download PDF report

## Prioritized Backlog

### P0 - Critical (Completed)
- ✅ Core assessment flow
- ✅ AI integration
- ✅ User authentication
- ✅ Company management
- ✅ Report generation
- ✅ PDF export

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
1. Test complete assessment flow end-to-end
2. Verify PDF export formatting
3. Add longitudinal tracking visualization for repeat assessments
4. Implement assessment comparison features
