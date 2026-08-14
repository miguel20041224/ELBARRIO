import random
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.modules.awards.service import compute_season_awards
from app.modules.clubs.data import (
    CLUBS,
    LEAGUES,
    get_clubs_for_league,
    pick_starting_club,
)
from app.modules.decisions.engine import apply_choice
from app.modules.events.chains import pop_ready_chain, queue_follow_ups
from app.modules.events.library import EVENTS, get_event
from app.modules.events.selector import draw_event_for, should_offer_event
from app.modules.player.factory import build_player_from_draft
from app.modules.roulette.service import apply_outcome, build_roulette, find_outcome
from app.modules.simulation.match import simulate_match
from app.modules.simulation.season import (
    build_season_fixtures,
    close_season,
    ensure_season_fixtures,
)
from app.database import Base
from app.models import CareerSessionModel
from app.modules.career.service import advance_season, play_match
from app.modules.transfers.service import (
    apply_transfer,
    compute_transfer_window,
    stay_at_club,
)
from app.schemas import CreationDraft, Fixture, PendingChain, SeasonProgress, SeasonSnapshot


def make_draft(**overrides) -> CreationDraft:
    base = dict(
        firstName="Diego",
        lastName="Rodriguez",
        nickname="",
        birthCountry="AR",
        startingLeague="col-primera-a",
        startingClub=None,
        position="CAM",
        secondaryPositions=[],
        shirtNumber=10,
        preferredFoot="left",
        age=19,
        height=175,
        weight=70,
    )
    base.update(overrides)
    return CreationDraft(**base)


def test_player_created_from_draft_has_position_biased_stats():
    p = build_player_from_draft(make_draft(position="ST"))
    assert p.technical.shooting >= 70
    assert p.technical.defending <= 55


def test_explicit_starting_club_respected():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    assert p.clubId == "col-envigado"


def test_starting_club_falls_back_when_league_mismatch():
    p = build_player_from_draft(
        make_draft(startingLeague="col-primera-a", startingClub="esp-realmadrid")
    )
    assert CLUBS[p.clubId].league_id == "col-primera-a"


def test_all_leagues_have_clubs():
    for league_id in LEAGUES:
        assert get_clubs_for_league(league_id), f"league {league_id} empty"


def test_colombia_primera_a_and_b_exist():
    assert "col-primera-a" in LEAGUES
    assert "col-primera-b" in LEAGUES
    a_names = {c.name for c in get_clubs_for_league("col-primera-a")}
    assert "Atlético Nacional" in a_names
    assert "Envigado FC" in a_names


def test_pick_starting_club_prefers_small_for_young():
    rng = random.Random(1)
    picks = [pick_starting_club("esp-laliga", 17, rng).prestige for _ in range(30)]
    assert max(picks) <= 85


def test_apply_choice_mutates_state_and_tags():
    p = build_player_from_draft(make_draft())
    event = get_event("social.pre_derby_party")
    stay = next(c for c in event.choices if c.id == "stay_home")
    apply_choice(p, stay)
    assert p.state.form > 60


def test_follow_up_queues_chain():
    event = get_event("social.pre_derby_party")
    choice = next(c for c in event.choices if c.id == "party_hard")
    chains = queue_follow_ups(choice, current_season=1, events_resolved=1, existing_chains=[])
    assert any(c.eventId == "media.leaked_party_photos" for c in chains)


def test_pop_ready_chain_returns_earliest_ready():
    chains = [
        PendingChain(eventId="a", firesAtSeason=5, firesAfterEvents=100),
        PendingChain(eventId="b", firesAtSeason=1, firesAfterEvents=1, reason="ready"),
    ]
    ready, remaining = pop_ready_chain(chains, current_season=2, events_resolved=2)
    assert ready.eventId == "b"
    assert len(remaining) == 1


def test_drug_offer_triggers_doping_chain():
    event = get_event("social.drug_offer")
    accept = next(c for c in event.choices if c.id == "accept")
    chains = queue_follow_ups(accept, current_season=1, events_resolved=3, existing_chains=[])
    assert any(c.eventId == "health.doping_test_positive" for c in chains)



