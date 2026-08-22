import { useMemo } from "react";
import { Link } from "react-router-dom";
import type { CareerSession } from "@/types/game";
import { formatMoney } from "@/lib/format";
import OverallCurve from "./OverallCurve";

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
    // Un palmarés se lee mejor agrupado: "LaLiga ×3" dice más que tres filas.
    const palmares = new Map<string, number>();
    for (const trophy of player.trophies) {
      if (trophy.kind !== "team") continue;
      palmares.set(trophy.name, (palmares.get(trophy.name) ?? 0) + 1);
    }
    const awards = new Map<string, number>();
    for (const trophy of player.trophies) {
      if (trophy.kind !== "individual") continue;
      awards.set(trophy.name, (awards.get(trophy.name) ?? 0) + 1);
    }
    const peakValue = Math.max(0, ...history.map((s) => s.marketValue));
    return {
      teamTitles,
      individualAwards,
      clubs: clubs.size,
      bestSeason,
      palmares: [...palmares.entries()].sort((a, b) => b[1] - a[1]),
      awards: [...awards.entries()].sort((a, b) => b[1] - a[1]),
      peakValue,
    };
  }, [player.trophies, history]);

  const verdict = session.careerVerdict;

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

      {verdict && (
        <div className="rounded border border-barrio-gold/50 bg-barrio-gold/5 p-4">
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Veredicto
          </p>
          <p className="heading text-xl text-barrio-gold">{verdict.title}</p>
          <p className="text-sm text-barrio-muted mt-1">{verdict.summary}</p>
        </div>
      )}

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Partidos" value={player.matchesPlayed} />
        <Stat label="Goles" value={player.goals} />
        <Stat label="Asistencias" value={player.assists} />
        <Stat label="Títulos" value={stats.teamTitles} />
      </dl>

      {verdict && (
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Stat label="OVR máximo" value={verdict.peakOverall} />
          <Stat label="Temporadas" value={verdict.seasons} />
          <Stat label="Clubes" value={verdict.clubs} />
        </dl>
      )}

      <OverallCurve history={history} />

      {stats.peakValue > 0 && (
        <p className="text-sm text-barrio-muted">
          Valor máximo alcanzado:{" "}
          <span className="text-barrio-gold font-semibold">
            {formatMoney(stats.peakValue)}
          </span>
          .
        </p>
      )}

      {stats.palmares.length > 0 && (
        <Palmares title="Palmarés" entries={stats.palmares} accent="text-barrio-gold" />
      )}

      {stats.awards.length > 0 && (
        <Palmares
          title="Distinciones"
          entries={stats.awards}
          accent="text-barrio-accent"
        />
      )}

      {stats.bestSeason && (
        <p className="text-sm text-barrio-muted">
          Mejor temporada: {stats.bestSeason.goals} goles y {stats.bestSeason.assists}{" "}
          asistencias en la {stats.bestSeason.season}
          {stats.bestSeason.clubName ? ` con ${stats.bestSeason.clubName}` : ""}.
        </p>
      )}

      <Link to="/create" className="btn btn-primary inline-block">
        Empezar otra carrera
      </Link>
    </div>
  );
}

function Palmares({
  title,
  entries,
  accent,
}: {
  title: string;
  entries: [string, number][];
  accent: string;
}) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-barrio-muted">{title}</p>
      <ul className="mt-2 flex flex-wrap gap-2">
        {entries.map(([name, count]) => (
          <li
            key={name}
            className="rounded border border-barrio-border bg-barrio-bg/40 px-2 py-1 text-xs"
          >
            <span className={accent}>{name}</span>
            {count > 1 && <span className="text-barrio-muted"> ×{count}</span>}
          </li>
        ))}
      </ul>
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
