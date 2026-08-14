import random
from uuid import uuid4

from app.modules.clubs.data import CLUBS, Club, get_club, get_league
from app.schemas import (
    ClubInfo,
    Player,
    SeasonSnapshot,
    TransferOffer,
    TransferWindow,
)


def _club_info(club: Club) -> ClubInfo:
    league = get_league(club.league_id)
    return ClubInfo(
        id=club.id,
        name=club.name,
        shortName=club.short_name,
        leagueId=club.league_id,
        leagueName=league.name if league else club.league_id,
        country=league.country if league else "",
        city=club.city,
        prestige=club.prestige,
        budget=club.budget,
        nickname=club.nickname,
    )


def _attractiveness_score(player: Player, snapshot: SeasonSnapshot) -> float:
    score = player.state.reputation
    score += (snapshot.averageRating - 6.5) * 18
    score += snapshot.goals * 2.2
    score += snapshot.assists * 1.4
    if snapshot.trophies:
        score += 12 * len(snapshot.trophies)
    if snapshot.individualAwards:
        score += 22 * len(snapshot.individualAwards)
    if player.age <= 23:
        score += 12
    elif player.age <= 27:
        score += 4
    elif player.age >= 32:
        score -= 18
    elif player.age >= 30:
        score -= 8
    if "european_transfer" in (player.tags or []):
        score += 8
    if "banned_doping" in (player.tags or []):
        score -= 25
    return max(0, score)


def _number_of_offers(score: float) -> int:
    if score >= 90:
        return 4
    if score >= 70:
        return 3
    if score >= 50:
        return 2
    if score >= 35:
        return 1
    return 0


def _release_clause_for(player: Player, current_club: Club) -> float:
    stored_clause = getattr(player.finance, "releaseClause", 0) or 0
    if stored_clause > 0:
        return float(stored_clause)
    return round(player.finance.weeklySalary * 52 * max(3.0, current_club.prestige / 10), 2)


def _window_reason(player: Player, score: float, snapshot: SeasonSnapshot) -> str | None:
    years = player.finance.contractYears
    tags = set(player.tags or [])
    if years <= 0:
        return "free_agent"
    if years <= 1:
        return "transfer_request" if "requested_transfer" in tags else "expiring_contract"
    if "requested_transfer" in tags and score >= 45:
        return "transfer_request"
    if score >= 180:
        return "release_clause"
    if snapshot.minutesPlayed < 700 and years > 1 and player.state.reputation >= 25:
        return "loan"
    return None


def _eligible_pool(current_club: Club, score: float) -> list[Club]:
    current = current_club.prestige
    pool: list[Club] = []
    if score >= 95:
        low, high = current - 5, min(99, current + 30)
    elif score >= 80:
        low, high = current - 5, min(99, current + 22)
    elif score >= 60:
        low, high = current - 8, min(99, current + 15)
    elif score >= 40:
        low, high = current - 10, min(99, current + 8)
    else:
        low, high = current - 12, current + 3
    for club in CLUBS.values():
        if club.id == current_club.id:
            continue
        if club.prestige < low:
            continue
        if club.prestige > high:
            continue
        pool.append(club)
    return pool


def _playing_chance(club: Club, player: Player) -> str:
    diff = club.prestige - player.state.reputation
    if diff > 28:
        return "backup"
    if diff > 12:
        return "rotation"
    return "starter"


def _generate_note(
    club: Club,
    player: Player,
    current_club: Club,
    chance: str,
    rng: random.Random,
) -> str:
    prestige_jump = club.prestige - current_club.prestige
    pieces: list[str] = []

    if prestige_jump >= 20:
        pieces.append(
            f"El {club.short_name} rompe el mercado por vos. Es un salto de calidad enorme."
        )
    elif prestige_jump >= 10:
        pieces.append(f"El {club.short_name} te mira como su próximo refuerzo top.")
    elif prestige_jump >= 0:
        pieces.append(f"{club.short_name} preparó una oferta seria.")
    else:
        pieces.append(f"En {club.short_name} te ofrecen ser referente del proyecto.")

    if chance == "starter":
        pieces.append("Te ven de titular indiscutido.")
    elif chance == "rotation":
        pieces.append("Serías parte del plantel principal con minutos regulares.")
    else:
        pieces.append("Arrancarías desde atrás pero con margen para ganarte el lugar.")

    if club.league_id != current_club.league_id:
        pieces.append(f"Sería el salto a {get_league(club.league_id).name}.")
    else:
        pieces.append("Te quedás en la misma liga pero cambiás de proyecto.")

    if rng.random() < 0.35:
        pieces.append("El técnico llamó personalmente para convencerte.")

    return " ".join(pieces)


