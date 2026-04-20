# PortfolioHealth Advisor - PRD

## Brand Identity
- **Name**: PortfolioHealth Advisor
- **Theme**: Deep Navy Corporate (#0A1628, gold #C9A84C, silver glass)
- **Logo**: Inline SVG LogoMark — deep-navy rounded tile with a gold "ascending pulse" signature + gold peak dot + fine corner crest bracket (Portfolio + Health motif). See `/app/frontend/src/components/LogoMark.jsx`.
- **Contact**: shalitha.samarakoonmudiyanselage@student.oulu.fi
- **Domain**: portfoliohealth.fi

## Architecture
React + Tailwind + FastAPI + MongoDB + Claude Sonnet 4.5 (Emergent LLM Key via `emergentintegrations`)

### Code Organisation (post-refactor, 2026-04-20)
**Backend**
- `backend/server.py` (routes; slim, 1454 lines)
- `backend/chat_service.py` — LLM wrappers (`call_llm_with_history`, `call_llm_greeting`, `extract_report_json`, `normalise_report_weights`)
- `backend/pdf_builder.py` — `build_full_assessment_pdf`, `build_quick_assessment_pdf` + section builders

**Frontend**
- `pages/ReportPage.jsx` (96 lines) orchestrates 9 sub-components in `components/report/`
- `pages/AssessmentChatPage.jsx` (144 lines) uses `components/chat/` (Header, PhaseIndicator, Messages, Input)
- `pages/AdminPage.jsx` (142 lines) uses `components/admin/` (StatsGrid, Filters, FullAssessmentsTable, QuickAssessmentsTable)
- `components/LogoMark.jsx` — inline SVG brand mark used across all pages

## Color Palette
- Background: #0A1628 (deep navy)
- Gold accent: #C9A84C
- Blue: #60A5FA · Green: #34D399 · Red: #EF4444 · Purple: #A78BFA

## Implemented Features
- JWT Auth (Bearer token, localStorage)
- Admin seeded account
- Dashboard with PPDT score cards (radar charts removed)
- Company CRUD + Delete + Download
- Full AI Assessment Chat (8 phases incl. strategic weighting) — Claude Sonnet 4.5
- Quick Assessment (15 questions, no login)
- Report Page (9 sections — now modularised)
- PDF Reports with Deep Navy corporate header + gold accents
- Admin Panel (all data, CSV export, PDF download)
- In-app Notifications
- HashRouter (page refresh works)
- Mobile responsive
- Deep Navy Corporate glassmorphism theme
- **NEW (2026-04-20):** Redesigned inline-SVG LogoMark
- **NEW (2026-04-20):** Backend split into `pdf_builder.py` + `chat_service.py`
- **NEW (2026-04-20):** Frontend large components split into small sub-components
- **NEW (2026-04-20):** useCallback wraps on `fetchAssessment`, `fetchData`, `startAssessment` for correct hook deps + console.error + toast error handling on all axios fetches

## Key API Endpoints
Auth, Companies, Assessments, Chat, PDF, Notifications, Admin, Quick Assessment

## Backlog
- P2: Email notifications on completion (e.g. Resend/SendGrid)
- P2: Advanced analytics/benchmarking across all companies
- P3: Revisit token storage (localStorage → httpOnly cookies) once CORS setup supports it
- P3: Chat completion UX polish (skeleton loader on LLM thinking, retry button on failure)
