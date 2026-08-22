"""Progresión y declive de atributos entre temporadas.

Hasta ahora `close_season` solo tocaba estado (forma, fatiga, reputación, edad),
así que un jugador terminaba una carrera de quince temporadas con los mismos
atributos con los que la empezó. Aquí vive la curva de desarrollo: los jóvenes
crecen, los veteranos se apagan, y jugar es lo que dispara ambas cosas.
"""

import random

from app.schemas import Player, RetirementOffer, SeasonSnapshot

# Edad a partir de la cual el motor empieza a mirar el declive.
RETIREMENT_WATCH_AGE = 32

# Edad a partir de la cual el retiro se ofrece siempre.
RETIREMENT_CERTAIN_AGE = 36

# Edad a la que la carrera se termina aunque el jugador quiera seguir. Sin este
# techo la oferta se podía rechazar indefinidamente y la edad subía sola: una
# carrera llegaba a los 60 años en cancha.
RETIREMENT_FORCED_AGE = 40

# Cada temporada jugada tras rechazar el retiro acelera la caída.
DECLINE_PENALTY_PER_REFUSAL = 0.22

# Puntos de atributo que puede moverse una temporada en el pico de la curva.
MAX_SEASON_GROWTH = 6.0

# Minutos que se consideran una temporada completa de titular.
FULL_SEASON_MINUTES = 2200.0

# Edad de pico y edad a la que arranca el declive, por tipo de atributo.
# Lo físico se va primero; lo mental sigue creciendo con la experiencia.
AGE_CURVES: dict[str, tuple[int, int]] = {
    "technical": (27, 31),
    "mental": (30, 36),
    "physical": (25, 29),
}

# `pace` vive en TechnicalStats pero envejece como un atributo físico.
PACE_CURVE = "physical"

ATTRIBUTE_GROUPS: dict[str, tuple[str, ...]] = {
    "technical": ("pace", "dribbling", "passing", "shooting", "heading", "defending"),
    "mental": ("concentration", "composure", "workRate", "leadership", "vision"),
    "physical": ("stamina", "strength", "jumping", "agility"),
}


def _age_curve(age: int, group: str) -> float:
    """Devuelve el signo y la fuerza del cambio: >0 crece, <0 decae."""
    peak, decline_start = AGE_CURVES[group]
    if age < peak:
        return min(1.0, (peak - age) / max(1, peak - 16))
    if age < decline_start:
        return 0.05
    return -min(1.0, (age - decline_start + 1) / 8)


def _development_drive(minutes_played: float, average_rating: float) -> float:
    """Cuánto empuja el jugador su propio desarrollo esta temporada.

    Quien no juega no mejora: los minutos pesan más que el rating, porque un
    suplente brillante en cinco partidos no progresa como un titular regular.
    """
    minutes_share = min(1.0, minutes_played / FULL_SEASON_MINUTES)
    performance = (average_rating - 6.2) / 1.2
    return max(0.2, min(1.5, 0.4 + minutes_share * 0.7 + performance * 0.4))


def _decline_drive(minutes_played: float, offers_declined: int) -> float:
    """Seguir jugando frena la caída; estirar la carrera la acelera."""
    minutes_share = min(1.0, minutes_played / FULL_SEASON_MINUTES)
    base = max(0.45, 1.2 - minutes_share * 0.55)
    return base * (1 + offers_declined * DECLINE_PENALTY_PER_REFUSAL)


def _group_for(attribute: str, group: str) -> str:
    return PACE_CURVE if attribute == "pace" else group


def develop_player(
    player: Player,
    minutes_played: float,
    average_rating: float,
    key_attributes: frozenset[str] = frozenset(),
    rng: random.Random | None = None,
) -> dict[str, float]:
    """Evoluciona los atributos del jugador y devuelve los cambios aplicados."""
    r = rng or random.Random()
    growth_drive = _development_drive(minutes_played, average_rating)
    decline_drive = _decline_drive(minutes_played, player.retirementOffersDeclined)
    changes: dict[str, float] = {}

    for group, attributes in ATTRIBUTE_GROUPS.items():
        stats = getattr(player, group)
        for attribute in attributes:
            current = getattr(stats, attribute)
            curve = _age_curve(player.age, _group_for(attribute, group))

            if curve > 0:
                # El techo frena el crecimiento a medida que se acerca.
                headroom = max(0.0, player.potential - current) / 25
                focus = 1.0 if attribute in key_attributes else 0.65
                delta = MAX_SEASON_GROWTH * curve * growth_drive * min(1.0, headroom) * focus
            else:
                delta = MAX_SEASON_GROWTH * curve * decline_drive

            delta *= r.uniform(0.7, 1.3)
            updated = max(20.0, min(99.0, current + delta))
            if updated != current:
                setattr(stats, attribute, round(updated, 1))
                changes[attribute] = round(updated - current, 1)

    return changes


def _decline_reasons(player: Player, snapshot: SeasonSnapshot) -> list[str]:
    reasons: list[str] = []
    if player.age >= RETIREMENT_CERTAIN_AGE:
        reasons.append(f"Tenés {player.age} años")
    if snapshot.minutesPlayed < 900:
        reasons.append("Cada vez jugás menos minutos")
    if snapshot.averageRating < 6.3:
        reasons.append("Tu rendimiento viene cayendo")
    if player.physical.stamina < 60:
        reasons.append("El físico ya no aguanta como antes")
    if player.retirementOffersDeclined > 0:
        reasons.append(f"Ya estiraste la carrera {player.retirementOffersDeclined} temporada(s)")
    return reasons


def should_offer_retirement(player: Player, snapshot: SeasonSnapshot) -> bool:
    """El motor solo sugiere: la decisión de colgar los botines es del jugador."""
    if player.retired or player.age < RETIREMENT_WATCH_AGE:
        return False
    if player.age >= RETIREMENT_CERTAIN_AGE:
        return True
    return snapshot.minutesPlayed < 900 or snapshot.averageRating < 6.3


def is_retirement_forced(player: Player) -> bool:
    """A los 40 no hay decisión que tomar: la carrera se terminó."""
    return not player.retired and player.age >= RETIREMENT_FORCED_AGE


def build_retirement_offer(
    player: Player,
    snapshot: SeasonSnapshot,
    seasons_played: int,
) -> RetirementOffer:
    forced = is_retirement_forced(player)
    if forced:
        message = "Hasta acá llegó. A esta edad ya no hay una temporada más que estirar."
    elif player.age >= RETIREMENT_CERTAIN_AGE:
        message = "Las piernas ya no responden igual. Nadie te va a discutir la decisión."
    else:
        message = "El cuerpo empieza a pasar factura y los minutos se achican."

    return RetirementOffer(
        title="Se terminó" if forced else "¿Colgás los botines?",
        message=message,
        forced=forced,
        reasons=_decline_reasons(player, snapshot),
        stayWarning=(
            "Si seguís, tus atributos van a caer más rápido, vas a jugar menos "
            "y las ofertas van a ser peores."
        ),
        seasonsPlayed=seasons_played,
        age=player.age,
    )
