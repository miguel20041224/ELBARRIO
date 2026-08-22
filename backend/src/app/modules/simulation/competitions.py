"""Reglas de avance en competiciones de eliminatoria.

El calendario dibuja el cuadro completo hasta la final. Quién sigue en carrera
lo decide el resultado del partido, no un sorteo hecho al generar la temporada:
antes se tiraba un dado por ronda contra el prestigio del club, así que se
avanzaba habiendo perdido y se quedaba eliminado habiendo ganado.
"""

from __future__ import annotations

from app.schemas import MatchResult


# En orden de disputa. Un club que gana una ronda juega la siguiente.
KNOCKOUT_STAGES: tuple[str, ...] = ("round-16", "quarterfinal", "semifinal", "final")

# Fase previa de la competición continental: no elimina partido a partido, se
# clasifica por puntos al terminarla.
LEAGUE_PHASE_STAGE = "league-phase"

# Puntos necesarios en la fase de liga para entrar a octavos. Con la tasa de
# victoria medida (~40 % W, ~25 % D) la esperanza en 6 partidos ronda los 8,7
# puntos, así que este corte deja pasar algo más de la mitad de las campañas.
LEAGUE_PHASE_QUALIFYING_POINTS = 7


def is_knockout(stage_id: str | None) -> bool:
    return stage_id in KNOCKOUT_STAGES


def needs_shootout(stage_id: str | None, result: str) -> bool:
    """Una eliminatoria no puede quedar empatada: alguien tiene que pasar."""
    return is_knockout(stage_id) and result == "D"


def advanced(match: MatchResult) -> bool:
    """Si el club superó esta ronda eliminatoria.

    Ganar en los 90' alcanza. Un empate se define en la tanda de penales, que
    es la única lectura válida de un resultado 'D' en eliminatoria.
    """
    if not is_knockout(match.stageId):
        return False
    if match.result == "W":
        return True
    if match.result == "D" and match.penaltiesFor is not None and match.penaltiesAgainst is not None:
        return match.penaltiesFor > match.penaltiesAgainst
    return False


def league_phase_points(matches: list[MatchResult], competition_id: str) -> int:
    points = 0
    for match in matches:
        if match.competitionId != competition_id or match.stageId != LEAGUE_PHASE_STAGE:
            continue
        points += 3 if match.result == "W" else 1 if match.result == "D" else 0
    return points
