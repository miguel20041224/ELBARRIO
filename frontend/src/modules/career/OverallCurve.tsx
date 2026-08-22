import type { SeasonSnapshot } from "@/types/game";

/**
 * Sparkline of the overall across the career. Two seasons is the minimum that
 * draws a line; older careers stored before the overall existed report 0 and
 * are left out rather than dragging the curve to the floor.
 */
export default function OverallCurve({ history }: { history: SeasonSnapshot[] }) {
  const points = history
    .filter((snapshot) => snapshot.overall > 0)
    .map((snapshot) => ({ season: snapshot.season, overall: snapshot.overall }));

  if (points.length < 2) return null;

  const width = 100;
  const height = 28;
  const values = points.map((p) => p.overall);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;

  const path = points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * width;
      const y = height - ((point.overall - min) / span) * height;
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="rounded border border-barrio-border bg-barrio-bg/40 p-3">
      <div className="flex items-baseline justify-between text-xs text-barrio-muted">
        <span className="uppercase tracking-widest">Evolución OVR</span>
        <span>
          {min} → {max}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="mt-2 h-12 w-full"
        role="img"
        aria-label={`Evolución del OVR: de ${min} a ${max} en ${points.length} temporadas`}
      >
        <path
          d={path}
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          vectorEffect="non-scaling-stroke"
          className="text-barrio-accent"
        />
      </svg>
    </div>
  );
}
