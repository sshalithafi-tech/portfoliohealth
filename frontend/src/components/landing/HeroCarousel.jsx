import { useEffect, useRef, useState } from "react";
import { Layers, AlertTriangle, MapIcon, FileText, ShieldAlert } from "lucide-react";

/* ─────────────────────────────────────────────────────────────────────────
   Hero visual carousel — auto-cycles through 4 illustrative PPM "product
   moment" mockups (pillar scores, bottleneck diagnostic, 90-day roadmap,
   executive summary). Each slide crossfades and carries 1-2 floating
   annotation tags. Pure CSS opacity transitions + a lightweight JS interval
   — no animation library. Pauses on hover/focus, respects
   prefers-reduced-motion, and simplifies to a single static slide (tags
   always visible) on narrow viewports.
   ───────────────────────────────────────────────────────────────────────── */

const SLIDE_MS = 4500;
const MOBILE_BREAKPOINT = 640;

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* Slide 1 — Pillar Score card */
const PillarScoreSlide = () => (
  <div className="ph-mock ph-mock-pillars">
    <div className="ph-mock-head">
      <Layers size={14} />
      <span>Pillar Scores</span>
    </div>
    {[
      { label: "People", val: 3.2 },
      { label: "Process", val: 2.4 },
      { label: "Data", val: 2.8 },
      { label: "Technology", val: 1.6 },
    ].map((p) => (
      <div className="ph-mock-bar-row" key={p.label}>
        <span className="ph-mock-bar-label">{p.label}</span>
        <div className="ph-mock-bar-track">
          <div className="ph-mock-bar-fill" style={{ width: `${(p.val / 5) * 100}%` }} />
        </div>
        <span className="ph-mock-bar-val">{p.val.toFixed(1)}</span>
      </div>
    ))}
  </div>
);

/* Slide 2 — Bottleneck diagnostic */
const BottleneckSlide = () => (
  <div className="ph-mock ph-mock-bottleneck">
    <div className="ph-mock-head">
      <AlertTriangle size={14} />
      <span>Bottleneck Diagnostic</span>
    </div>
    <div className="ph-mock-alert">
      <ShieldAlert size={22} />
      <div>
        <div className="ph-mock-alert-title">Technology pillar flagged</div>
        <div className="ph-mock-alert-sub">Decision Vulnerability: Critical</div>
      </div>
    </div>
    <div className="ph-mock-alert-bar" />
  </div>
);

/* Slide 3 — 90-day roadmap timeline */
const RoadmapSlide = () => (
  <div className="ph-mock ph-mock-roadmap">
    <div className="ph-mock-head">
      <MapIcon size={14} />
      <span>90-Day Roadmap</span>
    </div>
    <div className="ph-mock-timeline">
      {[
        { p: "Immediate", gain: "2.1 \u2192 2.6" },
        { p: "Short-term", gain: "2.6 \u2192 3.1" },
        { p: "Strategic", gain: "3.1 \u2192 3.7" },
      ].map((phase, i) => (
        <div className="ph-mock-phase" key={phase.p}>
          <div className="ph-mock-phase-dot">{i + 1}</div>
          <div className="ph-mock-phase-label">{phase.p}</div>
          <div className="ph-mock-phase-gain">{phase.gain}</div>
        </div>
      ))}
    </div>
  </div>
);

/* Slide 4 — Executive summary preview */
const ExecSummarySlide = () => (
  <div className="ph-mock ph-mock-exec">
    <div className="ph-mock-head">
      <FileText size={14} />
      <span>Executive Summary</span>
    </div>
    <div className="ph-mock-page">
      <div className="ph-mock-page-title" />
      <div className="ph-mock-page-line" style={{ width: "92%" }} />
      <div className="ph-mock-page-line" style={{ width: "78%" }} />
      <div className="ph-mock-page-line" style={{ width: "85%" }} />
      <div className="ph-mock-page-badge">2.6 / 5</div>
    </div>
  </div>
);

const SLIDES = [
  {
    key: "pillars",
    render: PillarScoreSlide,
    tags: [{ label: "4 Pillars Scored", desc: "People, Process, Data, Technology" }],
  },
  {
    key: "bottleneck",
    render: BottleneckSlide,
    tags: [{ label: "Bottleneck Identified", desc: "Technology pillar flagged" }],
  },
  {
    key: "roadmap",
    render: RoadmapSlide,
    tags: [{ label: "90-Day Roadmap", desc: "3 phases, owners assigned" }],
  },
  {
    key: "exec",
    render: ExecSummarySlide,
    tags: [{ label: "Executive Summary", desc: "Ready to share, board-ready" }],
  },
];

export const HeroCarousel = () => {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(prefersReducedMotion);
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth <= MOBILE_BREAKPOINT : false
  );
  const intervalRef = useRef(null);

  // Track viewport width + reduced-motion preference live.
  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth <= MOBILE_BREAKPOINT);
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onMotionChange = () => setReducedMotion(mq.matches);
    window.addEventListener("resize", onResize);
    mq.addEventListener ? mq.addEventListener("change", onMotionChange) : mq.addListener(onMotionChange);
    return () => {
      window.removeEventListener("resize", onResize);
      mq.removeEventListener ? mq.removeEventListener("change", onMotionChange) : mq.removeListener(onMotionChange);
    };
  }, []);

  const staticMode = reducedMotion || isMobile;

  useEffect(() => {
    if (staticMode || paused) return;
    intervalRef.current = setInterval(() => {
      setIndex((i) => (i + 1) % SLIDES.length);
    }, SLIDE_MS);
    return () => clearInterval(intervalRef.current);
  }, [staticMode, paused]);

  const activeIndex = staticMode ? 0 : index;

  return (
    <div
      className={`ph-carousel-wrap${staticMode ? " static" : ""}`}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      data-testid="hero-carousel"
    >
      <div className="ph-carousel-backdrop" aria-hidden="true" />
      <div className="ph-carousel-stage">
        {SLIDES.map((slide, i) => {
          const Visual = slide.render;
          const active = i === activeIndex;
          return (
            <div
              key={slide.key}
              className={`ph-carousel-slide${active ? " active" : ""}`}
              aria-hidden={!active}
            >
              <Visual />
              {active &&
                slide.tags.map((tag) => (
                  <div className={`ph-float-tag${staticMode ? " always-on" : ""}`} key={tag.label}>
                    <span className="ph-float-tag-label">{tag.label}</span>
                    <span className="ph-float-tag-desc">{tag.desc}</span>
                  </div>
                ))}
            </div>
          );
        })}
      </div>
      {!staticMode && (
        <div className="ph-carousel-dots" role="tablist" aria-label="Product preview slides">
          {SLIDES.map((slide, i) => (
            <button
              key={slide.key}
              type="button"
              role="tab"
              aria-selected={i === activeIndex}
              aria-label={`Show ${slide.key} preview`}
              className={`ph-carousel-dot${i === activeIndex ? " active" : ""}`}
              onClick={() => setIndex(i)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default HeroCarousel;
