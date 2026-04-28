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
- **PDF report — 13-section mirror (2026-04-20)** — `pdf_builder.py` rewritten to mirror the web report's numbered 13-section order. New helpers: `build_section_label` (numbered gold "01" label + italic subtitle + thin gold rule), `build_portfolio_context` (expanded company card with size/active products/strategic priority), `build_pillar_maturity_levels` (Hannila L1–L5 ladder + per-pillar interpretation table), `build_assessment_reliability` (High/Med/Low confidence badge + Signal/Tone/Detail factors table with heuristic fallback). Methodology blurb added to Weighted Score Calculation. All old inline section titles removed (numbered labels own them now). Verified via rendered PDF pages 1 + 3.
- **PDF report — professional layout pass (2026-04-20)** — major readability upgrade for management-level delivery:
  - Added branded **cover page** (`build_cover_page`): navy banner with brand, "PREPARED FOR" card (company + industry), centered maturity badge (overall score + level name), report date + respondent footer, confidentiality line.
  - Grouped the 13 sections into **8 per-page clusters** with `PageBreak` between each group so each card gets room to breathe.
  - Replaced plain string cells with `Paragraph`-wrapping cells throughout (Dimension Scores, Pillar Maturity interpretations, Reliability factors) — no more truncated "..." or column-bleed.
  - Removed the 60-char `summary` truncation and 140-char `interpretation` truncation that were causing mid-sentence cuts.
  - Added `_derive_level_name` fallback so the cover-page and overall-score cards never show "N/A" for level.
  - Added `_page_decoration` onLaterPages canvas callback — slim gold rule + brand + page-number footer on every content page (cover excluded).
  - Verified via rendered PDF: cover (page 1), context+maturity (page 2), ladder (page 3), dimension-scores with full summaries (page 4). 9 pages total, no overlaps.
- **PDF report — section-level polish + Academic References (2026-04-20)** — addressed specific user feedback:
  - **Section 02 Overall Maturity dual-score card** rebuilt as a stacked `Table` per column so the 24pt score number no longer overlaps the "Managed" level name or the descriptor line (old bug: single Paragraph with fixed `leading=13` collided with `<font size="22">`). Same fix applied to the cover-page 52pt headline badge.
  - **Section 11 Key Findings** and **Critical Capability Gaps** now each get a dedicated page with a hard `PageBreak` between them. The Gaps page re-renders a "(continued)" header so the reader keeps context.
  - **Section 10 Decision-Type Vulnerability** now also gets its own page (previously grouped with Findings).
  - **New Section 14 — Academic Framework & References** on a dedicated final page: 6 APA-style numbered references (Hannila Vierimaa Salonen 2026; Hannila Kuula Härkönen Haapasalo 2022; Hannila Härkönen Haapasalo Muhos 2022; Hannila Härkönen Haapasalo 2020; Hannila 2019; Wings Härkönen 2023) + grey-boxed italic attribution note crediting Shalitha Samarakoon and the Product Wellbeing research programme.
  - `build_pdf_closing` rewritten as the gold-bordered callout block with the exact academic closing wording + contact email + confidentiality line.
  - PDF grew to 12 pages (cover + 10 content + references), no overlaps, each major section gets its own breathing room.
