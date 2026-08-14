from app.schemas import EventChoice, EventFollowUp, GameEvent


def _event(
    id: str,
    category,
    title: str,
    narrative: str,
    choices: list[EventChoice],
    *,
    weight: float = 1.0,
    min_age: int | None = None,
    max_age: int | None = None,
    club_tiers: list[int] | None = None,
    requires_min_reputation: float | None = None,
    requires_tags: list[str] | None = None,
    forbid_tags: list[str] | None = None,
    chained: bool = False,
) -> GameEvent:
    return GameEvent(
        id=id,
        category=category,
        title=title,
        narrative=narrative,
        weight=weight,
        minAge=min_age,
        maxAge=max_age,
        requiresClubTier=club_tiers,
        requiresMinReputation=requires_min_reputation,
        requiresTags=requires_tags,
        forbidTags=forbid_tags,
        chained=chained,
        choices=choices,
    )


EVENTS: list[GameEvent] = [
    _event(
        "personal.wedding_proposal",
        "personal",
        "Tu pareja te pide casarse ya",
        (
            "Estás a semanas del arranque de la temporada más importante de tu carrera. "
            "Tu pareja te dice que quiere casarse ahora, antes de que empiece la locura. "
            "El DT ya avisó que la pretemporada es innegociable. "
            "Sabés que si aceptás, el viaje y todo lo emocional te va a distraer. "
            "Si esperás, la relación entra en zona de crisis."
        ),
        [
            EventChoice(
                id="accept_now",
                label="Acepto y me caso ya",
                description="Casamiento express antes de pretemporada.",
                effects={
                    "state": {"happiness": 12, "concentration": -8, "pressure": 6},
                    "relationships": {"family": 15, "coach": -6},
                    "finance": {"balance": -25000},
                },
                tags=["married"],
                followUps=[
                    EventFollowUp(
                        eventId="personal.honeymoon_hangover",
                        delayEvents=1,
                        reason="Volviste de la luna de miel y todavía tenés la cabeza allá.",
                    ),
                ],
            ),
            EventChoice(
                id="wait_end_season",
                label="Le pido esperar al final de la temporada",
                description="Priorizo la carrera. Le explico que después nos casamos con todo.",
                effects={
                    "state": {"happiness": -4, "pressure": 3},
                    "relationships": {"family": -8, "coach": 5},
                },
                followUps=[
                    EventFollowUp(
                        eventId="personal.relationship_crisis",
                        delaySeasons=1,
                        reason="Tu pareja está harta de esperar.",
                    ),
                ],
            ),
            EventChoice(
                id="offer_engagement",
                label="Le propongo compromiso, boda al año",
                description="Anillo ahora, boda cuando termine la temporada.",
                effects={
                    "state": {"happiness": 6, "pressure": 2},
                    "relationships": {"family": 6, "coach": 1},
                    "finance": {"balance": -8000},
                },
                tags=["engaged"],
            ),
        ],
        weight=0.8,
        min_age=20,
    ),
    _event(
        "personal.honeymoon_hangover",
        "personal",
        "Volviste de la luna de miel — pero no del todo",
        (
            "Después de tres semanas de playa, volver al frío de la pretemporada "
            "te está pegando. El DT te ve distraído. Tu pareja te reclama tiempo. "
            "Tenés que reordenarte."
        ),
        [
            EventChoice(
                id="focus_football",
                label="Fútbol total",
                description="Me clavo entero en entrenar. Le explico a mi pareja que ahora arranca la temporada.",
                effects={
                    "state": {"concentration": 6, "form": 4},
                    "relationships": {"family": -6, "coach": 5},
                },
            ),
            EventChoice(
                id="balance_both",
                label="Equilibrio",
                description="Divido tiempo. Nadie se queja del todo.",
                effects={
                    "state": {"concentration": 1, "happiness": 2},
                    "relationships": {"family": 3, "coach": 1},
                },
            ),
        ],
        chained=True,
    ),
    _event(
        "personal.relationship_crisis",
        "personal",
        "Crisis con tu pareja",
        (
            "Tu pareja te dice que ya no aguanta más. Que cada vez que vos priorizás "
            "la carrera, ella se queda sola. Está pensando en separarse."
        ),
        [
            EventChoice(
                id="prioritize_relationship",
                label="Freno todo — necesito arreglar esto",
                description="Le pido a mi representante que baje agenda. Voy a estar más presente.",
                effects={
                    "state": {"happiness": 8, "concentration": -6, "pressure": 4},
                    "relationships": {"family": 15, "coach": -3},
                },
            ),
            EventChoice(
                id="end_relationship",
                label="Le digo que corte",
                description="Prefiero perder la relación que perder la carrera.",
                effects={
                    "state": {"happiness": -18, "morale": -10, "pressure": 10},
                    "relationships": {"family": -25},
                },
                tags=["single"],
            ),
            EventChoice(
                id="propose_therapy",
                label="Le propongo terapia de pareja",
                description="Buscamos ayuda profesional. Compromiso real.",
                effects={
                    "state": {"happiness": 3, "pressure": 2},
                    "relationships": {"family": 8},
                    "finance": {"balance": -5000},
                },
            ),
        ],
        chained=True,
    ),
    _event(
        "personal.unexpected_child",
        "personal",
        "Vas a ser padre — sin planearlo",
        (
            "Recibís la noticia entre partido y partido: vas a ser padre. "
            "No lo estabas planeando. Tu carrera está en un momento clave y "
            "el vestuario ya te está mirando distinto. La familia te pide "
            "que reduzcas viajes."
        ),
        [
            EventChoice(
                id="embrace",
                label="Lo abrazo con todo",
                description="Le meto pecho. Voy a ser padre y jugador top al mismo tiempo.",
                effects={
                    "state": {"happiness": 10, "pressure": 8, "concentration": -4},
                    "relationships": {"family": 20, "press": 5},
                },
                tags=["father"],
            ),
            EventChoice(
                id="delegate_family",
                label="Delego responsabilidades familiares",
                description="Contrato ayuda, minimizo impacto en entrenamiento.",
                effects={
                    "state": {"happiness": -6, "concentration": -2},
                    "relationships": {"family": -12, "teammates": 3},
                    "finance": {"balance": -40000},
                },
                tags=["father"],
            ),
        ],
        weight=0.5,
        min_age=21,
    ),
    _event(
        "social.pre_derby_party",
        "social",
        "Fiesta la noche antes del clásico",
        (
            "Compañeros del equipo te invitan a una fiesta. Es la noche "
            "anterior al clásico más grande del año. El DT no lo sabe. "
            "Podés ir un rato y volver temprano — o quedarte lejos."
        ),
        [
            EventChoice(
                id="go_short",
                label="Voy un rato corto",
                description="Aparezco, saludo, y a las 12 estoy en cama.",
                effects={
                    "state": {"morale": 4, "fatigue": 6, "form": -3},
                    "relationships": {"teammates": 6},
                },
            ),
            EventChoice(
                id="stay_home",
                label="No voy — mañana es el clásico",
                description="Profesionalismo absoluto. Descanso.",
                effects={
                    "state": {"form": 5, "fitness": 4},
                    "relationships": {"teammates": -4, "coach": 3},
                },
                followUps=[
                    EventFollowUp(
                        eventId="media.professionalism_spotlight",
                        delayEvents=2,
                        reason="Se filtró que dijiste que no y la prensa te destacó.",
                    ),
                ],
            ),
            EventChoice(
                id="party_hard",
                label="Voy con todo — se vive una vez",
                description="Amanezco. Ya veré cómo salgo mañana.",
                effects={
                    "state": {"morale": 10, "fatigue": 25, "form": -18, "fitness": -15},
                    "relationships": {"teammates": 12, "coach": -15, "press": -5},
                },
                followUps=[
                    EventFollowUp(
                        eventId="media.leaked_party_photos",
                        delayEvents=1,
                        reason="Un fotógrafo estaba ahí.",
                    ),
                ],
            ),
        ],
        weight=1.2,
    ),
    _event(
        "media.professionalism_spotlight",
        "media",
        "Un medio grande te elogia por profesional",
        (
            "Un periodista respetado publicó una nota destacando tu profesionalismo. "
            "Habla de cómo priorizaste el clásico por sobre la fiesta. "
            "Redes explotadas. Empiezan a hablar de vos afuera."
        ),
        [
            EventChoice(
                id="humble_response",
                label="Respondo humilde: 'Es lo que corresponde'",
                description="No inflo pecho. Doy una nota corta, seria.",
                effects={
                    "state": {"reputation": 8},
                    "relationships": {"press": 10, "fans": 6, "coach": 4},
                },
                followUps=[
                    EventFollowUp(
                        eventId="career.big_club_scout_visit",
                        delaySeasons=1,
                        reason="Ojeadores europeos leyeron la nota.",
                    ),
                ],
            ),
            EventChoice(
                id="capitalize",
                label="Capitalizo el momento en redes",
                description="Posteo, hago hilo, tiro contenido inspirador.",
                effects={
                    "state": {"reputation": 4},
                    "relationships": {"press": 5, "fans": 12, "teammates": -2},
                },
            ),
        ],
        chained=True,
    ),
    _event(
        "media.leaked_party_photos",
        "media",
        "Se filtraron fotos tuyas en la fiesta",
        (
            "Aparecen en Twitter fotos tuyas rodeado de gente, con el vaso en alto, "
            "la noche antes del clásico. El club te llama urgente. La prensa está afuera "
            "de tu casa."
        ),
        [
            EventChoice(
                id="public_apology",
                label="Comunicado público pidiendo disculpas",
                description="Bajé la guardia. Acepto lo que corresponda.",
                effects={
                    "state": {"reputation": -8, "pressure": 6, "morale": -4},
                    "relationships": {"coach": 4, "fans": -6, "press": -2},
                    "finance": {"balance": -20000},
                },
            ),
            EventChoice(
                id="blame_photographer",
                label="Denuncio filtración y me victimizo",
                description="Digo que invadieron mi privacidad.",
                effects={
                    "state": {"reputation": -14, "pressure": 10},
                    "relationships": {"press": -20, "fans": -12, "coach": -6},
                },
            ),
            EventChoice(
                id="silent_fine",
                label="Silencio y pago la multa del club",
                description="No hablo. Multa interna y adentro.",
                effects={
                    "state": {"reputation": -4, "pressure": 3},
                    "relationships": {"coach": -8, "teammates": 4},
                    "finance": {"balance": -80000},
                },
            ),
        ],
        chained=True,
    ),
    _event(
        "social.drug_offer",
        "social",
        "Te ofrecen droga en un after",
        (
            "Terminó el partido, ganaron. Están en un after privado. Alguien "
            "que apenas conocés te tira una bolsita blanca sobre la mesa. "
            "Te dice que 'nadie se entera'. Pero vos sabés que alguien SIEMPRE se entera."
        ),
        [
            EventChoice(
                id="refuse_leave",
                label="Me levanto y me voy",
                description="Corto seco. Me vuelvo a casa.",
                effects={
                    "state": {"reputation": 4, "morale": 3},
                    "relationships": {"family": 4},
                },
            ),
            EventChoice(
                id="refuse_stay",
                label="Digo que no pero me quedo",
                description="No consumo, pero me quedo con el grupo.",
                effects={
                    "state": {"reputation": -3, "fatigue": 12, "form": -6},
                    "relationships": {"family": -3, "press": -2},
                },
                followUps=[
                    EventFollowUp(
                        eventId="media.leaked_party_photos",
                        delayEvents=1,
                        reason="Salieron fotos del after aunque vos no consumiste.",
                    ),
                ],
            ),
            EventChoice(
                id="accept",
                label="Acepto — solo una vez",
                description="Me tiento. Uno solo. Nadie se entera.",
                effects={
                    "state": {
                        "morale": 8,
                        "fatigue": 20,
                        "form": -18,
                        "fitness": -12,
                        "reputation": -6,
                        "concentration": -8,
                    },
                    "relationships": {"family": -8},
                },
                tags=["experimented_drugs"],
                followUps=[
                    EventFollowUp(
                        eventId="health.doping_test_positive",
                        delayEvents=2,
                        reason="Control antidoping sorpresa.",
                    ),
                ],
            ),
        ],
        weight=0.6,
        min_age=20,
        requires_min_reputation=35,
    ),
    _event(
        "health.doping_test_positive",
        "health",
        "Diste positivo en antidoping",
        (
            "El médico del club entra al vestuario blanco. La muestra dio positivo. "
            "La federación abrió expediente. Tu representante ya está en camino. "
            "Los sponsors te dejaron de responder los mensajes."
        ),
        [
            EventChoice(
                id="accept_ban",
                label="Acepto la sanción — 12 partidos",
                description="No apelo. Pido perdón público y arranco rehabilitación.",
                effects={
                    "state": {"reputation": -25, "morale": -20, "pressure": 15},
                    "relationships": {"coach": -15, "fans": -20, "press": -15, "family": -10},
                    "finance": {"balance": -200000, "weeklySalary": -3000},
                },
                tags=["banned_doping"],
            ),
            EventChoice(
                id="appeal_ban",
                label="Apelo — abogados a fondo",
                description="Contamos con contramuestra. Peleo la sanción.",
                effects={
                    "state": {"reputation": -18, "pressure": 20},
                    "relationships": {"press": -8, "fans": -10},
                    "finance": {"balance": -450000},
                },
                tags=["banned_doping"],
            ),
        ],
        chained=True,
    ),
    _event(
        "career.big_club_scout_visit",
        "career",
        "Un ojeador de un club top vino a verte",
        (
            "Después de tu partido, un tipo con acreditación de un club europeo top "
            "te encara en el estacionamiento. Te dice que están armando informe. "
            "Que si mantenés el nivel, en la próxima ventana te llaman."
        ),
        [
            EventChoice(
                id="promise_focus",
                label="Le digo que me tengo que enfocar más que nunca",
                description="No prometo nada. Me clavo en el trabajo.",
                effects={
                    "state": {"pressure": 8, "concentration": 6, "reputation": 4},
                    "relationships": {"press": 2},
                },
                followUps=[
                    EventFollowUp(
                        eventId="career.transfer_offer_european",
                        delaySeasons=1,
                        reason="El club top hizo oferta oficial.",
                    ),
                ],
            ),
            EventChoice(
                id="brag_publicly",
                label="Suelto la noticia en una entrevista",
                description="Menciono en un móvil que un grande me sigue.",
                effects={
                    "state": {"pressure": 15, "reputation": -4},
                    "relationships": {"coach": -8, "press": -4, "teammates": -6},
                },
            ),
        ],
        chained=True,
    ),
    _event(
        "career.transfer_offer_european",
        "career",
        "Oferta oficial de un club europeo top",
        (
            "Llegó la oferta. Es un club de la élite mundial. Salario triplicado, "
            "presión brutal, pero el sueño está ahí. Tu club actual ya aceptó la parte "
            "económica. Falta que digas que sí."
        ),
        [
            EventChoice(
                id="accept_top",
                label="Acepto y me voy",
                description="Firmo. Cambio de vida total.",
                effects={
                    "state": {"pressure": 25, "reputation": 20, "happiness": 8, "morale": 15},
                    "relationships": {"family": -6, "fans": -12, "press": 10},
                    "finance": {"balance": 500000, "weeklySalary": 60000, "signOnBonus": 2000000},
                },
                tags=["european_transfer"],
            ),
            EventChoice(
                id="reject_stay_hero",
                label="Rechazo — quiero ser leyenda del club",
                description="Le digo que no. Prefiero construir historia acá.",
                effects={
                    "state": {"reputation": 8, "happiness": 12, "pressure": -5},
                    "relationships": {"fans": 25, "press": -5, "coach": 6},
                },
                tags=["local_hero"],
            ),
            EventChoice(
                id="negotiate_higher",
                label="Negocio salario más alto",
                description="Le pido más plata. Si mejoran, voy.",
                effects={
                    "state": {"pressure": 12, "reputation": -3},
                    "relationships": {"press": -4, "fans": -4},
                },
                followUps=[
                    EventFollowUp(
                        eventId="career.transfer_negotiation_result",
                        delayEvents=1,
                        reason="El club respondió.",
                    ),
                ],
            ),
        ],
        chained=True,
    ),
    _event(
        "career.transfer_negotiation_result",
        "career",
        "El club top respondió tu contraoferta",
        (
            "Mejoraron la propuesta pero no todo lo que pediste. Tu representante "
            "te avisa que si dudás mucho más, otro nombre entra en la lista."
        ),
        [
            EventChoice(
                id="accept_final",
                label="Acepto — está bien",
                description="Firmo. Sirve para arrancar la nueva etapa.",
                effects={
                    "state": {"reputation": 15, "pressure": 22, "morale": 12},
                    "finance": {"balance": 300000, "weeklySalary": 50000},
                },
                tags=["european_transfer"],
            ),
            EventChoice(
                id="walk_away",
                label="Me bajo — no se dio",
                description="Prefiero seguir en el club actual otra temporada.",
                effects={
                    "state": {"reputation": -8, "happiness": -6, "morale": -8},
                    "relationships": {"press": -6, "fans": -4},
                },
            ),
        ],
        chained=True,
    ),
    _event(
        "career.tempting_saudi_offer",
        "career",
        "Oferta millonaria desde Arabia",
        (
            "Un club de la Saudi Pro League pone sobre la mesa un contrato "
            "que triplica tu salario actual. El proyecto deportivo es débil "
            "pero la plata es real. Tu representante te presiona. Tu familia "
            "no quiere mudarse. Tenés que decidir."
        ),
        [
            EventChoice(
                id="accept_money",
                label="Acepto — la plata primero",
                description="Firmo. La familia se adapta. La carrera deportiva pasa a segundo plano.",
                effects={
                    "state": {"happiness": -5, "pressure": -8, "reputation": -15},
                    "relationships": {"family": -20, "fans": -25, "press": -10},
                    "finance": {"balance": 3500000, "weeklySalary": 180000},
                },
                tags=["saudi_move"],
            ),
            EventChoice(
                id="reject_stay",
                label="Rechazo — quiero seguir compitiendo alto",
                description="Le digo que no. La plata no lo es todo.",
                effects={
                    "state": {"happiness": 8, "pressure": 5, "reputation": 12},
                    "relationships": {"family": 15, "fans": 20, "press": 8},
                },
            ),
            EventChoice(
                id="negotiate_delay",
                label="Pido esperar una temporada más",
                description="Negocio la oferta para dentro de 12 meses.",
                effects={
                    "state": {"pressure": 10},
                    "relationships": {"family": 3, "press": -3},
                },
            ),
        ],
        weight=0.4,
        min_age=27,
        club_tiers=[4, 5],
    ),
    _event(
        "career.coach_conflict",
        "career",
        "Choque con el DT",
        (
            "En pleno entrenamiento tuvieron una discusión fuerte. El DT "
            "te sacó del once titular para el próximo partido. La prensa "
            "se enteró y sale en todos lados."
        ),
        [
            EventChoice(
                id="apologize_public",
                label="Pido disculpas públicas",
                description="Bajo la cabeza. Recompongo relación.",
                effects={
                    "state": {"reputation": -3, "pressure": -4},
                    "relationships": {"coach": 12, "press": 5, "fans": -3},
                },
            ),
            EventChoice(
                id="stand_ground",
                label="Me planto — tengo razón",
                description="No cedo. El vestuario me tiene que respaldar.",
                effects={
                    "state": {"pressure": 10, "reputation": 3},
                    "relationships": {"coach": -18, "teammates": 4, "press": -6},
                },
            ),
            EventChoice(
                id="request_transfer",
                label="Pido salir del club",
                description="Le digo al club que no puedo trabajar con este DT.",
                effects={
                    "state": {"pressure": 15, "happiness": -10},
                    "relationships": {"coach": -25, "fans": -12, "press": -10},
                },
                followUps=[
                    EventFollowUp(
                        eventId="career.transfer_offer_european",
                        delaySeasons=1,
                        reason="Tu pedido de salida abrió puertas.",
                    ),
                ],
                tags=["requested_transfer"],
            ),
        ],
        weight=1.0,
    ),
    _event(
        "financial.investment_opportunity",
        "financial",
        "Amigo del barrio te ofrece invertir",
        (
            "Un amigo de toda la vida te propone poner plata en su negocio. "
            "Dice que es seguro, que en dos años estás cobrando el doble. "
            "No te mostró números serios."
        ),
        [
            EventChoice(
                id="invest_big",
                label="Meto una moneda grande — es mi amigo",
                description="Confío. Firmo cheque.",
                effects={
                    "state": {"happiness": 3, "pressure": 6},
                    "relationships": {"family": -4},
                    "finance": {"balance": -250000},
                },
                followUps=[
                    EventFollowUp(
                        eventId="financial.investment_result",
                        delaySeasons=2,
                        reason="El negocio de tu amigo tuvo su ciclo.",
                    ),
                ],
            ),
            EventChoice(
                id="invest_small",
                label="Le pongo poco — banco el intento",
                description="Meto una moneda chica. Que se prueben.",
                effects={
                    "state": {"pressure": 1},
                    "finance": {"balance": -35000},
                },
            ),
            EventChoice(
                id="decline",
                label="Le digo que no",
                description="Le paso el contacto de mi contador. Que le arme un plan serio.",
                effects={
                    "relationships": {"family": 4},
                    "state": {"happiness": -1},
                },
            ),
        ],
        weight=0.6,
        min_age=22,
    ),
    _event(
        "financial.investment_result",
        "financial",
        "El negocio de tu amigo colapsó",
        (
            "El emprendimiento no funcionó. Tu amigo desapareció. La plata que "
            "pusiste está perdida. Tu contador te llama para armar plan de "
            "recuperación fiscal."
        ),
        [
            EventChoice(
                id="accept_loss",
                label="Acepto la pérdida y sigo",
                description="Me la banco. Cierro capítulo.",
                effects={
                    "state": {"morale": -8, "pressure": 6},
                    "relationships": {"family": -3},
                },
            ),
            EventChoice(
                id="sue_friend",
                label="Le hago juicio a mi amigo",
                description="Meto abogados. Recupero lo que pueda.",
                effects={
                    "state": {"pressure": 12, "happiness": -6, "reputation": -4},
                    "relationships": {"family": -8},
                    "finance": {"balance": -30000},
                },
            ),
        ],
        chained=True,
    ),
    _event(
        "health.overtraining_warning",
        "health",
        "El kine te avisa: venís al límite",
        (
            "El kinesiólogo te frena en el pasillo. Te dice que los marcadores "
            "físicos están rojos. Si seguís al mismo ritmo, en dos semanas te "
            "rompés algo. El próximo partido es clave."
        ),
        [
            EventChoice(
                id="rest_now",
                label="Paro esta semana",
                description="Me pierdo el partido. Recupero.",
                effects={
                    "state": {"fatigue": -30, "fitness": 12, "form": -5},
                    "relationships": {"coach": -6, "fans": -8},
                },
            ),
            EventChoice(
                id="push_through",
                label="Aprieto los dientes",
                description="Juego igual. Después vemos.",
                effects={
                    "state": {"fatigue": 15, "fitness": -10, "pressure": 8},
                    "relationships": {"coach": 5, "fans": 6},
                },
                followUps=[
                    EventFollowUp(
                        eventId="health.serious_injury",
                        delayEvents=2,
                        reason="Forzaste el cuerpo y se rompió algo.",
                    ),
                ],
            ),
            EventChoice(
                id="light_training",
                label="Entreno liviano y juego 45 minutos",
                description="Negocio con el DT: entro al segundo tiempo.",
                effects={
                    "state": {"fatigue": -8, "fitness": 3},
                    "relationships": {"coach": 2},
                },
            ),
        ],
        weight=0.9,
    ),
    _event(
        "health.serious_injury",
        "health",
        "Lesión grave: rotura de ligamentos",
        (
            "Cayó mal en un pique. El médico del club te dice que son ligamentos "
            "cruzados. Entre 6 y 9 meses afuera. Tu carrera cambia de acá al año que viene."
        ),
        [
            EventChoice(
                id="operate_recover",
                label="Operación y rehabilitación intensiva",
                description="Confío en el cuerpo médico. Me clavo en recuperar.",
                effects={
                    "state": {"fitness": -50, "morale": -15, "pressure": 10, "fatigue": -20},
                    "relationships": {"coach": 3, "teammates": 5, "fans": 8},
                    "finance": {"balance": -30000},
                },
                tags=["serious_injury"],
            ),
            EventChoice(
                id="second_opinion",
                label="Busco segunda opinión afuera",
                description="Viajo a Europa. Consulto especialistas.",
                effects={
                    "state": {"fitness": -50, "morale": -10, "pressure": 8},
                    "finance": {"balance": -120000},
                },
                tags=["serious_injury"],
            ),
        ],
        chained=True,
    ),
    _event(
        "media.selection_call_up",
        "media",
        "Convocado a la selección nacional",
        (
            "Sonó el teléfono. El seleccionador te llama para la fecha FIFA. "
            "Es tu primera convocatoria. La cabala del barrio se vuelve loca. "
            "Tu club te bancó pero no le gusta que viajes en pretemporada."
        ),
        [
            EventChoice(
                id="accept_full",
                label="Acepto — es un sueño",
                description="Viajo, entreno con todo, juego lo que me den.",
                effects={
                    "state": {"morale": 20, "happiness": 15, "fatigue": 15, "pressure": 8, "reputation": 12},
                    "relationships": {"coach": -3, "fans": 15, "family": 8, "press": 10},
                },
                tags=["national_team"],
            ),
            EventChoice(
                id="accept_limited",
                label="Acepto pero pido gestión de minutos",
                description="Le explico al DT del club. Voy y cuido el cuerpo.",
                effects={
                    "state": {"morale": 12, "happiness": 8, "fatigue": 6, "reputation": 6},
                    "relationships": {"coach": 5, "fans": 8, "press": 4},
                },
                tags=["national_team"],
            ),
            EventChoice(
                id="decline",
                label="Rechazo — no es el momento",
                description="Le digo al seleccionador que no. Me clavo en el club.",
                effects={
                    "state": {"reputation": -18, "happiness": -8},
                    "relationships": {"coach": 8, "fans": -15, "press": -12, "family": -10},
                },
            ),
        ],
        weight=0.5,
        requires_min_reputation=45,
    ),
]


EVENTS_BY_ID: dict[str, GameEvent] = {event.id: event for event in EVENTS}


def get_event(event_id: str) -> GameEvent | None:
    return EVENTS_BY_ID.get(event_id)
