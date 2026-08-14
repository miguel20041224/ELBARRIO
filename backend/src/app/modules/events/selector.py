import random
from app.schemas import GameEvent, Player, SeasonProgress
from app.modules.events.library import EVENTS, get_event
from app.modules.clubs.data import get_club, get_league


def _tier_for_player(player: Player) -> int:
    if not player.clubId:
        return 1
    club = get_club(player.clubId)
    if club:
        league = get_league(club.league_id)
        if league:
            return league.tier
    return 1


def _event_matches(event: GameEvent, player: Player, tier: int) -> bool:
    if event.chained:
        return False
    if event.minAge is not None and player.age < event.minAge:
        return False
    if event.maxAge is not None and player.age > event.maxAge:
        return False
    if event.requiresClubTier and tier not in event.requiresClubTier:
        return False
    if event.requiresMinReputation is not None and player.state.reputation < event.requiresMinReputation:
        return False
    player_tags = set(player.tags or [])
    if event.requiresTags and not set(event.requiresTags).issubset(player_tags):
        return False
    if event.forbidTags and player_tags.intersection(event.forbidTags):
        return False
    return True


def _contextual_weight(event: GameEvent, player: Player) -> float:
    base = event.weight
    if event.category == "personal" and player.state.happiness < 40:
        base *= 1.4
    if event.category == "health" and player.state.fatigue > 60:
        base *= 2.0
    if event.category == "social" and player.state.pressure > 65:
        base *= 1.3
    if event.category == "career" and player.state.reputation > 60:
        base *= 1.5
    if event.category == "media" and player.state.reputation > 55:
        base *= 1.2
    if event.category == "financial" and player.finance.balance > 500000:
        base *= 1.3
    if event.id == "social.drug_offer" and player.state.happiness < 45 and player.state.fatigue > 55:
        base *= 2.0
    if event.id == "media.selection_call_up" and player.state.reputation > 55:
        base *= 2.5
    return base


def draw_event_for(player: Player, rng: random.Random | None = None) -> GameEvent | None:
    tier = _tier_for_player(player)
    candidates = [e for e in EVENTS if _event_matches(e, player, tier)]
    if not candidates:
        return None
    weights = [_contextual_weight(e, player) for e in candidates]
    r = rng or random.Random()
    return r.choices(candidates, weights=weights, k=1)[0]


def draw_chained_event(event_id: str) -> GameEvent | None:
    event = get_event(event_id)
    return event


def should_offer_event(
    progress: SeasonProgress,
    rng: random.Random | None = None,
) -> bool:
    if progress.eventsUsed >= progress.eventsMax:
        return False
    matches_between = max(1, progress.matchesTotal // (progress.eventsMax + 1))
    matches_since_last = progress.matchesPlayed - (progress.eventsUsed * matches_between)
    if matches_since_last < matches_between:
        return False
    trigger_chance = 0.55 + min(0.3, matches_since_last * 0.05)
    r = rng or random.Random()
    return r.random() < trigger_chance
