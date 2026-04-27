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
- **Final-report streaming progress indicator (2026-04-20)** — new `FinalReportIndicator.jsx` that replaces the generic "Thinking" dots when the user submits the likely-final turn (≥10 messages). Shows a shimmer gradient bar, rotating stage labels (Synthesising… → Scoring pillars… → Identifying bottleneck… → Drafting roadmap… → Finalising consultant's note…), elapsed-seconds counter, and a subtle "taking longer than usual" hint after 60s. New `progress-sweep` keyframe in `index.css`. Paired with the Regenerate button, a token-exhaustion / network hiccup now looks visually distinct from a real completion.

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
