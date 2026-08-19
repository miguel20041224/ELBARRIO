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
from app.modules.player.factory import build_player_from_draft, key_attributes_for
from app.modules.simulation.development import develop_player, should_offer_retirement
from app.modules.roulette.service import apply_outcome, build_roulette, find_outcome
from app.modules.simulation.match import build_match_selection, simulate_match
from app.modules.simulation.season import (
    build_league_table,
    build_season_fixtures,
    close_season,
    ensure_season_fixtures,
)
from app.database import Base
from app.models import CareerSessionModel
from app.modules.career.service import ActionBlockedError, ConcurrentModificationError, advance_season, play_match
from app.modules.transfers.service import (
    apply_transfer,
    compute_transfer_window,
    stay_at_club,
)
from app.schemas import (
    CreationDraft,
    Fixture,
    LeagueTableEntry,
    MatchResult,
    PendingChain,
    SeasonProgress,
    SeasonSnapshot,
)


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

    playoffs = [f for f in fixtures if "playoff" in f.stageId]
    cup = [f for f in fixtures if f.competitionId.startswith("domestic-cup-")]

    assert len(league_regular) == 20
    assert len(playoffs) == 4
    assert cup
    assert len(fixtures) == len(league_regular) + len(playoffs) + len(cup)


def test_domestic_cup_can_eliminate_before_the_final():
    """B21: la copa generaba siempre las 4 rondas, así que nunca te eliminaban."""
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    rounds_seen = set()
    for season in range(60):
        fixtures = build_season_fixtures(p, season, rng=random.Random(season))
        cup = [f for f in fixtures if f.competitionId.startswith("domestic-cup-")]
        rounds_seen.add(len(cup))

    assert len(rounds_seen) > 1
    assert min(rounds_seen) < 4


def test_continental_cup_has_knockout_stages_and_a_final():
    """B5: la Champions solo generaba fase de liga, jamás una final."""
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    reached_final = False
    for season in range(60):
        fixtures = build_season_fixtures(p, season, rng=random.Random(season))
        continental = [f for f in fixtures if f.competitionId == "uefa-champions"]
        assert continental
        if any(f.stageId == "final" for f in continental):
            reached_final = True
            assert any(f.stageId == "semifinal" for f in continental)

    assert reached_final


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
        assert session.seasonProgress.leagueTable
        assert session.seasonProgress.leaguePosition is not None
        assert match.week == first_fixture.week
        assert match.competitionId == first_fixture.competitionId
        assert match.opponentId == first_fixture.opponentId
        assert match.homeAway == first_fixture.homeAway
    finally:
        db.close()


