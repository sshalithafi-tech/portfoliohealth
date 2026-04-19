# PortfolioHealth Advisor - Product Requirements Document

## Original Problem Statement
SaaS application for PPM Capability Maturity Assessment across People, Process, Data, and Technology (PPDT).

## Brand Identity
- **Name**: PortfolioHealth Advisor
- **Contact Email**: shalitha.samarakoonmudiyanselage@student.oulu.fi
- **Custom Domain**: portfoliohealth.fi
- **Theme**: Glassmorphism + Liquid Glass

## Architecture
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python)
- Database: MongoDB
- AI: Claude Sonnet 4.5 via Emergent LLM Key (emergentintegrations)
- PDF: ReportLab

## What's Been Implemented

### Core Features
- JWT Auth with Bearer token (localStorage) — works cross-domain
- Admin seeded account (admin@ppdt.com / Admin123!)
- Dashboard with stats, radar charts, recent assessments
- Company management (CRUD + DELETE with confirmation)
- Full AI Assessment Chat (PPDT phases + governance indicators at L4-5)
- Quick Assessment (15 questions, no login, instant scoring)
- PDF Reports with logo header, governance section, closing statement
- Admin Panel (all assessments, all users, CSV export)
- In-app Notifications (bell icon, unread count, mark read)
- Assessment auto-redirect to dashboard on completion
- Closing statement with contact email in chat + report + PDF

### Design
- Glassmorphism + Liquid Glass theme across all pages
- Custom generated logo (shield + pulse + bars)
- Mobile responsive
- 3D liquid glass auth pages

### Governance Indicators (L4-5)
- People: Role-based data ownership, accountability frameworks
- Process: Review cycles, change control, escalation paths, audit trails
- Data: Governance policies, stewardship roles, data quality SLAs
- Technology: Access control, integration governance, PLM audit

## Key API Endpoints
- Auth: POST /api/auth/register, /api/auth/login, /api/auth/logout, GET /api/auth/me
- Companies: GET/POST/DELETE /api/companies
- Assessments: GET/POST /api/assessments, POST /api/assessments/{id}/start, POST /api/assessments/{id}/chat
- PDF: GET /api/assessments/{id}/pdf, GET /api/quick-assessment/{id}/pdf
- Notifications: GET /api/notifications, GET /api/notifications/unread-count, PATCH /api/notifications/{id}/read, POST /api/notifications/read-all
- Admin: GET /api/admin/stats, /api/admin/assessments, /api/admin/quick-assessments, /api/admin/export/*

## Backlog
- P2: Email notifications for assessment completions
- P2: Advanced analytics/benchmarking comparisons
- P3: Multi-language support
