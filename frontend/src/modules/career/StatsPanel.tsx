import type { Player } from "@/types/game";

interface Props {
  player: Player;
}

export default function StatsPanel({ player }: Props) {
  return (
    <div className="panel p-5 space-y-5">
      <h3 className="heading text-lg text-barrio-gold">Estado actual</h3>

      <Group title="Vida">
        <Bar label="Forma" value={player.state.form} tone="green" />
        <Bar label="Moral" value={player.state.morale} tone="green" />
        <Bar label="Fitness" value={player.state.fitness} tone="green" />
        <Bar label="Fatiga" value={player.state.fatigue} tone="red" invert />
        <Bar label="Presión" value={player.state.pressure} tone="red" invert />
        <Bar label="Felicidad" value={player.state.happiness} tone="gold" />
        <Bar label="Reputación" value={player.state.reputation} tone="gold" />
      </Group>

      <Group title="Técnica">
        <Bar label="Velocidad" value={player.technical.pace} tone="green" />
        <Bar label="Regate" value={player.technical.dribbling} tone="green" />
        <Bar label="Pase" value={player.technical.passing} tone="green" />
        <Bar label="Tiro" value={player.technical.shooting} tone="green" />
        <Bar label="Cabeza" value={player.technical.heading} tone="green" />
        <Bar label="Defensa" value={player.technical.defending} tone="green" />
      </Group>

      <Group title="Mental">
        <Bar label="Concentración" value={player.mental.concentration} tone="gold" />
        <Bar label="Templanza" value={player.mental.composure} tone="gold" />
        <Bar label="Trabajo" value={player.mental.workRate} tone="gold" />
        <Bar label="Liderazgo" value={player.mental.leadership} tone="gold" />
        <Bar label="Visión" value={player.mental.vision} tone="gold" />
      </Group>

      <Group title="Vínculos">
        <Bar label="DT" value={player.relationships.coach} tone="green" />
        <Bar label="Vestuario" value={player.relationships.teammates} tone="green" />
        <Bar label="Hinchada" value={player.relationships.fans} tone="green" />
        <Bar label="Prensa" value={player.relationships.press} tone="green" />
        <Bar label="Familia" value={player.relationships.family} tone="green" />
      </Group>
    </div>
  );
}

function Group({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-widest text-barrio-muted">
        {title}
      </p>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function Bar({
  label,
  value,
  tone,
  invert = false,
}: {
  label: string;
  value: number;
  tone: "green" | "red" | "gold";
  invert?: boolean;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const displayValue = invert ? 100 - clamped : clamped;
  const color =
    tone === "green"
      ? "bg-barrio-accent"
      : tone === "red"
        ? "bg-barrio-danger"
        : "bg-barrio-gold";
  return (
    <div className="grid grid-cols-[110px_1fr_36px] items-center gap-2 text-xs">
      <span className="text-barrio-muted">{label}</span>
      <div className="stat-bar">
        <div className={color} style={{ width: `${displayValue}%` }} />
      </div>
      <span className="text-right tabular-nums">{Math.round(clamped)}</span>
    </div>
  );
}