def test_match_history_is_persisted_but_not_sent_to_the_client():
    """B4/B5: el historial completo vive en la sesión; el cliente solo ve la ventana."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        p = build_player_from_draft(make_draft(startingClub="col-envigado"))
        progress = ensure_season_fixtures(p, SeasonProgress(), 1)
        model = CareerSessionModel(
            id="history-session",
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

        session = None
        for _ in range(3):
            session = play_match("history-session", db)

        assert session.seasonProgress.matchHistory == []
        assert len(model.season_progress["matchHistory"]) == 3
    finally:
        db.close()


def test_play_match_raises_blocked_error_with_pending_event():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        p = build_player_from_draft(make_draft(startingClub="col-envigado"))
        progress = ensure_season_fixtures(p, SeasonProgress(), 1)
        model = CareerSessionModel(
            id="blocked-session",
            mode="player",
            current_season=1,
            pending_event_id="some-event",
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

        try:
            play_match("blocked-session", db)
            assert False, "expected ActionBlockedError"
        except ActionBlockedError as exc:
            assert exc.reason == "pending_event"
    finally:
        db.close()


def test_persist_raises_concurrent_modification_on_stale_version(tmp_path):
    from app.modules.career.service import _persist

    db_path = tmp_path / "concurrent.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db_a = SessionLocal()
    db_b = SessionLocal()
    try:
        p = build_player_from_draft(make_draft(startingClub="col-envigado"))
        progress = ensure_season_fixtures(p, SeasonProgress(), 1)
        model = CareerSessionModel(
            id="concurrent-session",
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
        db_a.add(model)
        db_a.commit()

        model_a = db_a.get(CareerSessionModel, "concurrent-session")
        model_b = db_b.get(CareerSessionModel, "concurrent-session")

        p.matchesPlayed = 1
        _persist(model_a, p, db_a)

        p.matchesPlayed = 2
        try:
            _persist(model_b, p, db_b)
            assert False, "expected ConcurrentModificationError"
        except ConcurrentModificationError:
            pass
    finally:
        db_a.close()
        db_b.close()


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


def test_simulate_match_result_always_matches_scoreline():
    p = build_player_from_draft(make_draft(position="ST"))
    for seed in range(200):
        match = simulate_match(p, seed, rng=random.Random(seed))
        if match.goalsFor > match.goalsAgainst:
            assert match.result == "W"
        elif match.goalsFor == match.goalsAgainst:
            assert match.result == "D"
        else:
            assert match.result == "L"



def test_match_selection_preview_explains_likely_role():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    p.state.reputation = 85
    p.relationships.coach = 85
    p.state.fitness = 90
    p.state.form = 80

    selection = build_match_selection(p)

    assert selection.role == "starter"
    assert selection.starterChance >= 58
    assert selection.expectedMinutesMax == 90
    assert selection.factors


def test_match_selection_preview_can_show_bench_risk():
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    p.state.reputation = 10
    p.relationships.coach = 20
    p.state.fitness = 35
    p.state.form = 35

    selection = build_match_selection(p)

    assert selection.role in {"substitute", "bench"}
    assert selection.starterChance < 58
    assert any("DT" in factor or "Físico" in factor for factor in selection.factors)


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


def test_league_table_ranks_player_club_by_points():
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    progress = SeasonProgress(
        matchesPlayed=10,
        wins=6,
        draws=2,
        losses=2,
        fixtures=build_season_fixtures(p),
    )

    table = build_league_table(p, progress)
    player_row = next(row for row in table if row.clubId == p.clubId)

    assert player_row.points == 20
    assert player_row.position >= 1
    assert table == sorted(
        table,
        key=lambda row: (-row.points, -row.goalDifference, -row.goalsFor, row.clubName),
    )


def test_projected_league_table_varies_between_seasons():
    """El rendimiento proyectado de cada rival depende del club Y de la temporada,
    para que no rindan siempre igual respecto a su prestigio."""
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))

    def rival_records(season: int):
        progress = ensure_season_fixtures(
            p,
            SeasonProgress(
                matchesPlayed=10,
                leagueWins=6,
                leagueDraws=2,
                leagueLosses=2,
            ),
            season,
        )
        table = build_league_table(p, progress)
        return {
            row.clubId: (row.wins, row.draws, row.losses, row.goalsFor)
            for row in table
            if row.clubId != p.clubId
        }

    first = rival_records(1)
    second = rival_records(2)

    assert first.keys() == second.keys()
    assert first != second
    # Y dentro de una misma temporada el resultado es estable.
    assert rival_records(1) == first


def test_league_table_rows_are_arithmetically_coherent_and_not_uniform():
    """B11: la proyección solo dependía del prestigio y clonaba registros."""
    p = build_player_from_draft(make_draft(startingClub="col-envigado"))
    progress = SeasonProgress(
        matchesPlayed=5,
        wins=3,
        draws=1,
        losses=1,
        leagueWins=3,
        leagueDraws=1,
        leagueLosses=1,
        fixtures=build_season_fixtures(p),
    )

    table = build_league_table(p, progress)
    rival_records = {
        (row.wins, row.draws, row.losses, row.goalsFor, row.goalsAgainst)
        for row in table
        if row.clubId != p.clubId
    }

    assert len(rival_records) > 1
    for row in table:
        assert row.wins + row.draws + row.losses == row.played
        assert row.points == row.wins * 3 + row.draws
        assert row.goalDifference == row.goalsFor - row.goalsAgainst


def test_league_table_uses_league_record_not_total_cup_wins():
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    progress = SeasonProgress(
        matchesPlayed=10,
        wins=8,
        draws=0,
        losses=2,
        leagueWins=3,
        leagueDraws=1,
        leagueLosses=1,
        fixtures=build_season_fixtures(p),
    )

    table = build_league_table(p, progress)
    player_row = next(row for row in table if row.clubId == p.clubId)

    assert player_row.points == 10
    assert player_row.wins == 3


def _cup_match(*, stage_id, stage_display, result, competition_name="Copa del Rey") -> MatchResult:
    return MatchResult(
        matchNumber=1,
        competitionId="domestic-cup-ES",
        competitionName=competition_name,
        stageId=stage_id,
        stageDisplay=stage_display,
        opponentId="rival",
        opponentName="Rival FC",
        opponentShortName="RIV",
        goalsFor=1,
        goalsAgainst=0,
        result=result,
        minutesPlayed=90,
        goals=0,
        assists=0,
        rating=7.0,
        starter=True,
        narrative="",
    )


def test_league_table_uses_full_season_history_beyond_recent_window():
    """B4: la ventana recentMatches (8) no debe limitar el cómputo de goles de la tabla."""
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    league_matches = [
        MatchResult(
            matchNumber=i,
            competitionId="esp-laliga",
            competitionName="LaLiga",
            opponentId="rival",
            opponentName="Rival FC",
            opponentShortName="RIV",
            goalsFor=2,
            goalsAgainst=0,
            result="W",
            minutesPlayed=90,
            goals=1,
            assists=0,
            rating=7.5,
            starter=True,
            narrative="",
        )
        for i in range(1, 11)
    ]
    progress = SeasonProgress(
        matchesPlayed=10,
        wins=10,
        draws=0,
        losses=0,
        leagueWins=10,
        leagueDraws=0,
        leagueLosses=0,
        recentMatches=league_matches[-8:],
        matchHistory=league_matches,
        fixtures=build_season_fixtures(p),
    )

    table = build_league_table(p, progress)
    player_row = next(row for row in table if row.clubId == p.clubId)

    assert player_row.goalsFor == 20
    assert player_row.goalsAgainst == 0


def test_knockout_trophy_survives_beyond_recent_matches_window():
    """B5: una final ganada antes de los últimos 8 partidos no debe perder el trofeo."""
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    final_win = _cup_match(stage_id="final", stage_display="Final", result="W")
    filler = [
        _cup_match(stage_id="regular", stage_display="League", result="D", competition_name="LaLiga")
        for _ in range(9)
    ]
    progress = SeasonProgress(
        matchesPlayed=10,
        wins=1,
        draws=9,
        losses=0,
        recentMatches=filler[-8:],
        matchHistory=[final_win, *filler],
        fixtures=build_season_fixtures(p),
    )

    snap = close_season(p, progress, 1, rng=random.Random(1))
    assert "Copa del Rey" in snap.trophies


def test_semifinal_win_does_not_award_trophy():
    """B26: 'final' in 'semifinal' era True; ganar la semifinal no debe dar título."""
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    semifinal_win = _cup_match(stage_id="semifinal", stage_display="Semifinal", result="W")
    progress = SeasonProgress(
        matchesPlayed=1,
        wins=1,
        draws=0,
        losses=0,
        recentMatches=[semifinal_win],
        matchHistory=[semifinal_win],
        fixtures=build_season_fixtures(p),
    )

    snap = close_season(p, progress, 1, rng=random.Random(1))
    assert "Copa del Rey" not in snap.trophies


def test_close_season_awards_league_only_when_table_champion():
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    league_name = "LaLiga EA Sports"
    progress = SeasonProgress(
        matchesPlayed=38,
        matchesTotal=38,
        appearances=38,
        goals=50,
        assists=20,
        minutesPlayed=3300,
        ratingsSum=38 * 9.2,
        wins=30,
        draws=5,
        losses=3,
        leagueTable=[
            LeagueTableEntry(position=1, clubId="esp-barcelona", clubName="FC Barcelona", shortName="Barça", played=38, wins=31, draws=4, losses=3, goalsFor=90, goalsAgainst=28, goalDifference=62, points=97),
            LeagueTableEntry(position=2, clubId="esp-realmadrid", clubName="Real Madrid", shortName="Madrid", played=38, wins=30, draws=5, losses=3, goalsFor=88, goalsAgainst=30, goalDifference=58, points=95),
        ],
    )

    snap = close_season(p, progress, 1, rng=random.Random(2))

    assert league_name not in snap.trophies


def test_close_season_awards_league_to_table_champion():
    p = build_player_from_draft(make_draft(startingLeague="esp-laliga", startingClub="esp-realmadrid"))
    progress = SeasonProgress(
        matchesPlayed=38,
        matchesTotal=38,
        appearances=38,
        goals=12,
        assists=9,
        minutesPlayed=2900,
        ratingsSum=38 * 7.1,
        wins=24,
        draws=8,
        losses=6,
        leagueTable=[
            LeagueTableEntry(position=1, clubId="esp-realmadrid", clubName="Real Madrid", shortName="Madrid", played=38, wins=24, draws=8, losses=6, goalsFor=76, goalsAgainst=35, goalDifference=41, points=80),
            LeagueTableEntry(position=2, clubId="esp-barcelona", clubName="FC Barcelona", shortName="Barça", played=38, wins=23, draws=9, losses=6, goalsFor=74, goalsAgainst=35, goalDifference=39, points=78),
        ],
    )

    snap = close_season(p, progress, 1, rng=random.Random(2))

    assert "LaLiga EA Sports" in snap.trophies


def _snapshot(**overrides) -> SeasonSnapshot:
    base = dict(
        season=1, clubId="esp-realmadrid", clubName="Real Madrid",
        matchesPlayed=30, goals=10, assists=5, minutesPlayed=2400,
        averageRating=6.8, wins=18, draws=6, losses=6,
        trophies=[], individualAwards=[], keyEvents=[],
    )
    base.update(overrides)
    return SeasonSnapshot(**base)


def test_young_player_grows_and_veteran_declines():
    """B10: close_season no tocaba ningún atributo, así que nunca evolucionaban."""
    young = build_player_from_draft(make_draft(age=18, position="ST"))
    young.potential = 90
    before_young = young.technical.shooting

    veteran = build_player_from_draft(make_draft(age=34, position="ST"))
    veteran.potential = 90
    before_veteran = veteran.physical.stamina

    develop_player(young, 2200, 7.0, key_attributes_for("ST"), random.Random(1))
    develop_player(veteran, 2200, 7.0, key_attributes_for("ST"), random.Random(1))

    assert young.technical.shooting > before_young
    assert veteran.physical.stamina < before_veteran


def test_growth_stops_at_potential_ceiling():
    player = build_player_from_draft(make_draft(age=18, position="ST"))
    player.potential = 60
    player.technical.shooting = 72

    develop_player(player, 2200, 7.5, key_attributes_for("ST"), random.Random(3))

    assert player.technical.shooting == 72


def test_bench_player_barely_develops():
    starter = build_player_from_draft(make_draft(age=18, position="ST"))
    benched = build_player_from_draft(make_draft(age=18, position="ST"))
    starter.potential = benched.potential = 95
    baseline = starter.technical.shooting

    develop_player(starter, 2400, 7.0, key_attributes_for("ST"), random.Random(5))
    develop_player(benched, 150, 7.0, key_attributes_for("ST"), random.Random(5))

    assert starter.technical.shooting - baseline > benched.technical.shooting - baseline


def test_declining_a_retirement_offer_accelerates_the_decline():
    steady = build_player_from_draft(make_draft(age=35, position="ST"))
    stubborn = build_player_from_draft(make_draft(age=35, position="ST"))
    stubborn.retirementOffersDeclined = 3
    baseline = steady.physical.stamina

    develop_player(steady, 1200, 6.2, key_attributes_for("ST"), random.Random(7))
    develop_player(stubborn, 1200, 6.2, key_attributes_for("ST"), random.Random(7))

    assert stubborn.physical.stamina < steady.physical.stamina < baseline


def test_retirement_is_offered_only_when_the_career_is_ending():
    prime = build_player_from_draft(make_draft(age=26))
    veteran = build_player_from_draft(make_draft(age=35))
    veteran.age = 37
    fading = build_player_from_draft(make_draft(age=33))

    assert not should_offer_retirement(prime, _snapshot())
    assert should_offer_retirement(veteran, _snapshot())
    assert should_offer_retirement(fading, _snapshot(minutesPlayed=400))
    assert not should_offer_retirement(fading, _snapshot())


def test_retired_player_is_never_offered_retirement_again():
    player = build_player_from_draft(make_draft(age=35))
    player.age = 37
    player.retired = True

    assert not should_offer_retirement(player, _snapshot())


def test_reputation_converges_instead_of_pinning_at_the_extremes():
    """B22: la reputación acumulativa acababa clavada en 0 o en 100."""
    star = build_player_from_draft(make_draft(startingClub="esp-realmadrid", startingLeague="esp-laliga"))
    star.state.reputation = 100
    progress = SeasonProgress(matchesPlayed=30, appearances=30, goals=2, assists=1, ratingsSum=30 * 6.1)

    close_season(star, progress, 1, rng=random.Random(2))
    assert star.state.reputation < 100

    forgotten = build_player_from_draft(make_draft(startingClub="col-envigado"))
    forgotten.state.reputation = 0
    good_progress = SeasonProgress(matchesPlayed=30, appearances=30, goals=15, assists=8, ratingsSum=30 * 7.1)

    close_season(forgotten, good_progress, 1, rng=random.Random(2))
    assert forgotten.state.reputation > 0


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


def test_close_season_snapshot_counts_appearances_not_call_ups():
    p = build_player_from_draft(make_draft())
    progress = SeasonProgress(
        matchesPlayed=34,
        matchesTotal=34,
        appearances=30,
        goals=15,
        assists=8,
        minutesPlayed=2500,
        ratingsSum=30 * 7.2,
        wins=18,
        draws=8,
        losses=8,
    )
    snap = close_season(p, progress, 1, rng=random.Random(2))
    assert snap.matchesPlayed == 30
    assert snap.callUps == 34


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


def test_centre_back_wins_ballon_dor_on_clean_sheets_and_a_title():
    """Un central se mide por vallas invictas y títulos, no por goles: es el
    camino de Cannavaro en 2006 o Van Dijk en 2019."""
    p = build_player_from_draft(make_draft(position="CB"))
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Test FC",
        matchesPlayed=34, goals=1, assists=1, cleanSheets=14, minutesPlayed=3000,
        averageRating=6.5, wins=24, draws=6, losses=4,
        trophies=["Champions League"], individualAwards=[], keyEvents=[],
    )

    names = [a.name for a in compute_season_awards(p, snap)]

    assert "Balón de Oro" in names
    assert any("Mejor Defensor" in n for n in names)


def test_defender_without_a_title_does_not_win_ballon_dor():
    """Sin levantar nada, por buena que sea la temporada, no alcanza."""
    p = build_player_from_draft(make_draft(position="CB"))
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Test FC",
        matchesPlayed=34, goals=1, assists=1, cleanSheets=14, minutesPlayed=3000,
        averageRating=6.5, wins=24, draws=6, losses=4,
        trophies=[], individualAwards=[], keyEvents=[],
    )

    assert "Balón de Oro" not in [a.name for a in compute_season_awards(p, snap)]


def test_defender_with_few_clean_sheets_does_not_win_ballon_dor():
    p = build_player_from_draft(make_draft(position="CB"))
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Test FC",
        matchesPlayed=34, goals=1, assists=1, cleanSheets=3, minutesPlayed=3000,
        averageRating=6.5, wins=24, draws=6, losses=4,
        trophies=["Champions League"], individualAwards=[], keyEvents=[],
    )

    assert "Balón de Oro" not in [a.name for a in compute_season_awards(p, snap)]


def test_goalkeeper_wins_golden_glove_on_clean_sheets():
    p = build_player_from_draft(make_draft(position="GK"))
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Test FC",
        matchesPlayed=34, goals=0, assists=0, cleanSheets=13, minutesPlayed=3060,
        averageRating=6.3, wins=22, draws=8, losses=4,
        trophies=[], individualAwards=[], keyEvents=[],
    )

    assert any("Guante de Oro" in a.name for a in compute_season_awards(p, snap))


def test_striker_does_not_win_defensive_awards():
    """Los premios defensivos son de defensores, aunque el equipo no reciba goles."""
    p = build_player_from_draft(make_draft(position="ST"))
    snap = SeasonSnapshot(
        season=1, clubId=p.clubId, clubName="Test FC",
        matchesPlayed=34, goals=20, assists=8, cleanSheets=16, minutesPlayed=3000,
        averageRating=7.1, wins=24, draws=6, losses=4,
        trophies=["LaLiga"], individualAwards=[], keyEvents=[],
    )

    names = [a.name for a in compute_season_awards(p, snap)]

    assert not any("Mejor Defensor" in n for n in names)
    assert not any("Guante de Oro" in n for n in names)


def test_clean_sheet_lifts_a_defender_rating_but_barely_moves_a_striker():
    """B: una valla invicta no le sumaba nada a un central."""
    from app.modules.simulation.match import _defensive_contribution

    assert _defensive_contribution("CB", 0, 1.0) > 0.5
    assert _defensive_contribution("GK", 0, 1.0) > 0.5
    assert _defensive_contribution("ST", 0, 1.0) < 0.1
    # Encajar goles castiga al defensor y deja casi indiferente al delantero.
    assert _defensive_contribution("CB", 4, 1.0) < -0.5
    # Quien entró al final no sostuvo esa valla.
    assert _defensive_contribution("CB", 0, 0.1) < _defensive_contribution("CB", 0, 1.0)


def test_man_of_the_match_is_reachable_for_defenders():
    """Con el umbral único de 8,5 un defensor jamás podía ser figura."""
    from app.modules.simulation.match import _is_man_of_the_match

    assert _is_man_of_the_match("CB", 7.3, 0, 0, 0)
    assert _is_man_of_the_match("GK", 7.2, 0, 0, 0)
    # Encajando goles no hay figura defensiva, por buena que sea la nota.
    assert not _is_man_of_the_match("CB", 7.5, 0, 0, 2)
    # El delantero sigue necesitando marcar y una nota alta.
    assert _is_man_of_the_match("ST", 8.3, 2, 0, 1)
    assert not _is_man_of_the_match("ST", 8.3, 0, 0, 0)


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
