import math
import random
from app.modules.clubs.data import Club, get_club, get_clubs_for_league
from app.schemas import Fixture, MatchResult, MatchSelection, Player


GOAL_RATE_BY_POSITION: dict[str, float] = {
    "GK": 0.001,
    "CB": 0.03,
    "LB": 0.04,
    "RB": 0.04,
    "CDM": 0.06,
    "CM": 0.10,
    "CAM": 0.22,
    "LW": 0.28,
    "RW": 0.28,
    "ST": 0.42,
}

ASSIST_RATE_BY_POSITION: dict[str, float] = {
    "GK": 0.005,
    "CB": 0.03,
    "LB": 0.10,
    "RB": 0.10,
    "CDM": 0.12,
    "CM": 0.20,
    "CAM": 0.30,
    "LW": 0.25,
    "RW": 0.25,
    "ST": 0.18,
}


# Goles por equipo y partido en una liga real rondan 1,35.
BASE_TEAM_GOALS = 1.35

# Atributos que definen el rendimiento de cada puesto, para ponderar el rating.
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


def _rookie_factor(player: Player) -> float:
    if player.state.reputation < 30:
        return player.state.reputation / 60
    return min(1.0, (player.state.reputation - 30) / 70 + 0.5)


def _player_quality(player: Player) -> float:
    """Calidad global del jugador, 0..1, pesando lo que define su posición."""
    key = KEY_ATTRIBUTES_BY_POSITION.get(player.position, ())
    groups = (player.technical, player.mental, player.physical)
    values = [
        value
        for group in groups
        for attribute, value in vars(group).items()
    ]
    overall = sum(values) / len(values)
    key_values = [
        getattr(group, attribute)
        for group in groups
        for attribute in key
        if hasattr(group, attribute)
    ]
    specialised = sum(key_values) / len(key_values) if key_values else overall
    return max(0.0, min(1.0, (overall * 0.45 + specialised * 0.55) / 100))


def _pick_opponent(player_club: Club, rng: random.Random) -> Club:
    league_clubs = [c for c in get_clubs_for_league(player_club.league_id) if c.id != player_club.id]
    if not league_clubs:
        return player_club
    return rng.choice(league_clubs)


def _selection_chances(player: Player) -> tuple[float, float]:
    rookie = _rookie_factor(player)
    coach_relation = player.relationships.coach / 100
    fitness = player.state.fitness / 100
    starter_chance = 0.15 + rookie * 0.55 + (coach_relation - 0.5) * 0.4 + (fitness - 0.6) * 0.3
    starter_chance = max(0.05, min(0.95, starter_chance))
    sub_chance = 0.35 + rookie * 0.4 + (coach_relation - 0.5) * 0.3
    sub_chance = max(0.1, min(0.9, sub_chance))
    return starter_chance, sub_chance


def build_match_selection(player: Player, fixture: Fixture | None = None) -> MatchSelection:
    starter_chance, sub_chance = _selection_chances(player)
    starter_pct = round(starter_chance * 100)
    substitute_pct = round((1 - starter_chance) * sub_chance * 100)
    role = "bench"
    minutes_min = 0
    minutes_max = 15
    if starter_pct >= 58:
        role = "starter"
        minutes_min = 60
        minutes_max = 90
    elif starter_pct + substitute_pct >= 48:
        role = "substitute"
        minutes_min = 15
        minutes_max = 45

    factors: list[str] = []
    if player.relationships.coach >= 70:
        factors.append("El DT confía en vos")
    elif player.relationships.coach <= 40:
        factors.append("Relación tensa con el DT")
    if player.state.fitness >= 75:
        factors.append("Buen estado físico")
    elif player.state.fitness <= 45:
        factors.append("Físico comprometido")
    if player.state.form >= 75:
        factors.append("Venís en buena forma")
    elif player.state.form <= 45:
        factors.append("Necesitás levantar la forma")
    if player.state.reputation >= 70:
        factors.append("Tu reputación pesa en la convocatoria")
    elif player.state.reputation <= 30:
        factors.append("Todavía estás ganando lugar")
    if fixture and fixture.isClasico:
        factors.append("Clásico: el margen de error baja")

    if role == "starter":
        coach_message = "El DT te perfila como titular para este partido."
    elif role == "substitute":
        coach_message = "El DT te ve como cambio probable; entrá y ganate más minutos."
    else:
        coach_message = "Hoy arrancás peleando desde el banco; necesitás señales fuertes para entrar."

    return MatchSelection(
        role=role,
        starterChance=starter_pct,
        substituteChance=substitute_pct,
        expectedMinutesMin=minutes_min,
        expectedMinutesMax=minutes_max,
        coachMessage=coach_message,
        factors=factors[:4],
    )


