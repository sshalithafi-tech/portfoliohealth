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

## Premium Report Consolidation (2026-04-28 — current session)
User feedback: the standalone HTML report alongside the React web report was confusing. Action: the premium Navy+Gold layout was ported directly into `ReportPage.jsx`, the standalone HTML report and its endpoint were **deleted**, and the "View HTML" buttons were removed from `ChatHeader` and `ReportHeader`.

### Changes
- **NEW** `/app/frontend/src/lib/reportData.js` — JS port of the backend `_build_report_data` helper. Computes scores/levels/bottleneck/evidence/confidence/roadmap from `assessment.report` so the React report is fully self-contained.
- **NEW** `/app/frontend/src/components/report/premium.css` — scoped (`.ph-report`) light "consultant document" theme with all R1–R10 styles ported from the deleted HTML template (R1 navy cover with gold accent stripe + gold score panel + 4-pillar dark strip · R2 executive summary · R3 organisation profile · R4 pillar cards with score bars + L→L+1 gap callout · R5 navy calc block with monospace breakdown · R6 red bottleneck callout · R7 3-column roadmap board with phase numbers + outcomes · R8 decision impact 3-tier · R9 bar/benchmark/confidence charts · R10 academic foundation grid + thesis pill).
- **REWRITTEN** `/app/frontend/src/pages/ReportPage.jsx` (~720 lines) — full premium light report with all 10 sections, replacing the previous 13-numbered-section dark layout. Wrapped in white rounded container (radius 20px, deep shadow) so it sits as a "document" inside the dark app shell. Backed by the new `buildReportData` helper.
- **REMOVED** standalone HTML report endpoint `GET /api/assessments/{id}/report.html` from `server.py`.
- **DELETED** `/app/backend/html_report.py`, `/app/portfoliohealth-report.html`, `/app/frontend/src/components/report/ReportHeader.jsx` (no longer used).
- **CLEANED** `ChatHeader.jsx` — removed `openHtml` handler + "HTML" button + `ExternalLink` icon import.
- **CLEANED** `LandingPage.jsx` — removed the 3 stat cards (Peer-Reviewed / Doctoral Work / Empirical Study) from the Theory page hero.

### Verified via screenshot
- Premium R1 cover renders with navy bg, gold "2.4/5.0", "Developing" pill, 4 pillar tiles with Process (1.5) shown as bottleneck with red border.
- R4 pillar cards correctly colour-code by maturity level (red L1, gold L2/L3, green L4, navy L5).
- R5 calc block + R7 roadmap board (red/gold/green numbered phases) + R8 decision impact + R9 bar+benchmark+confidence + R10 academic citations all render with real Meridian Controls data.
- Light report sits cleanly inside dark app shell with rounded edges and shadow. Toolbar (Back · View Chat · Export PDF) remains in the dark theme above.

## Internal App Theme Unification (2026-04-28 — current session)
User feedback: "the dashboard and the rest still have that old navy theme — change all to the new theme as the home page". Action: updated the shared design tokens and component classes in `index.css` so every internal page (Dashboard, Assessments, Companies, Chat, Admin) automatically inherits the same premium Navy+Gold consultant aesthetic as the public home page.

### Changes
- **`index.css` shared classes rewritten** to mirror `landing.ph-dark-card` / `ph-btn-primary`:
  - `.glass-surface` / `.glass-surface-highlight` / `.glass-card` → solid `#162333` background with gold-tinted borders (`rgba(201,168,76,0.14–0.32)`), no more ghostly `rgba(255,255,255,0.03)` blur surfaces.
  - `.glass-card` now has a 3px gold top-border + lift-on-hover with gold accent — identical look to the home page's white cards but on dark surface.
  - `.btn-liquid` (primary CTA) → solid bright gold `#C9A84C` on navy text — matches the home-page hero CTA exactly.
  - `.btn-glass` (secondary) → gold-tinted surface with gold-bordered hover state.
  - `.glass-input` → navy input with gold focus ring.
  - `.chat-message-assistant` / `.chat-message-user` → navy/gold solid bubbles instead of white-alpha glass.
  - Killed the noisy `liquid-blob` background animations; replaced with subtle gold radial-gradient ambience.
- **Sidebar (`Layout.jsx`) active state** → pure gold pill (`bg-[#C9A84C]/12`, gold border, inset gold glow) instead of the previous blue/gold gradient mix.

### Verified via screenshot
- Dashboard cards, stat tiles, Recent Assessments rows, Quick Check / Companies / Assessments tiles, sidebar active state, "New Assessment" CTA — all now mirror the premium home-page aesthetic. No blue accents remain.

## Internal App Light-Theme Flip (2026-04-28 — current session)
User feedback: "the dashboard still has navy bg, chat looks ugly during assessment — I want the whole system like the front page, white background, premium feel". Action: flipped the entire internal app from dark navy to the same light Navy+Gold theme as the public landing page.

