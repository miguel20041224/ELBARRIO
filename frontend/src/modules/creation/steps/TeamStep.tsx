import { useEffect, useState } from "react";
import clsx from "clsx";
import { useCreationStore } from "@/store/creationStore";
import { careerApi } from "@/api/careerApi";
import type { TeamOption } from "@/types/game";

export default function TeamStep() {
  const league = useCreationStore((state) => state.draft.startingLeague);
  const chosenClub = useCreationStore((state) => state.draft.startingClub);
  const update = useCreationStore((state) => state.update);
  const [teams, setTeams] = useState<TeamOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!league) return;
    setLoading(true);
    setError(null);
    careerApi
      .listTeams(league)
      .then(setTeams)
      .catch((err) => setError(err instanceof Error ? err.message : "Error"))
      .finally(() => setLoading(false));
  }, [league]);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="heading text-2xl">Equipo inicial</h2>
        <p className="text-sm text-barrio-muted">
          Elegí en qué club querés arrancar. Los clubes grandes pagan más pero
          la presión es brutal — y como pibe difícil que te den lugar.
          Al azar, el sistema te asigna un club acorde a tu edad y reputación.
        </p>
      </header>

      <button
        type="button"
        onClick={() => update({ startingClub: null })}
        className={clsx(
          "w-full rounded border p-4 text-left transition-colors",
          chosenClub === null
            ? "border-barrio-gold bg-barrio-gold/10"
            : "border-barrio-border hover:border-barrio-muted",
        )}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎲</span>
          <div>
            <p className="font-semibold text-barrio-gold">
              Al azar (recomendado)
            </p>
            <p className="text-xs text-barrio-muted">
              El motor asigna un club apropiado según tu edad. Ideal para
              carreras realistas — arrancás desde abajo y subís.
            </p>
          </div>
        </div>
      </button>

      {loading && (
        <p className="text-sm text-barrio-muted">Cargando equipos...</p>
      )}
      {error && (
        <p className="text-sm text-barrio-danger">
          No se pudieron cargar los equipos: {error}
        </p>
      )}

      {!loading && teams.length > 0 && (
        <div className="grid gap-2 md:grid-cols-2">
          {teams.map((team) => {
            const selected = chosenClub === team.id;
            return (
              <button
                key={team.id}
                type="button"
                onClick={() => update({ startingClub: team.id })}
                className={clsx(
                  "rounded border p-3 text-left transition-colors",
                  selected
                    ? "border-barrio-accent bg-barrio-accent/10"
                    : "border-barrio-border hover:border-barrio-muted",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold">{team.name}</p>
                  <span className="text-barrio-gold text-xs">
                    ★ {team.prestige}
                  </span>
                </div>
                <p className="text-xs text-barrio-muted">
                  {team.city}
                  {team.nickname && (
                    <>
                      {" · "}
                      <span className="text-barrio-gold">{team.nickname}</span>
                    </>
                  )}
                </p>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
