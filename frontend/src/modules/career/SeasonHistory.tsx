import type { Position, SeasonSnapshot } from "@/types/game";
import { formatMoney } from "@/lib/format";

const DEFENSIVE_POSITIONS: Position[] = ["GK", "CB", "LB", "RB", "CDM"];

interface Props {
  history: SeasonSnapshot[];
  position: Position;
}

export default function SeasonHistory({ history, position }: Props) {
  // A un defensor se lo lee por las vallas que sostuvo, no por los goles.
  const defensive = DEFENSIVE_POSITIONS.includes(position);

  if (history.length === 0) {
    return (
      <div className="panel p-5">
        <h3 className="heading text-lg text-barrio-gold">Trayectoria</h3>
        <p className="mt-2 text-sm text-barrio-muted">
          Todavía no jugaste ninguna temporada. Cerrá esta primera y empieza
          a construir tu leyenda.
        </p>
      </div>
    );
  }
  return (
    <div className="panel p-5 space-y-3">
      <h3 className="heading text-lg text-barrio-gold">Trayectoria</h3>
      <OverallCurve history={history} />
      <ul className="space-y-2">
        {[...history].reverse().map((snapshot) => (
          <li
            key={snapshot.season}
            className="rounded border border-barrio-border bg-barrio-bg/40 p-3 text-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">
                  Temporada {snapshot.season}
                  {snapshot.overall > 0 && (
                    <span className="ml-2 text-barrio-accent">
                      OVR {snapshot.overall}
                    </span>
                  )}
                  {snapshot.marketValue > 0 && (
                    <span className="ml-2 text-barrio-gold">
                      {formatMoney(snapshot.marketValue)}
                    </span>
                  )}
                </p>
                {snapshot.clubName && (
                  <p className="text-xs text-barrio-accent">
                    {snapshot.clubName}
                  </p>
                )}
              </div>
              <span className="text-xs text-barrio-muted">
                {snapshot.matchesPlayed} PJ ·{" "}
                {defensive
                  ? `${snapshot.cleanSheets} VI`
                  : `${snapshot.goals}G · ${snapshot.assists}A`}{" "}
                · {snapshot.averageRating.toFixed(2)} · {snapshot.wins}-
                {snapshot.draws}-{snapshot.losses}
              </span>
            </div>
            {snapshot.trophies.length > 0 && (
              <p className="mt-1 text-xs">
                <span className="text-barrio-gold">🏆</span>{" "}
                <span className="text-barrio-muted">
                  {snapshot.trophies.join(" · ")}
                </span>
              </p>
            )}
            {snapshot.individualAwards.length > 0 && (
              <p className="mt-1 text-xs">
                <span className="text-barrio-accent">★</span>{" "}
                <span className="text-barrio-muted">
                  {snapshot.individualAwards.join(" · ")}
                </span>
              </p>
            )}
            {snapshot.keyEvents.length > 0 && (
              <ul className="mt-1 text-xs text-barrio-muted list-disc pl-5">
                {snapshot.keyEvents.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}


/**
 * Sparkline of the overall across the career. Two seasons is the minimum that
 * draws a line; older careers stored before the overall existed report 0 and
 * are left out rather than dragging the curve to the floor.
 */
function OverallCurve({ history }: { history: SeasonSnapshot[] }) {
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
