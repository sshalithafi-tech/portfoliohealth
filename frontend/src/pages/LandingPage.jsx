import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import {
  ClipboardCheck,
  Target,
  Layers,
  Map as MapIcon,
  Clock,
  ArrowRight,
  ArrowDown,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  FileText,
  GraduationCap,
  BookOpen,
  Users,
  Workflow,
  Database,
  Cpu,
  Search,
  Eye,
  Compass,
  Award,
  ShieldCheck,
  Microscope,
  Lightbulb,
  CircleSlash,
} from "lucide-react";

import "../components/landing/landing.css";

/* ─────────────────────────── HOME PAGE (Block 2) ─────────────────────────── */
const HomePage = ({ ctaTo, onShowTheory }) => (
  <main className="ph-page" id="page-home">
    {/* H1 — Hero */}
    <section className="ph-hero">
      <div className="ph-hero-bg" />
      <div className="ph-inner">
        <div className="ph-hero-badge">
          <span className="ph-pulse-dot" />
          Grounded in peer-reviewed IEM research · University of Oulu
        </div>

        <h1 className="ph-animate-in" style={{ "--i": 1 }}>
          Diagnose your{" "}
          <span style={{ color: "var(--gold-deep)" }}>product portfolio</span>{" "}
          decision-making maturity.
        </h1>

        <p className="ph-sub ph-animate-in" style={{ "--i": 2 }}>
          A structured, research-backed PPDT assessment that reveals exactly
          where your portfolio capability breaks down — and what to fix first.
        </p>

        <div className="ph-cta-row ph-animate-in" style={{ "--i": 3 }}>
          <Link to={ctaTo} data-testid="hero-start-btn" className="ph-btn-primary">
            Start Full Assessment <ArrowRight size={16} />
          </Link>
          <a
            href="#how-it-works"
            data-testid="hero-how-btn"
            className="ph-btn-secondary"
            onClick={(e) => {
              e.preventDefault();
              document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            How it works <ArrowDown size={16} />
          </a>
        </div>

        <div className="ph-meta-row">
          <Clock size={16} style={{ color: "var(--gold-deep)" }} />
          Full assessment: 45–60 minutes · Conversational format · Structured PDF report
        </div>

        <div className="ph-stat-grid">
          {[
            {
              icon: <ClipboardCheck size={20} />,
              label: "Assessment",
              val: "4 Pillars",
              desc: "People, Process, Data, Technology — evaluated in depth",
            },
            {
              icon: <Target size={20} />,
              label: "Output",
              val: "5-Level Score",
              desc: "Ad Hoc → Predictive with bottleneck diagnosis",
            },
            {
              icon: <FileText size={20} />,
              label: "Deliverable",
              val: "Full Report",
              desc: "Phased roadmap, decision risks, improvement actions",
            },
          ].map((s, i) => (
            <div key={s.label} className="ph-glass-card ph-stat-card ph-animate-in" style={{ "--i": 4 + i }}>
              <div className="ph-icon-badge">{s.icon}</div>
              <span className="ph-stat-label">{s.label}</span>
              <div className="ph-val">{s.val}</div>
              <p className="ph-desc">{s.desc}</p>
            </div>
          ))}
        </div>

        <div className="ph-section-footer" style={{ marginTop: "var(--space-xl)" }}>
          Assessment grounded in Hannila (2019) doctoral dissertation and IEM
          publications by Hannila, Härkönen, Haapasalo &amp; Silvola (2018–2022),
          University of Oulu.
        </div>
      </div>
    </section>

    {/* H2 — What you receive */}
    <section>
      <div className="ph-inner">
        <div className="ph-sec-head">
          <span className="ph-section-label">What you receive</span>
          <h2>One conversation. A clear, actionable picture.</h2>
          <p className="ph-sub">
            A 45–60 minute structured dialogue that becomes a consultant-grade
            portfolio maturity report.
          </p>
        </div>
        <div className="ph-three-grid">
          {[
            {
              tag: "01",
              icon: <Target size={28} />,
              title: "Maturity Score per Pillar",
              body: "Each PPDT pillar scored 1.0–5.0 against maturity level definitions. Every score is grounded in specific evidence from the conversation — not self-declaration.",
            },
            {
              tag: "02",
              icon: <AlertTriangle size={28} />,
              title: "Bottleneck Identification",
              body: "The weakest pillar caps your overall capability regardless of how strong the others score. The report names it explicitly and makes the decision risk concrete.",
            },
            {
              tag: "03",
              icon: <MapIcon size={28} />,
              title: "Phased Improvement Roadmap",
              body: "Three-phase plan (0–3 months, 3–12 months, 12+ months) with actions tied to each pillar, always sequenced bottleneck-first.",
            },
          ].map((c, i) => (
            <div key={c.tag} className="ph-glass-card ph-step-card ph-animate-in" style={{ "--i": i + 1 }}>
              <span className="ph-step-tag">{c.tag}</span>
              {c.icon}
              <h3>{c.title}</h3>
              <p>{c.body}</p>
            </div>
          ))}
        </div>
        <div className="ph-section-footer">
          Hannila (2019) · Hannila et al. (2020, 2022) · Silvola (2018) · IEM
          research group, University of Oulu.
        </div>
      </div>
    </section>

    {/* H3 — Four Pillars (navy) */}
    <section className="ph-dark-section" id="framework">
      <div className="ph-inner">
        <div className="ph-sec-head dark">
          <span className="ph-section-label dark">The PPDT Framework</span>
          <h2>Four interdependent pillars. One integrated system.</h2>
          <p className="ph-sub">
            Weakness in any single pillar acts as a ceiling on your entire
            portfolio capability — no matter how advanced the others are.
          </p>
        </div>

        <div className="ph-four-grid">
          {[
            {
              letter: "P",
              title: "People",
              desc: "Roles, responsibilities, governance ownership, data accountability.",
              icon: <Users size={20} />,
              levels: [
                { t: "L1 No defined PPM roles", active: false },
                { t: "L2 Informal, person-dependent", active: false },
                { t: "L3 Cross-functional accountability", active: true },
                { t: "L4 Formal data ownership", active: true },
                { t: "L5 Governance embedded in KPIs", active: true },
              ],
            },
            {
              letter: "P",
              title: "Process",
              desc: "Formal review cycles, change control, decision traceability.",
              icon: <Workflow size={20} />,
              levels: [
                { t: "L1 Verbal decisions, no audit trail", active: false },
                { t: "L2 Recurring meetings, no structure", active: false },
                { t: "L3 Formal change control, PLM-ERP", active: true },
                { t: "L4 Scheduled, minuted, traceable", active: true },
                { t: "L5 Automated workflows, end-to-end", active: true },
              ],
            },
            {
              letter: "D",
              title: "Data",
              desc: "The most common bottleneck. Siloed data caps the entire portfolio system regardless of technology.",
              icon: <Database size={20} />,
              levels: [
                { t: "L1 Spreadsheets and email threads", active: false },
                { t: "L2 Departmental silos, manual assembly", active: false },
                { t: "L3 Central repository, retrievable", active: true },
                { t: "L4 Data quality SLAs, master governance", active: true },
                { t: "L5 Real-time, automated, trusted feeds", active: true },
              ],
            },
            {
              letter: "T",
              title: "Technology",
              desc: "Not which tools you own — but which are open during portfolio decisions.",
              icon: <Cpu size={20} />,
              levels: [
                { t: "L1 Excel only, no integration", active: false },
                { t: "L2 Departmental tools in isolation", active: false },
                { t: "L3 Some PLM-ERP integration", active: true },
                { t: "L4 Enterprise platform, decision-support", active: true },
                { t: "L5 AI analytics, scenario modelling", active: true },
              ],
            },
          ].map((p, i) => (
            <div key={p.title} className="ph-dark-card ph-pillar-card ph-animate-in" style={{ "--i": i + 1 }}>
              <div className="ph-badge">{p.letter}</div>
              <h3>{p.title}</h3>
              <p className="ph-desc">{p.desc}</p>
              <ul>
                {p.levels.map((lv) => (
                  <li key={lv.t} className={lv.active ? "active" : ""}>
                    <span className="ph-li-dot" />
                    {lv.t}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="ph-bottleneck-callout">
          <AlertTriangle size={22} />
          <p>
            <strong>The Bottleneck Principle:</strong> If your lowest-scoring
            pillar is 1.0 or more below the overall average, your entire
            portfolio capability is capped at that level. This principle draws
            from Hannila et al. (2022): five preconditions for data-driven PPM
            that must all function together.
          </p>
        </div>

        <div className="ph-section-footer dark">
          PPDT framework: Hannila (2019). Operationalized through Hannila,
          Härkönen &amp; Haapasalo (2022), Journal of Decision Systems, 31(3),
          258–279.
        </div>
      </div>
    </section>

    {/* H4 — Maturity levels */}
    <section className="ph-alt-section" id="maturity-levels">
      <div className="ph-inner">
        <div className="ph-sec-head">
          <span className="ph-section-label">Maturity Model</span>
          <h2>Five precise levels. No interpretation required.</h2>
          <p className="ph-sub">
            Each level has exact definitions per pillar. Scores are tied to
            observable evidence from the conversation — not self-assessment.
          </p>
        </div>

        <div className="ph-level-track">
          <div className="ph-spine" />
          {[
            { lvl: 1, name: "Ad Hoc",     tag: "Foundational",  bg: "var(--l1)", desc: "No formal structures. Verbal decisions. Data in personal spreadsheets." },
            { lvl: 2, name: "Developing", tag: "Awareness",     bg: "var(--l2)", desc: "Departmental silos. Recurring meetings but no audit trail or central governance." },
            { lvl: 3, name: "Defined",    tag: "Established",   bg: "var(--l3)", desc: "Formal change control. PLM-ERP integration active. Product profitability retrievable.", l3: true },
            { lvl: 4, name: "Managed",    tag: "Governed",      bg: "var(--l4)", desc: "Enterprise governance. Data quality SLAs. Portfolio reviews minuted and traceable." },
            { lvl: 5, name: "Predictive", tag: "Optimised",     bg: "var(--l5)", desc: "AI-assisted. Automated governance. Real-time traceability end-to-end." },
          ].map((s) => (
            <div key={s.lvl} className={`ph-level-step ${s.l3 ? "l3" : ""}`}>
              <div className="ph-step-dot" style={{ background: s.bg }}>{s.lvl}</div>
              <div className="ph-step-name">{s.name}</div>
              <div className="ph-step-tag">{s.tag}</div>
              <div className="ph-glass-card ph-desc-card">{s.desc}</div>
            </div>
          ))}
        </div>

        <div className="ph-glass-card ph-formula-callout">
          <h4>How the overall score is calculated:</h4>
          <div className="ph-formula">
            (People × 0.25) + (Process × 0.25) + (Data × 0.25) + (Technology × 0.25) = Overall Score
          </div>
          <p className="ph-note">
            Equal weighting is the validated baseline. Business-model-specific
            weighting is an open research question (RQ5, current Master's
            thesis research).
          </p>
        </div>

        <div className="ph-section-footer">
          Hannila et al. (2020), Journal of Enterprise Information Management,
          33(1), 214–237. 8-company empirical study.
        </div>
      </div>
    </section>

    {/* H5 — How it works */}
    <section id="how-it-works">
      <div className="ph-inner">
        <div className="ph-sec-head">
          <span className="ph-section-label">The Assessment Process</span>
          <h2>Structured. Evidence-based. 45–60 minutes.</h2>
          <p className="ph-sub">
            Every score is earned through specific conversational evidence —
            you cannot score Level 3 by simply stating you have a PLM system.
          </p>
        </div>

        <div className="ph-process-grid">
          {[
            {
              n: "01", title: "Context Setting",
              body: "We understand your organisation before scoring anything.",
              items: [
                "Industry and company size",
                "Business model (ETO / CTO / CETO / Standard)",
                "Your role and what prompted the assessment",
              ],
            },
            {
              n: "02", title: "Pillar Assessment",
              body: "2–3 purposeful questions per pillar, probing beyond surface-level answers.",
              items: [
                "Who owns data quality cross-department?",
                "Can you reconstruct a decision from 18 months ago?",
                "What tool is open during portfolio reviews?",
              ],
            },
            {
              n: "03", title: "Governance Probe",
              body: "For organisations scoring ≥ 3.0, a critical follow-up is always asked.",
              items: [
                "Is this process audit-trailed or culture-dependent?",
                "What happens when a key person leaves?",
                "Are governance roles formally documented?",
              ],
            },
            {
              n: "04", title: "Report Generation",
              body: "A full HTML/PDF report with all mandatory sections.",
              items: [
                "Pillar scores and overall maturity level",
                "Bottleneck analysis and decision vulnerabilities",
                "Three-phase improvement roadmap",
              ],
            },
          ].map((p, i) => (
            <div key={p.n} className="ph-glass-card ph-phase-card ph-animate-in" style={{ "--i": i + 1 }}>
              <div className="ph-num">{p.n}</div>
              <h3>{p.title}</h3>
              <p>{p.body}</p>
              <ul>{p.items.map((it) => <li key={it}>{it}</li>)}</ul>
            </div>
          ))}
        </div>

        <div className="ph-section-footer">
          Protocol derived from Hannila (2019) five preconditions. Methodology
          consistent with Hannila et al. (2020) empirical study across eight
          companies.
        </div>
      </div>
    </section>

    {/* H6 — CTA */}
    <section className="ph-cta-section" id="cta">
      <div className="ph-inner">
        <span className="ph-section-label dark">Ready to begin?</span>
        <h2>Find out exactly where your portfolio management stands — and what to do next.</h2>
        <p className="ph-sub">
          One structured conversation. A research-grounded maturity score. A
          clear roadmap. No guesswork, no vague ratings, no generic advice.
        </p>
        <Link to={ctaTo} data-testid="cta-start-btn" className="ph-btn-primary">
          Start Full Assessment <ArrowRight size={16} />
        </Link>
        <div className="ph-meta">
          <div className="ph-meta-item"><Clock size={16} />45–60 minutes</div>
          <div className="ph-meta-item"><FileText size={16} />Full structured PDF report</div>
          <div className="ph-meta-item"><BookOpen size={16} />IEM research-grounded</div>
        </div>
      </div>
    </section>
  </main>
);

/* ─────────────────────────── THEORY PAGE (Block 3) ─────────────────────────── */
const TheoryPage = ({ ctaTo, onJumpToHomeCta }) => (
  <main className="ph-page" id="page-theory">
    {/* T1 — Hero */}
    <section className="ph-hero" style={{ minHeight: "55vh" }}>
      <div className="ph-hero-bg" />
      <div className="ph-inner">
        <div className="ph-hero-badge">
          <span className="ph-pulse-dot" />
          Peer-reviewed IEM research · University of Oulu
        </div>
        <h1 className="ph-animate-in" style={{ "--i": 1, maxWidth: 680 }}>
          Assessment grounded in research. Decisions grounded in evidence.
        </h1>
        <p className="ph-sub ph-animate-in" style={{ "--i": 2 }}>
          This tool is built on a published body of peer-reviewed academic
          research from the University of Oulu. Every scoring principle,
          maturity level, and improvement recommendation has an academic
          source behind it.
        </p>
        <div className="ph-cta-row ph-animate-in" style={{ "--i": 3 }}>
          <Link to={ctaTo} data-testid="theory-start-btn" className="ph-btn-primary">
            Start Full Assessment <ArrowRight size={16} />
          </Link>
          <a
            href="#research"
            className="ph-btn-secondary"
            onClick={(e) => { e.preventDefault(); document.getElementById("research")?.scrollIntoView({ behavior: "smooth" }); }}
          >
            Explore the Research <ArrowDown size={16} />
          </a>
        </div>
      </div>
    </section>

    {/* T2 — What this assessment measures */}
    <section>
      <div className="ph-inner">
        <div className="ph-sec-head">
          <span className="ph-section-label">The Assessment</span>
          <h2>What PortfolioHealth Advisor actually measures.</h2>
          <p className="ph-sub">
            Understanding what the tool assesses and why those four dimensions
            were chosen.
          </p>
        </div>

        <div className="ph-t2-grid">
          <div className="ph-glass-card ph-measure-card">
            <span className="ph-section-label">What is measured</span>
            <h3>Four capability dimensions. One integrated view.</h3>
            <p>The assessment evaluates four dimensions of your product portfolio management capability as one interconnected system, not four separate scores.</p>
            <p>What matters is not which dimension scores highest, but whether they function together. A weak link in any dimension limits the capability of the entire system.</p>
            <p>The result is a precise diagnosis: where you are, which dimension is your constraint, and a sequenced roadmap starting from the bottleneck.</p>
            <div className="ph-cite-strip">Four-dimension framework: Hannila (2019), University of Oulu.</div>
          </div>

          <div>
            {[
              { icon: <Users size={20} />, t: "People", b: "Governance, ownership, and human structures that make data-driven decisions possible." },
              { icon: <Workflow size={20} />, t: "Process", b: "Formal decision cycles and traceability that turn intent into repeatable outcomes." },
              { icon: <Database size={20} />, t: "Data", b: "Availability and quality of product information when portfolio decisions are made.", flag: true },
              { icon: <Cpu size={20} />, t: "Technology", b: "Systems actually used in the decision room — not the tools listed in the IT inventory." },
            ].map((d) => (
              <div key={d.t} className="ph-dim-card">
                {d.icon}
                <div>
                  <h4>{d.t}</h4>
                  <p>{d.b}</p>
                  {d.flag && <span className="ph-constraint-pill">Most common constraint</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="ph-section-footer">
          Individual scoring criteria are proprietary to the assessment
          instrument. Dimensions derived from Hannila (2019) IEM doctoral
          research.
        </div>
      </div>
    </section>

    {/* T3 — How theory supports */}
    <section className="ph-dark-section" id="research">
      <div className="ph-inner">
        <div className="ph-sec-head dark">
          <span className="ph-section-label dark">Academic Foundation</span>
          <h2>Built on published research. Not on opinion.</h2>
          <p className="ph-sub">
            Every dimension, maturity level, and improvement principle is
            grounded in IEM publications. The research tells us what matters —
            the assessment measures how much of it you have.
          </p>
        </div>

        <div className="ph-t3-grid">
          {[
            { icon: <Award size={22} />, t: "What good looks like", b: "Published doctoral research established what data-driven portfolio management looks like at full maturity. This benchmark anchors the top of the assessment scale.", c: "Hannila (2019) · University of Oulu" },
            { icon: <ShieldCheck size={22} />, t: "What must be in place first", b: "Research identified the conditions that must exist before data-driven portfolio decisions are possible. These form the structure of what the assessment evaluates.", c: "Hannila, Härkönen & Haapasalo (2022)" },
            { icon: <Microscope size={22} />, t: "What the data shows", b: "An empirical study across eight companies confirmed that maturity varies significantly — and that most companies cannot assess their own position without a structured instrument.", c: "Hannila, Koskinen, Härkönen & Haapasalo (2020)" },
            { icon: <Compass size={22} />, t: "What the ideal state looks like", b: "Separate doctoral research defined the endpoint: product data created once, governed centrally, used reliably across the full product lifecycle.", c: "Silvola (2018) · University of Oulu" },
          ].map((c, i) => (
            <div key={c.t} className="ph-dark-card ph-research-card ph-animate-in" style={{ "--i": i + 1 }}>
              {c.icon}
              <h3>{c.t}</h3>
              <p>{c.b}</p>
              <div className="ph-cite">{c.c}</div>
            </div>
          ))}
        </div>

        <div className="ph-dark-card ph-connecting-callout">
          <p>
            These four research contributions answer four questions the
            assessment is built to test: What does maturity look like? What
            must exist? Where do companies fall short? And what does the
            improvement journey look like?
          </p>
        </div>

        <div className="ph-section-footer dark">
          Scoring methodology is proprietary. Full citations on this page.
          Papers available through University of Oulu and respective journal
          publishers.
        </div>
      </div>
    </section>

    {/* T4 — Research gap */}
    <section className="ph-alt-section">
      <div className="ph-inner">
        <div className="ph-sec-head">
          <span className="ph-section-label">The Research Gap</span>
          <h2>The academic community identified the problem. This tool provides the solution.</h2>
          <p className="ph-sub">Multiple IEM publications explicitly noted that something was missing.</p>
        </div>

        <div className="ph-gap-grid">
          <div className="ph-glass-card ph-gap-col">
            <h3>What the research established.</h3>
            {[
              "A framework defining what data-driven PPM requires",
              "The conditions that must be satisfied for it to work",
              "Empirical proof that companies are at different stages",
              "A clear picture of what full maturity looks like",
            ].map((t) => (
              <div key={t} className="ph-item check">
                <CheckCircle2 size={18} />
                <span>{t}</span>
              </div>
            ))}
          </div>
          <div className="ph-glass-card ph-gap-col">
            <h3>What was explicitly missing.</h3>
            {[
              "A way for companies to assess their current position",
              "A structured instrument to identify specific gaps",
              "A validated path from current state to target state",
              "A tool that translates the theory into practical action",
            ].map((t) => (
              <div key={t} className="ph-item cross">
                <XCircle size={18} />
                <span>{t}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="ph-glass-card ph-bridge-callout">
          <h4>This is exactly what PortfolioHealth Advisor does.</h4>
          <p>
            The gap between academic framework and practical instrument is the
            difference between knowing what good looks like and knowing whether
            your organisation is getting there. This tool bridges that gap in a
            single structured conversation.
          </p>
        </div>

        <div className="ph-quote-grid">
          {[
            { q: "Companies have data but cannot use it for decisions.", s: "— Hannila (2019)" },
            { q: "No systematic approach to assess PPM capabilities was identified.", s: "— Hannila, Härkönen & Haapasalo (2022)" },
            { q: "Companies cannot self-assess their maturity level systematically.", s: "— Hannila, Koskinen, Härkönen & Haapasalo (2020)" },
          ].map((c) => (
            <div key={c.s} className="ph-quote-card">
              <p className="ph-q">"{c.q}"</p>
              <div className="ph-source">{c.s}</div>
            </div>
          ))}
        </div>

        <div className="ph-section-footer">
          Quotes are representative summaries from cited papers. Full papers
          available through University of Oulu and respective journal publishers.
        </div>
      </div>
    </section>

    {/* T5 — Decision impact */}
    <section>
      <div className="ph-inner">
        <div className="ph-sec-head">
          <span className="ph-section-label">Decision Impact</span>
          <h2>Better maturity means better decisions. Here is how.</h2>
          <p className="ph-sub">
            The assessment is the starting point for improving the decisions
            that drive product portfolio performance.
          </p>
        </div>

        <div className="ph-impact-grid">
          {[
            { icon: <Eye size={24} />, t: "See what you cannot currently see", b: "Most portfolio decisions are made without complete product-level data. The assessment identifies which information gaps are costing you decision quality.", n: "Common outcome: data teams thought existed is 2–4 days away from being assembled." },
            { icon: <Search size={24} />, t: "Name the constraint, not the symptom", b: "Portfolio problems are often misdiagnosed. The assessment frequently reveals the real constraint is in data ownership or governance roles never formally defined.", n: "Common outcome: the highest-scoring pillar is not the one teams expected." },
            { icon: <TrendingUp size={24} />, t: "Invest in the right thing first", b: "Roadmap actions are sequenced around the bottleneck — the one constraint limiting everything else. Fixing it first creates the largest improvement in decision quality.", n: "Common outcome: Phase 1 actions are simpler than expected but were never prioritised." },
          ].map((c, i) => (
            <div key={c.t} className="ph-glass-card ph-impact-card ph-animate-in" style={{ "--i": i + 1 }}>
              {c.icon}
              <h3>{c.t}</h3>
              <p>{c.b}</p>
              <p className="ph-note">{c.n}</p>
            </div>
          ))}
        </div>

        <div className="ph-ba-grid">
          <div className="ph-ba-col before">
            <h3>Before the assessment</h3>
            {[
              "Portfolio decisions made with incomplete data",
              "No clear picture of which products are profitable",
              "No single owner for product data quality",
              "Improvements attempted without knowing the constraint",
            ].map((t) => (
              <div key={t} className="ph-item">
                <CircleSlash size={16} />
                <span>{t}</span>
              </div>
            ))}
          </div>
          <div className="ph-ba-col after">
            <h3>After the assessment</h3>
            {[
              "Maturity score per dimension with specific evidence",
              "Bottleneck named and decision risk made explicit",
              "Three-phase roadmap sequenced around the constraint",
              "Clear starting point with named ownership actions",
            ].map((t) => (
              <div key={t} className="ph-item">
                <CheckCircle2 size={16} />
                <span>{t}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="ph-section-footer">
          Decision impact framing: Hannila (2019) and Hannila et al. (2022) on
          PPDT capability and portfolio decision quality.
        </div>
      </div>
    </section>

    {/* T6 — Thesis contribution */}
    <section className="ph-dark-section">
      <div className="ph-inner">
        <div className="ph-sec-head dark">
          <span className="ph-section-label dark">Master's Thesis</span>
          <h2>Where academic research ends. Where this tool begins.</h2>
          <p className="ph-sub">
            The research established the framework and confirmed the gap. The
            Master's thesis turns that framework into a working assessment
            instrument.
          </p>
        </div>

        <div className="ph-thesis-card">
          <div className="ph-thesis-head">
            <h3>What this thesis contributes.</h3>
            <span className="ph-thesis-pill">IEM · University of Oulu · 2026</span>
          </div>
          <p>
            The IEM research group produced the conceptual foundation. This
            thesis operationalizes it — taking the published framework and
            turning it into a structured, repeatable assessment that any
            company can complete without academic training.
          </p>
          <p>
            The contribution is the instrument itself: its assessment logic,
            maturity scoring approach, bottleneck identification method, and
            improvement roadmap structure — original research contributions,
            not reproductions of the underlying academic papers.
          </p>

          <div className="ph-thesis-tiles">
            {[
              { icon: <Target size={20} />, t: "Gap Addressed", b: "Converts published frameworks into a validated practitioner assessment." },
              { icon: <Lightbulb size={20} />, t: "Original Instrument", b: "Assessment protocol, scoring logic, and roadmap structure are original research output." },
              { icon: <Layers size={20} />, t: "Accessible Format", b: "Academic rigour delivered through a structured conversation. No specialist knowledge required." },
              { icon: <Compass size={20} />, t: "Open Research Path", b: "Opens questions for future IEM research on industry-specific maturity calibration." },
            ].map((c) => (
              <div key={c.t} className="ph-dark-card ph-thesis-tile">
                {c.icon}
                <h4>{c.t}</h4>
                <p>{c.b}</p>
              </div>
            ))}
          </div>

          <div className="ph-thesis-meta">
            {[
              { l: "Programme", v: "Industrial Engineering and Management" },
              { l: "Specialisation", v: "Product Development, PLM & PPM" },
              { l: "University", v: "University of Oulu, IPIC Programme" },
              { l: "Year", v: "2026" },
            ].map((m) => (
              <div key={m.l}>
                <span className="ph-mlbl">{m.l}</span>
                <span className="ph-mval">{m.v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="ph-section-footer dark">
          Assessment methodology is proprietary. Academic sources cited
          throughout are publicly available IEM publications.
        </div>
      </div>
    </section>

    {/* T7 — Bottom CTA */}
    <section className="ph-cta-section">
      <div className="ph-inner">
        <span className="ph-section-label dark">Ready to begin?</span>
        <h2>The research is clear. Your next step is simple.</h2>
        <p className="ph-sub">
          A 45–60 minute conversation produces a precise, evidence-based
          maturity score and a roadmap grounded in the IEM research you just
          read about.
        </p>
        <button
          type="button"
          onClick={onJumpToHomeCta}
          className="ph-btn-primary"
          data-testid="theory-cta-start-btn"
        >
          Start Full Assessment <ArrowRight size={16} />
        </button>
      </div>
    </section>
  </main>
);

/* ─────────────────────────── Shared footer ─────────────────────────── */
const SharedFooter = ({ onShowTheory }) => (
  <footer className="ph-footer">
    <div className="ph-inner-f">
      <div>
        <h4>PortfolioHealth Advisor</h4>
        <p className="ph-fcol-desc">
          A practitioner-facing PPDT maturity assessment for product portfolio
          management. Developed as original Master's thesis research in IEM at
          the University of Oulu.
        </p>
        <div className="ph-fcopy">© 2026 PortfolioHealth Advisor · IEM Master's Thesis Research</div>
      </div>
      <div>
        <span className="ph-fcol-label">Assessment</span>
        <a className="ph-flink" href="#how-it-works" onClick={(e) => { e.preventDefault(); document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" }); }}>How It Works</a>
        <a className="ph-flink" href="#framework" onClick={(e) => { e.preventDefault(); document.getElementById("framework")?.scrollIntoView({ behavior: "smooth" }); }}>The Framework</a>
        <a className="ph-flink" href="#maturity-levels" onClick={(e) => { e.preventDefault(); document.getElementById("maturity-levels")?.scrollIntoView({ behavior: "smooth" }); }}>Maturity Levels</a>
        <a className="ph-flink" href="#cta" onClick={(e) => { e.preventDefault(); document.getElementById("cta")?.scrollIntoView({ behavior: "smooth" }); }}>Start Assessment</a>
      </div>
      <div>
        <span className="ph-fcol-label">Research Basis</span>
        <a className="ph-flink" onClick={onShowTheory}>Academic Foundation</a>
        <a className="ph-flink" onClick={onShowTheory}>Thesis Contribution</a>
        <a className="ph-flink" onClick={onShowTheory}>Research Papers</a>
        <a className="ph-flink" onClick={onShowTheory}>The Research Gap</a>
      </div>
    </div>
    <div className="ph-fbottom">
      <div>
        <div className="ph-fcite-lbl">Academic Sources</div>
        <p className="ph-fcite-body">
          Hannila (2019) · Hannila, Härkönen &amp; Haapasalo (2022, Journal of
          Decision Systems) · Hannila, Silvola, Härkönen &amp; Haapasalo (2022,
          Journal of Computer Information Systems) · Hannila, Koskinen,
          Härkönen &amp; Haapasalo (2020, Journal of Enterprise Information
          Management) · Silvola (2018) · Silvola, Tolonen, Härkönen &amp;
          Haapasalo (2018, IJBIS) · University of Oulu, IEM Department.
        </p>
      </div>
      <div className="ph-fdisclaimer">
        PortfolioHealth Advisor is an independent practitioner tool. Not
        affiliated with or endorsed by the University of Oulu.
      </div>
    </div>
  </footer>
);

/* ─────────────────────────── Page shell + nav ─────────────────────────── */
const LandingPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [page, setPage] = useState("home");

  const ctaTo = user ? "/dashboard" : "/register";

  // Smooth-scroll to top whenever page changes
  useEffect(() => { window.scrollTo({ top: 0, behavior: "smooth" }); }, [page]);

  const showHome = () => setPage("home");
  const showTheory = () => setPage("theory");
  const jumpToHomeCta = () => {
    setPage("home");
    setTimeout(() => document.getElementById("cta")?.scrollIntoView({ behavior: "smooth" }), 80);
  };

  return (
    <div className="ph-site">
      <nav className="ph-nav" aria-label="Primary">
        <div className="ph-brand" onClick={showHome} role="button" style={{ cursor: "pointer" }}>
          <div className="ph-logo" data-testid="brand-logo">PH</div>
          <span className="ph-name">PortfolioHealth Advisor</span>
        </div>
        <div className="ph-nav-tabs">
          <button
            type="button"
            data-page="page-home"
            data-testid="nav-tab-home"
            className={`ph-nav-tab ${page === "home" ? "active" : ""}`}
            onClick={showHome}
          >
            Home
          </button>
          <button
            type="button"
            data-page="page-theory"
            data-testid="nav-tab-theory"
            className={`ph-nav-tab ${page === "theory" ? "active" : ""}`}
            onClick={showTheory}
          >
            Research &amp; Theory
          </button>
        </div>
        <div className="ph-nav-right">
          <span
            className="ph-nav-link"
            onClick={() => {
              if (page !== "home") setPage("home");
              setTimeout(() => document.getElementById("maturity-levels")?.scrollIntoView({ behavior: "smooth" }), 60);
            }}
          >
            Maturity Levels
          </span>
          <span
            className="ph-nav-link"
            onClick={() => {
              if (page !== "home") setPage("home");
              setTimeout(() => document.getElementById("framework")?.scrollIntoView({ behavior: "smooth" }), 60);
            }}
          >
            The Framework
          </span>
          {user ? (
            <Link to="/dashboard" data-testid="nav-dashboard-btn" className="ph-btn-primary ph-nav-cta">
              Dashboard <ArrowRight size={14} />
            </Link>
          ) : (
            <>
              <Link to="/login" data-testid="nav-login-link" className="ph-nav-link">Sign In</Link>
              <Link to={ctaTo} data-testid="nav-cta-btn" className="ph-btn-primary ph-nav-cta">
                Start Full Assessment <ArrowRight size={14} />
              </Link>
            </>
          )}
        </div>
      </nav>

      {page === "home"
        ? <HomePage ctaTo={ctaTo} onShowTheory={showTheory} />
        : <TheoryPage ctaTo={ctaTo} onJumpToHomeCta={jumpToHomeCta} />}

      <SharedFooter onShowTheory={showTheory} />
    </div>
  );
};

export default LandingPage;
