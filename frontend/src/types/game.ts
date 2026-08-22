export type Position =
  | "GK"
  | "CB"
  | "LB"
  | "RB"
  | "CDM"
  | "CM"
  | "CAM"
  | "LW"
  | "RW"
  | "ST";

export type PlayerFoot = "left" | "right" | "both";

export interface CountryOption {
  code: string;
  name: string;
  flag: string;
  reputation: number;
}

export interface LeagueOption {
  id: string;
  name: string;
  country: string;
  tier: number;
  reputation: number;
  averageSalary: number;
}

export type ClubTier = 1 | 2 | 3 | 4 | 5;

export interface TechnicalStats {
  pace: number;
  dribbling: number;
  passing: number;
  shooting: number;
  heading: number;
  defending: number;
}

export interface MentalStats {
  concentration: number;
  composure: number;
  workRate: number;
  leadership: number;
  vision: number;
}

export interface PhysicalStats {
  stamina: number;
  strength: number;
  jumping: number;
  agility: number;
}

export interface PlayerState {
  form: number;
  morale: number;
  fatigue: number;
  fitness: number;
  reputation: number;
  happiness: number;
  pressure: number;
}

export interface PlayerFinance {
  balance: number;
  weeklySalary: number;
  contractYears: number;
  signOnBonus: number;
  releaseClause: number;
}

export interface PlayerRelationships {
  coach: number;
  teammates: number;
  fans: number;
  press: number;
  family: number;
}

export interface TrophyRecord {
  kind: "team" | "individual";
  name: string;
  season: number;
  clubId?: string | null;
}

export interface Sanction {
  id: string;
  kind: "doping" | "discipline" | "injury";
  remainingSeasons: number;
  missedMatches: number;
  reason: string;
}

export interface ClubInfo {
  id: string;
  name: string;
  shortName: string;
  leagueId: string;
  leagueName: string;
  country: string;
  city: string;
  prestige: number;
  budget: number;
  nickname: string;
}

export interface Player {
  id: string;
  firstName: string;
  lastName: string;
  nickname?: string;
  birthCountry: string;
  nationality: string;
  position: Position;
  secondaryPositions: Position[];
  shirtNumber: number;
  preferredFoot: PlayerFoot;
  age: number;
  height: number;
  weight: number;
  technical: TechnicalStats;
  mental: MentalStats;
  physical: PhysicalStats;
  state: PlayerState;
  finance: PlayerFinance;
  relationships: PlayerRelationships;
  clubId: string | null;
  seasonYear: number;
  trophies: TrophyRecord[];
  sanctions: Sanction[];
  tags: string[];
  caps: number;
  goals: number;
  assists: number;
  matchesPlayed: number;
  retired: boolean;
  retirementOffersDeclined: number;
  createdAt: string;
}

export interface RetirementOffer {
  title: string;
  message: string;
  reasons: string[];
  stayWarning: string;
  seasonsPlayed: number;
  age: number;
  forced: boolean;
}

export type EventCategory =
  | "career"
  | "personal"
  | "social"
  | "financial"
  | "media"
  | "health";

export interface EventFollowUp {
  eventId: string;
  delaySeasons: number;
  delayEvents: number;
  reason: string;
}

export interface EventChoice {
  id: string;
  label: string;
  description: string;
  requires?: Partial<Record<keyof PlayerState | keyof PlayerRelationships, number>>;
  effects: {
    state?: Partial<PlayerState>;
    relationships?: Partial<PlayerRelationships>;
    finance?: Partial<Pick<PlayerFinance, "balance" | "weeklySalary">>;
    reputationDelta?: number;
  };
  followUps: EventFollowUp[];
  tags: string[];
  reasoning?: string;
}

export interface GameEvent {
  id: string;
  category: EventCategory;
  title: string;
  narrative: string;
  weight: number;
  minAge?: number | null;
  maxAge?: number | null;
  requiresClubTier?: ClubTier[] | null;
  requiresMinReputation?: number | null;
  chained?: boolean;
  choices: EventChoice[];
}

export interface PendingChain {
  eventId: string;
  firesAtSeason: number;
  firesAfterEvents: number;
  reason: string;
}

export interface TeamOption {
  id: string;
  name: string;
  shortName: string;
  city: string;
  prestige: number;
  nickname: string;
}

export interface Fixture {
  week: number;
  competitionId: string;
  competitionName: string;
  stageId: string;
  stageDisplay: string;
  opponentId: string;
  opponentName: string;
  opponentShortName: string;
  homeAway: "home" | "away" | "neutral";
  isClasico: boolean;
  leg: "single" | "first" | "second";
  aggregatePartner?: string | null;
}

export interface CompetitionProgress {
  competitionId: string;
  competitionName: string;
  played: number;
  total: number;
  currentStage: string;
}