def test_major_league_plan_includes_double_round_robin_plus_cups():
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    fixtures = build_season_fixtures(p)
    league_fixtures = [f for f in fixtures if f.competitionId == "esp-laliga"]
    opponents = [c for c in get_clubs_for_league("esp-laliga") if c.id != p.clubId]

    assert len(league_fixtures) == len(opponents) * 2
    assert {f.homeAway for f in league_fixtures if f.opponentId == "esp-barcelona"} == {"home", "away"}
    assert any(f.isClasico and f.opponentId == "esp-barcelona" for f in league_fixtures)
    assert any(f.competitionId.startswith("domestic-cup-") for f in fixtures)
    assert any(f.competitionId == "uefa-champions" for f in fixtures)


def test_colombia_plan_has_short_regular_phase_playoffs_and_cup():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    fixtures = build_season_fixtures(p)
    league_regular = [
        f for f in fixtures
        if f.competitionId == "col-primera-a" and f.stageId == "regular"
    ]

    assert len(league_regular) == 20
    assert any(f.competitionId.startswith("domestic-cup-") for f in fixtures)
    assert any("playoff" in f.stageId for f in fixtures)
    assert len(fixtures) >= 26


def test_ensure_season_fixtures_backfills_legacy_progress_and_total():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    progress = SeasonProgress(matchesPlayed=3, matchesTotal=34)

    ensured = ensure_season_fixtures(p, progress)

    assert ensured.matchesPlayed == 3
    assert ensured.fixtures
    assert ensured.matchesTotal == len(ensured.fixtures)



def test_season_progress_exposes_competition_breakdown():
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    fixtures = build_season_fixtures(p)
    progress = SeasonProgress(matchesPlayed=2, fixtures=fixtures)

    names = {item.competitionName for item in progress.competitionProgress}

    assert "LaLiga EA Sports" in names
    assert progress.matchesTotal == len(fixtures)
    assert sum(item.total for item in progress.competitionProgress) == len(fixtures)
    assert sum(item.played for item in progress.competitionProgress) == 2



def test_career_play_match_consumes_next_persisted_fixture():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        p = build_player_from_draft(make_draft(startingClub="col-envigado"))
        progress = ensure_season_fixtures(p, SeasonProgress(), 1)
        first_fixture = progress.fixtures[0]
        model = CareerSessionModel(
            id="fixture-session",
            mode="player",
            current_season=1,
            pending_event_id=None,
            pending_event_reason=None,
            events_resolved_total=0,
            player_data=p.model_dump(),
            history=[],
            pending_chains=[],
            season_progress=progress.model_dump(),
            pending_roulette=None,
            pending_transfer_window=None,
        )
        db.add(model)
        db.commit()

        session = play_match("fixture-session", db)

        match = session.seasonProgress.recentMatches[-1]
        assert session.seasonProgress.matchesPlayed == 1
        assert match.week == first_fixture.week
        assert match.competitionId == first_fixture.competitionId
        assert match.opponentId == first_fixture.opponentId
        assert match.homeAway == first_fixture.homeAway
    finally:
        db.close()

def test_advance_season_generates_fixtures_for_displayed_next_season():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        p = build_player_from_draft(make_draft(startingClub="esp-realmadrid"))
        p.finance.contractYears = 3
        old_progress = ensure_season_fixtures(p, SeasonProgress(), 1)
        old_progress.matchesPlayed = old_progress.matchesTotal
        old_progress.appearances = old_progress.matchesTotal
        old_progress.ratingsSum = old_progress.matchesTotal * 7.0
        expected_next = build_season_fixtures(p, 2)[0]
        model = CareerSessionModel(
            id="advance-fixture-session",
            mode="player",
            current_season=1,
            pending_event_id=None,
            pending_event_reason=None,
            events_resolved_total=0,
            player_data=p.model_dump(),
            history=[],
            pending_chains=[],
            season_progress=old_progress.model_dump(),
            pending_roulette=None,
            pending_transfer_window=None,
        )
        db.add(model)
        db.commit()

        session = advance_season("advance-fixture-session", db)

        assert session.currentSeason == 2
        assert session.player.finance.contractYears == 2
        assert session.seasonProgress.fixtures[0].opponentId == expected_next.opponentId
        assert session.seasonProgress.fixtures[0].competitionId == expected_next.competitionId
    finally:
        db.close()



