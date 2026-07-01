/* Adds subtle "alive" motion on top of the static fixed background image:
   a slowly drifting cyan glow + soft glowing dust particles floating upward.
   Purely decorative, pointer-events disabled, respects prefers-reduced-motion.
   Particle configs are generated once at module load (not per-render) so the
   layout doesn't jump/re-randomize on re-renders. */
const PARTICLE_COUNT = 26;
const PARTICLES = Array.from({ length: PARTICLE_COUNT }, (_, i) => {
  const seed = i * 137.5; // golden-angle spread for even distribution
  const left = (seed % 100).toFixed(1);
  const size = 2 + ((i * 7) % 5); // 2-6px
  const duration = 14 + ((i * 11) % 16); // 14-30s
  const delay = -((i * 3.7) % duration); // negative = starts mid-animation, staggers immediately
  const drift = (i % 2 === 0 ? 1 : -1) * (10 + (i % 4) * 6);
  const rise = 140 + ((i * 5) % 90);
  const opacity = (0.35 + ((i * 13) % 40) / 100).toFixed(2);
  const isGold = i % 5 === 0; // ~1 in 5 particles gets a warm gold tint mixed into the cyan field
  return { left, size, duration, delay, drift, rise, opacity, top: 60 + ((i * 17) % 40), isGold };
});

const AnimatedBgOverlay = () => (
  <>
    <div className="ph-bg-glow" aria-hidden="true" />
    <div className="ph-bg-particles" aria-hidden="true">
      {PARTICLES.map((p, i) => (
        <span
          key={i}
          className={`ph-particle${p.isGold ? " ph-particle-gold" : ""}`}
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
            "--drift-x": `${p.drift}px`,
            "--rise": `-${p.rise}px`,
            "--particle-opacity": p.opacity,
          }}
        />
      ))}
    </div>
  </>
);

export default AnimatedBgOverlay;
