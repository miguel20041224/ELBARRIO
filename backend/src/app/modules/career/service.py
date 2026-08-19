import random
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.models import CareerSessionModel
from app.modules.awards.service import compute_season_awards, snapshot_award_names
from app.modules.clubs.data import CLUBS, get_club, get_league
from app.modules.decisions.engine import apply_choice
from app.modules.events.chains import (
    decrement_sanctions,
    pop_ready_chain,
    queue_follow_ups,
)
from app.modules.events.library import get_event
from app.modules.events.selector import (
    draw_chained_event,
    draw_event_for,
    should_offer_event,
)
from app.modules.player.factory import build_player_from_draft
from app.modules.roulette.service import (
    apply_outcome,
    build_roulette,
    find_outcome,
)
from app.modules.simulation.match import build_match_selection, simulate_match
from app.modules.simulation.season import close_season, ensure_season_fixtures, refresh_league_table
from app.modules.transfers.service import (
    apply_transfer,
    compute_transfer_window,
    stay_at_club,
)
from app.schemas import (
    CareerSession,
    ClubInfo,
    CreateCareerPayload,
    MatchResult,
    PendingChain,
    Player,
    RouletteRoll,
    SeasonProgress,
    SeasonSnapshot,
    TransferOffer,
    TransferWindow,
)


RECENT_MATCH_LIMIT = 8


class ActionBlockedError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class ConcurrentModificationError(Exception):
    pass


def _tick_contract_year(player: Player) -> None:
    if player.clubId and player.finance.contractYears > 0:
        player.finance.contractYears = max(0, player.finance.contractYears - 1)


def _club_info(club_id: str | None) -> ClubInfo | None:
    if not club_id:
        return None
    club = get_club(club_id)
    if not club:
        return None
    league = get_league(club.league_id)
    if not league:
        return None
    return ClubInfo(
        id=club.id,
        name=club.name,
        shortName=club.short_name,
        leagueId=club.league_id,
        leagueName=league.name,
        country=league.country,
        city=club.city,
        prestige=club.prestige,
        budget=club.budget,
        nickname=club.nickname,
    )


def _to_response(model: CareerSessionModel) -> CareerSession:
    player = Player(**model.player_data)
    pending_event = get_event(model.pending_event_id) if model.pending_event_id else None
    history = [SeasonSnapshot(**snap) for snap in (model.history or [])]
    chains = [PendingChain(**c) for c in (model.pending_chains or [])]
    progress_data = model.season_progress or {}
    progress = SeasonProgress(**progress_data) if progress_data else SeasonProgress()
    progress = ensure_season_fixtures(player, progress, model.current_season)
    roulette = RouletteRoll(**model.pending_roulette) if model.pending_roulette else None
    transfer = (
        TransferWindow(**model.pending_transfer_window)
        if model.pending_transfer_window
        else None
    )
    season_complete = progress.matchesPlayed >= progress.matchesTotal
    next_fixture = progress.fixtures[progress.matchesPlayed] if not season_complete and progress.fixtures else None
    next_selection = None
    if next_fixture and not (model.pending_roulette or model.pending_transfer_window or model.pending_event_id):
        next_selection = build_match_selection(player, next_fixture)
    return CareerSession(
        id=model.id,
        player=player,
        mode=model.mode,
        currentSeason=model.current_season,
        history=history,
        seasonProgress=progress,
        seasonComplete=season_complete,
        pendingEventId=model.pending_event_id,
        pendingEvent=pending_event,
        pendingEventReason=model.pending_event_reason,
        pendingChains=chains,
        pendingRoulette=roulette,
        pendingTransferWindow=transfer,
        currentClub=_club_info(player.clubId),
        nextMatchSelection=next_selection,
    )


def _persist(
    model: CareerSessionModel,
    player: Player,
    db: Session,
    chains: list[PendingChain] | None = None,
    progress: SeasonProgress | None = None,
    roulette: RouletteRoll | None = ...,
    transfer: TransferWindow | None = ...,
) -> CareerSessionModel:
    model.player_data = player.model_dump()
    if chains is not None:
        model.pending_chains = [c.model_dump() for c in chains]
    if progress is not None:
        model.season_progress = progress.model_dump()
    if roulette is not ...:
        model.pending_roulette = roulette.model_dump() if roulette else None
    if transfer is not ...:
        model.pending_transfer_window = transfer.model_dump() if transfer else None
    db.add(model)
    try:
        db.commit()
    except StaleDataError:
        db.rollback()
        raise ConcurrentModificationError(
            "La carrera fue modificada por otra petición mientras tanto."
        ) from None
    db.refresh(model)
    return model


