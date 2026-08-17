"""Pruebas de robustez FASE 0: idempotencia, concurrencia y persistencia.

No modifica el código de la app. Solo ejerce la API real sobre una base SQLite
dedicada y reporta si los invariantes se rompen.

Uso:
    PYTHONPATH=backend/src python research/elbarrio-validation/robustness.py
"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend" / "src"))

OUT = Path(__file__).parent / "reports"
DB = Path(__file__).parent / "runs" / "robustness.db"

RESULTS: list[dict] = []


def record(test: str, status: str, detail: str, **extra) -> None:
    RESULTS.append({"test": test, "status": status, "detail": detail, **extra})
    mark = {"PASS": "ok  ", "FAIL": "FALLA", "INFO": "info"}[status]
    print(f"[{mark}] {test}: {detail}")
    for key, value in extra.items():
        print(f"          {key}: {value}")


def build_client(db_path: Path, fresh: bool):
    """Construye un TestClient nuevo. fresh=True borra la base antes."""
    if fresh and db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

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
    return TestClient(app), database


DRAFT = {
    "firstName": "Robust",
    "lastName": "Tester",
    "nickname": "RT",
    "birthCountry": "CO",
    "startingLeague": "esp-laliga",
    "startingClub": None,
    "position": "ST",
    "secondaryPositions": [],
    "shirtNumber": 9,
    "preferredFoot": "right",
    "age": 17,
    "height": 182,
    "weight": 78,
}


def create_career(client) -> dict:
    response = client.post("/api/careers", json={"mode": "player", "draft": DRAFT})
    response.raise_for_status()
    return response.json()


def clear_pending(client, session: dict) -> dict:
    """Resuelve ruleta / ventana / evento hasta poder jugar."""
    cid = session["id"]
    for _ in range(20):
        if session.get("pendingRoulette"):
            option = session["pendingRoulette"]["options"][0]["id"]
            session = client.post(
                f"/api/careers/{cid}/spin-roulette", json={"outcomeId": option}
            ).json()
            continue
        if session.get("pendingTransferWindow"):
            session = client.post(
                f"/api/careers/{cid}/accept-transfer", json={"offerId": None}
            ).json()
            continue
        if session.get("pendingEventId"):
            event = session["pendingEvent"]
            session = client.post(
                f"/api/careers/{cid}/resolve-event",
                json={"choiceId": event["choices"][0]["id"]},
            ).json()
            continue
        return session
    raise RuntimeError("no se pudo limpiar el estado pendiente")


def play_until_season_end(client, session: dict) -> dict:
    cid = session["id"]
    for _ in range(400):
        session = clear_pending(client, session)
        progress = session["seasonProgress"]
        if progress["matchesPlayed"] >= progress["matchesTotal"]:
            return session
        session = client.post(f"/api/careers/{cid}/play-match").json()
    raise RuntimeError("la temporada no terminó")


# ---------------------------------------------------------------- pruebas


def test_get_is_pure(client) -> None:
    """T1: un GET repetido (recarga del navegador) no debe alterar nada."""
    session = clear_pending(client, create_career(client))
    cid = session["id"]
    for _ in range(6):
        session = client.post(f"/api/careers/{cid}/play-match").json()

    baseline = client.get(f"/api/careers/{cid}").json()
    snapshots = [client.get(f"/api/careers/{cid}").json() for _ in range(5)]

    drift = [
        {
            "goals": s["player"]["goals"] - baseline["player"]["goals"],
            "matchesPlayed": s["seasonProgress"]["matchesPlayed"]
            - baseline["seasonProgress"]["matchesPlayed"],
        }
        for s in snapshots
        if s["player"]["goals"] != baseline["player"]["goals"]
        or s["seasonProgress"]["matchesPlayed"] != baseline["seasonProgress"]["matchesPlayed"]
    ]
    identical = all(json.dumps(s, sort_keys=True) == json.dumps(baseline, sort_keys=True) for s in snapshots)
    if drift:
        record("T1 GET puro", "FAIL", "GET repetido altera estadísticas", drift=drift)
    elif not identical:
        diffs = set()
        for s in snapshots:
            for key in baseline:
                if json.dumps(s.get(key), sort_keys=True) != json.dumps(baseline.get(key), sort_keys=True):
                    diffs.add(key)
        record("T1 GET puro", "INFO", "GET no muta estadísticas pero la respuesta no es estable", campos=sorted(diffs))
    else:
        record("T1 GET puro", "PASS", "6 GET consecutivos devuelven exactamente lo mismo")
    return cid


def test_play_match_repeat(client) -> None:
    """T2: reenviar la misma request de partido (doble click / retry)."""
    session = clear_pending(client, create_career(client))
    cid = session["id"]
    before = client.get(f"/api/careers/{cid}").json()["seasonProgress"]["matchesPlayed"]
    for _ in range(3):
        client.post(f"/api/careers/{cid}/play-match")
    after = client.get(f"/api/careers/{cid}").json()["seasonProgress"]["matchesPlayed"]
    record(
        "T2 play-match repetido",
        "FAIL" if after - before == 3 else "PASS",
        f"3 POST idénticos consecutivos avanzaron {after - before} partidos (sin clave de idempotencia)",
    )


def test_concurrent_play_match(client) -> None:
    """T3: N play-match simultáneos -> ¿lost update?"""
    session = clear_pending(client, create_career(client))
    cid = session["id"]
    before = client.get(f"/api/careers/{cid}").json()
    n = 8
    barrier = threading.Barrier(n)
    responses: list = [None] * n

    def worker(i: int):
        barrier.wait()
        responses[i] = client.post(f"/api/careers/{cid}/play-match")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    ok = sum(1 for r in responses if r is not None and r.status_code == 200)
    after = client.get(f"/api/careers/{cid}").json()
    advanced = after["seasonProgress"]["matchesPlayed"] - before["seasonProgress"]["matchesPlayed"]
    goals_progress = after["seasonProgress"]["goals"] - before["seasonProgress"]["goals"]
    goals_player = after["player"]["goals"] - before["player"]["goals"]
    lost = ok - advanced
    record(
        "T3 play-match concurrente",
        "FAIL" if lost > 0 or goals_player != goals_progress else "PASS",
        f"{ok}/{n} respuestas 200 pero el progreso avanzó {advanced} partidos ({lost} perdidos)",
        goles_en_progress=goals_progress,
        goles_en_player=goals_player,
    )


def test_concurrent_advance_season(client) -> None:
    """T4: N advance-season simultáneos sobre una temporada terminada."""
    session = clear_pending(client, create_career(client))
    cid = session["id"]
    session = play_until_season_end(client, session)
    before = client.get(f"/api/careers/{cid}").json()
    n = 6
    barrier = threading.Barrier(n)
    responses: list = [None] * n

    def worker(i: int):
        barrier.wait()
        responses[i] = client.post(f"/api/careers/{cid}/advance-season")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    after = client.get(f"/api/careers/{cid}").json()
    snapshots_added = len(after["history"]) - len(before["history"])
    age_delta = after["player"]["age"] - before["player"]["age"]
    season_delta = after["currentSeason"] - before["currentSeason"]
    seasons = [s["season"] for s in after["history"]]
    duplicated = len(seasons) != len(set(seasons))
    bad = snapshots_added != 1 or age_delta != 1 or season_delta != 1 or duplicated
    record(
        "T4 advance-season concurrente",
        "FAIL" if bad else "PASS",
        f"{n} cierres simultáneos -> {snapshots_added} snapshots, edad +{age_delta}, temporada +{season_delta}",
        temporadas_en_history=seasons,
        snapshots_duplicados=duplicated,
    )


def test_persistence_restart(db_path: Path) -> None:
    """T5: reiniciar el proceso/engine y recuperar la carrera por ID."""
    client, _ = build_client(db_path, fresh=True)
    session = clear_pending(client, create_career(client))
    cid = session["id"]
    for _ in range(10):
        session = clear_pending(client, session)
        session = client.post(f"/api/careers/{cid}/play-match").json()
    before = client.get(f"/api/careers/{cid}").json()
    client.close()

    # Simula reinicio del backend: engine nuevo, misma base.
    client2, _ = build_client(db_path, fresh=False)
    response = client2.get(f"/api/careers/{cid}")
    if response.status_code != 200:
        record("T5 persistencia tras reinicio", "FAIL", f"GET tras reinicio devolvió {response.status_code}")
        client2.close()
        return
    after = response.json()
    fields = {
        "goals": (before["player"]["goals"], after["player"]["goals"]),
        "assists": (before["player"]["assists"], after["player"]["assists"]),
        "matchesPlayed": (before["player"]["matchesPlayed"], after["player"]["matchesPlayed"]),
        "progressMatches": (
            before["seasonProgress"]["matchesPlayed"],
            after["seasonProgress"]["matchesPlayed"],
        ),
        "progressGoals": (before["seasonProgress"]["goals"], after["seasonProgress"]["goals"]),
        "clubId": (before["player"]["clubId"], after["player"]["clubId"]),
        "currentSeason": (before["currentSeason"], after["currentSeason"]),
    }
    mismatched = {k: v for k, v in fields.items() if v[0] != v[1]}
    record(
        "T5 persistencia tras reinicio",
        "FAIL" if mismatched else "PASS",
        "el estado sobrevive a un engine nuevo sobre la misma base"
        if not mismatched
        else "el estado cambió tras el reinicio",
        divergencias=mismatched or None,
    )

    # ¿La respuesta completa es idéntica?
    if json.dumps(before, sort_keys=True) != json.dumps(after, sort_keys=True):
        diffs = sorted(
            k for k in before
            if json.dumps(before.get(k), sort_keys=True) != json.dumps(after.get(k), sort_keys=True)
        )
        record("T5b respuesta idéntica tras reinicio", "INFO", "hay campos que difieren", campos=diffs)
    else:
        record("T5b respuesta idéntica tras reinicio", "PASS", "respuesta byte a byte idéntica")
    client2.close()


def test_unknown_career(client) -> None:
    response = client.get("/api/careers/no-existe")
    record(
        "T6 carrera inexistente",
        "PASS" if response.status_code == 404 else "FAIL",
        f"GET de un ID inexistente devuelve {response.status_code}",
    )
    response = client.post("/api/careers/no-existe/play-match")
    record(
        "T6b play-match sobre ID inexistente",
        "PASS" if response.status_code == 404 else "FAIL",
        f"devuelve {response.status_code}",
    )


def test_stale_client_replay(client) -> None:
    """T7: un cliente con estado viejo (pestaña sin refrescar) reenvía acciones."""
    session = clear_pending(client, create_career(client))
    cid = session["id"]
    stale = client.get(f"/api/careers/{cid}").json()
    for _ in range(5):
        client.post(f"/api/careers/{cid}/play-match")
    fresh = client.get(f"/api/careers/{cid}").json()
    # El cliente viejo reenvía resolve-event con un choice de su snapshot antiguo.
    detail = (
        f"la pestaña vieja cree que van {stale['seasonProgress']['matchesPlayed']} partidos, "
        f"el servidor {fresh['seasonProgress']['matchesPlayed']}; "
        "la API no expone versión ni ETag para detectarlo"
    )
    has_version = any(k.lower() in ("version", "revision", "etag") for k in fresh)
    record("T7 cliente desactualizado", "FAIL" if not has_version else "PASS", detail)


def test_league_table_goal_difference(client) -> None:
    """T8: goles a favor/en contra de tu equipo en la tabla vs partidos reales."""
    session = clear_pending(client, create_career(client))
    cid = session["id"]
    gf = ga = played_league = 0
    league_id = None
    for _ in range(200):
        session = clear_pending(client, session)
        progress = session["seasonProgress"]
        if progress["matchesPlayed"] >= progress["matchesTotal"]:
            break
        session = client.post(f"/api/careers/{cid}/play-match").json()
        match = session["seasonProgress"]["recentMatches"][-1]
        club = session.get("currentClub") or {}
        league_id = club.get("leagueId") or league_id
        if match["competitionId"] == league_id:
            gf += match["goalsFor"]
            ga += match["goalsAgainst"]
            played_league += 1

    table = session["seasonProgress"].get("leagueTable") or []
    club_id = session["player"]["clubId"]
    row = next((r for r in table if r["clubId"] == club_id), None)
    if not row:
        record("T8 diferencia de gol", "INFO", "el jugador no aparece en la tabla de liga")
        return
    bad = row["goalsFor"] != gf or row["goalsAgainst"] != ga or row["played"] != played_league
    record(
        "T8 diferencia de gol de la tabla",
        "FAIL" if bad else "PASS",
        f"tabla dice PJ={row['played']} GF={row['goalsFor']} GC={row['goalsAgainst']}; "
        f"los partidos reales dan PJ={played_league} GF={gf} GC={ga}",
        puntos_tabla=row["points"],
        puntos_reales=session["seasonProgress"]["leagueWins"] * 3 + session["seasonProgress"]["leagueDraws"],
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    client, _ = build_client(DB, fresh=True)
    test_get_is_pure(client)
    test_play_match_repeat(client)
    test_concurrent_play_match(client)
    test_concurrent_advance_season(client)
    test_unknown_career(client)
    test_stale_client_replay(client)
    test_league_table_goal_difference(client)
    client.close()

    test_persistence_restart(Path(__file__).parent / "runs" / "persistence.db")

    (OUT / "robustness.json").write_text(json.dumps(RESULTS, ensure_ascii=False, indent=1))
    failed = [r for r in RESULTS if r["status"] == "FAIL"]
    print(f"\n{len(RESULTS)} pruebas | {len(failed)} fallas")
    print(f"Detalle en {OUT}/robustness.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
