import clsx from "clsx";
import type { MatchResult, MatchSelection, SeasonProgress } from "@/types/game";

interface Props {
  progress: SeasonProgress;
  selection: MatchSelection | null;
  seasonComplete: boolean;
  season: number;
  busy: boolean;
  onPlayMatch: () => void;
  onAdvanceSeason: () => void;
}

export default function SeasonProgressPanel({
  progress,
  selection,
  seasonComplete,
  season,
  busy,
  onPlayMatch,
  onAdvanceSeason,
}: Props) {
  const matchesRemaining = Math.max(0, progress.matchesTotal - progress.matchesPlayed);
  const nextFixture = progress.fixtures?.[progress.matchesPlayed];
  const competitionProgress = progress.competitionProgress ?? [];
  const leagueTable = progress.leagueTable ?? [];
  const playerLeagueRow = leagueTable.find(
    (row) => row.position === progress.leaguePosition,
  );
  const percent = Math.min(
    100,
    Math.round((progress.matchesPlayed / Math.max(1, progress.matchesTotal)) * 100),
  );
  const avgRating =
    progress.appearances > 0
      ? (progress.ratingsSum / progress.appearances).toFixed(2)
      : "—";

  return (
    <div className="panel p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Temporada {season}
          </p>
          <p className="heading text-2xl leading-none">
            Fecha {progress.matchesPlayed} / {progress.matchesTotal}
          </p>
          {nextFixture && (
            <p className="mt-1 text-xs text-barrio-muted">
              Próximo: {nextFixture.stageDisplay} · {nextFixture.competitionName} · {nextFixture.homeAway === "away" ? "@" : nextFixture.homeAway === "neutral" ? "N" : "vs"} {nextFixture.opponentShortName}
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Eventos usados
          </p>
          <p className="font-display text-2xl text-barrio-gold">
            {progress.eventsUsed} / {progress.eventsMax}
          </p>
        </div>
      </div>

      <div className="stat-bar h-3">
        <div className="bg-barrio-accent" style={{ width: `${percent}%` }} />
      </div>

      <div className="grid grid-cols-4 gap-3 text-center">
        <Stat label="Goles" value={progress.goals.toString()} />
        <Stat label="Asist." value={progress.assists.toString()} />
        <Stat label="Rating" value={avgRating} />
        <Stat
          label="V-E-D"
          value={`${progress.wins}-${progress.draws}-${progress.losses}`}
        />
      </div>

      {progress.leaguePosition && (
        <div className="rounded border border-barrio-border/60 bg-barrio-bg/30 px-3 py-2 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-barrio-muted">Posición en liga</span>
            <span className="font-display text-xl text-barrio-gold">
              #{progress.leaguePosition}
            </span>
          </div>
          <p className="text-xs text-barrio-muted">
            {playerLeagueRow
              ? `${playerLeagueRow.points} pts · ${playerLeagueRow.wins}-${playerLeagueRow.draws}-${playerLeagueRow.losses}`
              : "Tabla en construcción"}
            {progress.leaguePointsFromTop
              ? ` · a ${progress.leaguePointsFromTop} pts del líder`
              : progress.leaguePosition === 1
                ? " · líderes"
                : ""}
          </p>
        </div>
      )}

      {selection && nextFixture && (
        <SelectionCard selection={selection} opponent={nextFixture.opponentShortName} />
      )}

      {competitionProgress.length > 0 && (
        <div className="grid gap-2 sm:grid-cols-2">
          {competitionProgress.map((competition) => (
            <div
              key={competition.competitionId}
              className="rounded border border-barrio-border/60 bg-barrio-bg/30 px-3 py-2"
            >
              <p className="text-[10px] uppercase tracking-widest text-barrio-muted">
                {competition.currentStage}
              </p>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate">{competition.competitionName}</span>
                <span className="tabular-nums text-barrio-gold">
                  {competition.played}/{competition.total}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        {!seasonComplete && (
          <button
            type="button"
            className="btn btn-primary flex-1"
            disabled={busy}
            onClick={onPlayMatch}
          >
            {busy
              ? "Simulando..."
              : nextFixture
                ? `Jugar ${nextFixture.competitionName}`
                : `Jugar fecha (${matchesRemaining} restantes)`}
          </button>
        )}
        {seasonComplete && (
          <button
            type="button"
            className="btn btn-gold flex-1"
            disabled={busy}
            onClick={onAdvanceSeason}
          >
            Cerrar temporada
          </button>
        )}
      </div>

      {leagueTable.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-barrio-border">
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Tabla de liga
          </p>
          <ul className="space-y-1">
            {leagueTable.slice(0, 5).map((row) => (
              <li
                key={row.clubId}
                className={clsx(
                  "flex items-center justify-between rounded border px-3 py-1 text-xs",
                  row.position === progress.leaguePosition
                    ? "border-barrio-gold bg-barrio-gold/10"
                    : "border-barrio-border/60 bg-barrio-bg/30",
                )}
              >
                <span className="truncate">
                  {row.position}. {row.shortName}
                </span>
                <span className="tabular-nums text-barrio-muted">
                  {row.points} pts · DG {row.goalDifference}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {progress.recentMatches.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-barrio-border">
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Últimos partidos
          </p>
          <ul className="space-y-1">
            {[...progress.recentMatches].reverse().map((m) => (
              <MatchRow key={m.matchNumber} match={m} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}


function SelectionCard({
  selection,
  opponent,
}: {
  selection: MatchSelection;
  opponent: string;
}) {
  const roleLabel = {
    starter: "Titular probable",
    substitute: "Cambio probable",
    bench: "Banco probable",
  }[selection.role];
  const roleTone = {
    starter: "text-barrio-accent",
    substitute: "text-barrio-gold",
    bench: "text-barrio-muted",
  }[selection.role];

  return (
    <div className="rounded border border-barrio-gold/40 bg-barrio-gold/10 px-4 py-3 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-barrio-muted">
            Convocatoria vs {opponent}
          </p>
          <p className={clsx("font-display text-xl", roleTone)}>{roleLabel}</p>
        </div>
        <div className="text-right text-xs text-barrio-muted">
          <p>{selection.starterChance}% titular</p>
          <p>{selection.substituteChance}% entrar</p>
        </div>
      </div>
      <p className="mt-2 text-barrio-text/90">{selection.coachMessage}</p>
      <p className="mt-1 text-xs text-barrio-muted">
        Minutos esperados: {selection.expectedMinutesMin}-{selection.expectedMinutesMax}'
      </p>
      {selection.factors.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-2 text-[11px] text-barrio-muted">
          {selection.factors.map((factor) => (
            <li
              key={factor}
              className="rounded-full border border-barrio-border/70 px-2 py-1"
            >
              {factor}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-barrio-border bg-barrio-bg/40 py-2">
      <p className="text-xs uppercase tracking-widest text-barrio-muted">
        {label}
      </p>
      <p className="font-display text-lg tabular-nums">{value}</p>
    </div>
  );
}

function MatchRow({ match }: { match: MatchResult }) {
  const resultColor = {
    W: "text-barrio-accent",
    D: "text-barrio-muted",
    L: "text-barrio-danger",
  }[match.result];
  const homeFirst = match.homeAway === "home" || match.homeAway === "neutral";
  const regulationScore = homeFirst
    ? `${match.goalsFor}-${match.goalsAgainst}`
    : `${match.goalsAgainst}-${match.goalsFor}`;
  // A knockout tie level after 90 minutes is settled on penalties, so the plain
  // scoreline would read as a draw that decided nothing.
  const shootout =
    match.penaltiesFor !== null && match.penaltiesAgainst !== null
      ? homeFirst
        ? ` (${match.penaltiesFor}-${match.penaltiesAgainst} pen.)`
        : ` (${match.penaltiesAgainst}-${match.penaltiesFor} pen.)`
      : "";
  const scoreDisplay = `${regulationScore}${shootout}`;
  const venue =
    match.homeAway === "home" ? "vs" : match.homeAway === "away" ? "@" : "N";

  return (
    <li className="rounded border border-barrio-border/60 bg-barrio-bg/30 px-3 py-2 text-xs">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span
            className={clsx(
              "text-[10px] uppercase w-4 text-center font-bold",
              resultColor,
            )}
          >
            {match.result}
          </span>
          <span className="text-barrio-muted">{venue}</span>
          <span className="truncate">{match.opponentShortName}</span>
          <span className="tabular-nums font-semibold">{scoreDisplay}</span>
          <span className="hidden sm:inline truncate text-barrio-muted">
            {match.stageDisplay
              ? `${match.stageDisplay} · ${match.competitionName}`
              : match.competitionName}
          </span>
        </div>
        {match.minutesPlayed > 0 ? (
          <div className="flex items-center gap-2 shrink-0 text-barrio-muted">
            <span>{match.minutesPlayed}'</span>
            {match.goals > 0 && (
              <span className="text-barrio-gold">⚽{match.goals}</span>
            )}
            {match.assists > 0 && (
              <span className="text-barrio-accent">🅰{match.assists}</span>
            )}
            <span
              className={clsx(
                "tabular-nums",
                match.rating >= 7.5 && "text-barrio-accent",
                match.rating < 6.0 && "text-barrio-danger",
              )}
            >
              {match.rating.toFixed(1)}
            </span>
            {match.momPlayer && <span title="Man of the match">🌟</span>}
          </div>
        ) : (
          <span className="text-barrio-muted italic shrink-0">Banco</span>
        )}
      </div>
    </li>
  );
}
