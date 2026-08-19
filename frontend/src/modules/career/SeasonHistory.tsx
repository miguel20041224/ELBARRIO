import type { Position, SeasonSnapshot } from "@/types/game";

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
      <ul className="space-y-2">
        {[...history].reverse().map((snapshot) => (
          <li
            key={snapshot.season}
            className="rounded border border-barrio-border bg-barrio-bg/40 p-3 text-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">Temporada {snapshot.season}</p>
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
