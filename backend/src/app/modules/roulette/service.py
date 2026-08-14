import random
from uuid import uuid4
from app.schemas import Player, RouletteKind, RouletteOutcome, RouletteRoll


POSITIVE_POOL: list[RouletteOutcome] = [
    RouletteOutcome(
        id="signing_bonus",
        tone="gift",
        icon="💰",
        title="Bonus del club",
        description="La directiva te tiró un extra por firmar. €50.000 al bolsillo.",
        effects={"finance": {"balance": 50000}},
    ),
    RouletteOutcome(
        id="physical_boost",
        tone="positive",
        icon="💪",
        title="Preparación intensiva",
        description="Subiste el nivel físico. +5 stamina permanente.",
        effects={"physical": {"stamina": 5}},
    ),
    RouletteOutcome(
        id="mental_boost",
        tone="positive",
        icon="🧠",
        title="Concentración total",
        description="Trabajaste la cabeza. +4 concentración permanente.",
        effects={"mental": {"concentration": 4}},
    ),
    RouletteOutcome(
        id="technical_shot",
        tone="positive",
        icon="⚽",
        title="Definición pulida",
        description="Sesiones extra con el especialista. +3 tiro permanente.",
        effects={"technical": {"shooting": 3}},
    ),
    RouletteOutcome(
        id="technical_pace",
        tone="positive",
        icon="⚡",
        title="Velocidad explosiva",
        description="Ganaste explosión. +3 velocidad permanente.",
        effects={"technical": {"pace": 3}},
    ),
    RouletteOutcome(
        id="technical_dribble",
        tone="positive",
        icon="🎯",
        title="Regate afinado",
        description="Mejoraste el 1v1. +3 regate permanente.",
        effects={"technical": {"dribbling": 3}},
    ),
    RouletteOutcome(
        id="form_streak",
        tone="positive",
        icon="🔥",
        title="Racha positiva",
        description="Te sentís imparable. +12 forma, +8 moral.",
        effects={"state": {"form": 12, "morale": 8}},
    ),
    RouletteOutcome(
        id="fan_favorite",
        tone="positive",
        icon="📣",
        title="Ídolo de la hinchada",
        description="Los hinchas cantan tu nombre. +10 relación con hinchada, +6 reputación.",
        effects={
            "relationships": {"fans": 10},
            "state": {"reputation": 6},
        },
    ),
    RouletteOutcome(
        id="coach_trust",
        tone="positive",
        icon="🎩",
        title="Confianza del DT",
        description="El técnico confía a full en vos. +12 con el DT.",
        effects={"relationships": {"coach": 12}},
    ),
    RouletteOutcome(
        id="sponsor_deal",
        tone="gift",
        icon="🤝",
        title="Nuevo sponsor",
        description="Firmaste contrato con una marca. +€3.000/semana + €40.000 de bono.",
        effects={"finance": {"balance": 40000, "weeklySalary": 3000}},
    ),
    RouletteOutcome(
        id="family_boost",
        tone="positive",
        icon="👨‍👩‍👦",
        title="Familia unida",
        description="Momento familiar hermoso. +12 felicidad, +8 con familia.",
        effects={
            "state": {"happiness": 12},
            "relationships": {"family": 8},
        },
    ),
    RouletteOutcome(
        id="press_love",
        tone="positive",
        icon="📰",
        title="La prensa te ama",
        description="Aparecen notas destacándote. +8 relación con prensa, +8 reputación.",
        effects={
            "relationships": {"press": 8},
            "state": {"reputation": 8},
        },
    ),
    RouletteOutcome(
        id="fitness_reset",
        tone="positive",
        icon="🏖️",
        title="Vacaciones exprés",
        description="Descanso reparador. Fatiga a 5, fitness a 95.",
        effects={"state": {"fatigue": -80, "fitness": 25}},
    ),
    RouletteOutcome(
        id="mental_leadership",
        tone="positive",
        icon="👑",
        title="Cinta de capitán simbólica",
        description="El vestuario te mira. +6 liderazgo, +6 con compañeros.",
        effects={
            "mental": {"leadership": 6},
            "relationships": {"teammates": 6},
        },
    ),
]

