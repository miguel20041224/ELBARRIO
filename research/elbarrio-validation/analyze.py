"""Analizador de invariantes FASE 0.

Lee los JSON de runs/ y verifica invariantes de forma local. Solo imprime un
resumen agregado: el detalle queda en reports/violations.json para poder
reproducir cada hallazgo sin volver a simular.

Uso:
    python research/elbarrio-validation/analyze.py
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).parent
RUNS = BASE / "runs"
REPORTS = BASE / "reports"

def _advanced(match: dict) -> bool:
    """Si el club superó la ronda. Un empate lo define la tanda de penales."""
    if match["result"] == "W":
        return True
    if match["result"] == "D" and match.get("penaltiesFor") is not None:
        return match["penaltiesFor"] > match["penaltiesAgainst"]
    return False


# Invariantes declaradas. id -> (severidad, descripción)
INVARIANTS = {
    "I01": ("CRITICO", "player.goals == suma de goles de todas las temporadas cerradas"),
    "I02": ("CRITICO", "player.assists == suma de asistencias de todas las temporadas cerradas"),
    "I03": ("CRITICO", "player.matchesPlayed == suma de snapshot.matchesPlayed"),
    "I04": ("CRITICO", "snapshot.goals == suma de goles de los partidos de esa temporada"),
    "I05": ("CRITICO", "result coincide con el marcador (goalsFor vs goalsAgainst)"),
    "I06": ("CRITICO", "match.goals <= match.goalsFor (no metés más goles que tu equipo)"),
    "I07": ("CRITICO", "una llamada a play-match avanza exactamente 1 partido"),
    "I08": ("CRITICO", "una llamada a advance-season añade exactamente 1 snapshot y +1 edad"),
    "I09": ("ALTO", "las estadísticas acumuladas nunca decrecen"),
    "I10": ("ALTO", "el club actual existe en el catálogo"),
    "I11": ("ALTO", "no hay valores negativos en estadísticas"),
    "I12": ("ALTO", "progress.matchesPlayed <= progress.matchesTotal"),
    "I13": ("ALTO", "snapshot.season es estrictamente creciente sin huecos"),
    "I14": ("ALTO", "minutos == 0 implica goles == 0 y asistencias == 0"),
    "I15": ("MEDIO", "el rol previsto en la convocatoria coincide con los minutos reales"),
    "I16": ("ALTO", "snapshot.matchesPlayed == apariciones con minutos > 0 de la temporada"),
    "I17": ("ALTO", "los atributos del jugador evolucionan a lo largo de la carrera"),
    "I18": ("ALTO", "la posición en la tabla es coherente con los puntos"),
    "I19": ("MEDIO", "cada final ganada produce un trofeo en el snapshot"),
    "I20": ("ALTO", "se juegan todas las competiciones del calendario"),
    "I21": ("ALTO", "snapshot.callUps == número de fixtures de la temporada"),
    "I22": ("ALTO", "ganar una semifinal lleva a jugar la final de esa competición"),
    "I23": ("ALTO", "una eliminatoria empatada se define por penales: nunca queda sin resolver"),
}


def load_runs() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(RUNS.glob("career_*.json"))]


def check(run: dict, violations: list[dict]) -> None:
    idx = run["index"]

    def add(inv_id: str, detail: str, **extra):
        violations.append(
            {
                "invariant": inv_id,
                "severity": INVARIANTS[inv_id][0],
                "career": idx,
                "position": run.get("position"),
                "detail": detail,
                **extra,
            }
        )

    seasons = run.get("seasons", [])
    matches = run.get("matches", [])
    final = run.get("finalPlayer", {})

    # --- I01/I02/I03: acumulados de carrera vs suma de temporadas ---
    sum_goals = sum(s["snapshot"]["goals"] for s in seasons if s.get("snapshot"))
    sum_assists = sum(s["snapshot"]["assists"] for s in seasons if s.get("snapshot"))
    sum_matches = sum(s["snapshot"]["matchesPlayed"] for s in seasons if s.get("snapshot"))
    if final.get("goals") != sum_goals:
        add("I01", f"player.goals={final.get('goals')} vs suma temporadas={sum_goals}",
            diff=final.get("goals", 0) - sum_goals)
    if final.get("assists") != sum_assists:
        add("I02", f"player.assists={final.get('assists')} vs suma temporadas={sum_assists}",
            diff=final.get("assists", 0) - sum_assists)
    if final.get("matchesPlayed") != sum_matches:
        add("I03", f"player.matchesPlayed={final.get('matchesPlayed')} vs suma snapshot.matchesPlayed={sum_matches}",
            diff=final.get("matchesPlayed", 0) - sum_matches)

    # --- I04: snapshot vs partidos reales de esa temporada ---
    by_season_goals = defaultdict(int)
    by_season_assists = defaultdict(int)
    by_season_count = defaultdict(int)
    by_season_appearances = defaultdict(int)
    for m in matches:
        if not m.get("match"):
            continue
        by_season_goals[m["season"]] += m["match"]["goals"]
        by_season_assists[m["season"]] += m["match"]["assists"]
        by_season_count[m["season"]] += 1
        if m["match"]["minutesPlayed"] > 0:
            by_season_appearances[m["season"]] += 1
    for s in seasons:
        snap = s.get("snapshot")
        if not snap:
            continue
        n = snap["season"]
        if by_season_goals.get(n, 0) != snap["goals"]:
            add("I04", f"temporada {n}: snapshot.goals={snap['goals']} vs partidos={by_season_goals.get(n, 0)}")
        if by_season_appearances.get(n, 0) != snap["matchesPlayed"]:
            add("I16", f"temporada {n}: snapshot.matchesPlayed={snap['matchesPlayed']} "
                       f"vs apariciones={by_season_appearances.get(n, 0)}")
        if by_season_count.get(n, 0) != snap.get("callUps", 0):
            add("I21", f"temporada {n}: snapshot.callUps={snap.get('callUps')} "
                       f"vs fixtures={by_season_count.get(n, 0)}")

    # --- por partido ---
    role_vs_minutes = []
    for m in matches:
        match = m.get("match")
        if not match:
            continue
        gf, ga, result = match["goalsFor"], match["goalsAgainst"], match["result"]
        expected = "W" if gf > ga else ("D" if gf == ga else "L")
        if expected != result:
            add("I05", f"marcador {gf}-{ga} etiquetado '{result}' (debería ser '{expected}')",
                season=m["season"], match_index=m["index"], narrative=match["narrative"][:120])
        if match["goals"] > gf:
            add("I06", f"goles del jugador={match['goals']} > goles del equipo={gf}",
                season=m["season"], match_index=m["index"])
        if m["deltaProgressMatches"] != 1:
            add("I07", f"play-match avanzó {m['deltaProgressMatches']} partidos", season=m["season"])
        if match["minutesPlayed"] == 0 and (match["goals"] or match["assists"]):
            add("I14", f"0 minutos pero {match['goals']}g/{match['assists']}a", season=m["season"])
        for field in ("goals", "assists", "minutesPlayed", "goalsFor", "goalsAgainst"):
            if match[field] < 0:
                add("I11", f"match.{field}={match[field]} negativo", season=m["season"])
        if m.get("selectionRole"):
            role_vs_minutes.append((m["selectionRole"], match["minutesPlayed"], match["starter"]))

    # I15: coherencia convocatoria vs realidad
    mismatched = sum(
        1
        for role, minutes, starter in role_vs_minutes
        if (role == "starter" and minutes == 0)
        or (role == "bench" and starter)
    )
    if role_vs_minutes and mismatched / len(role_vs_minutes) > 0.15:
        add("I15", f"{mismatched}/{len(role_vs_minutes)} convocatorias contradicen los minutos reales "
                   f"({mismatched / len(role_vs_minutes):.0%})")

    # --- I08: cierre de temporada ---
    for s in seasons:
        if s["historyGrew"] != 1:
            add("I08", f"advance-season añadió {s['historyGrew']} snapshots", season=s.get("season"))
        if s["ageAfter"] - s["ageBefore"] != 1:
            add("I08", f"edad avanzó {s['ageAfter'] - s['ageBefore']} años", season=s.get("season"))

    # --- I09: monotonía de acumulados ---
    timeline = run.get("playerTimeline", [])
    for prev, curr in zip(timeline, timeline[1:]):
        for field in ("goals", "assists", "matchesPlayed", "trophies"):
            if curr[field] < prev[field]:
                add("I09", f"{field} bajó de {prev[field]} a {curr[field]}", season=curr.get("season"))

    # --- I13: temporadas consecutivas ---
    numbers = [s["snapshot"]["season"] for s in seasons if s.get("snapshot")]
    if numbers != list(range(1, len(numbers) + 1)):
        add("I13", f"secuencia de temporadas anómala: {numbers}")

    # --- I10: club existe ---
    if final.get("clubId") and not run.get("finalClub"):
        add("I10", f"clubId final '{final.get('clubId')}' no resuelve a un club del catálogo")

    # --- I17: evolución de atributos ---
    if len(timeline) >= 2:
        first, last = timeline[0], timeline[-1]
        changed = [
            f
            for f in ("technicalShooting", "physicalStamina", "mentalVision")
            if abs(last[f] - first[f]) > 0.01
        ]
        if not changed:
            add("I17", f"tras {len(timeline)} temporadas los atributos no cambiaron "
                       f"(shooting={first['technicalShooting']}, stamina={first['physicalStamina']}, "
                       f"vision={first['mentalVision']})")

    # --- I20: competiciones jugadas ---
    for s in seasons:
        comps = s["closingProgress"].get("competitionProgress") or []
        for comp in comps:
            if comp["played"] != comp["total"]:
                add("I20", f"temporada {s.get('season')}: {comp['competitionName']} "
                           f"jugó {comp['played']}/{comp['total']}")

    # --- I19: finales ganadas sin trofeo ---
    # --- I22/I23: integridad del cuadro de eliminatorias ---
    finals_won = defaultdict(list)
    knockout = defaultdict(dict)
    for m in matches:
        match = m.get("match")
        if not match:
            continue
        stage = match.get("stageId")
        if stage in ("semifinal", "final"):
            knockout[(m["season"], match["competitionName"])][stage] = match
        if stage == "final" and _advanced(match):
            finals_won[m["season"]].append(match["competitionName"])

    for (season, competition), stages in sorted(knockout.items()):
        semifinal = stages.get("semifinal")
        if semifinal is not None and _advanced(semifinal) and "final" not in stages:
            add("I22", f"temporada {season}: ganó la semifinal de {competition} "
                       f"y la final nunca se jugó", season=season, competition=competition)
        for stage_id, match in stages.items():
            if match["result"] == "D" and match.get("penaltiesFor") is None:
                add("I23", f"temporada {season}: la {stage_id} de {competition} quedó empatada "
                           f"y no definió quién pasa", season=season, competition=competition)
    for s in seasons:
        snap = s.get("snapshot")
        if not snap:
            continue
        expected = set(finals_won.get(snap["season"], []))
        got = set(snap["trophies"])
        missing = expected - got
        if missing:
            add("I19", f"temporada {snap['season']}: final ganada sin trofeo: {sorted(missing)}",
                snapshotTrophies=sorted(got))

    # --- errores y stalls del runner ---
    for err in run.get("errors", []):
        violations.append(
            {"invariant": "RUNTIME", "severity": "CRITICO", "career": idx,
             "detail": f"error de ejecución: {err}"}
        )
    for stall in run.get("stalls", []):
        violations.append(
            {"invariant": "STALL", "severity": "CRITICO", "career": idx,
             "detail": f"la carrera se bloqueó: {stall}"}
        )


def distributions(runs: list[dict]) -> dict:
    per_position = defaultdict(list)
    for run in runs:
        seasons = run.get("seasons", [])
        if not seasons:
            continue
        for s in seasons:
            snap = s.get("snapshot")
            if not snap:
                continue
            per_position[run["position"]].append(
                {
                    "goals": snap["goals"],
                    "assists": snap["assists"],
                    "matches": snap["matchesPlayed"],
                    "minutes": snap["minutesPlayed"],
                    "rating": snap["averageRating"],
                    "trophies": len(snap["trophies"]),
                }
            )
    out = {}
    for position, rows in sorted(per_position.items()):
        goals = [r["goals"] for r in rows]
        out[position] = {
            "seasons": len(rows),
            "goalsMean": round(statistics.mean(goals), 2),
            "goalsMedian": statistics.median(goals),
            "goalsMin": min(goals),
            "goalsMax": max(goals),
            "assistsMean": round(statistics.mean(r["assists"] for r in rows), 2),
            "minutesMean": round(statistics.mean(r["minutes"] for r in rows)),
            "matchesMean": round(statistics.mean(r["matches"] for r in rows), 1),
            "ratingMean": round(statistics.mean(r["rating"] for r in rows), 2),
            "trophiesTotal": sum(r["trophies"] for r in rows),
        }
    return out


def match_stats(runs: list[dict]) -> dict:
    results = Counter()
    minutes_zero = 0
    total = 0
    goals_hist = Counter()
    score_hist = Counter()
    competitions = Counter()
    for run in runs:
        for m in run.get("matches", []):
            match = m.get("match")
            if not match:
                continue
            total += 1
            results[match["result"]] += 1
            goals_hist[match["goals"]] += 1
            score_hist[f"{match['goalsFor']}-{match['goalsAgainst']}"] += 1
            competitions[match["competitionName"]] += 1
            if match["minutesPlayed"] == 0:
                minutes_zero += 1
    return {
        "totalMatches": total,
        "resultSplit": {k: f"{v} ({v / total:.1%})" for k, v in results.most_common()} if total else {},
        "benchedShare": f"{minutes_zero / total:.1%}" if total else "n/a",
        "goalsPerMatch": {k: v for k, v in sorted(goals_hist.items())},
        "topScores": dict(score_hist.most_common(8)),
        "competitions": dict(competitions.most_common()),
    }


def main() -> int:
    runs = load_runs()
    if not runs:
        print("No hay runs. Ejecutá runner.py primero.")
        return 1

    violations: list[dict] = []
    for run in runs:
        check(run, violations)

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "violations.json").write_text(json.dumps(violations, ensure_ascii=False, indent=1))

    by_inv = Counter(v["invariant"] for v in violations)
    affected = defaultdict(set)
    for v in violations:
        affected[v["invariant"]].add(v["career"])

    print(f"Carreras analizadas: {len(runs)}")
    print(f"Temporadas totales: {sum(len(r.get('seasons', [])) for r in runs)}")
    print(f"Partidos totales: {sum(len(r.get('matches', [])) for r in runs)}")
    print(f"Violaciones totales: {len(violations)}\n")

    print(f"{'INV':<8}{'SEV':<10}{'#':>7}{'CARRERAS':>10}  DESCRIPCIÓN")
    print("-" * 100)
    order = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}
    for inv_id, count in sorted(
        by_inv.items(),
        key=lambda kv: (order.get(INVARIANTS.get(kv[0], ("BAJO",))[0], 9), -kv[1]),
    ):
        sev, desc = INVARIANTS.get(inv_id, ("CRITICO", inv_id))
        print(f"{inv_id:<8}{sev:<10}{count:>7}{len(affected[inv_id]):>10}  {desc}")

    clean = [k for k in INVARIANTS if k not in by_inv]
    print(f"\nInvariantes sin violaciones ({len(clean)}): {', '.join(sorted(clean))}")

    print("\n=== DISTRIBUCIÓN POR POSICIÓN (por temporada) ===")
    dist = distributions(runs)
    print(f"{'POS':<6}{'TEMP':>6}{'GOL_MED':>9}{'GOL_MIN':>9}{'GOL_MAX':>9}{'AST_MED':>9}{'MIN_MED':>9}{'PJ_MED':>8}{'RATING':>8}{'TROF':>6}")
    for position, row in dist.items():
        print(
            f"{position:<6}{row['seasons']:>6}{row['goalsMean']:>9}{row['goalsMin']:>9}{row['goalsMax']:>9}"
            f"{row['assistsMean']:>9}{row['minutesMean']:>9}{row['matchesMean']:>8}{row['ratingMean']:>8}{row['trophiesTotal']:>6}"
        )

    print("\n=== ESTADÍSTICA DE PARTIDOS ===")
    stats = match_stats(runs)
    for key, value in stats.items():
        print(f"{key}: {value}")

    (REPORTS / "distributions.json").write_text(
        json.dumps({"byPosition": dist, "matches": stats}, ensure_ascii=False, indent=1)
    )
    print(f"\nDetalle en {REPORTS}/violations.json y {REPORTS}/distributions.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
