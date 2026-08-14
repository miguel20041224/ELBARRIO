import random
from itertools import cycle

from app.modules.clubs.data import CLUBS, Club, get_club, get_clubs_for_league, get_league
from app.schemas import Fixture, Player, SeasonProgress, SeasonSnapshot, TrophyRecord


CLASICO_PAIRS: set[frozenset[str]] = {
    frozenset({"esp-realmadrid", "esp-barcelona"}),
    frozenset({"esp-realmadrid", "esp-atletico"}),
    frozenset({"arg-riverplate", "arg-bocajuniors"}),
    frozenset({"arg-racing", "arg-independiente"}),
    frozenset({"col-nacional", "col-medellin"}),
    frozenset({"col-millonarios", "col-santafe"}),
    frozenset({"col-america", "col-deportivocali"}),
    frozenset({"bra-flamengo", "bra-fluminense"}),
    frozenset({"ita-inter", "ita-milan"}),
    frozenset({"ger-bayern", "ger-dortmund"}),
}


def _is_clasico(club: Club, opponent: Club) -> bool:
    return (
        frozenset({club.id, opponent.id}) in CLASICO_PAIRS
        or (club.city == opponent.city and club.id != opponent.id)
    )


def _fixture(
    *,
    week: int,
    competition_id: str,
    competition_name: str,
    stage_id: str,
    stage_display: str,
    club: Club,
    opponent: Club,
    home_away: str,
    leg: str = "single",
) -> Fixture:
    return Fixture(
        week=week,
        competitionId=competition_id,
        competitionName=competition_name,
        stageId=stage_id,
        stageDisplay=stage_display,
        opponentId=opponent.id,
        opponentName=opponent.name,
        opponentShortName=opponent.short_name,
        homeAway=home_away,
        isClasico=_is_clasico(club, opponent),
        leg=leg,
    )


def _ordered_opponents(club: Club, rng: random.Random) -> list[Club]:
    opponents = [c for c in get_clubs_for_league(club.league_id) if c.id != club.id]
    opponents.sort(key=lambda c: (-_is_clasico(club, c), -c.prestige, c.id))
    clasicos = [c for c in opponents if _is_clasico(club, c)]
    rest = [c for c in opponents if not _is_clasico(club, c)]
    rng.shuffle(rest)
    return clasicos + rest


def _double_round_robin(club: Club, league_name: str, rng: random.Random) -> list[Fixture]:
    fixtures: list[Fixture] = []
    opponents = _ordered_opponents(club, rng)
    for opponent in opponents:
        fixtures.append(
            _fixture(
                week=len(fixtures) + 1,
                competition_id=club.league_id,
                competition_name=league_name,
                stage_id="regular",
                stage_display="League",
                club=club,
                opponent=opponent,
                home_away="home",
            )
        )
    for opponent in opponents:
        fixtures.append(
            _fixture(
                week=len(fixtures) + 1,
                competition_id=club.league_id,
                competition_name=league_name,
                stage_id="regular",
                stage_display="League",
                club=club,
                opponent=opponent,
                home_away="away",
            )
        )
    return fixtures


def _colombia_league_plan(club: Club, league_name: str, rng: random.Random) -> list[Fixture]:
    fixtures: list[Fixture] = []
    opponents = _ordered_opponents(club, rng)
    if not opponents:
        return fixtures

    regular_opponents = opponents + [o for o in opponents if o not in opponents[:0]]
    for opponent in regular_opponents[:20]:
        fixtures.append(
            _fixture(
                week=len(fixtures) + 1,
                competition_id=club.league_id,
                competition_name=league_name,
                stage_id="regular",
                stage_display="Todos contra todos",
                club=club,
                opponent=opponent,
                home_away="home" if len(fixtures) % 2 == 0 else "away",
            )
        )

    playoff_pool = sorted(opponents, key=lambda c: -c.prestige)[:4]
    for i, opponent in enumerate(playoff_pool, start=1):
        fixtures.append(
            _fixture(
                week=len(fixtures) + 1,
                competition_id=club.league_id,
                competition_name=league_name,
                stage_id="playoff-group",
                stage_display="Playoff group",
                club=club,
                opponent=opponent,
                home_away="home" if i % 2 else "away",
            )
        )
    return fixtures


def _domestic_cup(club: Club, country: str, rng: random.Random, start_week: int) -> list[Fixture]:
    candidates = [c for c in CLUBS.values() if c.id != club.id and (get_league(c.league_id) and get_league(c.league_id).country == country)]
    candidates.sort(key=lambda c: (abs(c.prestige - club.prestige), c.id))
    rng.shuffle(candidates)
    stages = [("round-16", "Round of 16"), ("quarterfinal", "Quarterfinal"), ("semifinal", "Semifinal"), ("final", "Final")]
    cup_name_by_country = {
        "CO": "Copa Colombia",
        "AR": "Copa Argentina",
        "BR": "Copa do Brasil",
        "ES": "Copa del Rey",
        "EN": "FA Cup",
        "IT": "Coppa Italia",
        "DE": "DFB-Pokal",
        "FR": "Coupe de France",
        "SA": "King Cup",
    }
    fixtures: list[Fixture] = []
    for idx, (stage_id, stage_display) in enumerate(stages):
        if not candidates:
            break
        opponent = candidates[idx % len(candidates)]
        fixtures.append(
            _fixture(
                week=start_week + idx,
                competition_id=f"domestic-cup-{country}",
                competition_name=cup_name_by_country.get(country, "Domestic Cup"),
                stage_id=stage_id,
                stage_display=stage_display,
                club=club,
                opponent=opponent,
                home_away="neutral" if stage_id == "final" else ("home" if idx % 2 == 0 else "away"),
            )
        )
    return fixtures


