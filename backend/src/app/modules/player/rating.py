"""Qué define a cada puesto, y el OVR agregado que sale de ahí.

Fuente única de los atributos clave por posición. Antes había dos tablas: una
en factory.py decidía qué atributos CRECEN y otra en match.py decidía por cuáles
se MIDE el rendimiento. Coincidían en nueve puestos y en el arquero no
solapaban en nada, así que un GK entrenaba defending/heading/passing mientras se
lo puntuaba por composure/concentration/jumping. Con una sola tabla eso no puede
volver a pasar.
"""

from __future__ import annotations

from app.schemas import Player


# Los tres atributos que definen el rendimiento de cada puesto.
KEY_ATTRIBUTES_BY_POSITION: dict[str, tuple[str, ...]] = {
    "GK": ("concentration", "composure", "jumping"),
    "CB": ("defending", "heading", "strength"),
    "LB": ("defending", "pace", "stamina"),
    "RB": ("defending", "pace", "stamina"),
    "CDM": ("defending", "passing", "workRate"),
    "CM": ("passing", "vision", "stamina"),
    "CAM": ("passing", "vision", "dribbling"),
    "LW": ("pace", "dribbling", "shooting"),
    "RW": ("pace", "dribbling", "shooting"),
    "ST": ("shooting", "heading", "pace"),
}

# Cuánto pesa el puesto frente al promedio global. Un jugador es sobre todo lo
# que hace en su puesto, pero no exclusivamente.
KEY_ATTRIBUTE_WEIGHT = 0.55

ATTRIBUTE_GROUPS = ("technical", "mental", "physical")


def key_attributes_for(position: str) -> frozenset[str]:
    """Atributos que definen la posición, y que por eso progresan más rápido."""
    return frozenset(KEY_ATTRIBUTES_BY_POSITION.get(position, ()))


def _attribute_values(player: Player) -> list[float]:
    return [
        value
        for group in ATTRIBUTE_GROUPS
        for value in vars(getattr(player, group)).values()
    ]


def _key_values(player: Player) -> list[float]:
    key = KEY_ATTRIBUTES_BY_POSITION.get(player.position, ())
    return [
        getattr(stats, attribute)
        for group in ATTRIBUTE_GROUPS
        for stats in (getattr(player, group),)
        for attribute in key
        if hasattr(stats, attribute)
    ]


def overall(player: Player) -> int:
    """OVR agregado en escala 1-99, ponderado por lo que exige el puesto.

    Derivado en cada lectura, nunca persistido: almacenarlo lo dejaría
    desincronizarse de los atributos que lo producen.
    """
    values = _attribute_values(player)
    if not values:
        return 1
    average = sum(values) / len(values)
    key_values = _key_values(player)
    specialised = sum(key_values) / len(key_values) if key_values else average
    blended = average * (1 - KEY_ATTRIBUTE_WEIGHT) + specialised * KEY_ATTRIBUTE_WEIGHT
    return max(1, min(99, round(blended)))
