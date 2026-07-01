/* Adds subtle "alive" motion on top of the static fixed background image:
   a slowly drifting cyan glow + soft glowing dust particles floating upward.
   Purely decorative, pointer-events disabled, respects prefers-reduced-motion.
   Particle configs are generated once at module load (not per-render) so the
   layout doesn't jump/re-randomize on re-renders. A seeded PRNG (not a
   linear/modulo formula) is used so positions look genuinely scattered
   instead of falling on a visible lattice/diagonal-line pattern. */
function mulberry32(seed) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const PARTICLE_COUNT = 42;
const rand = mulberry32(20260701);
const PARTICLES = Array.from({ length: PARTICLE_COUNT }, () => {
  const left = (rand() * 100).toFixed(1);
  const top = (4 + rand() * 92).toFixed(1);
  const size = (2 + rand() * 4).toFixed(1);
  const duration = (14 + rand() * 18).toFixed(1);
  const delay = -(rand() * duration).toFixed(1);
  const drift = (rand() > 0.5 ? 1 : -1) * (8 + rand() * 28);
  const rise = 110 + rand() * 150;
  const opacity = (0.32 + rand() * 0.45).toFixed(2);
  // Mixed palette: cyan stays dominant (~57%), gold ~29%, warm-white ~14%.
  const roll = rand();
  const variant = roll < 0.14 ? "white" : roll < 0.43 ? "gold" : "cyan";
  return { left, top, size, duration, delay, drift, rise, opacity, variant };
});

const VARIANT_CLASS = { gold: " ph-particle-gold", white: " ph-particle-white", cyan: "" };

const AnimatedBgOverlay = () => (
  <>
    <div className="ph-bg-glow" aria-hidden="true" />
    <div className="ph-bg-particles" aria-hidden="true">
      {PARTICLES.map((p, i) => (
        <span
          key={i}
          className={`ph-particle${VARIANT_CLASS[p.variant]}`}
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