NEGATIVE_POOL: list[RouletteOutcome] = [
    RouletteOutcome(
        id="minor_injury",
        tone="negative",
        icon="🩹",
        title="Molestia muscular",
        description="Vas a arrancar limitado. -15 fitness, -8 forma.",
        effects={"state": {"fitness": -15, "form": -8}},
    ),
    RouletteOutcome(
        id="fine_indiscipline",
        tone="negative",
        icon="🛑",
        title="Multa por indisciplina",
        description="Llegaste tarde tres veces. -€30.000 del salario.",
        effects={"finance": {"balance": -30000}},
    ),
    RouletteOutcome(
        id="press_rumor",
        tone="negative",
        icon="🗞️",
        title="Rumor mediático",
        description="Salió un rumor feo sobre vos. -10 prensa, -10 reputación.",
        effects={
            "relationships": {"press": -10},
            "state": {"reputation": -10},
        },
    ),
    RouletteOutcome(
        id="form_slump",
        tone="negative",
        icon="📉",
        title="Bajón anímico",
        description="Venís con la cabeza en otro lado. -12 forma, -8 felicidad.",
        effects={"state": {"form": -12, "happiness": -8}},
    ),
    RouletteOutcome(
        id="coach_doubt",
        tone="negative",
        icon="🤨",
        title="El DT duda de vos",
        description="Escuchaste que el técnico te bancó poco. -12 con el DT.",
        effects={"relationships": {"coach": -12}},
    ),
    RouletteOutcome(
        id="pressure_spike",
        tone="negative",
        icon="⚠️",
        title="Ola de presión",
        description="La hinchada se puso pesada. +15 presión, -6 felicidad.",
        effects={"state": {"pressure": 15, "happiness": -6}},
    ),
    RouletteOutcome(
        id="family_argument",
        tone="negative",
        icon="😤",
        title="Discusión familiar",
        description="Pelea fuerte en tu casa. -12 con familia, -8 felicidad.",
        effects={
            "relationships": {"family": -12},
            "state": {"happiness": -8},
        },
    ),
    RouletteOutcome(
        id="teammate_beef",
        tone="negative",
        icon="🥊",
        title="Pica en el vestuario",
        description="Cruce con un referente. -10 con compañeros.",
        effects={"relationships": {"teammates": -10}},
    ),
    RouletteOutcome(
        id="fatigue_spike",
        tone="negative",
        icon="🥵",
        title="Cargaste mal",
        description="Entrenamiento excesivo. +25 fatiga.",
        effects={"state": {"fatigue": 25}},
    ),
]

GIFT_POOL: list[RouletteOutcome] = [
    RouletteOutcome(
        id="lucky_streak",
        tone="gift",
        icon="🍀",
        title="Alineación cósmica",
        description="Todo te sale. +10 forma, +8 felicidad, +5 con la hinchada.",
        effects={
            "state": {"form": 10, "happiness": 8},
            "relationships": {"fans": 5},
        },
    ),
    RouletteOutcome(
        id="scholarship_family",
        tone="gift",
        icon="🎓",
        title="Beca para tu hermano/a",
        description="El club le paga estudios a alguien de tu familia. +15 con familia.",
        effects={"relationships": {"family": 15}},
    ),
    RouletteOutcome(
        id="donation",
        tone="gift",
        icon="❤️",
        title="Donación al club de tu barrio",
        description="Donaste equipamiento al club donde empezaste. +8 reputación, +12 con hinchada.",
        effects={
            "state": {"reputation": 8},
            "relationships": {"fans": 12},
        },
    ),
]


def _select_pool(kind: RouletteKind, player: Player, rng: random.Random) -> list[RouletteOutcome]:
    if kind == "career_start":
        options = rng.sample(POSITIVE_POOL, 2) + rng.sample(GIFT_POOL, 1)
    else:
        rating_bias = 0
        if player.state.form > 70:
            rating_bias += 1
        if player.state.reputation > 60:
            rating_bias += 1
        pos_count = max(1, min(3, 1 + rating_bias))
        neg_count = max(0, min(2, 3 - pos_count))
        gift_count = max(0, 3 - pos_count - neg_count)
        options: list[RouletteOutcome] = []
        options += rng.sample(POSITIVE_POOL, pos_count)
        if neg_count:
            options += rng.sample(NEGATIVE_POOL, neg_count)
        if gift_count:
            options += rng.sample(GIFT_POOL, gift_count)
    rng.shuffle(options)
    return options


LABELS: dict[RouletteKind, str] = {
    "career_start": "🎡 Ruleta de arranque de carrera",
    "season_start": "🎡 Ruleta de pretemporada",
    "season_end": "🎡 Ruleta de fin de temporada",
}


def build_roulette(kind: RouletteKind, player: Player, rng: random.Random | None = None) -> RouletteRoll:
    r = rng or random.Random()
    options = _select_pool(kind, player, r)
    return RouletteRoll(
        id=str(uuid4()),
        kind=kind,
        label=LABELS[kind],
        options=options,
    )


def find_outcome(roll: RouletteRoll, outcome_id: str) -> RouletteOutcome | None:
    return next((o for o in roll.options if o.id == outcome_id), None)


def apply_outcome(player: Player, outcome: RouletteOutcome) -> None:
    effects = outcome.effects or {}
    if state := effects.get("state"):
        for k, v in state.items():
            if hasattr(player.state, k):
                current = getattr(player.state, k)
                setattr(player.state, k, max(0, min(100, current + float(v))))
    if rel := effects.get("relationships"):
        for k, v in rel.items():
            if hasattr(player.relationships, k):
                current = getattr(player.relationships, k)
                setattr(player.relationships, k, max(0, min(100, current + float(v))))
    if fin := effects.get("finance"):
        for k, v in fin.items():
            if hasattr(player.finance, k):
                current = getattr(player.finance, k)
                setattr(player.finance, k, max(0, current + float(v)))
    if tech := effects.get("technical"):
        for k, v in tech.items():
            if hasattr(player.technical, k):
                current = getattr(player.technical, k)
                setattr(player.technical, k, max(0, min(99, current + float(v))))
    if mental := effects.get("mental"):
        for k, v in mental.items():
            if hasattr(player.mental, k):
                current = getattr(player.mental, k)
                setattr(player.mental, k, max(0, min(99, current + float(v))))
    if physical := effects.get("physical"):
        for k, v in physical.items():
            if hasattr(player.physical, k):
                current = getattr(player.physical, k)
                setattr(player.physical, k, max(0, min(99, current + float(v))))
    if outcome.tags:
        existing = set(player.tags or [])
        existing.update(outcome.tags)
        player.tags = sorted(existing)