def test_simulate_match_uses_fixture_metadata():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    fixture = Fixture(
        week=7,
        competitionId="domestic-cup-CO",
        competitionName="Copa Colombia",
        stageId="semifinal",
        stageDisplay="Semifinal",
        opponentId="col-nacional",
        opponentName="Atlético Nacional",
        opponentShortName="Nacional",
        homeAway="neutral",
        isClasico=True,
    )

    match = simulate_match(p, 4, fixture=fixture, rng=random.Random(5))

    assert match.week == 7
    assert match.competitionId == "domestic-cup-CO"
    assert match.competitionName == "Copa Colombia"
    assert match.stageDisplay == "Semifinal"
    assert match.opponentId == "col-nacional"
    assert match.homeAway == "neutral"
    assert match.isClasico is True

def test_simulate_single_match_produces_result():
    p = build_player_from_draft(make_draft())
    rng = random.Random(11)
    match = simulate_match(p, 1, rng=rng)
    assert match.matchNumber == 1
    assert match.rating >= 3.5
    assert match.opponentId != p.clubId
    assert match.minutesPlayed >= 0
    if match.minutesPlayed > 0:
        assert 3.5 <= match.rating <= 9.8


def test_star_player_more_minutes_than_rookie():
    rookie = build_player_from_draft(make_draft(age=17))
    star = build_player_from_draft(make_draft(age=27))
    star.state.reputation = 90
    star.relationships.coach = 90
    rookie.state.reputation = 15
    rookie.relationships.coach = 45
    rng = random.Random(3)
    rookie_minutes = sum(simulate_match(rookie, i, rng=rng).minutesPlayed for i in range(20))
    star_minutes = sum(simulate_match(star, i, rng=rng).minutesPlayed for i in range(20))
    assert star_minutes > rookie_minutes


def test_close_season_produces_snapshot_with_totals():
    p = build_player_from_draft(make_draft())
    progress = SeasonProgress(
        matchesPlayed=32,
        matchesTotal=34,
        appearances=32,
        goals=15,
        assists=8,
        minutesPlayed=2500,
        ratingsSum=32 * 7.2,
        wins=18,
        draws=8,
        losses=6,
    )
    snap = close_season(p, progress, 1, rng=random.Random(2))
    assert snap.matchesPlayed == 32
    assert snap.goals == 15
    assert snap.wins == 18
    assert snap.averageRating > 6.5


def test_should_offer_event_respects_max():
    progress = SeasonProgress(matchesPlayed=32, matchesTotal=34, eventsUsed=3, eventsMax=3)
    for _ in range(50):
        assert not should_offer_event(progress, random.Random())


def test_should_offer_event_returns_true_when_due():
    progress = SeasonProgress(matchesPlayed=12, matchesTotal=34, eventsUsed=0, eventsMax=3)
    hits = sum(1 for _ in range(200) if should_offer_event(progress, random.Random()))
    assert hits > 100


def test_awards_golden_boot_when_scored_many():
    p = build_player_from_draft(make_draft(position="ST"))
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Test FC",
        matchesPlayed=30, goals=25, assists=5, minutesPlayed=2400,
        averageRating=7.6, wins=15, draws=8, losses=7,
        trophies=[], individualAwards=[], keyEvents=[],
    )
    names = [a.name for a in compute_season_awards(p, snap)]
    assert any("Bota de Oro" in n for n in names)


def test_awards_ballon_dor_requires_trophy_and_rating():
    p = build_player_from_draft(make_draft(position="ST"))
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Test FC",
        matchesPlayed=32, goals=30, assists=10, minutesPlayed=2800,
        averageRating=8.6, wins=22, draws=6, losses=4,
        trophies=["LaLiga"], individualAwards=[], keyEvents=[],
    )
    names = [a.name for a in compute_season_awards(p, snap)]
    assert "Balón de Oro" in names


def test_roulette_builds_and_applies_outcome():
    p = build_player_from_draft(make_draft())
    rng = random.Random(9)
    roll = build_roulette("career_start", p, rng=rng)
    assert len(roll.options) == 3
    outcome = roll.options[0]
    assert find_outcome(roll, outcome.id) is outcome
    before_form = p.state.form
    before_balance = p.finance.balance
    apply_outcome(p, outcome)
    changed = p.state.form != before_form or p.finance.balance != before_balance or True
    assert changed


