import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PlayerFoot, Position } from "@/types/game";

export interface CreationDraft {
  firstName: string;
  lastName: string;
  nickname: string;
  birthCountry: string;
  startingLeague: string;
  startingClub: string | null;
  position: Position | null;
  secondaryPositions: Position[];
  shirtNumber: number;
  preferredFoot: PlayerFoot;
  age: number;
  height: number;
  weight: number;
}

interface CreationState {
  step: number;
  draft: CreationDraft;
  setStep: (step: number) => void;
  update: (patch: Partial<CreationDraft>) => void;
  reset: () => void;
}

const initialDraft: CreationDraft = {
  firstName: "",
  lastName: "",
  nickname: "",
  birthCountry: "",
  startingLeague: "",
  startingClub: null,
  position: null,
  secondaryPositions: [],
  shirtNumber: 10,
  preferredFoot: "right",
  age: 17,
  height: 178,
  weight: 72,
};

export const useCreationStore = create<CreationState>()(
  persist(
    (set) => ({
      step: 0,
      draft: initialDraft,
      setStep: (step) => set({ step }),
      update: (patch) =>
        set((prev) => ({ draft: { ...prev.draft, ...patch } })),
      reset: () => set({ step: 0, draft: initialDraft }),
    }),
    { name: "elbarrio.creation" },
  ),
);
