from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Position = Literal[
    "GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"
]
PlayerFoot = Literal["left", "right", "both"]
CareerMode = Literal["player", "manager"]
EventCategory = Literal[
    "career", "personal", "social", "financial", "media", "health"
]
RouletteKind = Literal["career_start", "season_end", "season_start"]


class CreationDraft(BaseModel):
    firstName: str = Field(min_length=1, max_length=30)
    lastName: str = Field(min_length=1, max_length=30)
    nickname: str = ""
    birthCountry: str = Field(min_length=2, max_length=8)
    startingLeague: str
    startingClub: str | None = None
    position: Position
    secondaryPositions: list[Position] = Field(default_factory=list)
    shirtNumber: int = Field(ge=1, le=99)
    preferredFoot: PlayerFoot = "right"
    age: int = Field(ge=16, le=35)
    height: int = Field(ge=150, le=210)
    weight: int = Field(ge=50, le=120)


class CreateCareerPayload(BaseModel):
    mode: CareerMode = "player"
    draft: CreationDraft


class ResolveEventPayload(BaseModel):
    choiceId: str


class ClubInfo(BaseModel):
    id: str
    name: str
    shortName: str
    leagueId: str
    leagueName: str
    country: str
    city: str
    prestige: int
    budget: int
    nickname: str = ""


class TeamOption(BaseModel):
    id: str
    name: str
    shortName: str
    city: str
    prestige: int
    nickname: str = ""


class TechnicalStats(BaseModel):
    pace: float
    dribbling: float
    passing: float
    shooting: float
    heading: float
    defending: float


class MentalStats(BaseModel):
    concentration: float
    composure: float
    workRate: float
    leadership: float
    vision: float


class PhysicalStats(BaseModel):
    stamina: float
    strength: float
    jumping: float
    agility: float


class PlayerState(BaseModel):
    form: float
    morale: float
    fatigue: float
    fitness: float
    reputation: float
    happiness: float
    pressure: float


class PlayerFinance(BaseModel):
    balance: float
    weeklySalary: float
    contractYears: int
    signOnBonus: float
    releaseClause: float = 0.0


class PlayerRelationships(BaseModel):
    coach: float
    teammates: float
    fans: float
    press: float
    family: float


class Sanction(BaseModel):
    id: str
    kind: Literal["doping", "discipline", "injury"]
    remainingSeasons: int
    missedMatches: int
    reason: str


class TrophyRecord(BaseModel):
    kind: Literal["team", "individual"]
    name: str
    season: int
    clubId: str | None = None


class Player(BaseModel):
    id: str
    firstName: str
    lastName: str
    nickname: str | None = None
    birthCountry: str
    nationality: str
    position: Position
    secondaryPositions: list[Position]
    shirtNumber: int
    preferredFoot: PlayerFoot
    age: int
    height: int
    weight: int
    technical: TechnicalStats
    mental: MentalStats
    physical: PhysicalStats
    potential: float = 78.0
    state: PlayerState
    finance: PlayerFinance
    relationships: PlayerRelationships
    clubId: str | None
    seasonYear: int
    trophies: list[TrophyRecord] = Field(default_factory=list)
    sanctions: list[Sanction] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    caps: int
    goals: int
    assists: int
    matchesPlayed: int
    retired: bool = False
    retirementOffersDeclined: int = 0
    createdAt: str

    model_config = ConfigDict(populate_by_name=True)


class EventFollowUp(BaseModel):
    eventId: str
    delaySeasons: int = 0
    delayEvents: int = 0
    reason: str = ""


class EventChoice(BaseModel):
    id: str
    label: str
    description: str
    effects: dict[str, Any] = Field(default_factory=dict)
    followUps: list[EventFollowUp] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    requires: dict[str, float] | None = None
    reasoning: str | None = None


class GameEvent(BaseModel):
    id: str
    category: EventCategory
    title: str
    narrative: str
    weight: float
    minAge: int | None = None
    maxAge: int | None = None
    requiresClubTier: list[int] | None = None
    requiresMinReputation: float | None = None
    requiresTags: list[str] | None = None
    forbidTags: list[str] | None = None
    chained: bool = False
    choices: list[EventChoice]


class PendingChain(BaseModel):
    eventId: str
    firesAtSeason: int
    firesAfterEvents: int
    reason: str = ""


class Fixture(BaseModel):
    week: int
    competitionId: str
    competitionName: str
    stageId: str
    stageDisplay: str
    opponentId: str
    opponentName: str
    opponentShortName: str
    homeAway: Literal["home", "away", "neutral"]
    isClasico: bool = False
    leg: Literal["single", "first", "second"] = "single"
    aggregatePartner: str | None = None




class CompetitionProgress(BaseModel):
    competitionId: str
    competitionName: str
    played: int
    total: int
    currentStage: str