- **PPDT System Prompt v2 (2026-04-20)** — replaced the LLM's `PPDT_SYSTEM_PROMPT` with the new consultant-grade spec from the user:
  - **Framework attribution** updated: operationalises the **Product Wellbeing framework** via Hannila / Härkönen / Haapasalo doctoral research (no more "University of Oulu" ownership claims).
  - **Multilingual opener** — every conversation begins with "Welcome / Tervetuloa / Välkommen" and locks into English / Finnish / Swedish for the entire session (including pillar-name translations Ihmiset/Prosessit/Data/Teknologia for FI and Människor/Processer/Data/Teknologi for SE).
  - **Exact 5-level maturity names**: AD HOC · DEVELOPING · DEFINED · MANAGED · PREDICTIVE (no paraphrasing).
  - **Equal-weighted scoring only** (25% × 4) — contextual / business-model weights explicitly prohibited pending empirical validation.
  - **DATA-FIRST rule**: Data < 3.0 is a critical blocker regardless of other pillars.
  - **Bottleneck rule**: if lowest pillar is 1.0+ below overall, narrative is capped at bottleneck level.
  - **4-phase conversation flow**: Context (5–6 Qs) → Pillar Assessment (2–3 per pillar) → Governance Probe (if any pillar ≥ 3.0) → Confirm & Close.
  - **Fast Screening Mode** opt-in (8–12 Qs, traffic-light output, no full scored report).
  - **Strict guardrails** (9 explicit "never do" rules: no tool-name shortcuts, no pure-positive reports, no custom weights, etc.).
  - **Question formatting rule** — numbered questions must stay on a single line (`1. **Label:** text`) to prevent the broken-rendering bug we fixed in chat.
  - **Emission contract preserved**: after Phase 4 the LLM still emits the same ```json block the backend parses (`ready_for_report: true`, scores, level_names, roadmap, assessment_reliability, etc.) — so all downstream logic (status-flip, PDF generation, report page) continues to work unchanged.
- **P1/P2/P3 polish pass (2026-04-20)**:
  - **P1 — New Company form**: added `company_size` and `active_products` fields to the Pydantic models (`CompanyCreate`, `CompanyResponse`), the POST `/companies` insert doc, the GET projection, and the React form (side-by-side grid, glass-input theme preserved). Assessment docs now snapshot these fields from their parent company at creation time so the PDF cover page + Report PortfolioContext populate automatically.
  - **P2 — "Optimising" → "Predictive"**: renamed in `scoring.js` (web level-name map), `constants.js` (maturity-ladder description), `server.py` (backend scoring map), `pdf_builder.py` (ladder + `_derive_level_name` fallback) to match the v2 system prompt's exact five level names: Ad Hoc · Developing · Defined · Managed · Predictive.
  - **P3 — Table of Contents page**: new `build_toc_page` renders after the cover with all 14 entries (gold numerals · navy titles · italic grey subtitles · right-aligned SECTION marker · hairline dividers). Fixed a latent double-`PageBreak` bug in the cover that was producing a blank page. PDF now renders 13 pages, no blanks, cover → TOC → Sections 01–14 with page-number footer starting from content.
- **Final-report streaming progress indicator (2026-04-20)** — new `FinalReportIndicator.jsx` that replaces the generic "Thinking" dots when the user submits the likely-final turn (≥10 messages). Shows a shimmer gradient bar, rotating stage labels (Synthesising… → Scoring pillars… → Identifying bottleneck… → Drafting roadmap… → Finalising consultant's note…), elapsed-seconds counter, and a subtle "taking longer than usual" hint after 60s. New `progress-sweep` keyframe in `index.css`. Paired with the Regenerate button, a token-exhaustion / network hiccup now looks visually distinct from a real completion.

## Testing
- `backend/tests/test_completion_pipeline.py` — synthetic pipeline test (parser → DB → PDF). All 7 checks pass. ✅
- `backend/tests/test_trimmed_prompt_e2e.py` / `test_completion_e2e_clear.py` — real-LLM E2E tests. Deferred pending LLM budget top-up.
- `backend/tests/test_completion_flow_e2e.py` — ambiguous-answer E2E. Deferred (budget).

## Premium Navy + Gold Theme + Report v2 (2026-04-28)
Major theme overhaul to match the user's premium, paid-tool spec across the **entire** product (landing, internal app, and the standalone HTML report).

### Design tokens (everywhere)
- `--navy: #0C1B2A` (primary dark) · `--navy-mid: #162333` (cards on dark) · `--navy-deep: #091622` (recessed)
- `--gold: #C9A84C` (accent) · `--gold-soft: #F7F0DC` · `--gold-mid: #E8D49A` · `--gold-deep: #A88A2E`
- Maturity colours per spec: L1 `#C0392B` · L2 `#D4850A` · L3 `#B8860B` · L4 `#27AE60` · L5 `#1A5276`
- Primary CTA: navy bg + gold text (verified rgb(12,27,42) + rgb(201,168,76)) — pill, premium shadow
- Cards: white bg + 1px `#E2E8F0` border + 3px gold top border + 16px radius
- Dropdown popover: opaque `#162333` (HSL 216 42% 14%) — fixes dropdown transparency issue

