/* Adds subtle "alive" motion on top of the static fixed background image:
   (b) a slowly drifting cyan glow, and (c) glowing pulses that travel along
   a few PCB-style circuit traces — tying into the tech-blueprint texture
   already baked into the background photo. Purely decorative, pointer-events
   disabled, and respects prefers-reduced-motion. */
const CircuitTrace = ({ d, duration, delay }) => (
  <>
    <path d={d} className="ph-circuit-base" />
    <path
      d={d}
      className="ph-circuit-pulse"
      style={{ animationDuration: `${duration}s`, animationDelay: `${delay}s` }}
    />
  </>
);

const AnimatedBgOverlay = () => (
  <>
    <div className="ph-bg-glow" aria-hidden="true" />
    <svg
      className="ph-bg-circuit"
      aria-hidden="true"
      viewBox="0 0 1600 900"
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <filter id="ph-circuit-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g filter="url(#ph-circuit-glow)">
        <CircuitTrace d="M 1180 0 L 1180 140 L 1340 140 L 1340 320 L 1520 320" duration={9} delay={0} />
        <CircuitTrace d="M 1600 260 L 1420 260 L 1420 480 L 1240 480 L 1240 640" duration={11} delay={1.4} />
        <CircuitTrace d="M 60 900 L 60 700 L 240 700 L 240 520" duration={10} delay={0.6} />
        <CircuitTrace d="M 0 120 L 180 120 L 180 300 L 380 300" duration={12} delay={2.2} />
        <CircuitTrace d="M 1500 700 L 1500 560 L 1320 560" duration={8} delay={0.9} />
      </g>
    </svg>
  </>
);

export default AnimatedBgOverlay;
