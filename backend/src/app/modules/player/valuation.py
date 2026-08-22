"""Valor de mercado del jugador.

Es el marcador emocional de la carrera: una sola cifra que resume nivel, edad y
escaparate. Como el OVR, se deriva en cada lectura y no se persiste, para que no
pueda contradecir a los atributos que lo producen.

Anclas tomadas del dataset de Copero (INFORME §4.5): 16 años y OVR 50 ronda los
€100K, 22 años y OVR ~72 en una liga media ronda los €4,7M, y 25 años con OVR 90
en una liga fuerte llega a €98M.
"""

from __future__ import annotations

import math

from app.modules.clubs.data import get_club, get_league
from app.modules.player.rating import overall
from app.schemas import Player


# Valor de referencia: OVR 50, en su mejor edad, en una liga media.
BASE_VALUE = 220_000.0

# Cada punto de OVR por encima de 50 multiplica el valor. Calibrado para que el
# salto de OVR 50 a 90 sea de unas 500 veces, como en las anclas de Copero.
OVERALL_GROWTH = 0.155

# Reputación de liga que se considera media y no mueve el valor.
NEUTRAL_LEAGUE_REPUTATION = 70.0

MINIMUM_VALUE = 10_000.0


def _age_factor(age: int) -> float:
    """Un jugador vale más cerca de su mejor momento que en las puntas.

    El juvenil todavía no rinde y el veterano ya no se amortiza; entre los 23 y
    los 27 el club paga por lo que ve, no por lo que espera.
    """
    if age <= 17:
        return 0.55
    if age <= 19:
        return 0.75
    if age <= 22:
        return 0.92
    if age <= 27:
        return 1.0
    if age <= 30:
        return 0.82
    if age <= 32:
        return 0.55
    if age <= 34:
        return 0.32
    if age <= 36:
        return 0.16
    return 0.07


def _league_factor(player: Player) -> float:
    """El escaparate cotiza: el mismo jugador vale más en una liga que se ve."""
    club = get_club(player.clubId) if player.clubId else None
    league = get_league(club.league_id) if club else None
    if not league:
        return 0.6
    return max(0.25, min(1.6, league.reputation / NEUTRAL_LEAGUE_REPUTATION))


def _standing_factor(player: Player) -> float:
    """Reputación y forma del jugador, alrededor de 1: modulan, no dominan."""
    reputation = max(0.0, min(100.0, player.state.reputation))
    form = max(0.0, min(100.0, player.state.form))
    return 0.75 + (reputation / 100) * 0.4 + (form / 100 - 0.5) * 0.1


def market_value(player: Player) -> float:
    """Valor de mercado en euros, redondeado a una cifra presentable."""
    rating = overall(player)
    value = (
        BASE_VALUE
        * math.exp(OVERALL_GROWTH * (rating - 50))
        * _age_factor(player.age)
        * _league_factor(player)
        * _standing_factor(player)
    )
    value = max(MINIMUM_VALUE, value)
    if value >= 1_000_000:
        return round(value, -5)
    if value >= 100_000:
        return round(value, -4)
    return round(value, -3)
