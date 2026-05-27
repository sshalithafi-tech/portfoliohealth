# R6 Bottleneck Card — Complete Explainer

> **File:** `frontend/src/components/report/BottleneckSection.jsx`
> **CSS:** `frontend/src/components/report/bottleneck.css`
> **Constants:** `frontend/src/components/report/constants.js`
> **Author note:** Shalitha Samarakoon, Masters Thesis — University of Oulu, IPIC / IEM programme.
> **Framework:** Product Wellbeing™ / PPDT — Hannila, Salonen & Vierimaa (2024)

---

## Overview

The R6 Bottleneck card is the **most theoretically dense card in the report**. It does not simply display a low score — it names the single pillar (People, Process, Data, or Technology) that is acting as the binding constraint on the entire portfolio decision-making system, explains the mechanism by which that constraint operates, and anchors every sentence to peer-reviewed academic evidence.

This document explains what is rendered in each of the five zones, where the data comes from, what logic determines the content, and what academic theory underpins each zone.

---

## Five Render Zones

```
┌─────────────────────────────────────────────────────────┐
│  Zone 1  │  Header: pillar label · score/level pill     │
├─────────────────────────────────────────────────────────┤
│  Zone 2  │  AI narrative paragraph                       │
├────────────────────────┬────────────────────────────────┤
│  Zone 3L               │  Zone 3R                        │
│  What the assessment   │  Why this constrains maturity   │
│  found                 │                                 │
├─────────────┬──────────┴──────────────┬─────────────────┤
│  Zone 4     │  Profit leakage  │  Strategic drift  │  Decision latency  │
├─────────────────────────────────────────────────────────┤
│  Zone 5  │  Academic footer citation                     │
└─────────────────────────────────────────────────────────┘
```

---

## Zone 1 — Header

**Renders:** `AlertTriangle` icon · `"Bottleneck — {Pillar}"` · score pill (`1.5 / 5.0 · Ad Hoc`) · optional `"Score capped"` badge.

**Data source:**
```js
const key   = String(bottleneckPillar).toLowerCase();   // e.g. "data"
const label = PILLAR_LABELS[key];                        // e.g. "Data"
const score = scores[key];                               // e.g. 1.5
const level = levelName(score);                          // e.g. "Ad Hoc"
```

The `bottleneckPillar` prop is set in the parent report page by comparing all four pillar scores and selecting the minimum. The `bottleneckCapped` prop is `true` when `overall_score` was held down to match this pillar's level rather than being the simple average — this is rendered as the "Score capped" badge.

**Theory:** The concept that the weakest pillar caps overall maturity — rather than being averaged away — comes from the **bottleneck principle** in Hannila et al. (2022). The paper demonstrates empirically that PPM capability is a system of interdependent preconditions, not a portfolio of independent scores. A company with Data at Level 1 and Technology at Level 5 cannot act on any of the technology investment; the data precondition must be met first. The card header makes this visible immediately.

---

## Zone 2 — AI Narrative Paragraph

**Renders:** A multi-sentence, assessment-specific paragraph written by the AI during the chat session.

**Data priority chain (from `BottleneckSection.jsx`):**
```js
const narrative =
  report?.bottleneck_narrative ??          // Primary: AI-authored field
  report?.decision_vulnerability ??        // Fallback 1: vulnerability prose
  report?.pillar_interpretations?.[key] ?? // Fallback 2: pillar-specific text
  formulaString;                           // Fallback 3: static computed string
```

**How the AI generates this:** The AI (Claude, via `chat_service.py`) is given the full `PPDT_SYSTEM_PROMPT` from `server.py` which instructs it to classify portfolio decisions by type (Discontinuation, New Launch, Engineering Change, Capability Investment) and rate each as Low / Medium / High / Critical risk based on the user's actual answers. After PHASE 4 ("Confirm & Close"), the AI writes `bottleneck_narrative` as a free-prose synthesis of all four decision types and their risk ratings for this specific organisation.

The AI uses the user's own system names (e.g. Sage, Creo PDM, SAP IBP, Windchill), incident references (e.g. "2022 firmware knowledge loss", "2024 lost bid", "LX-Metrix margin deterioration"), and operational details from the chat to populate this field — making it impossible to confuse with a generic output.

**Theory underpinning the structure:**
- **Decision type classification:** Hannila (2019) doctoral dissertation — specifically the taxonomy of four portfolio decision types: discontinuation, new product launch, change management, and capability investment. Each is treated as a distinct decision with different information requirements and different consequences at each maturity level.
- **Cooper et al. (2001) Stage-Gate trigger:** The `PPDT_SYSTEM_PROMPT` contains **Mandatory Rule 3a** — if `new_launch` is rated "High" or "Critical", the narrative *must* include the verbatim sentence: *"Where new product launch governance is absent or immature, a formal Stage-Gate intake process (Cooper, Edgett & Kleinschmidt, 2001) provides structured go/kill criteria at each development gate, directly addressing Process pillar gaps."* This is why the Cooper citation appears in Assessment 1 (new launch risk was High) but not Assessment 2.
- **"Most Vulnerable Decision" framing:** Comes from Hannila's finding that investment prioritisation is uniquely dangerous at lower maturity levels because its consequences have the longest lag time — misallocation of R&D budget takes years to manifest as missed revenue, whereas a bad discontinuation decision manifests in quarters.
- **Product Wellbeing™ connection:** The narrative answers "what happens to product health when this pillar is missing?" — each decision type failure is a product wellbeing failure. The 2024 lost bid (Assessment 1) and the LX-Metrix six-month lag (Assessment 2) are both real-world product wellbeing consequences named in the narrative.

