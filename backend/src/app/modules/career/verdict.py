"""Veredicto de fin de carrera.

Cierra la carrera con una lectura: no alcanza con listar totales, hay que decir
qué fue esa carrera. Es una regla de juego —qué cuenta como leyenda— así que
vive en el backend y se testea, en vez de decidirse en la pantalla.
"""

from __future__ import annotations

from app.schemas import CareerVerdict


# Puntos necesarios para cada escalón, de mayor a menor.
TIER_THRESHOLDS: tuple[tuple[int, int, str, str], ...] = (
    (5, 78, "Leyenda", "Tu nombre ya no se discute: se cuenta."),
    (4, 55, "Ídolo", "Dejaste huella donde jugaste y una vitrina que lo prueba."),
    (3, 34, "Referente", "Una carrera sólida, de las que sostienen un equipo."),
    (2, 14, "Profesional", "Viviste del fútbol y te ganaste cada minuto."),
    # Quince temporadas en primera son una carrera profesional aunque no haya
    # vitrina: el escalón más bajo es para las que no llegaron a sostenerse.
    (1, 0, "De barrio", "No llegaste arriba, pero la jugaste hasta el final."),
)


def _score(peak_overall: int, seasons: int, team_titles: int, individual_awards: int) -> int:
    """Puntaje de carrera. El nivel alcanzado pesa, pero lo ganado pesa más.

    Un jugador de OVR 90 sin títulos no es una leyenda; uno de 80 con una vitrina
    llena, sí. Por eso los títulos valen más por unidad que los puntos de OVR.
    """
    level = max(0, peak_overall - 60) // 2
    longevity = min(10, seasons // 2)
    return level + longevity + team_titles * 3 + individual_awards * 2


def build_career_verdict(
    *,
    peak_overall: int,
    seasons: int,
    team_titles: int,
    individual_awards: int,
    clubs: int,
) -> CareerVerdict:
    score = _score(peak_overall, seasons, team_titles, individual_awards)
    tier, _, title, summary = next(
        entry for entry in TIER_THRESHOLDS if score >= entry[1]
    )
    return CareerVerdict(
        tier=tier,
        title=title,
        summary=summary,
        peakOverall=peak_overall,
        seasons=seasons,
        teamTitles=team_titles,
        individualAwards=individual_awards,
        clubs=clubs,
    )
