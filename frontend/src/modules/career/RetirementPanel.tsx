import { useState } from "react";
import type { RetirementOffer } from "@/types/game";

interface Props {
  offer: RetirementOffer;
  busy: boolean;
  onResolve: (retire: boolean) => void;
}

export default function RetirementPanel({ offer, busy, onResolve }: Props) {
  const [confirming, setConfirming] = useState(false);

  const resolve = (retire: boolean) => {
    if (confirming || busy) return;
    setConfirming(true);
    onResolve(retire);
  };

  return (
    <div className="panel p-6 space-y-5 border border-barrio-gold/40">
      <div>
        <p className="text-xs uppercase tracking-widest text-barrio-muted">
          Fin de temporada · {offer.age} años · {offer.seasonsPlayed} temporadas
        </p>
        <h3 className="heading text-2xl">{offer.title}</h3>
        <p className="text-sm text-barrio-muted mt-2">{offer.message}</p>
      </div>

      {offer.reasons.length > 0 && (
        <ul className="space-y-1 text-sm text-barrio-muted">
          {offer.reasons.map((reason) => (
            <li key={reason} className="flex gap-2">
              <span aria-hidden="true">·</span>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      )}

      {!offer.forced && (
        <p className="rounded border border-amber-500/40 bg-amber-950/30 p-3 text-sm text-amber-200/90">
          {offer.stayWarning}
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="btn btn-primary"
          disabled={busy || confirming}
          onClick={() => resolve(true)}
        >
          Colgar los botines
        </button>
        {/* A los 40 seguir ya no es una opción: ofrecerla sería mentir. */}
        {!offer.forced && (
          <button
            type="button"
            className="btn"
            disabled={busy || confirming}
            onClick={() => resolve(false)}
          >
            Seguir un año más
          </button>
        )}
      </div>
    </div>
  );
}
