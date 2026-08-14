import random
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import (
    CreationDraft,
    MentalStats,
    PhysicalStats,
    Player,
    PlayerFinance,
    PlayerRelationships,
    PlayerState,
    TechnicalStats,
)
from app.modules.clubs.data import get_club, get_league, pick_starting_club


POSITION_BASE_STATS: dict[str, dict[str, float]] = {
    "GK": {"defending": 60, "heading": 45, "passing": 55},
    "CB": {"defending": 70, "heading": 68, "strength": 70},
    "LB": {"pace": 68, "defending": 60, "stamina": 68},
    "RB": {"pace": 68, "defending": 60, "stamina": 68},
    "CDM": {"defending": 65, "passing": 65, "workRate": 72},
    "CM": {"passing": 70, "vision": 65, "stamina": 68},
    "CAM": {"passing": 68, "vision": 72, "dribbling": 70},
    "LW": {"pace": 74, "dribbling": 72, "shooting": 65},
    "RW": {"pace": 74, "dribbling": 72, "shooting": 65},
    "ST": {"shooting": 72, "heading": 65, "pace": 66},
}


def _base_stat(position: str, key: str, default: float) -> float:
    return POSITION_BASE_STATS.get(position, {}).get(key, default)


def build_player_from_draft(draft: CreationDraft, rng: random.Random | None = None) -> Player:
    r = rng or random.Random()
    league = get_league(draft.startingLeague)
    club = None
    if draft.startingClub:
        club = get_club(draft.startingClub)
        if not club or club.league_id != draft.startingLeague:
            club = None
    if not club and league:
        club = pick_starting_club(draft.startingLeague, draft.age, r)
    pos = draft.position

    technical = TechnicalStats(
        pace=_base_stat(pos, "pace", 55),
        dribbling=_base_stat(pos, "dribbling", 55),
        passing=_base_stat(pos, "passing", 55),
        shooting=_base_stat(pos, "shooting", 55),
        heading=_base_stat(pos, "heading", 55),
        defending=_base_stat(pos, "defending", 45),
    )
    mental = MentalStats(
        concentration=55,
        composure=50,
        workRate=_base_stat(pos, "workRate", 60),
        leadership=40,
        vision=_base_stat(pos, "vision", 55),
    )
    physical = PhysicalStats(
        stamina=_base_stat(pos, "stamina", 65),
        strength=_base_stat(pos, "strength", 60),
        jumping=60,
        agility=65,
    )

    club_salary_factor = club.prestige / 100 if club else 0.35
    league_salary = league.average_salary if league else 500
    base_salary = max(400, league_salary * club_salary_factor * 0.9)
    starting_state = PlayerState(
        form=60,
        morale=70,
        fatigue=20,
        fitness=85,
        reputation=25,
        happiness=75,
        pressure=15,
    )
    finance = PlayerFinance(
        balance=base_salary * 4,
        weeklySalary=base_salary,
        contractYears=3,
        signOnBonus=base_salary * 8,
    )
    relationships = PlayerRelationships(
        coach=55,
        teammates=55,
        fans=45,
        press=45,
        family=80,
    )

    return Player(
        id=str(uuid4()),
        firstName=draft.firstName,
        lastName=draft.lastName,
        nickname=draft.nickname or None,
        birthCountry=draft.birthCountry,
        nationality=draft.birthCountry,
        position=draft.position,
        secondaryPositions=draft.secondaryPositions,
        shirtNumber=draft.shirtNumber,
        preferredFoot=draft.preferredFoot,
        age=draft.age,
        height=draft.height,
        weight=draft.weight,
        technical=technical,
        mental=mental,
        physical=physical,
        state=starting_state,
        finance=finance,
        relationships=relationships,
        clubId=club.id if club else None,
        seasonYear=datetime.now(timezone.utc).year,
        trophies=[],
        sanctions=[],
        tags=[],
        caps=0,
        goals=0,
        assists=0,
        matchesPlayed=0,
        createdAt=datetime.now(timezone.utc).isoformat(),
    )
