from app.schemas import Player, SeasonSnapshot, TrophyRecord
from app.modules.clubs.data import get_club, get_league


# Un delantero, un central y un arquero no viven en la misma escala de rating.
# Medidos sobre ~430 temporadas de carreras completas en un club grande:
#
#   escala      mediana   p85    p95    techo
#   ataque       6,71     6,93   7,05   7,16
#   defensa      6,25     6,37   6,45   6,63
#   arquero      6,11     6,23   6,31   6,39
#
# Medir a los tres con la misma vara es lo que hacía que un defensor no pudiera
# ganar absolutamente nada en quince temporadas.
DEFENSIVE_POSITIONS = frozenset({"CB", "LB", "RB", "CDM"})

# Cada umbral se sitúa en el mismo percentil de su escala, para que un premio
# cueste lo mismo en cualquier puesto.
PLAYER_OF_MATCH_THRESHOLD = {"attacking": 6.85, "defensive": 6.36, "goalkeeper": 6.22}
XI_IDEAL_MIN_RATING = {"attacking": 6.90, "defensive": 6.42, "goalkeeper": 6.28}
PLAYER_OF_SEASON_MIN_RATING = {"attacking": 7.02, "defensive": 6.50, "goalkeeper": 6.35}

# El Balón de Oro pide menos rating que el Jugador de la Temporada porque exige
# además un título y una aportación sostenida: sus filtros son otros, no más
# blandos. Medido, sale mucho más raro que aquél.
BALLON_DOR_MIN_RATING = {"attacking": 7.02, "defensive": 6.44, "goalkeeper": 6.31}

GOLDEN_BOOT_MIN_GOALS = 18

# Lo que hay que aportar, además del rating, para el Balón de Oro. Un '9' se
# mide por lo que produce; un central y un arquero, por las vallas que sostienen.
BALLON_DOR_MIN_CONTRIBUTION = {"attacking": 26, "defensive": 11, "goalkeeper": 11}

BEST_DEFENDER_MIN_CLEAN_SHEETS = 9
GOLDEN_GLOVE_MIN_CLEAN_SHEETS = 11


def _scale_for(position: str) -> str:
    if position == "GK":
        return "goalkeeper"
    return "defensive" if position in DEFENSIVE_POSITIONS else "attacking"


def _award(name: str, snapshot: SeasonSnapshot, player: Player) -> TrophyRecord:
    return TrophyRecord(
        kind="individual",
        name=name,
        season=snapshot.season,
        clubId=player.clubId,
    )


def _deserves_ballon_dor(snapshot: SeasonSnapshot, scale: str) -> bool:
    """El Balón de Oro exige ser decisivo Y levantar algo esa temporada.

    El título no es un adorno: es lo que separa una gran temporada individual de
    una temporada que marcó el año, y es el camino por el que un central llega
    al premio sin marcar goles.
    """
    if not snapshot.trophies:
        return False
    if snapshot.averageRating < BALLON_DOR_MIN_RATING[scale]:
        return False
    contribution = (
        snapshot.cleanSheets
        if scale in ("defensive", "goalkeeper")
        else snapshot.goals + snapshot.assists
    )
    return contribution >= BALLON_DOR_MIN_CONTRIBUTION[scale]


def compute_season_awards(
    player: Player,
    snapshot: SeasonSnapshot,
) -> list[TrophyRecord]:
    awards: list[TrophyRecord] = []
    club = get_club(player.clubId) if player.clubId else None
    league = get_league(club.league_id) if club else None
    league_name = league.name if league else "Liga"
    scale = _scale_for(player.position)

    if snapshot.matchesPlayed > 5:
        margin = max(0.0, snapshot.averageRating - PLAYER_OF_MATCH_THRESHOLD[scale])
        pom_count = int(snapshot.matchesPlayed * margin / 3)
        if pom_count > 0:
            awards.append(_award(f"{pom_count}x Jugador del Partido", snapshot, player))

    if snapshot.goals >= GOLDEN_BOOT_MIN_GOALS and snapshot.averageRating >= 7.0:
        awards.append(_award(f"Bota de Oro — {league_name}", snapshot, player))

    if (
        scale == "goalkeeper"
        and snapshot.cleanSheets >= GOLDEN_GLOVE_MIN_CLEAN_SHEETS
        and snapshot.matchesPlayed >= 20
    ):
        awards.append(_award(f"Guante de Oro — {league_name}", snapshot, player))

    if (
        scale == "defensive"
        and snapshot.cleanSheets >= BEST_DEFENDER_MIN_CLEAN_SHEETS
        and snapshot.averageRating >= XI_IDEAL_MIN_RATING["defensive"]
        and snapshot.matchesPlayed >= 25
    ):
        awards.append(_award(f"Mejor Defensor — {league_name}", snapshot, player))

    if (
        snapshot.averageRating >= PLAYER_OF_SEASON_MIN_RATING[scale]
        and snapshot.matchesPlayed >= 20
    ):
        awards.append(_award(f"Jugador de la Temporada — {league_name}", snapshot, player))

    if _deserves_ballon_dor(snapshot, scale):
        awards.append(_award("Balón de Oro", snapshot, player))

    if (
        snapshot.averageRating >= XI_IDEAL_MIN_RATING[scale]
        and snapshot.matchesPlayed >= 25
    ):
        awards.append(_award(f"XI Ideal — {league_name}", snapshot, player))

    return awards


def snapshot_award_names(awards: list[TrophyRecord]) -> list[str]:
    return [a.name for a in awards]