def _highlight(club: Club, current_club: Club) -> str:
    diff = club.prestige - current_club.prestige
    if diff >= 25:
        return "🚀 Salto de era"
    if diff >= 15:
        return "🔥 Salto importante"
    if diff >= 5:
        return "📈 Mejora clara"
    if diff <= -10:
        return "🎩 Proyecto de referente"
    return ""


def compute_transfer_window(
    player: Player,
    snapshot: SeasonSnapshot,
    rng: random.Random | None = None,
) -> TransferWindow | None:
    if not player.clubId:
        return None
    current_club = get_club(player.clubId)
    if not current_club:
        return None
    r = rng or random.Random()

    score = _attractiveness_score(player, snapshot)
    reason = _window_reason(player, score, snapshot)
    if not reason:
        return None

    num = _number_of_offers(score)
    if reason == "free_agent":
        num = max(2, num)
    elif reason == "loan":
        num = 1
    if num == 0:
        return None

    pool = _eligible_pool(current_club, score)
    if reason == "loan":
        pool = [club for club in pool if club.prestige <= current_club.prestige + 8]
    if not pool:
        return None

    picks = r.sample(pool, min(num, len(pool)))
    picks.sort(key=lambda c: -c.prestige)

    release_clause = _release_clause_for(player, current_club)
    offers: list[TransferOffer] = []
    for club in picks:
        league = get_league(club.league_id)
        base_salary = (league.average_salary if league else 500) * (club.prestige / 100) * 0.95
        chance = _playing_chance(club, player)
        if chance == "starter":
            base_salary *= 1.25
        elif chance == "backup":
            base_salary *= 0.7
        sign_on_multiplier = 18 if reason == "free_agent" else (14 if club.prestige >= 85 else 9)
        sign_on = base_salary * sign_on_multiplier
        transfer_fee = 0.0
        pays_release_clause = False
        transfer_kind = "transfer"
        offer_clause = None

        if reason == "free_agent":
            transfer_kind = "free_agent"
        elif reason == "loan":
            transfer_kind = "loan"
            base_salary *= 0.85
            sign_on = base_salary * 3
        elif player.finance.contractYears > 1:
            pays_release_clause = True
            offer_clause = release_clause
            transfer_fee = round(release_clause * r.uniform(1.0, 1.18), 2)

        note = _generate_note(club, player, current_club, chance, r)
        if reason == "release_clause":
            note += " El club comprador está dispuesto a pagar la cláusula de rescisión."
        elif reason == "free_agent":
            note += " Llegás libre: no hay fee de transferencia y tu prima de firma sube."
        elif reason == "loan":
            note += " Es una cesión para recuperar minutos sin romper tu contrato actual."
        elif reason == "expiring_contract":
            note += " Tu contrato entra en su último año y el club escucha ofertas."
        elif reason == "transfer_request":
            note += " Tu pedido de salida obligó al club a sentarse a negociar."

        offers.append(
            TransferOffer(
                id=str(uuid4()),
                club=_club_info(club),
                weeklySalary=round(base_salary, 2),
                contractYears=1 if transfer_kind == "loan" else r.choice([2, 3, 3, 4, 4, 5]),
                signOnBonus=round(sign_on, 2),
                playingChance=chance,
                reputationRequired=max(0, club.prestige - 15),
                note=note,
                highlight=_highlight(club, current_club) or ("📝 Libre" if reason == "free_agent" else "🔐 Cláusula" if reason == "release_clause" else ""),
                transferKind=transfer_kind,
                transferFee=transfer_fee,
                releaseClause=offer_clause,
                paysReleaseClause=pays_release_clause,
            )
        )

    stay_note = _stay_note(player, current_club, offers)
    if reason == "free_agent":
        stay_note = "Terminó tu contrato. Si tu club quiere retenerte, tiene que competir como uno más."
    elif reason == "loan":
        stay_note = "Podés quedarte y pelearla, pero una cesión te daría minutos reales."
    elif reason == "release_clause":
        stay_note = f"Tenés contrato por {player.finance.contractYears} años más. Solo una cláusula pagada puede sacarte sin que el club bloquee la operación."

    return TransferWindow(
        id=str(uuid4()),
        label=f"Ventana de fichajes — verano {player.seasonYear}",
        currentClub=None if reason == "free_agent" else _club_info(current_club),
        stayNote=stay_note,
        offers=offers,
        reason=reason,
        contractYearsRemaining=max(0, player.finance.contractYears),
        renewalOfferYears=3 if player.finance.contractYears <= 1 and reason != "loan" else None,
    )