### Changes
- **`index.css` rewritten** — `:root` and shadcn HSL tokens flipped to light: `--background: #FFFFFF`, `--foreground: #0C1B2A` navy, `--card: #FFFFFF`, `--muted-foreground: #4A5568` slate, `--border: #E2E8F0`. Body bg is now white. Component classes:
  - `glass-surface` / `glass-surface-highlight` / `glass-heavy` → solid white with `#E2E8F0` borders
  - `glass-card` → white with 3px gold top border (matches landing `.ph-glass-card`)
  - `btn-liquid` (primary CTA) → solid navy `#0C1B2A` with gold `#C9A84C` text (matches landing `.ph-btn-primary`)
  - `btn-glass` (secondary) → white with light border, gold-soft hover
  - `glass-input` → white with gold focus ring
  - `chat-message-user` → solid navy bubble with white text
  - `chat-message-assistant` → white card with 3px gold left border
  - Killed all dark `liquid-blob` animations; replaced with subtle gold-on-white radial glows
  - Scrollbar reskinned to navy-tint
- **`Layout.jsx` rewritten** — sidebar is now white with gold-soft active pill, navy text, light borders. Mobile header white. Footer light gray with navy text.
- **`LoginPage.jsx` & `RegisterPage.jsx` rewritten** — both panes are now white with soft gold ambient bloom on the left. Navy CTA with gold text. Light error banners (`bg-red-50` / `border-red-200`).
- **`ChatMessages.jsx`** — UserBubble switched to white-on-navy text, AssistantBubble switched to navy-on-white prose, code/pre backgrounds light gray, ClosingCard switched to gold-soft gradient with navy text.
- **`ChatHeader.jsx`** (already light from auto-migration) — back button hover updated.
- **`FinalReportIndicator.jsx`** — light gold-cream bg with navy text.
- **`AssessmentChatPage.jsx`** — page wrapper bg-white, loading spinner re-themed.
- **`PhaseIndicator.jsx`** — connector lines updated for white bg visibility.
- **`ReportPage.jsx`** toolbar — back button + headings use navy/slate.
- **Bulk migration** — programmatic regex pass over 28 files in `pages/`, `components/admin/`, `components/chat/`, `components/companies/`, `components/dashboard/`, `components/assessments/`, `components/report/` → all `text-white/X` → slate/navy, `bg-white/[0.0X]` → `bg-[#F8F9FA]`, `border-white/[0.0X]` → `border-[#E2E8F0]`.

### Verified via screenshot
- Login, Dashboard, Assessments, Companies, Chat (active assessment), Report — all rendering as a clean white app with gold accents and navy CTAs. Identical premium feel to the public landing page. Lint passes across `/app/frontend/src/`.

## Cool Off-White Theme + Premium Stepper (2026-04-28 — current session)
User feedback: ivory cream looked ugly; pure white looked too plain. Picked option (b) **cool off-white (Linear/Vercel/Stripe SaaS premium)**. Also fixed the chat phase indicator which was visually broken and didn't reflect the actual assessment status.

### Changes
- **Palette flipped to cool off-white** in `index.css`:
  - `--paper: #F7F8FA` body (was `#F5F1E8` ivory) · `--surface: #FFFFFF` cards
  - `--border-soft: #E5E7EB` cool gray (was `#E8E2D2` warm beige)
  - `--text-secondary: #4B5563`, `--text-muted: #6B7280`
  - Removed paper-grain SVG noise overlay; replaced with subtle gold + violet-blue radial blooms
  - Refined shadows tinted with `rgba(15, 23, 42, ...)` for crisper depth
  - Shadcn HSL tokens updated to match
- **Layout sidebar** hex codes migrated from warm beige (`#E8E2D2`/`#FAF8F1`) to cool gray (`#E5E7EB`/`#F7F8FA`).
- **`PhaseIndicator.jsx` rewritten** as a premium segmented stepper:
  - Reduced from 8 → 7 phases (combined "Decision Types" + "Benchmark" into single "Governance" matching the protocol)
  - Numbered circles with gold gradient progress bar between them
  - Active step has white circle with gold border + ping animation + 4px gold halo
  - Completed steps show gold circle with check icon
  - Eyebrow shows "Assessment Progress · 3 / 7 · People" so user always knows where they are
- **`AssessmentChatPage.jsx` phase logic fixed**:
  - `phaseFromMessageCount` rewritten to match Hannila's real 6-turn protocol (~12 messages):
    msgs 1: welcome · 2-3: people · 4-5: process · 6-7: data · 8-9: technology · 10-11: governance · 12+: report
  - On fetch, phase is now derived from `chat_history.length` directly (truthful state), not from a possibly stale `current_phase` field
  - When `status === "completed"` the phase jumps straight to "Report"

