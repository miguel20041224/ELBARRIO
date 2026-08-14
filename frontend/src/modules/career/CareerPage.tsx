import { useState } from "react";
import { Link } from "react-router-dom";
import { useCareerStore } from "@/store/careerStore";
import { careerApi } from "@/api/careerApi";
import PlayerCard from "./PlayerCard";
import StatsPanel from "./StatsPanel";
import EventPanel from "./EventPanel";
import SeasonHistory from "./SeasonHistory";
import TrophiesPanel from "./TrophiesPanel";
import RouletteOverlay from "./RouletteOverlay";
import SeasonProgressPanel from "./SeasonProgressPanel";
import TransferWindowPanel from "./TransferWindowPanel";

export default function CareerPage() {
  const session = useCareerStore((state) => state.session);
  const setSession = useCareerStore((state) => state.setSession);
  const setError = useCareerStore((state) => state.setError);
  const [busy, setBusy] = useState(false);

  const wrap = async (fn: () => Promise<unknown>) => {
    try {
      setBusy(true);
      setError(null);
      await fn();
    } catch (err) {
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

  if (!session) {
    return (
      <div className="panel p-8 text-center space-y-4">
        <p className="text-barrio-muted">
          Todavía no arrancaste ninguna carrera.
        </p>
        <Link to="/create" className="btn btn-primary">
          Crear jugador
        </Link>
      </div>
    );
  }

  return (
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
        {session.pendingRoulette ? (
          <RouletteOverlay
            roll={session.pendingRoulette}
            busy={busy}
            onSpin={spinRoulette}
          />
        ) : session.pendingTransferWindow ? (
          <TransferWindowPanel
            window={session.pendingTransferWindow}
            busy={busy}
            onAccept={acceptTransfer}
          />
        ) : session.pendingEvent ? (
          <EventPanel session={session} busy={busy} />
        ) : (
          <SeasonProgressPanel
            progress={session.seasonProgress}
            seasonComplete={session.seasonComplete}
            season={session.currentSeason}
            busy={busy}
            onPlayMatch={playMatch}
            onAdvanceSeason={advanceSeason}
          />
        )}
        <SeasonHistory history={session.history} />
      </div>
    </div>
  );
}