### HTML Report (`portfoliohealth-report.html`) — major redesign
- **R1 Cover redesigned for premium readability** — gold accent stripe down the left edge, gold-bordered score panel on the right, ample whitespace, pill-style "Bottleneck-capped" tag, dedicated dark-strip pillar tile band, tag pill + meta line + duration chip. Score numbers always rendered in gold (per chosen option ii); maturity-level pill below carries the semantic colour.
- **Removed 3 charts**: C1 KPI tiles, C2 Gauge SVG, C3 Maturity Journey track, C5 PPDT Radar. Kept: C4 Bar (full-width), C6 Capability Matrix, C7 Roadmap (rebuilt), C8 Benchmark, C9 Confidence, C10 What-If.
- **C7 Roadmap rebuilt** — replaced the broken Gantt (overlapping markers, dashed trajectory, axis labels colliding) with a clean 3-column phase board: numbered circle (red/gold/green), phase tag, title, duration window, bulleted actions, divider, projected score with green delta badge.
- All blue/glass tokens replaced with navy/gold; `--blue` aliased to `--gold` so legacy references keep working.

### Landing page (`LandingPage.jsx` + `landing.css`)
- Full token swap to navy/gold premium palette.
- Hero accent word now in `--gold-deep`; meta-row clock icon in gold-deep.
- All 4-pillar cards on navy section now show gold badges; bottleneck callout uses gold border-left.
- Bottom CTA section now uses navy-mid → navy gradient with a gold radial glow + gold CTA button (gold bg, navy text — for highest contrast in the dark section).
- Footer uses gold accents; cite labels in gold-deep.
- `.ph-glass-card` now white card with 3px gold top border and `--border` outline (no more glass blur on light bg).

### Internal app (`index.css`)
- `--background` updated to `#0C1B2A` (per spec, was `#0A1628`).
- Shadcn HSL tokens updated: `--background: 211 56% 11%` · `--card`/`--popover: 216 42% 14%` (= `#162333` opaque, eliminates transparent dropdown issue) · `--border` switched to gold @ 0.10 alpha · `--destructive` recoloured to spec red `#C0392B` · `--success` & `--warning` realigned to spec.
- Login/Register page background hardcoded `#0A1628` updated to `#0C1B2A`.
- All chat / dashboard / report / admin / login pages automatically pick up the new tokens via the existing `bg-background` / `bg-card` / `bg-popover` references — no layout rewrites.

### Verified
- Backend report endpoint still returns 200 with company name, gold score, hydrated tiles, 3-column roadmap with 3 actions per phase.
- Zero console errors after gauge/radar/track/Gantt JS removal (each renderer already had `if(!el) return;` guards).
- Computed CTA style: `background-color: rgb(12, 27, 42); color: rgb(201, 168, 76);` ✅
Two self-contained, brand-consistent HTML files generated outside the React app, per user's 5-Block spec (design system + dashboard charts + report layout). No external dependencies beyond Google Fonts (Inter). Inline SVG / Vanilla JS Canvas only — no charting libraries.

- **`/app/portfoliohealth-site.html`** (1,043 lines) — Marketing site (single-file SPA, Home + Theory tabs).
- **`/app/portfoliohealth-report.html`** (1,950+ lines) — Standalone Assessment Report Template with all R1–R10 sections + 10 dashboard charts (KPI tiles, gauge SVG, maturity track, bar chart, radar, capability matrix, Gantt with stepped trajectory, benchmark, confidence bars, what-if simulator). Editable `window.REPORT_DATA` drives all sections. Includes hydration script that rewrites R1 cover (company, meta, score, pillar tiles), R5 overall calc, R6 bottleneck visibility from REPORT_DATA so the same template can be served per-assessment.