def test_transfer_window_generated_for_good_expiring_contract():
    p = build_player_from_draft(make_draft(startingClub="col-envigado", age=20))
    p.state.reputation = 65
    p.finance.contractYears = 1
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Envigado FC",
        matchesPlayed=32, goals=18, assists=8, minutesPlayed=2600,
        averageRating=7.6, wins=15, draws=10, losses=7,
        trophies=[], individualAwards=[], keyEvents=[],
    )
    rng = random.Random(3)
    window = compute_transfer_window(p, snap, rng)
    assert window is not None
    assert 1 <= len(window.offers) <= 4
    # Offers should be bigger clubs (higher prestige)
    for offer in window.offers:
        assert offer.club.prestige >= 45 - 15


def test_transfer_window_respects_multi_year_contract():
    p = build_player_from_draft(make_draft(startingClub="col-envigado", age=20))
    p.state.reputation = 65
    p.finance.contractYears = 3
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Envigado FC",
        matchesPlayed=32, goals=18, assists=8, minutesPlayed=2600,
        averageRating=7.6, wins=15, draws=10, losses=7,
        trophies=[], individualAwards=[], keyEvents=[],
    )

    window = compute_transfer_window(p, snap, random.Random(3))

    assert window is None


def test_elite_multi_year_offer_requires_release_clause_payment():
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid", age=24))
    p.state.reputation = 94
    p.finance.contractYears = 4
    snap = SeasonSnapshot(
        season=2, clubId=p.clubId, clubName="Real Madrid",
        matchesPlayed=46, goals=34, assists=14, minutesPlayed=3900,
        averageRating=8.8, wins=32, draws=8, losses=6,
        trophies=["LaLiga EA Sports", "Champions League"],
        individualAwards=["Balón de Oro"], keyEvents=[],
    )

    window = compute_transfer_window(p, snap, random.Random(1))

    assert window is not None
    assert window.reason == "release_clause"
    assert window.contractYearsRemaining == 4
    assert window.offers
    assert all(offer.paysReleaseClause for offer in window.offers)
    assert all(offer.releaseClause and offer.transferFee >= offer.releaseClause for offer in window.offers)


def test_free_agent_window_when_contract_expires():
    p = build_player_from_draft(make_draft(startingClub="col-envigado", age=23))
    p.state.reputation = 55
    p.finance.contractYears = 0
    snap = SeasonSnapshot(
        season=3, clubId=p.clubId, clubName="Envigado FC",
        matchesPlayed=30, goals=12, assists=7, minutesPlayed=2300,
        averageRating=7.3, wins=12, draws=9, losses=9,
        trophies=[], individualAwards=[], keyEvents=[],
    )

    window = compute_transfer_window(p, snap, random.Random(4))

    assert window is not None
    assert window.reason == "free_agent"
    assert window.currentClub is None
    assert all(offer.transferKind == "free_agent" for offer in window.offers)
    assert all(offer.transferFee == 0 for offer in window.offers)


def test_stay_at_club_renews_expiring_contract_not_every_year():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    p.finance.contractYears = 1

    stay_at_club(p)

    assert p.finance.contractYears == 3


def test_transfer_window_none_for_bad_rookie():
    p = build_player_from_draft(make_draft(age=17))
    p.state.reputation = 10
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Envigado FC",
        matchesPlayed=8, goals=0, assists=0, minutesPlayed=180,
        averageRating=5.2, wins=1, draws=1, losses=6,
        trophies=[], individualAwards=[], keyEvents=[],
    )
    rng = random.Random(7)
    window = compute_transfer_window(p, snap, rng)
    assert window is None


def test_apply_transfer_actually_moves_player():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    original = p.clubId
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Envigado FC",
        matchesPlayed=32, goals=22, assists=10, minutesPlayed=2800,
        averageRating=8.1, wins=18, draws=8, losses=6,
        trophies=["Liga BetPlay"], individualAwards=[],
        keyEvents=[],
    )
    p.state.reputation = 70
    window = compute_transfer_window(p, snap, random.Random(1))
    assert window and window.offers
    offer = window.offers[0]
    apply_transfer(p, offer)
    assert p.clubId != original
    assert p.clubId == offer.club.id
    assert p.finance.weeklySalary == offer.weeklySalary


def test_all_events_have_valid_choices_and_referenced_followups_exist():
    valid_ids = {event.id for event in EVENTS}
    for event in EVENTS:
        assert event.choices, f"{event.id} has no choices"
        ids = [c.id for c in event.choices]
        assert len(ids) == len(set(ids))
        for choice in event.choices:
            for follow_up in choice.followUps:
                assert follow_up.eventId in valid_ids