export interface MatchResult {
  matchNumber: number;
  week: number;
  competitionId: string;
  competitionName: string;
  stageId: string;
  stageDisplay: string;
  opponentId: string;
  opponentName: string;
  opponentShortName: string;
  homeAway: "home" | "away" | "neutral";
  goalsFor: number;
  goalsAgainst: number;
  result: "W" | "D" | "L";
  minutesPlayed: number;
  goals: number;
  assists: number;
  rating: number;
  starter: boolean;
  narrative: string;
  momPlayer: boolean;
  isClasico: boolean;
  /** Only set when a knockout tie was level after 90 minutes. */
  penaltiesFor: number | null;
  penaltiesAgainst: number | null;
}


export interface LeagueTableEntry {
  position: number;
  clubId: string;
  clubName: string;
  shortName: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
}

export interface SeasonProgress {
  season: number;
  matchesPlayed: number;
  matchesTotal: number;
  eventsUsed: number;
  eventsMax: number;
  appearances: number;
  goals: number;
  assists: number;
  cleanSheets: number;
  minutesPlayed: number;
  ratingsSum: number;
  wins: number;
  draws: number;
  losses: number;
  leagueWins: number;
  leagueDraws: number;
  leagueLosses: number;
  recentMatches: MatchResult[];
  fixtures?: Fixture[];
  competitionProgress?: CompetitionProgress[];
  leagueTable?: LeagueTableEntry[];
  leaguePosition?: number | null;
  leaguePointsFromTop?: number | null;
}

export type RouletteKind = "career_start" | "season_start" | "season_end";
export type RouletteTone = "positive" | "negative" | "gift";

export interface RouletteOutcome {
  id: string;
  tone: RouletteTone;
  icon: string;
  title: string;
  description: string;
  effects: Record<string, unknown>;
  tags: string[];
}

export interface RouletteRoll {
  id: string;
  kind: RouletteKind;
  label: string;
  options: RouletteOutcome[];
  autoApply: boolean;
}

export type PlayingChance = "starter" | "rotation" | "backup";
export type TransferKind = "transfer" | "free_agent" | "loan";
export type TransferWindowReason =
  | "expiring_contract"
  | "release_clause"
  | "transfer_request"
  | "free_agent"
  | "loan";

export interface TransferOffer {
  id: string;
  club: ClubInfo;
  weeklySalary: number;
  contractYears: number;
  signOnBonus: number;
  playingChance: PlayingChance;
  reputationRequired: number;
  note: string;
  highlight: string;
  transferKind: TransferKind;
  transferFee: number;
  releaseClause?: number | null;
  paysReleaseClause: boolean;
}

export interface TransferWindow {
  id: string;
  label: string;
  currentClub: ClubInfo | null;
  stayNote: string;
  offers: TransferOffer[];
  reason: TransferWindowReason;
  contractYearsRemaining: number;
  renewalOfferYears?: number | null;
}

export type CareerMode = "player" | "manager";

export type MatchSelectionRole = "starter" | "substitute" | "bench";

export interface MatchSelection {
  role: MatchSelectionRole;
  starterChance: number;
  substituteChance: number;
  expectedMinutesMin: number;
  expectedMinutesMax: number;
  coachMessage: string;
  factors: string[];
}

export interface CareerSession {
  id: string;
  player: Player;
  mode: CareerMode;
  currentSeason: number;
  history: SeasonSnapshot[];
  pendingEventId: string | null;
  pendingEvent: GameEvent | null;
  pendingEventReason: string | null;
  pendingChains: PendingChain[];
  pendingRoulette: RouletteRoll | null;
  pendingTransferWindow: TransferWindow | null;
  pendingRetirement: RetirementOffer | null;
  seasonProgress: SeasonProgress;
  seasonComplete: boolean;
  currentClub: ClubInfo | null;
  nextMatchSelection: MatchSelection | null;
  /** Derived from the player's attributes on every response, never stored. */
  overall: number;
  marketValue: number;
  /** Only present once the player has retired. */
  careerVerdict: CareerVerdict | null;
}

export interface CareerVerdict {
  tier: number;
  title: string;
  summary: string;
  peakOverall: number;
  seasons: number;
  teamTitles: number;
  individualAwards: number;
  clubs: number;
}

export interface SeasonSnapshot {
  season: number;
  clubId: string | null;
  clubName?: string | null;
  overall: number;
  marketValue: number;
  matchesPlayed: number;
  callUps: number;
  goals: number;
  assists: number;
  cleanSheets: number;
  minutesPlayed: number;
  averageRating: number;
  wins: number;
  draws: number;
  losses: number;
  trophies: string[];
  individualAwards: string[];
  keyEvents: string[];
}