def _stay_note(player: Player, current_club: Club, offers: list[TransferOffer]) -> str:
    if not offers:
        return "Nadie serio golpeó la puerta. Toca seguir demostrando."
    top_offer = max(offers, key=lambda o: o.club.prestige)
    if top_offer.club.prestige > current_club.prestige + 15:
        return (
            f"El {current_club.short_name} quiere retenerte y ofrecerte un rol clave. "
            f"Pero {top_offer.club.shortName} está tirando la casa por la ventana. "
            "¿Priorizás plata y presión o construcción y estabilidad?"
        )
    return (
        f"El {current_club.short_name} te renueva y quiere que sigas siendo el eje "
        "del proyecto. La opción segura si querés seguir creciendo acá."
    )


def apply_transfer(player: Player, offer: TransferOffer) -> dict:
    from app.modules.clubs.data import get_club as _get_club

    new_club = _get_club(offer.club.id)
    if not new_club:
        return {"error": "unknown_club"}
    current_club = _get_club(player.clubId) if player.clubId else None

    player.clubId = new_club.id
    player.finance.weeklySalary = float(offer.weeklySalary)
    player.finance.signOnBonus = float(offer.signOnBonus)
    player.finance.balance += float(offer.signOnBonus)
    player.finance.contractYears = int(offer.contractYears)
    player.finance.releaseClause = round(
        player.finance.weeklySalary * 52 * max(3.0, new_club.prestige / 10),
        2,
    )

    player.relationships.coach = 55.0
    player.relationships.teammates = 45.0
    player.relationships.fans = 40.0
    player.relationships.press = 48.0

    prestige_diff = new_club.prestige - (current_club.prestige if current_club else new_club.prestige)
    reputation_shift = prestige_diff * 0.35
    player.state.reputation = max(0, min(100, player.state.reputation + reputation_shift))

    if prestige_diff >= 15:
        player.state.pressure = min(100, player.state.pressure + 18)
        player.state.morale = min(100, player.state.morale + 12)
    elif prestige_diff >= 5:
        player.state.pressure = min(100, player.state.pressure + 8)
        player.state.morale = min(100, player.state.morale + 6)
    elif prestige_diff <= -10:
        player.state.pressure = max(0, player.state.pressure - 12)
        player.state.happiness = min(100, player.state.happiness + 5)

    tags = set(player.tags or [])
    if offer.transferKind == "loan":
        tags.add("loan_move")
    if new_club.league_id != (current_club.league_id if current_club else ""):
        league = get_league(new_club.league_id)
        if league and league.country in {"ES", "EN", "IT", "DE", "FR", "PT", "NL"}:
            tags.add("european_transfer")
        elif league and league.country == "SA":
            tags.add("saudi_move")
    player.tags = sorted(tags)

    return {
        "moved_to": new_club.id,
        "from": current_club.id if current_club else None,
        "prestige_diff": prestige_diff,
        "reputation_shift": reputation_shift,
    }


def stay_at_club(player: Player) -> dict:
    renewal_years = 3 if player.finance.contractYears <= 1 else player.finance.contractYears
    player.finance.contractYears = min(5, renewal_years)
    current_club = get_club(player.clubId) if player.clubId else None
    if current_club:
        player.finance.releaseClause = _release_clause_for(player, current_club)
    tags = set(player.tags or [])
    tags.discard("requested_transfer")
    player.tags = sorted(tags)
    return {"renewed": True, "clubId": player.clubId}
