"""Runner de validación FASE 0 para el modo carrera de ELBARRIO.

Ejecuta N carreras completas contra la API real (TestClient sobre una base
SQLite dedicada) y vuelca un JSON por carrera en runs/. No analiza nada: solo
mide y registra. El análisis vive en analyze.py.

Uso:
    PYTHONPATH=backend/src python research/elbarrio-validation/runner.py \
        --careers 12 --seasons 12 --out research/elbarrio-validation/runs
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend" / "src"))


POSITIONS = ["ST", "CAM", "CM", "CB", "GK", "LW", "CDM", "RB"]

# Ligas y clubes de arranque variados para cubrir el plan de Colombia, el
# doble round-robin normal y ligas de distinto tier.
STARTS = [
    ("col-primera-a", None),
    ("arg-primera", None),
    ("bra-brasileirao", None),
    ("esp-laliga", None),
    ("eng-premier", None),
    ("col-primera-b", None),
]


def build_client(db_path: Path):
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    # config.settings se construye al importar; forzamos el import después de
    # fijar la env var para que tome la base de pruebas.
    from app.config import settings

    settings.database_url = f"sqlite:///{db_path}"

    import app.database as database

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    database.engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )
    database.SessionLocal = sessionmaker(
        bind=database.engine, autoflush=False, autocommit=False
    )

    from fastapi.testclient import TestClient
    from app.main import app

    database.init_db()
    return TestClient(app)


def make_draft(rng: random.Random, index: int) -> dict:
    position = POSITIONS[index % len(POSITIONS)]
    league_id, club_id = STARTS[index % len(STARTS)]
    return {
        "firstName": "Test",
        "lastName": f"Player{index:02d}",
        "nickname": f"T{index:02d}",
        "birthCountry": "CO",
        "startingLeague": league_id,
        "startingClub": club_id,
        "position": position,
        "secondaryPositions": [],
        "shirtNumber": (index % 99) + 1,
        "preferredFoot": rng.choice(["left", "right"]),
        "age": 17,
        "height": rng.randint(168, 192),
        "weight": rng.randint(62, 88),
    }


def post(client, path: str, body=None):
    response = client.post(path, json=body if body is not None else None)
    return response


def run_career(client, index: int, max_seasons: int, rng: random.Random) -> dict:
    draft = make_draft(rng, index)
    started = time.time()

    response = client.post("/api/careers", json={"mode": "player", "draft": draft})
    if response.status_code != 200:
        return {
            "index": index,
            "draft": draft,
            "fatal": f"create failed {response.status_code}: {response.text[:400]}",
        }
    session = response.json()
    career_id = session["id"]

    log: dict = {
        "index": index,
        "careerId": career_id,
        "draft": draft,
        "position": draft["position"],
        "startLeague": draft["startingLeague"],
        "initialPlayer": {
            "age": session["player"]["age"],
            "clubId": session["player"]["clubId"],
            "goals": session["player"]["goals"],
            "assists": session["player"]["assists"],
            "matchesPlayed": session["player"]["matchesPlayed"],
            "reputation": session["player"]["state"]["reputation"],
        },
        "initialClub": session.get("currentClub"),
        "matches": [],
        "seasons": [],
        "events": [],
        "roulettes": [],
        "transfers": [],
        "playerTimeline": [],
        "errors": [],
        "stalls": [],
    }

    steps = 0
    max_steps = max_seasons * 120
    seasons_done = 0
    last_signature = None
    stall_count = 0

    while seasons_done < max_seasons and steps < max_steps:
        steps += 1

        signature = (
            session["currentSeason"],
            session["seasonProgress"]["matchesPlayed"],
            bool(session.get("pendingRoulette")),
            bool(session.get("pendingTransferWindow")),
            session.get("pendingEventId"),
        )
        if signature == last_signature:
            stall_count += 1
            if stall_count > 3:
                log["stalls"].append({"step": steps, "signature": list(map(str, signature))})
                break
        else:
            stall_count = 0
        last_signature = signature

        if session.get("pendingRoulette"):
            roll = session["pendingRoulette"]
            choice = rng.choice(roll["options"])
            response = post(
                client,
                f"/api/careers/{career_id}/spin-roulette",
                {"outcomeId": choice["id"]},
            )
            if response.status_code != 200:
                log["errors"].append(
                    {"step": steps, "op": "spin", "status": response.status_code, "body": response.text[:300]}
                )
                break
            log["roulettes"].append(
                {"season": session["currentSeason"], "kind": roll["kind"], "outcome": choice["id"], "tone": choice["tone"]}
            )
            session = response.json()
            continue

        if session.get("pendingTransferWindow"):
            window = session["pendingTransferWindow"]
            offers = window.get("offers") or []
            # 60% acepta la primera oferta si existe, si no se queda.
            offer_id = offers[0]["id"] if offers and rng.random() < 0.6 else None
            before_club = session["player"].get("clubId")
            response = post(
                client,
                f"/api/careers/{career_id}/accept-transfer",
                {"offerId": offer_id},
            )
            if response.status_code != 200:
                log["errors"].append(
                    {"step": steps, "op": "transfer", "status": response.status_code, "body": response.text[:300]}
                )
                break
            session = response.json()
            log["transfers"].append(
                {
                    "season": session["currentSeason"],
                    "reason": window.get("reason"),
                    "offersCount": len(offers),
                    "accepted": offer_id is not None,
                    "fromClub": before_club,
                    "toClub": session["player"].get("clubId"),
                    "contractYearsAfter": session["player"]["finance"]["contractYears"],
                }
            )
            continue

        if session.get("pendingEventId"):
            event = session.get("pendingEvent")
            if not event:
                log["errors"].append(
                    {"step": steps, "op": "event", "detail": f"pendingEventId {session['pendingEventId']} sin definición"}
                )
                break
            choice = rng.choice(event["choices"])
            response = post(
                client,
                f"/api/careers/{career_id}/resolve-event",
                {"choiceId": choice["id"]},
            )
            if response.status_code != 200:
                log["errors"].append(
                    {"step": steps, "op": "resolve-event", "status": response.status_code, "body": response.text[:300]}
                )
                break
            log["events"].append(
                {"season": session["currentSeason"], "eventId": event["id"], "choiceId": choice["id"]}
            )
            session = response.json()
            continue

        progress = session["seasonProgress"]
        if progress["matchesPlayed"] < progress["matchesTotal"]:
            before = {
                "goals": session["player"]["goals"],
                "assists": session["player"]["assists"],
                "matchesPlayed": session["player"]["matchesPlayed"],
                "progressGoals": progress["goals"],
                "progressMatches": progress["matchesPlayed"],
                "progressAppearances": progress["appearances"],
                "progressMinutes": progress["minutesPlayed"],
            }
            selection = session.get("nextMatchSelection")
            fixture = (
                progress["fixtures"][progress["matchesPlayed"]]
                if progress["fixtures"] and progress["matchesPlayed"] < len(progress["fixtures"])
                else None
            )
            response = post(client, f"/api/careers/{career_id}/play-match")
            if response.status_code != 200:
                log["errors"].append(
                    {"step": steps, "op": "play-match", "status": response.status_code, "body": response.text[:300]}
                )
                break
            session = response.json()
            new_progress = session["seasonProgress"]
            recent = new_progress["recentMatches"]
            match = recent[-1] if recent else None
            log["matches"].append(
                {
                    "season": session["currentSeason"],
                    "index": before["progressMatches"],
                    "fixtureCompetition": fixture["competitionId"] if fixture else None,
                    "fixtureStage": fixture["stageDisplay"] if fixture else None,
                    "fixtureOpponent": fixture["opponentId"] if fixture else None,
                    "fixtureHomeAway": fixture["homeAway"] if fixture else None,
                    "selectionRole": selection["role"] if selection else None,
                    "selectionStarterPct": selection["starterChance"] if selection else None,
                    "selectionMinMin": selection["expectedMinutesMin"] if selection else None,
                    "selectionMinMax": selection["expectedMinutesMax"] if selection else None,
                    "match": match,
                    "deltaPlayerGoals": session["player"]["goals"] - before["goals"],
                    "deltaPlayerAssists": session["player"]["assists"] - before["assists"],
                    "deltaPlayerMatches": session["player"]["matchesPlayed"] - before["matchesPlayed"],
                    "deltaProgressGoals": new_progress["goals"] - before["progressGoals"],
                    "deltaProgressMatches": new_progress["matchesPlayed"] - before["progressMatches"],
                    "deltaProgressAppearances": new_progress["appearances"] - before["progressAppearances"],
                    "deltaProgressMinutes": new_progress["minutesPlayed"] - before["progressMinutes"],
                    "leaguePosition": new_progress.get("leaguePosition"),
                    "clubId": session["player"].get("clubId"),
                }
            )
            continue

        # temporada completa -> cerrar
        before_age = session["player"]["age"]
        before_history = len(session["history"])
        before_trophies = len(session["player"]["trophies"])
        final_progress = dict(session["seasonProgress"])
        response = post(client, f"/api/careers/{career_id}/advance-season")
        if response.status_code != 200:
            log["errors"].append(
                {"step": steps, "op": "advance-season", "status": response.status_code, "body": response.text[:300]}
            )
            break
        session = response.json()
        seasons_done += 1
        snapshot = session["history"][-1] if session["history"] else None
        log["seasons"].append(
            {
                "season": snapshot["season"] if snapshot else None,
                "snapshot": snapshot,
                "closingProgress": {
                    "matchesPlayed": final_progress["matchesPlayed"],
                    "matchesTotal": final_progress["matchesTotal"],
                    "appearances": final_progress["appearances"],
                    "goals": final_progress["goals"],
                    "assists": final_progress["assists"],
                    "minutesPlayed": final_progress["minutesPlayed"],
                    "wins": final_progress["wins"],
                    "draws": final_progress["draws"],
                    "losses": final_progress["losses"],
                    "leagueWins": final_progress["leagueWins"],
                    "leagueDraws": final_progress["leagueDraws"],
                    "leagueLosses": final_progress["leagueLosses"],
                    "leaguePosition": final_progress.get("leaguePosition"),
                    "eventsUsed": final_progress["eventsUsed"],
                    "competitionProgress": final_progress.get("competitionProgress"),
                },
                "ageBefore": before_age,
                "ageAfter": session["player"]["age"],
                "historyGrew": len(session["history"]) - before_history,
                "trophiesGained": len(session["player"]["trophies"]) - before_trophies,
                "playerGoalsAfter": session["player"]["goals"],
                "playerAssistsAfter": session["player"]["assists"],
                "playerMatchesAfter": session["player"]["matchesPlayed"],
                "reputationAfter": session["player"]["state"]["reputation"],
                "clubAfter": session["player"].get("clubId"),
                "contractYearsAfter": session["player"]["finance"]["contractYears"],
            }
        )
        log["playerTimeline"].append(
            {
                "season": snapshot["season"] if snapshot else None,
                "age": session["player"]["age"],
                "club": session["player"].get("clubId"),
                "goals": session["player"]["goals"],
                "assists": session["player"]["assists"],
                "matchesPlayed": session["player"]["matchesPlayed"],
                "reputation": session["player"]["state"]["reputation"],
                "form": session["player"]["state"]["form"],
                "fitness": session["player"]["state"]["fitness"],
                "fatigue": session["player"]["state"]["fatigue"],
                "technicalShooting": session["player"]["technical"]["shooting"],
                "physicalStamina": session["player"]["physical"]["stamina"],
                "mentalVision": session["player"]["mental"]["vision"],
                "balance": session["player"]["finance"]["balance"],
                "trophies": len(session["player"]["trophies"]),
            }
        )

    log["steps"] = steps
    log["seasonsCompleted"] = seasons_done
    log["elapsedSeconds"] = round(time.time() - started, 2)
    log["finalPlayer"] = {
        "age": session["player"]["age"],
        "clubId": session["player"].get("clubId"),
        "goals": session["player"]["goals"],
        "assists": session["player"]["assists"],
        "matchesPlayed": session["player"]["matchesPlayed"],
        "caps": session["player"]["caps"],
        "reputation": session["player"]["state"]["reputation"],
        "trophies": session["player"]["trophies"],
        "sanctions": session["player"]["sanctions"],
        "tags": session["player"]["tags"],
        "contractYears": session["player"]["finance"]["contractYears"],
        "balance": session["player"]["finance"]["balance"],
    }
    log["finalClub"] = session.get("currentClub")
    log["historyLength"] = len(session["history"])
    log["finalSession"] = {
        "currentSeason": session["currentSeason"],
        "seasonComplete": session["seasonComplete"],
        "pendingEventId": session.get("pendingEventId"),
    }
    return log


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--careers", type=int, default=12)
    parser.add_argument("--seasons", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--out", default=str(Path(__file__).parent / "runs"))
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "validation.db"
    if db_path.exists():
        db_path.unlink()

    client = build_client(db_path)
    rng = random.Random(args.seed)

    for index in range(args.careers):
        log = run_career(client, index, args.seasons, random.Random(args.seed + index))
        target = out_dir / f"career_{index:02d}.json"
        target.write_text(json.dumps(log, ensure_ascii=False, indent=1))
        print(
            f"[{index:02d}] pos={log.get('position')} liga={log.get('startLeague')} "
            f"temporadas={log.get('seasonsCompleted')} partidos={len(log.get('matches', []))} "
            f"errores={len(log.get('errors', []))} stalls={len(log.get('stalls', []))} "
            f"{log.get('elapsedSeconds')}s",
            flush=True,
        )
    print(f"\nRuns escritos en {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
