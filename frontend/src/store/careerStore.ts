import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CareerSession, Player } from "@/types/game";

interface CareerState {
  session: CareerSession | null;
  loading: boolean;
  error: string | null;
  setSession: (session: CareerSession | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updatePlayer: (patch: Partial<Player>) => void;
}

export const useCareerStore = create<CareerState>()(
  persist(
    (set) => ({
      session: null,
      loading: false,
      error: null,
      setSession: (session) => set({ session }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
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
    { name: "elbarrio.career" },
  ),
);
