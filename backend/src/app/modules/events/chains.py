from app.schemas import EventChoice, PendingChain


def queue_follow_ups(
    choice: EventChoice,
    current_season: int,
    events_resolved: int,
    existing_chains: list[PendingChain],
) -> list[PendingChain]:
    new_chains = list(existing_chains)
    for follow_up in choice.followUps:
        fires_at_season = current_season + max(0, follow_up.delaySeasons)
        fires_after_events = events_resolved + max(0, follow_up.delayEvents)
        new_chains.append(
            PendingChain(
                eventId=follow_up.eventId,
                firesAtSeason=fires_at_season,
                firesAfterEvents=fires_after_events,
                reason=follow_up.reason,
            )
        )
    return new_chains


def pop_ready_chain(
    chains: list[PendingChain],
    current_season: int,
    events_resolved: int,
) -> tuple[PendingChain | None, list[PendingChain]]:
    ready_index = None
    for i, chain in enumerate(chains):
        if (
            chain.firesAtSeason <= current_season
            and chain.firesAfterEvents <= events_resolved
        ):
            ready_index = i
            break
    if ready_index is None:
        return None, chains
    ready = chains[ready_index]
    remaining = chains[:ready_index] + chains[ready_index + 1 :]
    return ready, remaining


def decrement_sanctions(sanctions: list) -> tuple[list, list[str]]:
    active: list = []
    expired: list[str] = []
    for sanction in sanctions:
        remaining = sanction.remainingSeasons - 1
        if remaining <= 0:
            expired.append(sanction.id)
        else:
            sanction.remainingSeasons = remaining
            active.append(sanction)
    return active, expired
