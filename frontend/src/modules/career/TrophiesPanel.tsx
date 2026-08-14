import { useMemo } from "react";
import type { Player } from "@/types/game";

interface Props {
  player: Player;
}

export default function TrophiesPanel({ player }: Props) {
  const { team, individual } = useMemo(() => {
    const team = player.trophies.filter((t) => t.kind === "team");
    const individual = player.trophies.filter((t) => t.kind === "individual");
    return { team, individual };
  }, [player.trophies]);

  if (player.trophies.length === 0) {
    return null;
  }

  return (
    <div className="panel p-5 space-y-4">
      <h3 className="heading text-lg text-barrio-gold">Palmarés</h3>

      {team.length > 0 && (
        <section>
          <p className="text-xs uppercase tracking-widest text-barrio-muted mb-2">
            Títulos con el equipo
          </p>
          <ul className="space-y-1 text-sm">
            {team.map((t, i) => (
              <li
                key={`${t.name}-${t.season}-${i}`}
                className="flex items-center gap-2"
              >
                <span className="text-barrio-gold">🏆</span>
                <span className="flex-1">{t.name}</span>
                <span className="text-xs text-barrio-muted">
                  Temp. {t.season}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {individual.length > 0 && (
        <section>
          <p className="text-xs uppercase tracking-widest text-barrio-muted mb-2">
            Premios individuales
          </p>
          <ul className="space-y-1 text-sm">
            {individual.map((t, i) => (
              <li
                key={`${t.name}-${t.season}-${i}`}
                className="flex items-center gap-2"
              >
                <span className="text-barrio-accent">★</span>
                <span className="flex-1">{t.name}</span>
                <span className="text-xs text-barrio-muted">
                  Temp. {t.season}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
