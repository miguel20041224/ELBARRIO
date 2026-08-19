from app.schemas import Player, SeasonSnapshot, TrophyRecord
from app.modules.clubs.data import get_club, get_league


# Calibrados contra la distribución real del motor: sobre 360 temporadas de un
# delantero de élite la mediana es 6,95, el p90 7,21, el p99 7,44 y el techo
# medido 7,61. Los umbrales anteriores (7,8 / 8,0 / 8,4) eran inalcanzables.
PLAYER_OF_MATCH_THRESHOLD = 6.9
GOLDEN_BOOT_MIN_GOALS = 18
XI_IDEAL_MIN_RATING = 7.15
PLAYER_OF_SEASON_MIN_RATING = 7.25
BALLON_DOR_MIN_RATING = 7.45
BALLON_DOR_MIN_GOALS = 25


def compute_season_awards(
    player: Player,
    snapshot: SeasonSnapshot,
) -> list[TrophyRecord]:
    awards: list[TrophyRecord] = []
    club = get_club(player.clubId) if player.clubId else None
    league = get_league(club.league_id) if club else None
    league_name = league.name if league else "Liga"

    if snapshot.matchesPlayed > 5:
        pom_count = int(snapshot.matchesPlayed * max(0, snapshot.averageRating - PLAYER_OF_MATCH_THRESHOLD) / 3)
        if pom_count > 0:
            awards.append(
                TrophyRecord(
                    kind="individual",
                    name=f"{pom_count}x Jugador del Partido",
                    season=snapshot.season,
                    clubId=player.clubId,
                )
            )

    if snapshot.goals >= GOLDEN_BOOT_MIN_GOALS and snapshot.averageRating >= 7.0:
        awards.append(
            TrophyRecord(
                kind="individual",
                name=f"Bota de Oro — {league_name}",
                season=snapshot.season,
                clubId=player.clubId,
            )
        )

    if snapshot.averageRating >= PLAYER_OF_SEASON_MIN_RATING and snapshot.matchesPlayed >= 20:
        awards.append(
            TrophyRecord(
                kind="individual",
                name=f"Jugador de la Temporada — {league_name}",
                season=snapshot.season,
                clubId=player.clubId,
            )
        )

    if (
        snapshot.averageRating >= BALLON_DOR_MIN_RATING
        and (snapshot.goals + snapshot.assists) >= BALLON_DOR_MIN_GOALS
        and len(snapshot.trophies) >= 1
    ):
        awards.append(
            TrophyRecord(
                kind="individual",
                name="Balón de Oro",
                season=snapshot.season,
                clubId=player.clubId,
            )
        )

    if snapshot.averageRating >= XI_IDEAL_MIN_RATING and snapshot.matchesPlayed >= 25:
        awards.append(
            TrophyRecord(
                kind="individual",
                name=f"XI Ideal — {league_name}",
                season=snapshot.season,
                clubId=player.clubId,
            )
        )

    return awards


def snapshot_award_names(awards: list[TrophyRecord]) -> list[str]:
    return [a.name for a in awards]
