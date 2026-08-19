import { api } from "./client";
import type {
  CareerMode,
  CareerSession,
  EventChoice,
  TeamOption,
} from "@/types/game";
import type { CreationDraft } from "@/store/creationStore";

interface CreateCareerPayload {
  mode: CareerMode;
  draft: CreationDraft;
}

interface ResolveEventPayload {
  choiceId: string;
}

interface SpinRoulettePayload {
  outcomeId: string;
}

interface AcceptTransferPayload {
  offerId: string | null;
}

interface ResolveRetirementPayload {
  retire: boolean;
}

export const careerApi = {
  listTeams: (leagueId: string) =>
    api.get<TeamOption[]>(`/leagues/${leagueId}/teams`),
  create: (payload: CreateCareerPayload) =>
    api.post<CareerSession>("/careers", payload),
  get: (id: string) => api.get<CareerSession>(`/careers/${id}`),
  playMatch: (id: string) =>
    api.post<CareerSession>(`/careers/${id}/play-match`),
  spinRoulette: (id: string, body: SpinRoulettePayload) =>
    api.post<CareerSession>(`/careers/${id}/spin-roulette`, body),
  resolveEvent: (id: string, body: ResolveEventPayload) =>
    api.post<CareerSession>(`/careers/${id}/resolve-event`, body),
  advanceSeason: (id: string) =>
    api.post<CareerSession>(`/careers/${id}/advance-season`),
  acceptTransfer: (id: string, body: AcceptTransferPayload) =>
    api.post<CareerSession>(`/careers/${id}/accept-transfer`, body),
  resolveRetirement: (id: string, body: ResolveRetirementPayload) =>
    api.post<CareerSession>(`/careers/${id}/resolve-retirement`, body),
};

export type { CreateCareerPayload, ResolveEventPayload, EventChoice };
