import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CareerSession, Player } from "@/types/game";

/**
 * Estado de sincronización con el servidor.
 *
 * `session` es una CACHÉ de lo que el backend tiene persistido, nunca la fuente
 * de verdad. Se guarda en localStorage sólo para pintar algo mientras llega la
 * respuesta del servidor y para conocer el id de la carrera entre recargas.
 */
type SyncStatus = "idle" | "syncing" | "synced" | "offline";

interface CareerState {
  session: CareerSession | null;
  loading: boolean;
  error: string | null;
  syncStatus: SyncStatus;
  setSession: (session: CareerSession | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSyncStatus: (status: SyncStatus) => void;
  updatePlayer: (patch: Partial<Player>) => void;
}

export const useCareerStore = create<CareerState>()(
  persist(
    (set) => ({
      session: null,
      loading: false,
      error: null,
      syncStatus: "idle",
      setSession: (session) => set({ session }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setSyncStatus: (syncStatus) => set({ syncStatus }),
      updatePlayer: (patch) =>
        set((prev) =>
          prev.session
            ? {
                session: {
                  ...prev.session,
                  player: { ...prev.session.player, ...patch },
                },
              }
            : prev,
        ),
    }),
    {
      name: "elbarrio.career",
      // Sólo la caché de la sesión sobrevive a la recarga. El estado de
      // sincronización y los errores se recalculan siempre contra el servidor.
      partialize: (state) => ({ session: state.session }),
    },
  ),
);