### Backend (P0 — wired up)
- **NEW** `GET /api/assessments/{id}/report.html` (`?download=1` to force download). Reads the static template, deep-replaces `window.REPORT_DATA` with the assessment-specific payload via `_build_report_data()`, also rewrites the `<title>` with company + date.
- New module `/app/backend/html_report.py` builds the REPORT_DATA shape: maps assessment.report → scores/levels/bottleneck/evidence/confidence/roadmap; cleans up "LEVEL 3: DEFINED" → "DEFINED" prefixes; computes bottleneck-capped flag; projects Phase-1 score; falls back to safe defaults when fields are missing.
- `_TEMPLATE_CACHE` caches the file in memory for performance.
- Verified end-to-end against a real Meridian Controls assessment: title shows the company, cover hydrates correctly (Meridian Controls · Industrial Equipment · STD · Director · 2026-04-20 · score 2.4/5.0 Developing), 4 pillar tiles per real scores (P 2.0 / Pr 1.5 / D 3.0 / T 3.0), overall calc reflects pillar values, all 10 charts render zero-error, R6 bottleneck-capped panel shows/hides based on data.

### Frontend (P0)
- `ChatHeader.jsx` — when assessment status is `completed`, header shows three actions: HTML (opens interactive HTML report in new tab via Blob URL), PDF (downloads the PDF), View Report (existing dashboard).
- `ReportHeader.jsx` — same HTML + PDF buttons on the dashboard report page header.

### Website Revamp (P1 — done)
Applied the Block 1/2/3 design system to the public-facing site. The internal app pages (chat, companies, admin, login) keep their existing dark-navy theme — design tokens are scoped via `.ph-site` so nothing else is affected.

- **NEW** `/app/frontend/src/components/landing/landing.css` — full Block 1 design system as scoped CSS variables + component classes (`.ph-glass-card`, `.ph-dark-card`, `.ph-btn-primary`, `.ph-btn-secondary`, `.ph-section-label`, `.ph-section-footer`, `.ph-hero-badge`, `.ph-pulse-dot`, `.ph-level-pill`, `.ph-animate-in`, `.ph-hero-bg`, `.ph-nav`, etc.).
- **REWRITTEN** `/app/frontend/src/pages/LandingPage.jsx` — Block 2 (Home: H1 hero, H2 What You Receive, H3 Four Pillars on navy, H4 Maturity Levels with 5-step track, H5 How It Works, H6 CTA) and Block 3 (Theory: T1 hero, T2 What This Measures, T3 Academic Foundation on navy, T4 Research Gap, T5 Decision Impact, T6 Thesis Contribution, T7 Bottom CTA) plus shared footer with citation strip + disclaimer. Tab switching via React state. All Lucide icons (no emoji). All copy follows the spec verbatim — never "Product Wellbeing", never "quick assessment", always "Full Assessment · 45–60 minutes".

## Open / Backlog
- P1: Real-LLM E2E verification of auto-emission after Turn 5 (pending Emergent LLM Key budget top-up).
- P1: Hydration could expand to also rewrite R2 callout/bullets, R4 evidence, R7 roadmap actions, R8 decision impact when those exist on `assessment.report` — currently they remain static narrative from the template. Today's hydration covers R1, R5, R6 (the data-driven sections); narrative sections still show the Northpine demo content unless future LLM output populates new keys.
- P2: Email notifications on completion (Resend/SendGrid).
- P2: Advanced analytics / benchmarking dashboard across all companies.
- P3: Revisit token storage (localStorage → httpOnly cookies) once CORS supports it.

## Known Issue (recurring)
Testing agent has historically replaced `from emergentintegrations.llm.chat import ...` with direct `import anthropic` in `chat_service.py` — ALWAYS check after running testing agent and revert if needed. App uses Emergent Universal Key, not a raw Anthropic SDK key.
