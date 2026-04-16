# PortfolioHealth Advisor - Product Requirements Document

## Original Problem Statement
SaaS application for PPM (Product Portfolio Management) Capability Maturity Assessment. The tool assesses organizations across People, Process, Data, and Technology (PPDT) dimensions using:
1. Conversational AI Assessment (Claude Sonnet 4.5)
2. 10-Minute Quick Assessment (15 static MCQ, no login)
3. User Authentication & Dashboard (tracking history per company)
4. PDF Report Generation with radar charts and scoring
5. Dark professional theme with glassmorphism + liquid glass design

## Brand Identity
- **Name**: PortfolioHealth Advisor
- **Tagline**: "Academically grounded in published PPM research · University of Oulu"
- **Custom Logo**: Shield + pulse/bar chart mark (generated, not uploaded)
- **Theme**: Glassmorphism + Liquid Glass (deep void black with cyan/blue fluid blobs)

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key
- **PDF**: WeasyPrint/ReportLab

## What's Been Implemented (as of April 16, 2026)

### Core Features ✅
- JWT Authentication (register, login, logout, refresh)
- Admin seeded account (admin@ppdt.com)
- Consultant Dashboard with stats, radar charts, recent assessments
- Company management (CRUD)
- Full AI-guided Assessment Chat (multi-phase: People → Process → Data → Technology → Decision → Benchmark → Report)
- Quick Assessment flow (15 static questions, no login required, instant scoring)
- PDF Report Generation for both assessment types
- Complete application routing with protected/public routes

### Design & Theme ✅
- Glassmorphism + Liquid Glass theme overhaul (April 2026)
  - Deep void black background (#05050A)
  - Animated liquid blobs (blue/cyan gradient)
  - Glass surfaces with backdrop-blur and specular highlights
  - Liquid gradient buttons (blue → cyan)
  - Glass input fields with cyan focus states
  - Floating glass sidebar panel
- Custom generated logo (shield + pulse + ascending bars)
- 3D liquid glass shapes for auth pages
- Holographic radar charts (cyan stroke, transparent fill)
- Mobile-responsive across all pages (April 2026)
  - Compact mobile headers
  - 2-column stat grids on mobile
  - Stacked CTA cards
  - Mobile logo on auth pages
  - Hamburger menu with slide-out sidebar
  - Scrollable phase indicators
  - Responsive text scaling

### Admin Panel ✅ (April 2026)
- Admin-only page at /admin showing ALL assessments across all users
- Global stats: total assessments, completed, quick assessments, companies, users
- Tabbed tables: Full Assessments and Quick Assessments with search/filter
- CSV export for both assessment types
- Role-based access (admin role required)
- API endpoints: /api/admin/stats, /api/admin/assessments, /api/admin/quick-assessments, /api/admin/export/*

### Code Quality ✅
- Custom React hooks (useData.js)
- Extracted UI components (ScoreComponents.jsx)
- Scoring utilities (scoring.js)
- Clean component separation

## Key API Endpoints
- POST `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`
- GET `/api/auth/me`
- GET/POST `/api/companies`
- GET/POST `/api/assessments`
- POST `/api/assessments/{id}/start`, `/api/assessments/{id}/chat`
- GET `/api/assessments/{id}/pdf`
- POST `/api/quick-assessment/submit`
- GET `/api/quick-assessment/{id}/pdf`

## DB Schema
- users: {email, hashed_password, name, role, created_at}
- companies: {name, industry, product_count, created_by, created_at}
- assessments: {company_id, created_by, status, phase, overall_score, dimension_scores, findings, created_at}
- chat_messages: {assessment_id, role, content, created_at}
- quick_assessments: {company_name, industry, scores, overall_score, answers, created_at}

## Backlog / Future Tasks
- P2: Email notifications for assessment completions
- P2: Advanced analytics/benchmarking data comparisons across companies
- P3: Multi-language support
- P3: Team/organization management