def _minutes(player: Player, rng: random.Random) -> tuple[int, bool]:
    starter_chance, sub_chance = _selection_chances(player)
    form = player.state.form / 100

    if rng.random() < starter_chance:
        base = 82 + (form - 0.6) * 10
        minutes = max(55, min(90, int(rng.gauss(base, 6))))
        return minutes, True

    if rng.random() < sub_chance:
        minutes = max(5, min(45, int(rng.gauss(22, 12))))
        return minutes, False
    return 0, False


MAX_GOALS_PER_SIDE = 7


def _poisson(expected: float, rng: random.Random) -> int:
    """Muestreo de Poisson por el método de Knuth.

    Los goles son sucesos raros e independientes dentro del partido, que es
    justo lo que modela una Poisson. El bucle anterior recorría `ceil(expected)`
    iteraciones y, como `expected` nunca llegaba a 1, jamás podía devolver 2.
    """
    if expected <= 0:
        return 0
    limit = math.exp(-expected)
    product = 1.0
    count = 0
    while count < MAX_GOALS_PER_SIDE:
        product *= rng.random()
        if product <= limit:
            break
        count += 1
    return count


def _compute_score(
    player_club: Club,
    opponent: Club,
    player_rating: float,
    home_away: str,
    rng: random.Random,
) -> tuple[int, int, str]:
    # Cada equipo marca según su propia Poisson: así los empates aparecen solos,
    # en vez de depender de que dos randint independientes coincidan.
    strength = (player_club.prestige - opponent.prestige) / 100
    home_boost = 0.20 if home_away == "home" else (-0.12 if home_away == "away" else 0.0)

    expected_for = BASE_TEAM_GOALS + strength * 0.85 + (player_rating - 6.5) * 0.08 + home_boost
    expected_against = BASE_TEAM_GOALS - strength * 0.85 - home_boost * 0.6

    gf = _poisson(max(0.15, expected_for), rng)
    ga = _poisson(max(0.15, expected_against), rng)

    if gf > ga:
        result = "W"
    elif gf == ga:
        result = "D"
    else:
        result = "L"
    return gf, ga, result


def _generate_narrative(
    player: Player,
    result: str,
    gf: int,
    ga: int,
    opponent: Club,
    home_away: str,
    minutes: int,
    goals: int,
    assists: int,
    starter: bool,
) -> str:
    if home_away == "home":
        where = "de local"
    elif home_away == "neutral":
        where = "en cancha neutral"
    else:
        where = f"de visitante en {opponent.city}"
    outcome = {"W": f"Ganaron {gf}-{ga}", "D": f"Empataron {gf}-{ga}", "L": f"Perdieron {gf}-{ga}"}[result]

    if minutes == 0:
        return f"{outcome} contra {opponent.short_name} {where}. Vos te quedaste en el banco."

    role = "de titular" if starter else "entrando desde el banco"
    parts = [f"{outcome} contra {opponent.short_name} {where}. Jugaste {minutes}' {role}"]
    if goals > 0 and assists > 0:
        parts.append(f", metiste {goals} y diste {assists} asistencia{'s' if assists > 1 else ''}")
    elif goals > 0:
        parts.append(f", clavaste {goals} gol{'es' if goals > 1 else ''}")
    elif assists > 0:
        parts.append(f", diste {assists} asistencia{'s' if assists > 1 else ''}")
    parts.append(".")
    return "".join(parts)


