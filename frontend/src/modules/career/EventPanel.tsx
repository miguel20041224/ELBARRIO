import { useState } from "react";
import clsx from "clsx";
import type { CareerSession, EventChoice } from "@/types/game";
import { useCareerStore } from "@/store/careerStore";
import { careerApi } from "@/api/careerApi";

interface Props {
  session: CareerSession;
  busy: boolean;
}

export default function EventPanel({ session, busy }: Props) {
  const setSession = useCareerStore((state) => state.setSession);
  const setError = useCareerStore((state) => state.setError);
  const [pickingId, setPickingId] = useState<string | null>(null);
  const pending = session.pendingEvent;

  if (!pending) return null;

  const resolveChoice = async (choice: EventChoice) => {
    try {
      setPickingId(choice.id);
      const next = await careerApi.resolveEvent(session.id, {
        choiceId: choice.id,
      });
      setSession(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo resolver el evento");
    } finally {
      setPickingId(null);
    }
  };

  return (
    <div className="panel p-5 space-y-4">
      <div className="flex items-center justify-between">
        <span
          className={clsx(
            "text-[10px] uppercase tracking-widest rounded px-2 py-0.5",
            categoryColor(pending.category),
          )}
        >
          {categoryLabel(pending.category)}
        </span>
        <span className="text-xs text-barrio-muted">
          Temporada {session.currentSeason}
        </span>
      </div>

      <div>
        {session.pendingEventReason && (
          <p className="mb-2 text-xs italic text-barrio-gold border-l-2 border-barrio-gold/50 pl-2">
            ⏳ {session.pendingEventReason}
          </p>
        )}
        <h3 className="heading text-2xl">{pending.title}</h3>
        <p className="mt-3 text-sm leading-relaxed text-barrio-text">
          {pending.narrative}
        </p>
      </div>

      <div className="space-y-2">
        {pending.choices.map((choice) => (
          <button
            key={choice.id}
            type="button"
            className="w-full rounded border border-barrio-border p-3 text-left transition-colors hover:border-barrio-accent hover:bg-barrio-accent/5 disabled:opacity-60"
            onClick={() => resolveChoice(choice)}
            disabled={busy || pickingId !== null}
          >
            <p className="font-semibold text-barrio-text">
              {choice.label}
              {pickingId === choice.id && (
                <span className="ml-2 text-xs text-barrio-muted">
                  Aplicando...
                </span>
              )}
            </p>
            <p className="mt-1 text-sm text-barrio-muted">
              {choice.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}

function categoryColor(category: string) {
  switch (category) {
    case "career":
      return "bg-blue-500/20 text-blue-300";
    case "personal":
      return "bg-pink-500/20 text-pink-300";
    case "social":
      return "bg-purple-500/20 text-purple-300";
    case "financial":
      return "bg-emerald-500/20 text-emerald-300";
    case "media":
      return "bg-yellow-500/20 text-yellow-300";
    case "health":
      return "bg-red-500/20 text-red-300";
    default:
      return "bg-barrio-muted/20 text-barrio-muted";
  }
}

function categoryLabel(category: string) {
  const labels: Record<string, string> = {
    career: "Carrera",
    personal: "Vida personal",
    social: "Social",
    financial: "Financiero",
    media: "Prensa",
    health: "Salud",
  };
  return labels[category] ?? category;
}
