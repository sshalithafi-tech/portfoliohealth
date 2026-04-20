# PortfolioHealth Advisor - PRD

## Brand Identity
- **Name**: PortfolioHealth Advisor
- **Theme**: Deep Navy Corporate (#0A1628, gold #C9A84C, silver glass)
- **Logo**: Inline SVG `LogoMark` — deep-navy rounded tile + gold "ascending pulse" line + peak dot + gold corner crest. `/app/frontend/src/components/LogoMark.jsx`
- **Contact**: shalitha.samarakoonmudiyanselage@student.oulu.fi
- **Domain**: portfoliohealth.fi

## Architecture
React + Tailwind + FastAPI + MongoDB + Claude Sonnet 4.5 (Emergent LLM Key via `emergentintegrations`).

### Code Organisation
**Backend**
- `server.py` — routes + slim handlers
- `chat_service.py` — LLM wrappers: `call_llm_with_history`, `call_llm_greeting`, `extract_report_json`, `normalise_report_weights`
- `pdf_builder.py` — `build_full_assessment_pdf` + section builders (header, company_info, overall_score, dimension_scores, weighted_breakdown, **bottleneck**, governance, **management_commitment**, findings_and_gaps, **decision_vulnerability**, roadmap, benchmark_and_note, closing)

**Frontend**
- `pages/ReportPage.jsx` — thin orchestrator (15 sub-components in `components/report/`)
- `pages/AssessmentChatPage.jsx` — uses `components/chat/*`
- `pages/AdminPage.jsx` — uses `components/admin/*`

## AI Prompt
Currently active: 5-turn Hannila/PPDT prompt with mandatory JSON emission (ready_for_report=true). See `PPDT_SYSTEM_PROMPT` in `server.py`.

**Emission contract** — `chat_service.extract_report_json` looks for a ` ```json ` fenced block containing `"ready_for_report": true`. The backend then persists `report`, flips status to `completed`, and triggers PDF generation.

## Report Schema Fields (rendered in UI + PDF)
- `scores.{people,process,data,technology,overall}` — overall equals `equal_weighted_score`
- `equal_weighted_score` (primary) + `contextual_score` (secondary) — dual display
- `weights_raw`, `weights_normalised`, `contextual_weights`
- `level_names`, `dimension_summaries`, `pillar_interpretations`
- `business_model` (ETO/CETO/CTO/Standard/Bulk) — shown in Report header chip + PDF
- `strategic_priority` (People/Process/Data/Technology) — shown in Report header chip + PDF
- `bottleneck_pillar` — dedicated Bottleneck section
- `management_commitment` (Low/Medium/High) — badge in Report + PDF rating line
- `management_commitment_assessment` — narrative
- `governance_observations` per pillar + `governance_assessment`
- `decision_vulnerability_ratings.{discontinuation,new_launch,product_change,portfolio_investment}` — 4-card risk grid in UI + table in PDF
- `decision_vulnerability` — narrative
- `key_findings`, `critical_gaps`
- `roadmap.{immediate,short_term,strategic}` — each with `actions`, `pillar_focus`, `governance_milestone`, `management_required` (or legacy `management_commitment`), `expected_gain`, `timeframe`
- `benchmark_context`, `consultant_note`, `closing_statement`

## Implemented (2026-04-20)
- JWT Auth (localStorage Bearer tokens, cross-domain-compatible)
- HashRouter (production reloads work)
- Dashboard + PPDT score cards + company CRUD
- Full AI chat + Quick assessment
- **New prompt (Hannila PPDT, 5 turns, auto-emit)**
- **Dual-score Report page** — Equal-Weighted primary + Contextual secondary side-by-side
- **Business Model + Strategic Priority** context chips (header)
- **Bottleneck Pillar** dedicated section
- **Management Commitment** Low/Med/High badge
- **Decision-Type Vulnerability** 4-card risk grid
- Updated PDF with all new sections (dual score, bottleneck, management rating, decision ratings table)
- Redesigned inline-SVG LogoMark (gold pulse on deep navy tile)
- Admin panel with CSV export + PDF download
- Refactored backend into `pdf_builder.py` + `chat_service.py`
- Refactored large React components (ReportPage, AssessmentChatPage, AdminPage)
- **Assessments Dashboard card grid (2026-04-20)** — converted `AssessmentsPage.jsx` table to a polished 1/2/3-column glass card grid with score ring + level name, respondent/role row, date row, status badge, and gold-hover Download PDF action
- **Dashboard Recent Assessments redesign (2026-04-20)** — converted the table into compact card rows with company icon tile, status badge, score, and chevron affordance
- **Report Page full redesign (2026-04-20)** — new 13-section numbered layout (01 Portfolio Context → 13 Benchmark & Consultant Note). New components: `PortfolioContext.jsx` (company card with industry, size, business model, active products, strategic priority, respondent) and `AssessmentReliability.jsx` (High/Med/Low confidence badge with 3 heuristic factors: data availability, respondent scope, answer clarity). ReportHeader slimmed (PortfolioContext now owns metadata). Section labels use 01/02/03 mono-numerals with Outfit titles + italic subtitles.
- **LLM stuck-in-progress fix (2026-04-20)** — root cause: LLM ran out of `max_tokens` mid-JSON-emission, leaving truncated JSON that the backend couldn't parse. Fixes:
  - `chat_service.py` rewritten for **dual-path LLM client**: direct `anthropic` SDK when `ANTHROPIC_API_KEY` is set (production / Render), fallback to `emergentintegrations` + `EMERGENT_LLM_KEY` when not (preview).
  - `max_tokens` bumped from 8096 → **16000** so the full prose report + JSON fits.
  - Tolerant `extract_report_json` — now handles fenced, untagged-fenced, and un-fenced JSON via brace-balanced scan.
  - New `POST /api/assessments/{id}/regenerate-report` endpoint: first tries cheap salvage by re-parsing the last assistant message, then falls back to a JSON-only LLM follow-up using existing chat history.
  - "Report Not Ready" page now has a **Regenerate Report** button that calls this endpoint.

## Testing
- `backend/tests/test_completion_pipeline.py` — synthetic pipeline test (parser → DB → PDF). All 7 checks pass. ✅
- `backend/tests/test_trimmed_prompt_e2e.py` / `test_completion_e2e_clear.py` — real-LLM E2E tests. Deferred pending LLM budget top-up.
- `backend/tests/test_completion_flow_e2e.py` — ambiguous-answer E2E. Deferred (budget).

## Open / Backlog
- P1: Real-LLM E2E verification of auto-emission after Turn 5 (pending Emergent LLM Key budget top-up).
- P2: Email notifications on completion (Resend/SendGrid).
- P2: Advanced analytics / benchmarking across companies.
- P3: Revisit token storage (localStorage → httpOnly cookies) once CORS supports it.
- P3: Admin panel could show new fields (`business_model`, `management_commitment`) in the full-assessments table.

## Known Issue (recurring)
Testing agent has historically replaced `from emergentintegrations.llm.chat import ...` with direct `import anthropic` in `chat_service.py` — ALWAYS check after running testing agent and revert if needed. App uses Emergent Universal Key, not a raw Anthropic SDK key.