class MatchSelection(BaseModel):
    role: Literal["starter", "substitute", "bench"]
    starterChance: int
    substituteChance: int
    expectedMinutesMin: int
    expectedMinutesMax: int
    coachMessage: str
    factors: list[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    matchNumber: int
    week: int = 0
    competitionId: str = "friendly"
    competitionName: str = "Amistoso"
    stageId: str = ""
    stageDisplay: str = ""
    opponentId: str
    opponentName: str
    opponentShortName: str
    homeAway: Literal["home", "away", "neutral"] = "home"
    goalsFor: int
    goalsAgainst: int
    result: Literal["W", "D", "L"]
    minutesPlayed: int
    goals: int
    assists: int
    rating: float
    starter: bool
    narrative: str
    momPlayer: bool = False
    isClasico: bool = False
    # Solo se completan cuando una eliminatoria termina empatada a los 90'.
    penaltiesFor: int | None = None
    penaltiesAgainst: int | None = None




class LeagueTableEntry(BaseModel):
    position: int
    clubId: str
    clubName: str
    shortName: str
    played: int
    wins: int
    draws: int
    losses: int
    goalsFor: int
    goalsAgainst: int
    goalDifference: int
    points: int


class SeasonProgress(BaseModel):
    season: int = 0
    matchesPlayed: int = 0
    matchesTotal: int = 34
    eventsUsed: int = 0
    eventsMax: int = 3
    appearances: int = 0
    goals: int = 0
    assists: int = 0
    cleanSheets: int = 0
    minutesPlayed: int = 0
    ratingsSum: float = 0.0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    leagueWins: int = 0
    leagueDraws: int = 0
    leagueLosses: int = 0
    recentMatches: list[MatchResult] = Field(default_factory=list)
    matchHistory: list[MatchResult] = Field(default_factory=list)
    fixtures: list[Fixture] = Field(default_factory=list)
    competitionProgress: list[CompetitionProgress] = Field(default_factory=list)
    leagueTable: list[LeagueTableEntry] = Field(default_factory=list)
    leaguePosition: int | None = None
    leaguePointsFromTop: int | None = None

    @model_validator(mode="after")
    def align_fixture_derived_progress(self):
        if self.fixtures:
            self.matchesTotal = len(self.fixtures)
            by_competition: dict[str, CompetitionProgress] = {}
            for fixture in self.fixtures:
                progress = by_competition.get(fixture.competitionId)
                if not progress:
                    progress = CompetitionProgress(
                        competitionId=fixture.competitionId,
                        competitionName=fixture.competitionName,
                        played=0,
                        total=0,
                        currentStage=fixture.stageDisplay,
                    )
                    by_competition[fixture.competitionId] = progress
                progress.total += 1
            for played_fixture in self.fixtures[: self.matchesPlayed]:
                progress = by_competition.get(played_fixture.competitionId)
                if progress:
                    progress.played += 1
                    progress.currentStage = played_fixture.stageDisplay
            next_fixture = (
                self.fixtures[self.matchesPlayed]
                if self.matchesPlayed < len(self.fixtures)
                else None
            )
            if next_fixture and next_fixture.competitionId in by_competition:
                by_competition[next_fixture.competitionId].currentStage = next_fixture.stageDisplay
            self.competitionProgress = list(by_competition.values())
        return self


class SeasonSnapshot(BaseModel):
    season: int
    clubId: str | None
    clubName: str | None = None
    matchesPlayed: int
    callUps: int = 0
    goals: int
    assists: int
    cleanSheets: int = 0
    minutesPlayed: int = 0
    averageRating: float
    wins: int = 0
    draws: int = 0
    losses: int = 0
    trophies: list[str]
    individualAwards: list[str] = Field(default_factory=list)
    keyEvents: list[str]


class RouletteOutcome(BaseModel):
    id: str
    tone: Literal["positive", "negative", "gift"]
    icon: str
    title: str
    description: str
    effects: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class RouletteRoll(BaseModel):
    id: str
    kind: RouletteKind
    label: str
    options: list[RouletteOutcome]
    autoApply: bool = False


class SpinRoulettePayload(BaseModel):
    outcomeId: str


class TransferOffer(BaseModel):
    id: str
    club: ClubInfo
    weeklySalary: float
    contractYears: int
    signOnBonus: float
    playingChance: Literal["starter", "rotation", "backup"]
    reputationRequired: float
    note: str
    highlight: str = ""
    transferKind: Literal["transfer", "free_agent", "loan"] = "transfer"
    transferFee: float = 0.0
    releaseClause: float | None = None
    paysReleaseClause: bool = False


class TransferWindow(BaseModel):
    id: str
    label: str
    currentClub: ClubInfo | None
    stayNote: str
    offers: list[TransferOffer]
    reason: Literal["expiring_contract", "release_clause", "transfer_request", "free_agent", "loan"] = "expiring_contract"
    contractYearsRemaining: int = 0
    renewalOfferYears: int | None = None


class AcceptTransferPayload(BaseModel):
    offerId: str | None = None


class RetirementOffer(BaseModel):
    """Decisión de fin de carrera. El motor la sugiere; el jugador decide."""

    title: str
    message: str
    reasons: list[str] = Field(default_factory=list)
    stayWarning: str
    seasonsPlayed: int
    age: int


class ResolveRetirementPayload(BaseModel):
    retire: bool


class CareerSession(BaseModel):
    id: str
    player: Player
    mode: CareerMode
    currentSeason: int
    history: list[SeasonSnapshot]
    seasonProgress: SeasonProgress = Field(default_factory=SeasonProgress)
    seasonComplete: bool = False
    pendingEventId: str | None
    pendingEvent: GameEvent | None
    pendingEventReason: str | None = None
    pendingChains: list[PendingChain] = Field(default_factory=list)
    pendingRoulette: RouletteRoll | None = None
    pendingTransferWindow: TransferWindow | None = None
    pendingRetirement: RetirementOffer | None = None
    currentClub: ClubInfo | None = None
    nextMatchSelection: MatchSelection | None = None