### Verified via screenshot
- Dashboard, Chat (with new stepper showing Welcome active + remaining steps numbered), Report all render with cool off-white backdrop, white cards with subtle shadows, and gold accents that read precisely against the cool-gray paper.

## Cyan Accent Pivot + Benchmarks Page (2026-04-28 — current session)
User feedback: ivory looked ugly; pure white too plain → went **cool off-white** (Linear/Vercel SaaS feel). Then "the gold doesn't feel SaaS enough" → switched primary accent from gold to **deep cyan `#0891B2`** while keeping gold ONLY for the consultant Report doc (R1 cover / score panels) where it adds the premium consultant feel.

### Changes
- **Cyan accent introduced** in `index.css`: `--accent #0891B2`, `--accent-deep #0E7490`, `--accent-mid #67E8F9`, `--accent-soft #ECFEFF`. Gold variables retained for the Report only.
- **Shared classes rewritten** to use cyan: `.glass-card` 3px top border, `.btn-liquid` (navy CTA with cyan text), `.btn-glass` hover, `.glass-input` focus halo, `.eyebrow`, `.gold-rule`, `.navy-panel` accent, `.gold-corner`, scrollbar hover, selection, chat assistant left-border, phase badges. `pulse-glow` keyframe re-tinted cyan.
- **22 internal files migrated** programmatically — gold hex codes (`#C9A84C`/`#A88A2E`/`#E8D49A`/`#F7F0DC`/etc) and matching `rgba(201,168,76,*)` swapped to cyan equivalents. Skipped: `components/report/*`, `pages/ReportPage.jsx`, `LandingPage.jsx`, `lib/reportData.js`, `premium.css` — these intentionally keep gold for the report doc.
- **LogoMark redesigned** — clean navy tile with smooth cyan ascending curve (cubic Bezier), peak vertex with soft glow, anchored base dot. Modern SaaS aesthetic, no more crowded zigzag pulse + corner bracket.
- **Logo is clickable** — wrapped LogoMark in `<Link to="/dashboard">` in both desktop sidebar (`data-testid="sidebar-logo-home"`) and mobile header (`data-testid="mobile-logo-home"`). Hover scales the logo and tints the text cyan.
- **NEW Benchmarks page** (`/benchmarks`) — Lite cross-company benchmarking:
  - Header stat tiles: Cohort Size · Avg Overall · Strongest Pillar · Most Common Bottleneck
  - Per-pillar distribution row with cyan gradient bar showing cohort avg + each company as a dot positioned along the 1–5 scale (hover for score tooltip)
  - "Your Companies vs Cohort" section — each row is a clickable card with mini-bars per pillar (bottleneck shown red), overall score, and ±delta vs cohort badge (green positive / red negative)
  - Empty state with friendly CTA when no completed assessments yet
- **Backend `/api/benchmarks` endpoint added** — aggregates `cohort_avg`, `distribution`, `bottleneck_counts`, `common_bottleneck`, `strongest/weakest_pillar`, plus per-assessment summaries scoped to the current user. Tested: returns 3 assessments / cohort_avg `{people:2.5, process:2.33, data:2.67, technology:3.0, overall:2.63}` for the user.
- **Sidebar nav** — added "Benchmarks" item with `BarChart3` icon between Companies and Admin.
- **Report toolbar** — Print, Export PDF, View Chat buttons all verified working. Print triggers `window.print()` with the A4 page-break CSS already in `premium.css`.
- **Account fix** — reset `sshalitha.fi@gmail.com` password to `Welcome2026!` (was invalidated during my earlier screenshot testing). Updated `/app/memory/test_credentials.md`.

### Verified via screenshot
- Login → Dashboard → Benchmarks (with full cohort + pillar dots + comparison rows) → Report all render with the cool off-white + cyan aesthetic. Logo click → dashboard works. Report still gold-accented (intentional consultant feel).

## Report Redesign + Home Page Cyan + Pillar Accordion (2026-04-28 — current session)
User feedback in two waves:
1. "PPDT Maturity Assessment looks ugly, long pillar cards aren't premium — make them clickable to read more"
2. "Home page logo broken + still missing cyan accent across home & some pages"

### Changes
- **R1 Cover refined** in `ReportPage.jsx` + `premium.css`:
  - Single-line eyebrow ("PPDT Maturity Assessment", was wrapping to 2 lines as "...· Full Report")
  - Tighter proportions: padding `56/64/36`, score panel reduced from 72→64px and centered, level pill upper-cased
  - Gold radial bloom moved to top-right corner
  - 4-pillar dark strip: smaller tiles (badge 26px, score 26px), bottleneck mark inline next to label