def create_career(payload: CreateCareerPayload, db: Session) -> CareerSession:
    player = build_player_from_draft(payload.draft)
    initial_progress = ensure_season_fixtures(player, SeasonProgress(), 1)
    initial_roulette = build_roulette("career_start", player)
    model = CareerSessionModel(
        id=str(uuid4()),
        mode=payload.mode,
        current_season=1,
        pending_event_id=None,
        pending_event_reason=None,
        events_resolved_total=0,
        player_data=player.model_dump(),
        history=[],
        pending_chains=[],
        season_progress=initial_progress.model_dump(),
        pending_roulette=initial_roulette.model_dump(),
        pending_transfer_window=None,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return _to_response(model)


def get_career(session_id: str, db: Session) -> CareerSession | None:
    model = db.get(CareerSessionModel, session_id)
    return _to_response(model) if model else None


def spin_roulette(session_id: str, outcome_id: str, db: Session) -> CareerSession | None:
    model = db.get(CareerSessionModel, session_id)
    if not model or not model.pending_roulette:
        return None
    roll = RouletteRoll(**model.pending_roulette)
    outcome = find_outcome(roll, outcome_id)
    if not outcome:
        return None
    player = Player(**model.player_data)
    apply_outcome(player, outcome)

    transfer_window: TransferWindow | None = ...
    if roll.kind == "season_end" and model.history:
        last_snap = SeasonSnapshot(**model.history[-1])
        window = compute_transfer_window(player, last_snap)
        transfer_window = window
    _persist(model, player, db, roulette=None, transfer=transfer_window)
    return _to_response(model)


def _record_match_progress(player: Player, progress: SeasonProgress, match: MatchResult) -> SeasonProgress:
    progress.matchesPlayed += 1
    progress.goals += match.goals
    progress.assists += match.assists
    progress.minutesPlayed += match.minutesPlayed
    if match.minutesPlayed > 0:
        progress.ratingsSum += match.rating
        progress.appearances += 1
    if match.result == "W":
        progress.wins += 1
    elif match.result == "D":
        progress.draws += 1
    else:
        progress.losses += 1

    club = get_club(player.clubId) if player.clubId else None
    if club and match.competitionId == club.league_id:
        if match.result == "W":
            progress.leagueWins += 1
        elif match.result == "D":
            progress.leagueDraws += 1
        else:
            progress.leagueLosses += 1
    recent = list(progress.recentMatches or [])
    recent.append(match)
    if len(recent) > RECENT_MATCH_LIMIT:
        recent = recent[-RECENT_MATCH_LIMIT:]
    progress.recentMatches = recent
    progress = refresh_league_table(player, progress)
    return SeasonProgress(**progress.model_dump())


def play_match(session_id: str, db: Session) -> CareerSession | None:
    model = db.get(CareerSessionModel, session_id)
    if not model:
        return None
    if model.pending_roulette:
        raise ActionBlockedError("pending_roulette")
    if model.pending_transfer_window:
        raise ActionBlockedError("pending_transfer_window")
    if model.pending_event_id:
        raise ActionBlockedError("pending_event")

    progress = ensure_season_fixtures(
        Player(**model.player_data),
        SeasonProgress(**(model.season_progress or {})),
        model.current_season,
    )
    if progress.matchesPlayed >= progress.matchesTotal:
        return _to_response(model)

    player = Player(**model.player_data)
    progress = ensure_season_fixtures(player, progress, model.current_season)
    fixture = progress.fixtures[progress.matchesPlayed] if progress.fixtures else None
    match = simulate_match(player, progress.matchesPlayed + 1, fixture=fixture)
    progress = _record_match_progress(player, progress, match)

    if progress.matchesPlayed < progress.matchesTotal and should_offer_event(progress):
        event = draw_event_for(player)
        if event:
            model.pending_event_id = event.id
            model.pending_event_reason = None
            progress.eventsUsed += 1

    _persist(model, player, db, progress=progress)
    return _to_response(model)


def resolve_event(session_id: str, choice_id: str, db: Session) -> CareerSession | None:
    model = db.get(CareerSessionModel, session_id)
    if not model or not model.pending_event_id:
        return None
    event = get_event(model.pending_event_id)
    if not event:
        return None
    choice = next((c for c in event.choices if c.id == choice_id), None)
    if not choice:
        return None
    player = Player(**model.player_data)
    apply_choice(player, choice)
    _handle_event_transfer(player, event.id, choice.id)

    chains = [PendingChain(**c) for c in (model.pending_chains or [])]
    model.events_resolved_total = (model.events_resolved_total or 0) + 1
    new_chains = queue_follow_ups(
        choice, model.current_season, model.events_resolved_total, chains
    )

    ready_chain, remaining_chains = pop_ready_chain(
        new_chains, model.current_season, model.events_resolved_total
    )
    if ready_chain:
        chained_event = draw_chained_event(ready_chain.eventId)
        model.pending_event_id = chained_event.id if chained_event else None
        model.pending_event_reason = ready_chain.reason or None
        new_chains = remaining_chains
        progress = SeasonProgress(**(model.season_progress or {}))
        progress.eventsUsed += 1
        _persist(model, player, db, chains=new_chains, progress=progress)
    else:
        model.pending_event_id = None
        model.pending_event_reason = None
        _persist(model, player, db, chains=new_chains)

    return _to_response(model)


def _handle_event_transfer(player: Player, event_id: str, choice_id: str) -> None:
    """When specific event/choice pairs fire, force a real club transfer."""
    if not player.clubId:
        return
    current_club = get_club(player.clubId)
    if not current_club:
        return

    if event_id == "career.transfer_offer_european" and choice_id in {"accept_top", "accept_final"}:
        _force_transfer_to_tier(player, current_club, target_country_group={"ES", "EN", "IT", "DE"})
    elif event_id == "career.transfer_negotiation_result" and choice_id == "accept_final":
        _force_transfer_to_tier(player, current_club, target_country_group={"ES", "EN", "IT", "DE"})
    elif event_id == "career.tempting_saudi_offer" and choice_id == "accept_money":
        _force_transfer_to_tier(player, current_club, target_country_group={"SA"})


def _force_transfer_to_tier(player: Player, current_club, target_country_group: set[str]) -> None:
    candidates = []
    for club in CLUBS.values():
        if club.id == current_club.id:
            continue
        league = get_league(club.league_id)
        if not league or league.country not in target_country_group:
            continue
        if club.prestige < 78:
            continue
        candidates.append(club)
    if not candidates:
        return
    club = random.choice(candidates)
    league = get_league(club.league_id)
    from app.schemas import ClubInfo as CI, TransferOffer as TO
    club_info = CI(
        id=club.id,
        name=club.name,
        shortName=club.short_name,
        leagueId=club.league_id,
        leagueName=league.name if league else "",
        country=league.country if league else "",
        city=club.city,
        prestige=club.prestige,
        budget=club.budget,
        nickname=club.nickname,
    )
    salary = (league.average_salary if league else 500) * (club.prestige / 100) * 1.15
    offer = TO(
        id=str(uuid4()),
        club=club_info,
        weeklySalary=salary,
        contractYears=4,
        signOnBonus=salary * 12,
        playingChance="starter" if player.state.reputation >= club.prestige - 15 else "rotation",
        reputationRequired=max(0, club.prestige - 20),
        note="Transferencia disparada por el evento aceptado.",
        highlight="🌍 Nuevo club",
    )
    apply_transfer(player, offer)


def advance_season(session_id: str, db: Session) -> CareerSession | None:
    model = db.get(CareerSessionModel, session_id)
    if not model:
        return None
    if model.pending_roulette or model.pending_transfer_window:
        return _to_response(model)

    player = Player(**model.player_data)
    progress = ensure_season_fixtures(player, SeasonProgress(**(model.season_progress or {})), model.current_season)
    if progress.matchesPlayed < progress.matchesTotal:
        return _to_response(model)

    snapshot = close_season(player, progress, model.current_season, rng=random.Random())
    individual_awards = compute_season_awards(player, snapshot)
    if individual_awards:
        player.trophies.extend(individual_awards)
        snapshot.individualAwards = snapshot_award_names(individual_awards)

    _tick_contract_year(player)

    active_sanctions, expired_ids = decrement_sanctions(player.sanctions)
    player.sanctions = active_sanctions
    if expired_ids:
        snapshot.keyEvents.append(f"Sanciones cumplidas: {', '.join(expired_ids)}")

    history = list(model.history or [])
    history.append(snapshot.model_dump())
    model.history = history
    model.current_season += 1
    model.pending_event_id = None
    model.pending_event_reason = None

    new_progress = ensure_season_fixtures(player, SeasonProgress(), model.current_season)
    end_roulette = build_roulette("season_end", player)

    _persist(model, player, db, progress=new_progress, roulette=end_roulette)
    return _to_response(model)


def accept_transfer(
    session_id: str,
    offer_id: str | None,
    db: Session,
) -> CareerSession | None:
    model = db.get(CareerSessionModel, session_id)
    if not model or not model.pending_transfer_window:
        return None
    window = TransferWindow(**model.pending_transfer_window)
    player = Player(**model.player_data)

    if offer_id is None:
        stay_at_club(player)
    else:
        offer = next((o for o in window.offers if o.id == offer_id), None)
        if not offer:
            return None
        apply_transfer(player, offer)

    new_progress = ensure_season_fixtures(player, SeasonProgress(), model.current_season)
    _persist(model, player, db, progress=new_progress, transfer=None)
    return _to_response(model)