---

## Zone 3 — Two-Column Findings

### Zone 3L: "What the Assessment Found"

**Data priority chain:**
```js
const foundText =
  report?.dimension_summaries?.[key] ??   // Primary: AI summary of the pillar
  report?.pillar_findings?.[key]?.[0] ??  // Fallback 1
  BN_ROOT_CAUSE_FALLBACK[key] ??          // Fallback 2: static fallback from constants.js
  null;
```

This is the AI's compressed factual summary of what the user described for this pillar — written in present tense, using specific system names and process descriptions. It is the "evidence" sentence: what actually exists (or doesn't) in the organisation.

Examples from real assessments:
- Assessment 1 (Data, 1.5): *"Capability family profitability requires 1 week manual work; cost data project-structured in Sage, cannot aggregate to capability view; BOMs fragmented across Creo PDM, network folders, Excel; no single source of truth"*
- Assessment 2 (Data, 3.0): *"Product-level profitability is real-time, trusted, and dashboard-ready (Power BI ← SAP). Leading indicators (IBP, EOL, competitive intel) are structurally isolated from decision systems."*

**Theory:** The AI evaluates the user's described systems against the **five preconditions** from Hannila et al. (2020) — *"Product-level profitability: preconditions for data-driven PPM"*, JEIM 33(1), 214–237. Precondition 3 (holistic corporate-level data model) and Precondition 4 (data governance) are the most frequently triggered for the Data pillar. Silvola (2018) — *One product data for integrated business processes* — provides the specific definition of what "single source of truth" means in a PLM/ERP context.

### Zone 3R: "Why This Constrains Maturity"

**Data priority chain:**
```js
const constrainText =
  report?.bottleneck_constraint ??         // Primary: AI-authored constraint field
  report?.pillar_interpretations?.[key] ?? // Fallback 1
  report?.pillar_findings?.[key]?.[1] ??   // Fallback 2
  BN_CONSEQUENCE_FALLBACK[key] ??          // Fallback 3: static fallback
  null;
```