- **R4 Pillar Cards → Accordion** in `ReportPage.jsx` + `premium.css`:
  - Click anywhere on the card header to expand/collapse (chevron rotates 180°)
  - Default: bottleneck pillar open; all others collapsed
  - Collapsed state shows a quote-styled summary line + "CLICK TO READ FULL EVIDENCE →" hint
  - Expanded state shows full evidence bullets + maturity-gap callout (L→L+1) + footer citation
  - Smooth grid-template-rows animation (no JS height calc)
  - Bottleneck card has subtle red gradient background
  - Score badge now compact pill (18px number + "/ 5.0" suffix)
  - Always-visible compact bar with maturity scale (1–5)
- **Home page logo fixed**: replaced the CSS-only `<div class="ph-logo">PH</div>` with the proper `<LogoMark>` SVG component (now consistent with sidebar). New `.ph-logo-mark` selector adds 36px sizing + box shadow + scale-on-hover.
- **Home page cyan accent applied**: redefined `--gold`, `--gold-soft`, `--gold-mid`, `--gold-deep`, `--blue*`, `--info` tokens **inside `.ph-site` scope** to map directly to the cyan palette (`#0891B2`, `#ECFEFF`, `#67E8F9`, `#0E7490`). One change flips the entire landing page navigation, hero, badges, card top borders, CTAs, "product portfolio" highlight, and footer accents to cyan in lock-step with the rest of the app.
- **Inline `rgba(201,168,76,*)`** references in `landing.css` (18 occurrences in shadows/glows) batch-migrated to `rgba(8,145,178,*)`.

### Verified via screenshot
- Home page: clean cyan logo, cyan "Grounded in peer-reviewed IEM research" pill, cyan "product portfolio" highlight, cyan card top borders, cyan numbered "What you receive" cards.
- Report: refined R1 cover renders with tight typography. R4 People card opens cleanly with full evidence; Process card collapses to a single quote line with cyan-tinted "click to expand" hint.
- Logo click navigates to dashboard from any internal page.

## Report Cyan Migration + R1 Redesign (2026-04-28 — current session)
User feedback (two screenshots): R1 cover looked ugly with "Meridian Controls" wrapping awkwardly to two lines, and the report still used gold accents that didn't match the rest of the SaaS app. Wanted cyan accent applied to the report **but maturity colors (L1–L5) and score colors kept as-is**.

### Changes
- **`premium.css` — gold variables remapped to cyan in `.ph-report` scope only**:
  - `--gold #C9A84C → #0891B2`, `--gold-soft #F7F0DC → #ECFEFF`, `--gold-mid #E8D49A → #67E8F9`, `--gold-deep #A88A2E → #0E7490`
  - **L1–L5 maturity colors UNTOUCHED** (red `#C0392B`, amber `#D4850A`, gold `#B8860B`, green `#27AE60`, deep blue `#1A5276` — these are the traffic-light maturity scale, not brand colors)
  - 25 inline `rgba(201,168,76,*)` references in shadows/glows batch-migrated to `rgba(8,145,178,*)`
- **R1 Cover redesigned** for tighter, premium SaaS proportions:
  - Company title now uses `clamp(30px, 4.4vw, 46px)` so it scales with viewport — "Meridian Controls" fits on one line at any reasonable width
  - `min-width: 0` on left grid column so it can shrink properly
  - Score panel constrained to `min-width 200px / max-width 260px` instead of growing unbounded
  - Score number "2.4" now has a soft cyan glow `text-shadow`
  - Cyan radial bloom moved to top-right corner; left rail uses navy→cyan→transparent gradient
  - Eyebrow pill has bright cyan dot with glow
  - Padding tightened (48/56/32 vs 56/64/36 previously)
