import { useState } from "react";
import clsx from "clsx";
import type { RouletteOutcome, RouletteRoll } from "@/types/game";

interface Props {
  roll: RouletteRoll;
  busy: boolean;
  onSpin: (outcomeId: string) => void;
}

export default function RouletteOverlay({ roll, busy, onSpin }: Props) {
  const [spinning, setSpinning] = useState(false);
  const [selected, setSelected] = useState<RouletteOutcome | null>(null);

  const spin = () => {
    if (busy || spinning) return;
    setSpinning(true);
    let ticks = 0;
    const maxTicks = 18 + Math.floor(Math.random() * 8);
    const finalIndex = Math.floor(Math.random() * roll.options.length);
    const interval = window.setInterval(() => {
      ticks++;
      setSelected(roll.options[ticks % roll.options.length]);
      if (ticks >= maxTicks) {
        window.clearInterval(interval);
        setSelected(roll.options[finalIndex]);
        setSpinning(false);
      }
    }, 90);
  };

  return (
    <div className="panel p-6 space-y-5">
      <div>
        <p className="text-xs uppercase tracking-widest text-barrio-muted">
          {roll.label}
        </p>
        <p className="text-sm text-barrio-text mt-1">
          Girá la ruleta. Puede tocar bien o mal — así es el fútbol.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {roll.options.map((opt) => {
          const isSelected = selected?.id === opt.id;
          return (
            <div
              key={opt.id}
              className={clsx(
                "rounded-md border p-3 text-center transition-all duration-100",
                isSelected
                  ? "scale-105 border-barrio-gold bg-barrio-gold/10 shadow-lg"
                  : "border-barrio-border bg-barrio-bg/40",
                spinning && !isSelected && "opacity-40",
              )}
            >
              <div className="text-3xl">{opt.icon}</div>
              <p className="text-xs mt-1 font-semibold">{opt.title}</p>
              <span
                className={clsx(
                  "text-[9px] uppercase tracking-widest mt-1 inline-block",
                  opt.tone === "positive" && "text-barrio-accent",
                  opt.tone === "negative" && "text-barrio-danger",
                  opt.tone === "gift" && "text-barrio-gold",
                )}
              >
                {toneLabel(opt.tone)}
              </span>
            </div>
          );
        })}
      </div>

      {selected && !spinning && (
        <div className="rounded-md border border-barrio-gold/40 bg-barrio-gold/5 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{selected.icon}</span>
            <p className="font-display text-xl">{selected.title}</p>
          </div>
          <p className="text-sm text-barrio-muted">{selected.description}</p>
        </div>
      )}

      <div className="flex justify-end gap-2">
        {!selected || spinning ? (
          <button
            type="button"
            className="btn btn-gold"
            onClick={spin}
            disabled={busy || spinning}
          >
            {spinning ? "Girando..." : "Girar ruleta"}
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            disabled={busy}
            onClick={() => onSpin(selected.id)}
          >
            Aceptar
          </button>
        )}
      </div>
    </div>
  );
}

function toneLabel(tone: string) {
  switch (tone) {
    case "positive":
      return "Mejora";
    case "negative":
      return "Castigo";
    case "gift":
      return "Regalo";
    default:
      return tone;
  }
}
