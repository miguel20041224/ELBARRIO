import clsx from "clsx";
import { POSITIONS } from "@/data/positions";
import { useCreationStore } from "@/store/creationStore";
import type { PlayerFoot } from "@/types/game";

const FEET: { value: PlayerFoot; label: string }[] = [
  { value: "right", label: "Derecha" },
  { value: "left", label: "Izquierda" },
  { value: "both", label: "Ambas" },
];

export default function PositionStep() {
  const draft = useCreationStore((state) => state.draft);
  const update = useCreationStore((state) => state.update);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="heading text-2xl">Posición y número</h2>
        <p className="text-sm text-barrio-muted">
          Elegí en qué parte de la cancha querés jugar. Cada posición prioriza
          stats distintos — el motor entrena eso primero.
        </p>
      </header>

      <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
        {POSITIONS.map((p) => {
          const selected = draft.position === p.code;
          return (
            <button
              key={p.code}
              type="button"
              onClick={() => update({ position: p.code })}
              className={clsx(
                "rounded border p-3 text-left transition-colors",
                selected
                  ? "border-barrio-accent bg-barrio-accent/10"
                  : "border-barrio-border hover:border-barrio-muted",
              )}
            >
              <div className="flex items-center justify-between">
                <p className="font-display text-xl">{p.code}</p>
                <span
                  className={clsx(
                    "text-[10px] uppercase tracking-widest rounded px-2 py-0.5",
                    p.category === "goalkeeper" && "bg-yellow-500/20 text-yellow-300",
                    p.category === "defender" && "bg-blue-500/20 text-blue-300",
                    p.category === "midfielder" && "bg-green-500/20 text-green-300",
                    p.category === "forward" && "bg-red-500/20 text-red-300",
                  )}
                >
                  {p.category}
                </span>
              </div>
              <p className="text-sm font-semibold mt-1">{p.name}</p>
              <p className="text-xs text-barrio-muted">
                {p.primaryStats.join(" · ")}
              </p>
            </button>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs uppercase tracking-widest text-barrio-muted">
            Número de camiseta
          </label>
          <input
            type="number"
            min={1}
            max={99}
            value={draft.shirtNumber}
            onChange={(e) => update({ shirtNumber: Number(e.target.value) })}
            className="w-full bg-barrio-border/50 border border-barrio-border rounded px-3 py-2 focus:border-barrio-accent focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-widest text-barrio-muted">
            Pierna hábil
          </label>
          <div className="flex gap-2">
            {FEET.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => update({ preferredFoot: f.value })}
                className={clsx(
                  "flex-1 rounded border px-3 py-2 text-sm transition-colors",
                  draft.preferredFoot === f.value
                    ? "border-barrio-accent bg-barrio-accent/10 text-barrio-accent"
                    : "border-barrio-border hover:border-barrio-muted",
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