- **Pillar tiles** in the dark strip — hover lift, refined typography, smaller badges (24px)
- **`.ph-report` shell** — softened to `border-radius: 16px` + crisp `0 12px 32px rgba(15,23,42,0.10)` shadow (was the ivory's heavy 24px shadow)
- **New responsive breakpoint at 1099px** for tighter padding on mid-size screens; full stack at <900px

### Verified via screenshot (1920×1100 + 1280×900)
- R1 cover: "Meridian Controls" on a single line, cyan eyebrow + score, white "Developing" pill on navy
- R4 pillar accordion: Process bottleneck card opens with **red maturity score badge** correctly preserved (L1 colors untouched), evidence bullets readable
- R2/R3: cyan card top borders, cyan "STD" pill, "Strongest pillar — Data" still has score-3 amber, "Critical bottleneck — Process" still has bottleneck red — maturity colors preserved
- Sidebar gradient rail and `Export PDF` button cyan, consistent with the rest of the app

## Thesis-Aligned Scoring Updates — DBI + Ambiguous Priority Cleanup (2026-05-27 — third pass)
User uploaded the PDF "PPDT Scoring Logic & Business-Model-Contextual Weighting" thesis. I audited every scoring rule against the PDF and made the following changes.

### Audit summary
| PDF rule | Status before | Action |
|---|---|---|
| Equal-weighted = mean of 4 pillars | ✅ matched | no change |
| Contextual = Σ(score × w_i) + boost | ✅ matched | no change |
| Business-model weight matrix (ETO 35/30/20/15, CETO 25/30/25/20, CTO 20/25/30/25, Standard 15/30/35/20, Bulk 10/35/20/35) | ✅ exact | no change |
| Strategic priority +5%/−1.67% with normalisation | ✅ matched | no change |
| `scores.overall == equal_weighted_score` (primary) | ✅ enforced | no change |
| **DBI = pillar with largest gap between contextual and equal-weighted** | ❌ missing | **NEW: implemented** |
| Per-pillar contextual contribution gaps | ❌ missing | **NEW: exposed** |
| Ambiguous priority list ("Portfolio simplification, profitability, complexity, Digital transformation, innovation") | ⚠ had extra `growth` + drifted phrasings | **fixed to exact PDF wording** |

### DBI implementation
Per-pillar gap formula (literal PDF reading):
```
gap_i = (w_i − 0.25) × score_i
∑ gap_i  =  contextual_score − equal_weighted_score
```
The DBI is the pillar with the largest absolute gap. `direction` is `above-baseline` (gap > 0 — pillar contributes more to contextual than equal) or `below-baseline` (gap < 0).

### Files changed
- `/app/backend/chat_service.py`:
  - Added `compute_pillar_contextual_gaps(scores, weights)`
  - Added `compute_decision_bottleneck_index(scores, weights)` → returns `{pillar, gap, direction, gaps_by_pillar}`
  - Tightened `AMBIGUOUS_PRIORITY_TERMS` to exact PDF Table 2 wording
  - `recompute_dual_scores` now writes `pillar_contextual_gaps` and `decision_bottleneck_index` onto the report
- `/app/backend/server.py`:
  - System prompt: replaced the duplicate "STEP 3" label with "STEP 5 — DECISION BOTTLENECK INDEX (DBI)" + full DBI documentation
  - System prompt: aligned ambiguous-priority example wording to PDF Table 2
  - `GET /api/assessments/{id}` now lazily backfills DBI + pillar gaps on read for reports created before this change (in-memory, idempotent)
- `/app/frontend/src/lib/reportData.js`:
  - Passes through `decision_bottleneck_index` and `pillar_contextual_gaps` so the dashboard / report can render them
- NEW: `/app/backend/tests/test_dbi_scoring.py` — 10 unit tests covering the weight matrix, gap formula, DBI selection (both above- and below-baseline), ambiguous-priority guardrails, priority boost, and end-to-end recompute path.

### Verified
- **10/10 new tests pass** + 8/8 existing dual-score tests pass (no regression).
- **Live API check**: `GET /api/assessments/6a1338f66fe46ca1fb55073e` now returns:
  - `decision_bottleneck_index = {pillar: "people", gap: -0.35, direction: "below-baseline", gaps_by_pillar: {...}}`
  - `pillar_contextual_gaps = {people: -0.35, process: 0.225, data: 0.3, technology: -0.175}`
- Ruff clean on `chat_service.py` + `tests/test_dbi_scoring.py`.

## Assessment Dashboard v2 — Hero·Half/Half·Hero (2026-05-27 — second pass)
Iterated on yesterday's 2×2 grid into a more academically grounded, more visually impressive 3-row layout. Same 4-card surface language, sharper hierarchy, theory-numbered labels, executive radar visual.

### Layout
| Row | Card(s) |
|---|---|
| 1 | **Bottleneck** — full-width hero with thick ring gauge + composed 2–3 sentence explanation + risk pills + collective note |
| 2 | **Preconditions** (half) · **Portfolio Decision Impact** (half) |
| 3 | **Portfolio Renewal Radar** — full-width SVG radar (deep teal gradient polygon, severity-colored vertex dots, full legend on the right) |

### Theory grounding
- Preconditions now use Hannila et al. (2020) numbered P1–P5 with theory names + 1-line blurbs + academic footer.
- Portfolio Decision Impact now uses theory-aligned decision names (Discontinuation, New Product Launch, Engineering Change, Capability Investment, Ramp-down / Retirement, Product Family Rationalisation) + footer citing Hannila (2019); Tolonen et al. (2015); Cooper et al. (2001).

### Bottleneck explanation composer
Deterministic 3-sentence builder — never echoes raw AI prose:
1. Definition sentence (pillar-specific, static).
2. Optional "why" sentence pulled from `dimension_summaries` / `pillar_interpretations` / `bottleneck_narrative` / `decision_vulnerability_narrative`, first-letter lowercased so it flows after "because" while preserving acronyms (SAP, BI, ERP…).
3. Consequence sentence (pillar-specific, static).
Total bounded to 360 chars; "why" is dropped first if it overflows so the consequence is always preserved.

### Radar visual
- Hand-rolled inline SVG (no chart library) — `radialGradient` fill, dashed concentric rings labelled LOW / MEDIUM / HIGH, axis spokes, short axis labels (Launch / Change / Investment / Discontinue / Retire / Rationalise) with full names in the right-hand legend.
- Polygon radii driven by the same Decision Impact derivation: Low=0.25 · Medium=0.55 · High=0.92 of `rMax`.
- Overall exposure summary chip ("High overall exposure" / "Moderate overall exposure" / "Contained exposure") derived from the average radius.

### Consistency checks (verified via screenshot @ 1600×1080)
- All four cards left-aligned at 336px, full-width=1224px, half-width=603px (exact match).
- Shared `--bn-critical / warning / good / advanced` severity tokens drive every chip, bar, vertex dot, ring band.
- Shared `bn-card` surface: 16px radius, 22–26px padding, white surface, 1px #E5E7EB border, identical eyebrow + footer styling.

### Files
- Rewrote `/app/frontend/src/components/report/AssessmentDashboard.jsx` (now 530+ lines, modular: `BottleneckCard`, `PreconditionsCard`, `PortfolioDecisionImpactCard`, `PortfolioRenewalRadarCard`, `PortfolioRenewalRadar` SVG, `RingGauge`, `StatusChip`, `SeverityBar`, `CardHead`, `CardFooter`, helpers `composeBottleneckExplanation`, `derivePreconditionStatus`, `deriveDecisionImpact`, `buildSignalCorpus`, `extractFirstSentence`, `truncateInsight`).
- Replaced the dashboard CSS block in `/app/frontend/src/components/report/premium.css` (deleted old `.bn-grid` + `.bn-gov-*`; added `.bn-grid-v2`, `.bn-row--full/half`, `.bn-card--hero`, `.bn-precon-list--theory`, `.bn-precon-num`, `.bn-card-foot`, `.bn-radar-*`, `.bn-dot--*`).
- `/app/backend/pdf_builder.py` intentionally untouched — full narrative still ships in downloads.

## Assessment Dashboard Redesign — 4-Card 2×2 Grid (2026-05-27 — earlier in session)
Replaced the verbose R6 Bottleneck + R8 Decision Impact prose blocks in the consultant report with a compact, scannable **2×2 dashboard** of four visually consistent cards. The PDF export pipeline (`/app/backend/pdf_builder.py`) was intentionally NOT touched — the full-text version still ships in downloads.

### New section layout (Report → between R5 Calculation and R7 Roadmap)
| Row | Left card | Right card |
|---|---|---|
| 1 | **Bottleneck** (ring gauge + insight + risk chips) | **Preconditions** (6-row checklist) |
| 2 | **Portfolio Decision Impact** (6 severity rows) | **PPM Governance Readiness** (4 segmented bars) |

### Files
- New: `/app/frontend/src/components/report/AssessmentDashboard.jsx` (modular: `BottleneckCard`, `PreconditionsCard`, `PortfolioDecisionImpactCard`, `GovernanceReadinessCard`, plus `RingGauge`, `StatusChip`, `SeverityBar` atoms and helpers `extractFirstSentence`, `truncateInsight`, `deriveDecisionImpact`, `derivePreconditionStatus`, `deriveGovernanceReadiness`)
- Edited: `/app/frontend/src/lib/reportData.js` — passes through `pillar_interpretations` and `dimension_summaries`
- Edited: `/app/frontend/src/components/report/premium.css` — `.bn-dashboard`, `.bn-card`, `.bn-chip`, `.bn-sev`, `.bn-ring`, `.bn-precon-*`, `.bn-dec-*`, `.bn-gov-*` token set, plus severity CSS variables (`--bn-critical`, `--bn-warning`, `--bn-good`, `--bn-advanced`)
- Edited: `/app/frontend/src/pages/ReportPage.jsx` — replaced `<R6Bottleneck/>` + `<R8DecisionImpact/>` with `<AssessmentDashboardSection/>` (old components retained for safety but unused)

### Data-handling rule
All AI-generated paragraphs go through a deterministic pipeline before render:
1. `extractFirstSentence` → 2. `truncateInsight(text, 170)` → 3. Pillar-specific fallback if both empty.
The cards never dump raw narrative; they normalise into chips, dots, bars, and ring fills.

### Severity color system (aliased to the global maturity-band palette)
- `--bn-critical: #DC2626` (red) — Critical / Very weak / High impact / Missing / Weak
- `--bn-warning: #F59E0B` (amber) — Moderate / Partial / Medium impact / Emerging
- `--bn-good: #10B981` (green) — Good / Established / Low impact / Met
- `--bn-advanced: #0EA5E9` (sky) — Advanced / Strong (Band 4 maturity)

### Verified
- Screenshot @ 1920×1080: all four cards render side-by-side; Lumivex Photonics report shows Data bottleneck @ 3.0/5 green ring, 3/6 preconditions met (Strategic classification + PPM cadence missing), Portfolio Investment + Product Family Rationalisation flagged High (with red left-bar highlight on the worst), Governance 3/4 established.
- Screenshot @ 420px (mobile): cards collapse to single column; `mobile cards=4` confirms full grid render.
- `data-testid="report-r6"` and `data-testid="report-r8"` confirmed absent in the new render path.
- ESLint clean on both `ReportPage.jsx` and `AssessmentDashboard.jsx`.

## 5-Point Design Polish (2026-05-24)
User requested a precise 5-point design update to unify the dashboard + PDF and complete the premium SaaS polish.

### Spec
1. Primary accent everywhere → **deep teal `#0891B2`** (was `#22D3EE`)
2. Overall maturity score number/suffix **stays `#22D3EE`** (cyan) on web + PDF
3. Pillar/maturity colors driven by **numeric band**, not discrete level index:
   - 1.0–1.4 red `#DC2626` · 1.5–2.4 amber `#F59E0B` · 2.5–3.4 green `#10B981` · 3.5–4.4 sky `#0EA5E9` · 4.5–5.0 emerald `#059669`
4. Text selection highlight → light gray `#E5E7EB`
5. **Remove** "Score Confidence" + "Benchmark Context" cards from the React R9 dashboard view (kept in PDF export)

### Changes
- **`/app/frontend/src/index.css`** — `::selection { background: #E5E7EB; color: var(--navy); }`
- **`/app/frontend/src/components/report/premium.css`**:
  - `--gold #22D3EE → #0891B2` (brand accent), `--gold-mid` `--gold-deep` `--gold-soft` retained
  - `--l1..--l5` palette swapped to new numeric-band colors (red / amber / green / sky / emerald)
  - `.r1-score` & `.r5-score` overridden to `#22D3EE` cyan with matching opacity'd suffix
  - `.r4-score-badge.l3` override removed (default white text now applies on dark-green background)
  - R2 bullet `:nth-child(3) .dot` → `#0891B2` deep teal
- **`/app/frontend/src/lib/reportData.js`** — new `scoreToBand(score)`, `BAND_COLORS`, `BAND_TEXT_COLORS` exports
- **`/app/frontend/src/pages/ReportPage.jsx`**:
  - `lvlClass(level)` → `bandClass(score)` driven by numeric band
  - `R5Calculation` overall score `style={{ color: LEVEL_COLORS[lvl] }}` removed (lets CSS keep it cyan)
  - `BarChart` uses `BAND_COLORS[scoreToBand(p.score)]` per row
  - `R9Dashboard` no longer renders `ConfidenceChart` or `BenchmarkChart` (definitions deleted)
- **`/app/backend/pdf_builder.py`**:
  - `GOLD` constant → `#0891B2` (deep teal); added `SCORE_CYAN = #22D3EE`
  - `BAND_COLORS_HEX`, `score_band()`, `band_color()` helpers added
  - All `#22D3EE` brand-accent literals → `#0891B2` (TOC, section labels, footer rules, ladder, consultant note, page strip)
  - Cover overall score number + EQ-score number → `#22D3EE` cyan to match web
  - `build_pillar_maturity_levels` and `build_dimension_scores_table` now render the Score and Level cells in the band color per pillar

### Verified
- Screenshot R1 cover: bright cyan 2.4 score, deep-teal "Developing" pill, teal eyebrow ✅
- Screenshot R5: cyan 2.4 score on navy panel, dynamic green/amber bar fills, teal "Overall Score" total ✅
- Screenshot R9: only one chart container (Pillar Scores), confidence + benchmark cards absent ✅
- PDF download HTTP 200, 28KB, valid `%PDF-1.4`/`%%EOF`
- PDF page 4 analysis confirms band coloring: People/Process/Tech 2.5 → green, Data 2.0 → amber ✅

## Landing/Auth Polish Pass (2026-07-01 — current session)
User shared 4 zoomed screenshots with attached instructions and asked for direct fixes (no test agent needed):
- **Hero primary CTA contrast fix**: `#home-hero .ph-btn-primary` ("Start Full Assessment") was navy-bg/cyan-text sitting directly on the new dark global background — nearly invisible next to the white "How it works" secondary button. Added scoped override in `landing.css` so the hero primary CTA now renders white-bg/navy-text (matches secondary button's high-contrast treatment) with a bolder shadow to keep primary prominence. Other `.ph-btn-primary` usages (nav, CTA section, theory hero) were left untouched since they already have adequate contrast in their own contexts.
- **Hero stat cards uniform sizing**: added `min-height: 232px` to `.ph-stat-card` (4 Pillars / Dual Score / Full Report) as a fail-safe so all three cards render the same height/width regardless of description text length or animation-timing artifacts (grid already had `align-items:stretch`).
- **Login/Register brand panel**: `BrandPanel` (shared between `LoginPage.jsx` and `RegisterPage.jsx`) changed from `justify-between` (content split top/bottom) to `justify-center` (vertically centered). Added a "← Back to Home" link (`data-testid="brand-panel-home-link"`) top-left of the panel, and made the logo+wordmark clickable (`data-testid="brand-panel-logo-link"`) — both route to `/`.
- **Liquid-glass card readability** (carried over from previous session's fix): verified via live screenshot — `#maturity-levels` and `#how-it-works` liquid-glass cards render dark navy bg with clear white/light-gray text against the shared background image, fully legible. No further change needed.
- Verified via screenshots (desktop 1920px): hero CTAs, stat cards, login page, register page all render correctly. User declined formal testing_agent pass for this round.
- **Animated background (2026-07-01, same session)** — user asked to "animate the background image to match the theme", chose mix of (b) drifting glow + (c) circuit-trace pulses. New `components/landing/AnimatedBgOverlay.jsx` renders on the Home page only, layered between `.ph-global-bg` (static photo) and all content (z-index -1, pointer-events none):
  - `.ph-bg-glow` — two radial cyan gradients, `mix-blend-mode: screen`, `background-position` animated via `ph-glow-drift` keyframes (26s ease-in-out infinite alternate) for a slow drifting light effect.
  - ~~Circuit-trace pulses~~ — **removed in follow-up** (see below).
  - Respects `prefers-reduced-motion: reduce` (animations disabled).
- **Circuit traces → floating dust particles (2026-07-01, follow-up)** — user asked to remove the PCB circuit-trace overlay and replace with glowing floating dust particles instead. `AnimatedBgOverlay.jsx` rewritten: `.ph-bg-circuit` SVG removed entirely; new `.ph-bg-particles` container renders 26 small glowing cyan motes (`ph-particle`, module-level generated configs so positions don't re-randomize on re-render) that float upward with a gentle horizontal sway and fade in/out (`ph-particle-float` keyframes, 14-30s duration, staggered negative delays, per-particle CSS custom properties `--drift-x`/`--rise`/`--particle-opacity`). `ph-glow-drift` kept unchanged. Verified via 2 screenshots 4s apart — particle positions/opacity visibly changed, no console errors, no text-contrast regression.
- **Gold-tint particles + hero stat cards removed (2026-07-01, follow-up 2)** — user asked to (a) mix in a few warm gold-tinted particles and (b) remove the 3 hero stat cards (4 Pillars / Dual Score / Full Report) shown in an uploaded screenshot.
  - `AnimatedBgOverlay.jsx`: every 5th particle (`i % 5 === 0`) now gets a `ph-particle-gold` class; new CSS variant uses a warm gold radial-gradient + glow (`rgba(255,224,158,*)` / `rgba(232,180,90,*)`) instead of cyan, same float animation/timing.
  - `LandingPage.jsx`: removed the entire `.ph-stat-grid` block (3 cards) from the hero; the scoring-disclosure callout now sits directly under the meta-row. Removed the now-unused `ClipboardCheck` icon import (`FileText`/`Target` still used elsewhere).
  - Verified via screenshot: hero renders cleanly without the 3 cards, gold + cyan particles both visible drifting through the background, no console errors.

## Open / Backlog
- P1: Real-LLM E2E verification of auto-emission after Turn 5 (pending Emergent LLM Key budget top-up).
- P1: Hydration could expand to also rewrite R2 callout/bullets, R4 evidence, R7 roadmap actions, R8 decision impact when those exist on `assessment.report` — currently they remain static narrative from the template. Today's hydration covers R1, R5, R6 (the data-driven sections); narrative sections still show the Northpine demo content unless future LLM output populates new keys.
- P2: Email notifications on completion (Resend/SendGrid).
- P2: Advanced analytics / benchmarking dashboard across all companies.
- P3: Revisit token storage (localStorage → httpOnly cookies) once CORS supports it.

## Known Issue (recurring)
Testing agent has historically replaced `from emergentintegrations.llm.chat import ...` with direct `import anthropic` in `chat_service.py` — ALWAYS check after running testing agent and revert if needed. App uses Emergent Universal Key, not a raw Anthropic SDK key.
