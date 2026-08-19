import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useCareerStore } from "@/store/careerStore";
import { careerApi } from "@/api/careerApi";
import { ApiError } from "@/api/client";
import PlayerCard from "./PlayerCard";
import StatsPanel from "./StatsPanel";
import EventPanel from "./EventPanel";
import SeasonHistory from "./SeasonHistory";
import TrophiesPanel from "./TrophiesPanel";
import RouletteOverlay from "./RouletteOverlay";
import SeasonProgressPanel from "./SeasonProgressPanel";
import TransferWindowPanel from "./TransferWindowPanel";
import RetirementPanel from "./RetirementPanel";
import CareerEndPanel from "./CareerEndPanel";

export default function CareerPage() {
  const session = useCareerStore((state) => state.session);
  const setSession = useCareerStore((state) => state.setSession);
  const error = useCareerStore((state) => state.error);
  const setError = useCareerStore((state) => state.setError);
  const syncStatus = useCareerStore((state) => state.syncStatus);
  const setSyncStatus = useCareerStore((state) => state.setSyncStatus);
  const [busy, setBusy] = useState(false);

  const sessionId = session?.id ?? null;

  // El servidor es la fuente de verdad. Lo que hay en localStorage es una caché
  // que puede estar obsoleta (otra pestaña, otro dispositivo, una petición que
  // se perdió), así que al montar se relee siempre el estado real.
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    const hydrate = async () => {
      setSyncStatus("syncing");
      try {
        const fresh = await careerApi.get(sessionId);
        if (cancelled) return;
        setSession(fresh);
        setError(null);
        setSyncStatus("synced");
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          // La carrera ya no existe en el servidor: la caché local es basura.
          setSession(null);
          setError(
            "Esta carrera ya no existe en el servidor. Creá una nueva para empezar.",
          );
          setSyncStatus("idle");
          return;
        }
        setSyncStatus("offline");
        setError(
          err instanceof Error
            ? `No se pudo sincronizar con el servidor: ${err.message}`
            : "No se pudo sincronizar con el servidor.",
        );
      }
    };

    void hydrate();
    return () => {
      cancelled = true;
    };
  }, [sessionId, setSession, setError, setSyncStatus]);

  const wrap = async (fn: () => Promise<unknown>) => {
    try {
      setBusy(true);
      setError(null);
      await fn();
      setSyncStatus("synced");
    } catch (err) {
      setSyncStatus("offline");
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setBusy(false);
    }
  };

  const playMatch = () =>
    wrap(async () => {
      if (!session) return;
      const next = await careerApi.playMatch(session.id);
      setSession(next);
    });

  const spinRoulette = (outcomeId: string) =>
    wrap(async () => {
      if (!session) return;
      const next = await careerApi.spinRoulette(session.id, { outcomeId });
      setSession(next);
    });

  const advanceSeason = () =>
    wrap(async () => {
      if (!session) return;
      const next = await careerApi.advanceSeason(session.id);
      setSession(next);
    });

  const acceptTransfer = (offerId: string | null) =>
    wrap(async () => {
      if (!session) return;
      const next = await careerApi.acceptTransfer(session.id, { offerId });
      setSession(next);
    });

  const resolveRetirement = (retire: boolean) =>
    wrap(async () => {
      if (!session) return;
      const next = await careerApi.resolveRetirement(session.id, { retire });
      setSession(next);
    });

  if (!session) {
    return (
      <div className="panel p-8 text-center space-y-4">
        {error ? (
          <p role="alert" className="text-sm text-red-300">
            {error}
          </p>
        ) : null}
        <p className="text-barrio-muted">
          Todavía no arrancaste ninguna carrera.
        </p>
        <Link to="/create" className="btn btn-primary">
          Crear jugador
        </Link>
      </div>
    );
  }

  const syncing = syncStatus === "syncing";
  const actionsBusy = busy || syncing;

  return (
    <div className="space-y-4">
      {error ? (
        <div
          role="alert"
          className="panel border border-red-500/50 bg-red-950/40 p-4 flex flex-wrap items-center justify-between gap-3"
        >
          <div className="space-y-1">
            <p className="font-semibold text-red-300">
              {syncStatus === "offline"
                ? "Sin conexión con el servidor"
                : "Algo salió mal"}
            </p>
            <p className="text-sm text-red-200/90">{error}</p>
          </div>
          <button
            type="button"
            className="btn"
            disabled={syncing}
            onClick={() => {
              if (!sessionId) return;
              void wrap(async () => {
                const fresh = await careerApi.get(sessionId);
                setSession(fresh);
              });
            }}
          >
            {syncing ? "Reintentando…" : "Reintentar"}
          </button>
        </div>
      ) : null}

      {syncing ? (
        <p className="text-sm text-barrio-muted" aria-live="polite">
          Sincronizando con el servidor…
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        <div className="space-y-6">
          <PlayerCard
            player={session.player}
            season={session.currentSeason}
            club={session.currentClub}
          />
          <StatsPanel player={session.player} />
          <TrophiesPanel player={session.player} />
        </div>

        <div className="space-y-6">
          {session.player.retired ? (
            <CareerEndPanel session={session} />
          ) : session.pendingRetirement ? (
            <RetirementPanel
              offer={session.pendingRetirement}
              busy={actionsBusy}
              onResolve={resolveRetirement}
            />
          ) : session.pendingRoulette ? (
            <RouletteOverlay
              roll={session.pendingRoulette}
              busy={actionsBusy}
              onSpin={spinRoulette}
            />
          ) : session.pendingTransferWindow ? (
            <TransferWindowPanel
              window={session.pendingTransferWindow}
              busy={actionsBusy}
              onAccept={acceptTransfer}
            />
          ) : session.pendingEvent ? (
            <EventPanel session={session} busy={actionsBusy} />
          ) : (
            <SeasonProgressPanel
              progress={session.seasonProgress}
              selection={session.nextMatchSelection}
              seasonComplete={session.seasonComplete}
              season={session.currentSeason}
              busy={actionsBusy}
              onPlayMatch={playMatch}
              onAdvanceSeason={advanceSeason}
            />
          )}
          <SeasonHistory
            history={session.history}
            position={session.player.position}
          />
        </div>
      </div>
    </div>
  );
}