This column is **contextually adaptive** — its length and detail scales with how much nuance the AI found. Assessment 1 is short because the gap is foundational (Data simply doesn't exist at portfolio level). Assessment 2 is long because the gap is architectural (retrospective data is excellent, but predictive signals are structurally isolated) — the AI correctly identified this as a more sophisticated bottleneck requiring more explanation.

The column uses the **bottleneck-capping logic** from Hannila et al. (2022) to explain *why* this pillar score suppresses the overall score. In Assessment 2, the AI explicitly states that the real-time retrospective data (Level 4) combined with the structurally isolated predictive signals (Level 2 integration) produces a composite Data score at the threshold of Level 3 — demonstrating a direct application of the paper's precondition framework to a concrete case.

---

## Zone 4 — Risk Pills

**Labels** (static, from `RISK_PILL_DEFS` in `constants.js`):
1. Profit leakage
2. Strategic drift
3. Decision latency

**Descriptions** (dynamic, from `buildRiskItems()`):
```js
function buildRiskItems(report, pillarKey) {
  const gaps     = report?.critical_gaps  ?? [];
  const findings = report?.key_findings   ?? [];

  return RISK_PILL_DEFS.map(({ key, label, Icon, fallback }) => {
    // 1. Dedicated risk_pills field keyed by pillar
    if (report?.risk_pills?.[pillarKey]?.[key]) {
      return { Icon, label, desc: report.risk_pills[pillarKey][key] };
    }
    // 2/3. Scan critical_gaps then key_findings for a sentence matching the label
    const needle = label.toLowerCase();
    const match =
      gaps.find(g     => g.toLowerCase().includes(needle)) ??
      findings.find(f => f.toLowerCase().includes(needle));
    return { Icon, label, desc: match ?? fallback };
  });
}
```

The three descriptions are sentences from the AI's `critical_gaps` or `key_findings` arrays, filtered to those containing the pill's label keyword. This means the pill descriptions are always evidence-specific to this assessment — they reference the user's actual systems and situations.

Each `critical_gaps` entry must end with a Precondition label per **Mandatory Rule 1** in the system prompt:
```
"... (Precondition N: [name])"
```

**Theory per pill:**

| Pill | Mechanism | Academic source |
|---|---|---|
| **Profit leakage** | Companies with weak portfolio data governance retain under-performing products too long, causing measurable margin erosion | Hannila (2019); Cooper, Edgett & Kleinschmidt (1999, 2001) — empirical studies showing best-performing portfolios have 2–3× better data practices than average |
| **Strategic drift** | Without product-level lifecycle data, resource allocation decouples from actual portfolio performance | Tolonen et al. (2015) — *Product portfolio management: Targets and KPIs for product portfolio renewal over life cycle* |
| **Decision latency** | Manual data reconciliation introduces time lag between real-world events and portfolio responses | Silvola (2018); Hannila et al. (2022) — the finding that data fragmentation degrades timeliness of retirement and renewal decisions |

All three pills are implicitly grounded in **Product Wellbeing™** (Hannila, Salonen & Vierimaa, 2024): the framework treats data maturity as a prerequisite for knowing whether a product is healthy (profitable, strategically relevant, lifecycle-appropriate) vs. declining. Without the data precondition, product wellbeing cannot be assessed — meaning all three risks (leakage, drift, latency) are the direct consequence of undiagnosed product health.

---

## Zone 5 — Academic Footer

**Renders (static):**
```
Bottleneck principle: Hannila et al. (2022) · Hannila (2019) · Hannila, Koskinen, Härkönen & Haapasalo (2020), JEIM 33(1).
```

This footer is hardcoded in `BottleneckSection.jsx` — it applies to every assessment regardless of content. The three citations are the foundational sources for the bottleneck concept itself:

1. **Hannila et al. (2022)** — *Digitalisation of a company decision-making system*, Journal of Decision Systems 31(3), 258–279. Establishes the bottleneck principle operationally: the weakest pillar caps all others.
2. **Hannila (2019)** — Doctoral dissertation. Establishes the four-pillar PPDT framework and the taxonomy of portfolio decision types.
3. **Hannila, Koskinen, Härkönen & Haapasalo (2020)** — *Product-level profitability: preconditions for data-driven PPM*, JEIM 33(1), 214–237. Defines the five preconditions and establishes Data as the most common bottleneck in industrial portfolios.

---

## Full Data Flow Summary

```
User answers in chat
        │
        ▼
AI synthesises against reference documents
(Hannila 2019, 2020, 2022; Silvola 2018; Cooper 1999/2001; Tolonen 2015)
        │
        ▼
report JSON stored in assessment.report:
  bottleneck_narrative      → Zone 2
  dimension_summaries[key]  → Zone 3L
  bottleneck_constraint     → Zone 3R
  pillar_interpretations    → Zone 3R fallback
  critical_gaps             → Zone 4 pill descriptions (primary)
  key_findings              → Zone 4 pill descriptions (fallback)
        │
        ▼
buildReportData() maps report → BottleneckSection props:
  bottleneckPillar   (string)  → Zone 1 label
  scores[pillar]     (number)  → Zone 1 score/level pill
  bottleneckCapped   (boolean) → Zone 1 "Score capped" badge
  report             (object)  → Zones 2, 3, 4
        │
        ▼
BottleneckSection renders:
  Zone 1 — Header (levelName + levelClass determine pill colour)
  Zone 2 — AI narrative (fallback chain: 4 levels deep)
  Zone 3 — Two-col (each side has its own fallback chain)
  Zone 4 — buildRiskItems() scans gaps → findings → static fallback
  Zone 5 — Static academic footer (always shown)
```

---

## Static Fallback System

If the AI report is missing any field, the component never shows an empty zone — it falls through to `constants.js` fallbacks:

| Constant | Used in | Purpose |
|---|---|---|
| `BN_ROOT_CAUSE_FALLBACK[key]` | Zone 3L | Generic root cause text per pillar |
| `BN_CONSEQUENCE_FALLBACK[key]` | Zone 3R | Generic constraint text per pillar |
| `RISK_PILL_DEFS[i].fallback` | Zone 4 | Generic pill description per risk type |

These fallbacks ensure the card renders meaningfully even if the AI's JSON was truncated or a field was omitted — maintaining the academic rigour of the layout regardless of API reliability.

---

## Key References

| Citation | Role in the card |
|---|---|
| Hannila (2019) — doctoral dissertation | Decision type taxonomy; PPDT framework origin |
| Hannila, Koskinen, Härkönen & Haapasalo (2020), JEIM 33(1) | Five preconditions; data as primary bottleneck |
| Hannila et al. (2022), JDS 31(3) | Bottleneck-capping principle; overall score suppression logic |
| Hannila, Salonen & Vierimaa (2024) — Product Wellbeing™ | Product health as the outcome the card is protecting |
| Cooper, Edgett & Kleinschmidt (2001) | Stage-Gate trigger in narrative (Mandatory Rule 3a) |
| Tolonen et al. (2015) | Strategic drift mechanism (pill theory) |
| Silvola (2018) | Single source of truth definition; decision latency mechanism |

---

*This document was generated from a detailed code-and-theory trace of `BottleneckSection.jsx`, `constants.js`, `server.py` (PPDT_SYSTEM_PROMPT), and the academic sources underpinning the Product Wellbeing™ / PPDT framework. Last updated: May 2026.*
