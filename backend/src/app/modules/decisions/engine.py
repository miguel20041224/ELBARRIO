from typing import Any
from app.schemas import EventChoice, Player


def _clamp(value: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, value))


def _apply_state_deltas(player: Player, deltas: dict[str, float]) -> None:
    state = player.state
    for key, delta in deltas.items():
        if hasattr(state, key):
            current = getattr(state, key)
            setattr(state, key, _clamp(current + float(delta)))


def _apply_relationship_deltas(player: Player, deltas: dict[str, float]) -> None:
    rel = player.relationships
    for key, delta in deltas.items():
        if hasattr(rel, key):
            current = getattr(rel, key)
            setattr(rel, key, _clamp(current + float(delta)))


def _apply_finance_deltas(player: Player, deltas: dict[str, float]) -> None:
    fin = player.finance
    for key, delta in deltas.items():
        if hasattr(fin, key):
            current = getattr(fin, key)
            setattr(fin, key, max(0.0, current + float(delta)))


def _apply_reputation(player: Player, delta: float) -> None:
    player.state.reputation = _clamp(player.state.reputation + delta)


def _apply_tags(player: Player, tags: list[str]) -> None:
    existing = set(player.tags or [])
    existing.update(tags)
    player.tags = sorted(existing)


def apply_choice(player: Player, choice: EventChoice) -> dict[str, Any]:
    effects = choice.effects or {}
    diff: dict[str, Any] = {"choice_id": choice.id, "label": choice.label}

    if state_deltas := effects.get("state"):
        _apply_state_deltas(player, state_deltas)
        diff["state"] = state_deltas
    if rel_deltas := effects.get("relationships"):
        _apply_relationship_deltas(player, rel_deltas)
        diff["relationships"] = rel_deltas
    if fin_deltas := effects.get("finance"):
        _apply_finance_deltas(player, fin_deltas)
        diff["finance"] = fin_deltas
    if reputation_delta := effects.get("reputationDelta"):
        _apply_reputation(player, float(reputation_delta))
        diff["reputationDelta"] = reputation_delta
    if choice.tags:
        _apply_tags(player, choice.tags)
        diff["tags"] = choice.tags

    return diff
