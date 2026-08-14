import { useState } from "react";
import clsx from "clsx";
import type { PlayingChance, TransferOffer, TransferWindow } from "@/types/game";

interface Props {
  window: TransferWindow;
  busy: boolean;
  onAccept: (offerId: string | null) => void;
}

export default function TransferWindowPanel({ window, busy, onAccept }: Props) {
  const [selected, setSelected] = useState<TransferOffer | null>(null);
  const [pickedStay, setPickedStay] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const handleConfirm = () => {
    if (confirming || busy) return;
    setConfirming(true);
    onAccept(selected ? selected.id : null);
  };

  return (
    <div className="panel p-6 space-y-5">
      <div>
        <p className="text-xs uppercase tracking-widest text-barrio-muted">
          {window.label}
        </p>
        <h3 className="heading text-2xl">Ventana de fichajes</h3>
        <p className="text-sm text-barrio-muted mt-2">
          {reasonCopy[window.reason]}
        </p>
        <p className="mt-2 text-xs text-barrio-muted">
          Contrato restante: {window.contractYearsRemaining} año
          {window.contractYearsRemaining === 1 ? "" : "s"}
          {window.renewalOfferYears
            ? ` · Renovación disponible por ${window.renewalOfferYears} años`
            : ""}
        </p>
      </div>

      {window.currentClub && (
        <button
          type="button"
          onClick={() => {
            setSelected(null);
            setPickedStay(true);
          }}
          className={clsx(
            "w-full rounded border p-4 text-left transition-colors",
            pickedStay
              ? "border-barrio-gold bg-barrio-gold/10"
              : "border-barrio-border hover:border-barrio-muted",
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-widest text-barrio-muted">
                Renovar / Quedarme
              </p>
              <p className="text-lg font-semibold text-barrio-gold">
                {window.currentClub.name}
              </p>
              <p className="text-xs text-barrio-muted">
                {window.currentClub.leagueName} · Prestigio{" "}
                {window.currentClub.prestige}
              </p>
            </div>
            <span className="text-3xl">🎩</span>
          </div>
          <p className="text-sm text-barrio-text mt-2">{window.stayNote}</p>
        </button>
      )}

      <div className="space-y-3">
        <p className="text-xs uppercase tracking-widest text-barrio-muted">
          Ofertas ({window.offers.length})
        </p>
        {window.offers.map((offer) => {
          const isSelected = selected?.id === offer.id;
          return (
            <button
              key={offer.id}
              type="button"
              onClick={() => {
                setSelected(offer);
                setPickedStay(false);
              }}
              className={clsx(
                "w-full rounded border p-4 text-left transition-colors",
                isSelected
                  ? "border-barrio-accent bg-barrio-accent/10"
                  : "border-barrio-border hover:border-barrio-muted",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-lg font-semibold">{offer.club.name}</p>
                    {offer.highlight && (
                      <span className="text-[10px] uppercase tracking-widest bg-barrio-gold/20 text-barrio-gold rounded px-2 py-0.5">
                        {offer.highlight}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-barrio-muted">
                    {offer.club.leagueName} · {offer.club.city} · Prestigio{" "}
                    {offer.club.prestige}
                  </p>
                </div>
                <PlayingBadge chance={offer.playingChance} />
              </div>

              <dl className="mt-3 grid grid-cols-4 gap-3 text-xs">
                <div>
                  <dt className="text-barrio-muted uppercase tracking-widest">
                    Salario
                  </dt>
                  <dd className="text-barrio-accent font-semibold">
                    €{Math.round(offer.weeklySalary).toLocaleString()}/sem
                  </dd>
                </div>
                <div>
                  <dt className="text-barrio-muted uppercase tracking-widest">
                    Firma
                  </dt>
                  <dd className="text-barrio-gold font-semibold">
                    €{Math.round(offer.signOnBonus).toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className="text-barrio-muted uppercase tracking-widest">
                    Contrato
                  </dt>
                  <dd>{offer.contractYears} años</dd>
                </div>
                <div>
                  <dt className="text-barrio-muted uppercase tracking-widest">
                    Operación
                  </dt>
                  <dd>{operationLabel(offer)}</dd>
                </div>
              </dl>

              <p className="mt-3 text-sm text-barrio-text">{offer.note}</p>
            </button>
          );
        })}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-barrio-border">
        <p className="text-xs text-barrio-muted">
          {selected
            ? `Elegiste ${selected.club.name}`
            : pickedStay
              ? `Te quedás en ${window.currentClub?.name ?? "tu club"}`
              : "Elegí una opción arriba"}
        </p>
        <button
          type="button"
          className="btn btn-primary"
          disabled={busy || confirming || (!selected && !pickedStay)}
          onClick={handleConfirm}
        >
          {confirming ? "Firmando..." : "Confirmar"}
        </button>
      </div>
    </div>
  );
}

const reasonCopy = {
  expiring_contract:
    "Tu contrato entra en el último año. Ahora sí hay mercado real: el club escucha ofertas o te renueva.",
  release_clause:
    "Tenés contrato largo. Solo aparecen ofertas serias porque están dispuestos a pagar la cláusula.",
  transfer_request:
    "Pediste salir. El club abre la puerta, pero la operación todavía tiene costo deportivo y emocional.",
  free_agent:
    "Terminó tu contrato. Llegás libre y negociás como dueño de tu pase.",
  loan:
    "No estás jugando lo suficiente. Una cesión puede darte minutos sin romper el contrato principal.",
};

function operationLabel(offer: TransferOffer) {
  if (offer.transferKind === "free_agent") return "Libre";
  if (offer.transferKind === "loan") return "Cesión";
  if (offer.paysReleaseClause) {
    return `Cláusula €${Math.round(offer.transferFee).toLocaleString()}`;
  }
  return "Traspaso";
}

function PlayingBadge({ chance }: { chance: PlayingChance }) {
  const config = {
    starter: { label: "Titular", color: "bg-barrio-accent/20 text-barrio-accent" },
    rotation: { label: "Rotación", color: "bg-barrio-gold/20 text-barrio-gold" },
    backup: { label: "Suplente", color: "bg-barrio-muted/20 text-barrio-muted" },
  }[chance];
  return (
    <span
      className={clsx(
        "text-[10px] uppercase tracking-widest rounded px-2 py-1 shrink-0",
        config.color,
      )}
    >
      {config.label}
    </span>
  );
}