def simulate_match(
    player: Player,
    match_number: int,
    fixture: Fixture | None = None,
    rng: random.Random | None = None,
) -> MatchResult:
    r = rng or random.Random()
    club = get_club(player.clubId) if player.clubId else None
    if not club:
        return MatchResult(
            matchNumber=match_number,
            opponentId="unknown",
            opponentName="Sin oponente",
            opponentShortName="—",
            homeAway="home",
            goalsFor=0,
            goalsAgainst=0,
            result="D",
            minutesPlayed=0,
            goals=0,
            assists=0,
            rating=6.0,
            starter=False,
            narrative="Sin club asignado. Sin partido.",
        )

    opponent = get_club(fixture.opponentId) if fixture else None
    if not opponent:
        opponent = _pick_opponent(club, r)
    fixture_home_away = fixture.homeAway if fixture else None
    minutes, starter = _minutes(player, r)

    if minutes == 0:
        home = fixture_home_away or ("home" if r.random() < 0.5 else "away")
        gf, ga, result = _compute_score(club, opponent, 6.5, home, r)
        return MatchResult(
            matchNumber=match_number,
            week=fixture.week if fixture else 0,
            competitionId=fixture.competitionId if fixture else "friendly",
            competitionName=fixture.competitionName if fixture else "Amistoso",
            stageId=fixture.stageId if fixture else "",
            stageDisplay=fixture.stageDisplay if fixture else "",
            opponentId=opponent.id,
            opponentName=opponent.name,
            opponentShortName=opponent.short_name,
            homeAway=home,
            goalsFor=gf,
            goalsAgainst=ga,
            result=result,
            minutesPlayed=0,
            goals=0,
            assists=0,
            rating=6.0,
            starter=False,
            narrative=_generate_narrative(player, result, gf, ga, opponent, home, 0, 0, 0, False),
            isClasico=fixture.isClasico if fixture else False,
        )

    home_away = fixture_home_away or ("home" if r.random() < 0.5 else "away")

    form = player.state.form / 100
    fitness = player.state.fitness / 100
    minute_factor = minutes / 90
    goal_rate = GOAL_RATE_BY_POSITION.get(player.position, 0.1)
    assist_rate = ASSIST_RATE_BY_POSITION.get(player.position, 0.1)

    # Forma y estado físico modulan alrededor de 1, no multiplican hacia abajo:
    # encadenar tres factores menores que 1 aplastaba la tasa a un tercio.
    sharpness = (0.75 + 0.5 * form) * (0.8 + 0.4 * fitness)
    shot_quality = 0.55 + (player.technical.shooting / 100) * 0.9
    vision_quality = 0.55 + (player.technical.passing / 100) * 0.5 + (player.mental.vision / 100) * 0.4

    expected_goals = goal_rate * minute_factor * shot_quality * sharpness
    expected_assists = assist_rate * minute_factor * vision_quality * sharpness

    goals = _poisson(expected_goals, r)
    assists = _poisson(expected_assists, r)

    # La calidad del jugador entra en el rating: sin este término un crack y un
    # juvenil puntuaban igual, y toda la escala vivía en una banda de 0,3.
    quality = _player_quality(player)
    base_rating = 5.35 + quality * 1.45
    base_rating += (form - 0.5) * 0.8 + (fitness - 0.6) * 0.5
    base_rating += goals * 0.85 + assists * 0.5
    base_rating += r.gauss(0, 0.35)
    if not starter and minutes < 30 and goals + assists == 0:
        base_rating -= 0.2
    rating = round(max(3.5, min(9.8, base_rating)), 2)

    gf, ga, result = _compute_score(club, opponent, rating, home_away, r)
    if goals > gf:
        gf = goals
        result = "W" if gf > ga else "D" if gf == ga else "L"

    fatigue_added = int(minutes * 0.35)
    player.state.fatigue = min(100, player.state.fatigue + fatigue_added)
    player.state.fitness = max(15, player.state.fitness - int(minutes * 0.08))
    if goals + assists > 0:
        player.state.form = min(100, player.state.form + goals * 3 + assists * 2)
    if rating < 5.5:
        player.state.form = max(20, player.state.form - 3)
    if rating >= 8.0:
        player.state.morale = min(100, player.state.morale + 2)
    match_pay = player.finance.weeklySalary * (minutes / 90)
    player.finance.balance += match_pay

    player.matchesPlayed += 1
    player.goals += goals
    player.assists += assists

    mom = rating >= 8.5 and (goals + assists) >= 1

    narrative = _generate_narrative(
        player, result, gf, ga, opponent, home_away, minutes, goals, assists, starter
    )

    return MatchResult(
        matchNumber=match_number,
        week=fixture.week if fixture else 0,
        competitionId=fixture.competitionId if fixture else "friendly",
        competitionName=fixture.competitionName if fixture else "Amistoso",
        stageId=fixture.stageId if fixture else "",
        stageDisplay=fixture.stageDisplay if fixture else "",
        opponentId=opponent.id,
        opponentName=opponent.name,
        opponentShortName=opponent.short_name,
        homeAway=home_away,
        goalsFor=gf,
        goalsAgainst=ga,
        result=result,
        minutesPlayed=minutes,
        goals=goals,
        assists=assists,
        rating=rating,
        starter=starter,
        narrative=narrative,
        momPlayer=mom,
        isClasico=fixture.isClasico if fixture else False,
    )
