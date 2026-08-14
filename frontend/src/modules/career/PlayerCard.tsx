import type { ClubInfo, Player } from "@/types/game";
import { COUNTRIES } from "@/data/countries";
import { POSITIONS } from "@/data/positions";

interface Props {
  player: Player;
  season: number;
  club: ClubInfo | null;
}

export default function PlayerCard({ player, season, club }: Props) {
  const country = COUNTRIES.find((c) => c.code === player.birthCountry);
  const position = POSITIONS.find((p) => p.code === player.position);

  return (
    <div className="panel p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Temporada {season}
          </p>
          <h2 className="heading text-2xl leading-tight">
            {player.firstName}{" "}
            <span className="text-barrio-accent">{player.lastName}</span>
          </h2>
          {player.nickname && (
            <p className="text-sm text-barrio-muted italic">
              "{player.nickname}"
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="font-display text-5xl text-barrio-gold leading-none">
            {player.shirtNumber}
          </p>
          <p className="mt-1 text-xs uppercase tracking-widest text-barrio-muted">
            {position?.code}
          </p>
        </div>
      </div>

      {club && (
        <div className="rounded-md border border-barrio-accent/30 bg-barrio-accent/5 p-3">
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Club actual
          </p>
          <p className="text-lg font-semibold text-barrio-accent leading-tight">
            {club.name}
          </p>
          <p className="text-xs text-barrio-muted">
            {club.leagueName} · {club.city}
            {club.nickname && (
              <span className="text-barrio-gold"> · {club.nickname}</span>
            )}
          </p>
          <p className="text-[10px] uppercase tracking-widest text-barrio-muted mt-1">
            Prestigio {club.prestige} · Presupuesto €{(club.budget / 1_000_000).toFixed(1)}M
          </p>
        </div>
      )}

      <dl className="grid grid-cols-2 gap-3 text-sm">
        <Row label="Edad">{player.age}</Row>
        <Row label="Origen">
          {country?.flag} {country?.name}
        </Row>
        <Row label="Posición">{position?.name}</Row>
        <Row label="Pie">{player.preferredFoot}</Row>
        <Row label="Partidos">{player.matchesPlayed}</Row>
        <Row label="Goles / Asist">
          {player.goals} / {player.assists}
        </Row>
        <Row label="Salario">
          €{Math.round(player.finance.weeklySalary).toLocaleString()}/sem
        </Row>
        <Row label="Balance">
          €{Math.round(player.finance.balance).toLocaleString()}
        </Row>
      </dl>

      {player.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {player.tags.map((tag) => (
            <span
              key={tag}
              className="text-[10px] uppercase tracking-widest rounded bg-barrio-border/60 text-barrio-muted px-2 py-0.5"
            >
              {tagLabel(tag)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function tagLabel(tag: string) {
  const labels: Record<string, string> = {
    married: "Casado",
    engaged: "Comprometido",
    father: "Padre",
    single: "Soltero",
    experimented_drugs: "Consumió",
    banned_doping: "Sancionado",
    european_transfer: "Fichado Europa",
    saudi_move: "Saudí",
    local_hero: "Ídolo local",
    national_team: "Selección",
    serious_injury: "Lesión grave",
  };
  return labels[tag] ?? tag;
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-widest text-barrio-muted">
        {label}
      </dt>
      <dd className="text-barrio-text">{children}</dd>
    </div>
  );
}
