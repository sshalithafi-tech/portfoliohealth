import { Layers } from "lucide-react";

/* ─────────────────────────────────────────────────────────────────────────
   Static hero visual — a single, clean "pillar scores" product-moment card.
   No auto-cycling, no crossfade, no floating-tag animation, no dot
   indicators — per feedback, all motion was removed from this element.
   ───────────────────────────────────────────────────────────────────────── */

export const HeroCarousel = () => (
  <div className="ph-carousel-wrap static" data-testid="hero-carousel">
    <div className="ph-carousel-stage">
      <div className="ph-carousel-visual">
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
      </div>
    </div>
  </div>
);

export default HeroCarousel;
