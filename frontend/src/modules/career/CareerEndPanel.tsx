import { useMemo } from "react";
import { Link } from "react-router-dom";
import type { CareerSession } from "@/types/game";

interface Props {
  session: CareerSession;
}

export default function CareerEndPanel({ session }: Props) {
  const { player, history } = session;

  const stats = useMemo(() => {
    const teamTitles = player.trophies.filter((t) => t.kind === "team").length;
    const individualAwards = player.trophies.filter((t) => t.kind === "individual").length;
    const clubs = new Set(history.map((s) => s.clubName).filter(Boolean));
    const bestSeason = history.reduce<(typeof history)[number] | null>(
      (best, season) => (!best || season.goals > best.goals ? season : best),
      null,
    );
    return { teamTitles, individualAwards, clubs: clubs.size, bestSeason };
  }, [player.trophies, history]);

  return (
    <div className="panel p-6 space-y-5 border border-barrio-gold/40">
      <div>
        <p className="text-xs uppercase tracking-widest text-barrio-muted">
          Carrera terminada
        </p>
        <h3 className="heading text-2xl text-barrio-gold">
          {player.firstName} {player.lastName} colgó los botines
        </h3>
        <p className="text-sm text-barrio-muted mt-2">
          {history.length} temporada{history.length === 1 ? "" : "s"} · se retiró a los{" "}
          {player.age} años
          {stats.clubs > 0 ? ` · ${stats.clubs} club${stats.clubs === 1 ? "" : "es"}` : ""}
        </p>
      </div>

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Partidos" value={player.matchesPlayed} />
        <Stat label="Goles" value={player.goals} />
        <Stat label="Asistencias" value={player.assists} />
        <Stat label="Títulos" value={stats.teamTitles} />
      </dl>

      {stats.bestSeason && (
        <p className="text-sm text-barrio-muted">
          Mejor temporada: {stats.bestSeason.goals} goles y {stats.bestSeason.assists}{" "}
          asistencias en la {stats.bestSeason.season}
          {stats.bestSeason.clubName ? ` con ${stats.bestSeason.clubName}` : ""}.
        </p>
      )}

      {stats.individualAwards > 0 && (
        <p className="text-sm text-barrio-muted">
          {stats.individualAwards} premio{stats.individualAwards === 1 ? "" : "s"} individual
          {stats.individualAwards === 1 ? "" : "es"} en las vitrinas.
        </p>
      )}

      <Link to="/create" className="btn btn-primary inline-block">
        Empezar otra carrera
      </Link>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded border border-barrio-border p-3">
      <dt className="text-xs uppercase tracking-widest text-barrio-muted">{label}</dt>
      <dd className="text-xl font-semibold text-barrio-gold">{value}</dd>
    </div>
  );
}