def _continental_cup(club: Club, country: str, league_tier: int, rng: random.Random, start_week: int) -> list[Fixture]:
    is_europe = country in {"ES", "EN", "IT", "DE", "FR"}
    qualifies = (is_europe and league_tier >= 4 and club.prestige >= 82) or (
        country in {"CO", "AR", "BR"} and league_tier >= 3 and club.prestige >= 80
    )
    if not qualifies:
        return []

    competition_id = "uefa-champions" if is_europe else "conmebol-libertadores"
    competition_name = "Champions League" if is_europe else "Copa Libertadores"
    candidates = [
        c for c in CLUBS.values()
        if c.id != club.id and (get_league(c.league_id) and get_league(c.league_id).country != country)
    ]
    candidates = sorted(candidates, key=lambda c: (-c.prestige, c.id))[:16]
    rng.shuffle(candidates)
    fixtures: list[Fixture] = []
    for idx, opponent in enumerate(candidates[:6]):
        fixtures.append(
            _fixture(
                week=start_week + idx,
                competition_id=competition_id,
                competition_name=competition_name,
                stage_id="league-phase",
                stage_display="League phase",
                club=club,
                opponent=opponent,
                home_away="home" if idx % 2 == 0 else "away",
            )
        )
    return fixtures


def build_season_fixtures(
    player: Player,
    season_number: int = 1,
    rng: random.Random | None = None,
) -> list[Fixture]:
    r = rng or random.Random(f"{player.id}:{season_number}:{player.clubId}")
    club = get_club(player.clubId) if player.clubId else None
    league = get_league(club.league_id) if club else None
    if not club or not league:
        return []

    if league.country == "CO" and club.league_id == "col-primera-a":
        fixtures = _colombia_league_plan(club, league.name, r)
    else:
        fixtures = _double_round_robin(club, league.name, r)

    fixtures.extend(_domestic_cup(club, league.country, r, len(fixtures) + 1))
    fixtures.extend(_continental_cup(club, league.country, league.tier, r, len(fixtures) + 1))
    return [fixture.model_copy(update={"week": index}) for index, fixture in enumerate(fixtures, start=1)]


def ensure_season_fixtures(
    player: Player,
    progress: SeasonProgress,
    season_number: int = 1,
) -> SeasonProgress:
    if not progress.fixtures:
        progress.fixtures = build_season_fixtures(player, season_number)
    if progress.fixtures:
        progress.matchesTotal = len(progress.fixtures)
    return progress


def _team_trophies_for_club(
    player: Player,
    average_rating: float,
    wins: int,
    matches: int,
    rng: random.Random,
) -> list[str]:
    trophies: list[str] = []
    club = get_club(player.clubId) if player.clubId else None
    league = get_league(club.league_id) if club else None
    if not club or not league or matches == 0:
        return trophies

    win_ratio = wins / matches if matches else 0
    prestige_factor = club.prestige / 100
    team_bonus = prestige_factor * 0.5
    league_chance = max(0.02, win_ratio * 1.2 - 0.5 + team_bonus + (average_rating - 6.5) * 0.15)
    if rng.random() < min(0.55, league_chance):
        trophies.append(f"{league.name}")
    cup_chance = max(0.02, win_ratio * 0.6 - 0.15 + team_bonus * 0.3)
    if rng.random() < min(0.35, cup_chance):
        trophies.append(f"Copa {league.country}")
    if league.tier >= 4 and prestige_factor >= 0.82 and average_rating >= 8.0:
        if rng.random() < 0.18:
            trophies.append("Champions League")

    return trophies


def close_season(
    player: Player,
    progress: SeasonProgress,
    season_number: int,
    rng: random.Random | None = None,
) -> SeasonSnapshot:
    r = rng or random.Random()
    played = max(1, progress.appearances)
    average_rating = round(progress.ratingsSum / played, 2) if progress.appearances > 0 else 6.0

    club = get_club(player.clubId) if player.clubId else None
    club_name = club.name if club else None

    team_trophies = _team_trophies_for_club(
        player, average_rating, progress.wins, progress.matchesPlayed, r
    )
    if team_trophies:
        for name in team_trophies:
            player.trophies.append(
                TrophyRecord(
                    kind="team",
                    name=name,
                    season=season_number,
                    clubId=player.clubId,
                )
            )

    reputation_gain = (average_rating - 6.0) * 8 + (progress.goals * 0.5)
    player.state.reputation = max(0, min(100, player.state.reputation + reputation_gain))
    player.state.fatigue = max(10, player.state.fatigue - 30)
    player.state.fitness = min(95, player.state.fitness + 15)
    player.state.form = 60
    player.age += 1

    return SeasonSnapshot(
        season=season_number,
        clubId=player.clubId,
        clubName=club_name,
        matchesPlayed=progress.matchesPlayed,
        goals=progress.goals,
        assists=progress.assists,
        minutesPlayed=progress.minutesPlayed,
        averageRating=average_rating,
        wins=progress.wins,
        draws=progress.draws,
        losses=progress.losses,
        trophies=team_trophies,
        individualAwards=[],
        keyEvents=[],
    )
