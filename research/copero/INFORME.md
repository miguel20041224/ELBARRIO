# Investigación Copero Career Simulator → ELBARRIO

Fecha: 2026-08-16
Dataset: `research/copero/RAW/` (14 MB, 253 archivos, 9 carreras)
Derivados generados en esta investigación (reproducibles, no hace falta releer RAW):

| Ruta | Qué es | Tamaño |
| --- | --- | --- |
| `research/copero/CLEAN/` | Markdown sin cabecera/footer/imágenes/links | 78 KB |
| `research/copero/CORPUS/{intensa,normal,expres}.md` | Corpus deduplicado por modo | ~25 KB c/u |

---

## 1. Inventario del dataset

### 1.1 Estructura

```
RAW/
├── feedback_general.md          inventario automático previo (poco útil)
├── intensa/carrera_{1,2,3}/
├── normal/carrera_{1,2,3}/
└── expres/carrera_{1,2,3}/
    ├── carrera.json             perfil + volcado de pasos
    ├── 000_inicio.{md,html}     selección de modo
    ├── 001_identidad.{md,html}  formulario vacío
    ├── 002_identidad_rellenada  formulario completo
    └── 00{3..8}_{estado.md, estado.html, accion.txt, interacciones.txt}
```

### 1.2 Hallazgos sobre la calidad del dataset (relevantes antes de sacar conclusiones)

1. **Las 9 carreras están truncadas.** Solo 6 estados de carrera por carrera. Edad final alcanzada: Intensa 19-20, Normal 22-24, Exprés 25-28. **Ninguna llega al retiro.**
2. **`_accion.txt` e `_interacciones.txt` son copias byte a byte** del snapshot de página, no listas de botones. Verificado por hash: `expres/carrera_3/003_accion.txt` = `004_estado.md` = `004_interacciones.txt` (md5 `8ad9452f81`). De 172 archivos de texto, solo **119 blobs únicos**.
3. **El Markdown pierde información crítica.** Los trofeos, badges y celebraciones se renderizan como `<img alt="...">` y `aria-label`, que el conversor a MD descarta. Conclusión errónea que esto induce: "vitrina siempre vacía, sin competiciones". **Es falsa** — ver §4.6.
4. `000_inicio.md` de la primera carrera de cada modo muestra la descripción del modo por defecto (Normal), no del modo elegido: artefacto de captura (snapshot antes del click). El eje de edad confirma el modo real.

### 1.3 Inventario funcional (extraído de HTML, no de MD)

- **Fases**: `data-career-phase` ∈ {`identity`, `career`}. Solo dos pantallas en toda la app.
- **Clases funcionales**: `career-phase`, `career-history-row`, `career-events`, `career-trophy-celebration` (+ `-glow`, `-particle`, `-item`).
- **Assets**: `career-simulator/{pitch.svg, goal.svg, kit-v2.svg, header2.jpg}`, `career-events/<event_id>-<choice>.jpg`.
- **Ids de evento con ilustración**: `training_extra-{accept,reject}.jpg`, `finish_high_school-{accept,reject}.jpg`.
- **Identidad**: apellido (texto), dorsal (1-99), pierna hábil (Izquierda/Derecha), **24 nacionalidades** + "Ver más", **12 posiciones** (EI, DC, ED, MI, MCO, MD, LI, MC, LD, MCD, DFC, POR) sobre un campo interactivo.
- **Ligas observadas**: Liga Dimayor (CO), Liga Profesional y Primera Nacional (AR), Brasileirão (BR), Liga1 (PE), Liga FUTVE (VE), Championship y Premier League (EN), Serie A (IT), Bundesliga (DE), Ligue 1 (FR).
- **Competiciones ganables observadas**: Liga Profesional, Brasileirão, Premier League, Copa Argentina, Copa do Brasil, FA Cup, Coppa Italia, Copa Libertadores, Copa Sudamericana, **Copa América** (selección).

---

## 2. Flujo de carrera (idéntico en los tres modos)

```
000  Elegir modo (Intensa | Normal | Exprés) → "Comenzar carrera"
001  Identidad: apellido, dorsal, pierna, nacionalidad, posición
002  → "Confirmar identidad"
003  Estado inicial: OVR 50, edad 16, club "Libre", PJ/Gls/Ast 0
     └─ Decisión "Oferta de cantera": 3 clubes de la liga del país elegido
004+ Bucle por tramo:
     ├─ (overlay) Celebración de trofeo / badge de descenso, si aplica
     ├─ Se resuelven N temporadas de golpe (N = 1 / 2 / 3 según modo)
     ├─ Se actualizan OVR, valor, PJ/Gls/Ast y la fila de la tabla histórica
     └─ Decisión del tramo (una de: mercado de pases | préstamo | regreso de
        préstamo | evento narrativo)
```

Elementos permanentes de la pantalla de carrera:

- Ficha: `OVR<n>`, país (3 letras), `#<dorsal> <POS>`, club actual (o "Libre"), `Edad`, `Valor` (€100K / €4.7M / €98M), `PJ`, `Gls`, `Ast`.
- Vitrina de trofeos (`🏆Vitrina vacía` o fila de escudos apilados con `aria-label` acumulativo).
- Tabla histórica: `Edad | Club | OVR | PJ | Gls | Ast`, con el eje de edad **pre-listado completo** desde el primer paso; filas futuras como `?` / "Eligiendo club..." / "Decisión de carrera...".
- Fila de selección nacional: país + PJ/Gls/Ast.
- Botón "Ver logros" (sistema de achievements aparte de los trofeos deportivos).

---

## 3. Diferencias entre modos

| | Intensa | Normal | Exprés |
| --- | --- | --- | --- |
| Descripción oficial | "1 decisión por temporada, inmersión profunda." | "Decisiones cada 2 temporadas, una experiencia equilibrada." | "Decisiones cada 3 temporadas para disfrutarlo rápido." |
| Eje de edad | 16,17,18…39 (24 filas) | 16,18,20…38 (12 filas) | 16,19,22…37 (8 filas) |
| Decisiones en toda la carrera | ~24 | ~12 | ~8 |
| Edad alcanzada en el dataset | 19-20 | 22-24 | 25-28 |
| Trofeos observados | 1 (Copa Libertadores) | 0 (sí un descenso) | muchos (hasta 8 en vitrina) |
| Selección nacional activa | 0/0/0 | 0/0/0 | sí (COL 51/22/16) |

**Conclusión clave sobre los modos:** son **la misma simulación con distinta granularidad de decisión**. No cambian reglas, ni catálogo de eventos, ni competiciones. Lo único que varía es cuántas temporadas se resuelven entre decisión y decisión. Las diferencias observadas en trofeos y selección son consecuencia de la profundidad alcanzada por el scraper, **no** del modo.

Evidencia: `RAW/{modo}/carrera_2/000_inicio.md` (textos), tablas históricas de `RAW/{modo}/carrera_*/008_estado.md` (ejes de edad).

---

## 4. Reglas y mecánicas

### 4.1 Arranque
Siempre OVR 50, edad 16, club "Libre", valor €100K. La **oferta de cantera** presenta 3 clubes **de la liga del país de nacionalidad** (COL → Liga Dimayor, ARG → Primera Nacional o Liga Profesional, BRA → Brasileirão).
`RAW/*/carrera_*/003_accion.txt`

### 4.2 Mercado de pases
Decisión recurrente: **2 ofertas "Fichar por X" + 1 "Quedarse en Y"**. Cada tarjeta muestra club y liga; `aria-label` = `"Fichar por <corto>. Firmar por <nombre completo>"`. Las ofertas pueden cruzar país y liga (BRA→ARG efectivo en `intensa/carrera_3/006_accion.txt`; BRA→PE ofrecido en `005_accion.txt`). No hay cifras de traspaso, salario, contrato ni cláusula.

### 4.3 Préstamos
Tipo de decisión propio, con 3 destinos: `"Préstamo en X. Ir cedido a X"` (`expres/carrera_3/005_accion.txt`, "Tu club quiere que sumes minutos en otro equipo"). Genera un badge `Período a préstamo` en la fila de historial, y al tramo siguiente dispara **"Regreso a tu club"**: 2 ofertas externas + quedarse en el club **dueño** (no en el de cesión). `expres/carrera_3/006_accion.txt`

### 4.4 Eventos narrativos (catálogo completo observado — 6 tipos)

| Evento | Opciones y efectos exactos | Prob. | Evidencia |
| --- | --- | --- | --- |
| Oferta de cantera | 3 clubes | — | `*/003_accion.txt` |
| Mercado de pases | 2 fichar + quedarse | — | recurrente |
| Salida a préstamo | 3 destinos | — | `expres/carrera_3/005_accion.txt` |
| Regreso a tu club | 2 ofertas + quedarse | — | `expres/carrera_3/006_accion.txt` |
| **Concentración extra** | "Hacerla" → **+4 OVR (65%) / −3 OVR (35%)**; "Preparación habitual" → sin cambios | explícita | `expres/carrera_1/007_accion.txt` |
| **Terminar el secundario** | "Aceptar" → **+1 OVR por madurez, menos minutos temporalmente**; "Rechazar" → sin cambios | no mostrada | `expres/carrera_2/006_accion.txt` |
| **Abuelo de otra nacionalidad** | "Cambiar de selección <País>" → representás otra selección; "Quedarse con la que tenés" | — | `normal/carrera_2/007_accion.txt` |

Los eventos con ilustración exponen su id interno: `training_extra`, `finish_high_school`. Ambos tienen imagen por cada rama (`-accept` / `-reject`), lo que indica un catálogo de eventos ilustrados con estructura binaria.

### 4.5 Progresión
- El OVR sube por tramo sin barra de potencial ni desglose de atributos: **un único número**. Ejemplos: 50→56→70→72→73 (`normal/carrera_1`), 50→61→64→67→69 (`normal/carrera_3`), 50→…→90 (`expres/carrera_1`, edad 25).
- El valor de mercado sigue al OVR y a la liga: €100K (16) → €4.7M (22, Perú) → €98M (25, River Plate, OVR 90).
- Las estadísticas se acumulan de golpe al resolver el tramo; la fila histórica guarda el desglose por tramo.

### 4.6 Trofeos y competiciones — **corrección importante**
Copero **sí** tiene competiciones y trofeos. La información vive solo en el HTML:

- Overlay modal a pantalla completa `career-trophy-celebration` (`z-50`, `backdrop-blur`, partículas), con `aria-label` = nombre del trofeo y botón **"Ver logro"**. Se dispara al entrar al estado tras ganar algo, **bloqueando la UI hasta descartarlo**.
- Vitrina acumulativa: escudos apilados con `aria-label` conjunto. Ej. `expres/carrera_1/008_estado.html`: `"Liga Profesional, Copa Argentina, Copa América, Liga Profesional, Copa Argentina, Copa Libertadores, Liga Profesional, Copa Libertadores"` (8 títulos, repeticiones incluidas).
- El mismo overlay se usa para **hitos negativos**: `aria-label="Descenso"` con paleta roja (`normal/carrera_2/006_estado.html`).
- Trofeos confirmados en el dataset: Liga Profesional, Brasileirão, Premier League, Copa Argentina, Copa do Brasil, FA Cup, Coppa Italia, Copa Libertadores, Copa Sudamericana, Copa América.

### 4.7 Selección nacional
Fila propia con PJ/Gls/Ast acumulados, que **crece automáticamente sin decisión del jugador** a partir de cierto nivel (0/0/0 a los 19 → 4/1/0 a los 22 → 51/22/16 a los 25 en `expres/carrera_1`). La Copa América aparece en la vitrina, así que hay torneos de selección. Único punto de decisión relacionado: el evento "Abuelo de otra nacionalidad".

### 4.8 Fin de carrera
**No observado.** El eje de edad se pre-lista hasta **39** en Intensa y **37** en Exprés, lo que indica ese techo. No hay evidencia de pantalla de retiro, resumen final ni palmarés de cierre en el dataset.

---

## 5. Variabilidad observada (las 9 carreras)

| Carrera | Perfil | OVR final | Valor final | Hitos |
| --- | --- | --- | --- | --- |
| intensa/1 | TESTA #10 MCO COL | 64 (18) | €650K | — |
| intensa/2 | TESTB #9 DC ARG | 64 (19) | — | asciende de Primera Nacional a Liga Profesional |
| intensa/3 | TESTC #11 EI BRA | 66 (19) | €1.1M | Copa Libertadores; BRA→ARG |
| normal/1 | TESTA #10 MCO COL | 73 (22) | €4.7M | COL→PE (Alianza Lima) |
| normal/2 | TESTB #9 DC ARG | 75 (24) | €3.2M | **Descenso** con Instituto; evento de nacionalidad |
| normal/3 | TESTC #11 EI BRA | 69 (24) | €2.2M | ofertas internacionales rechazadas |
| expres/1 | TESTA #10 MCO COL | **90** (25) | **€98M** | 8 trofeos, Copa América, 51 caps; COL→ARG→River |
| expres/2 | TESTB #9 DC ARG | ~82 (28) | — | Liga Profesional, Copa Sudamericana; evento secundario |
| expres/3 | TESTC #11 EI BRA | ~89 (25) | — | préstamo→regreso; Copa do Brasil, Coppa Italia, Premier |

Fuentes de varianza reales: rendimiento simulado por tramo (OVR/stats), **tipo de evento del tramo** (no es fijo por número de tramo), clubes ofertantes, resultados de club (títulos/descensos), y trayectoria internacional. La estructura de UI y el copy son idénticos.

Nota sobre las identidades: los tres perfiles (TESTA/TESTB/TESTC) se repiten en los tres modos por diseño del scraper. Confirmado que **no hay cruce de datos** entre carreras (`002_identidad_rellenada.md` correcto en las 9).

---

## 6. Gap analysis: Copero vs ELBARRIO

### 6.1 Estado actual de ELBARRIO

Backend FastAPI + SQLAlchemy, ~7.700 líneas totales.

| Módulo | Contenido real |
| --- | --- |
| `clubs/data.py` | **17 ligas, 210 clubes** con prestigio, presupuesto, ciudad, apodo |
| `events/library.py` | **19 eventos**, 6 categorías, con requisitos (edad, tier, reputación, tags) y cadenas |
| `roulette/service.py` | **26 outcomes** (12 positivos, 9 negativos, 5 regalo), 3 tipos de tirada |
| `simulation/season.py` | Calendario real: liga doble vuelta, plan especial Colombia, copa doméstica, copa continental; tabla de posiciones; trofeos por tabla |
| `simulation/match.py` | Convocatoria previa (titular/suplente/banco, chance %, minutos esperados, mensaje del DT), simulación partido a partido |
| `transfers/service.py` | Ventanas con contrato: cláusula de rescisión, contrato expirando, agente libre, préstamo, renovación |
| `awards/service.py` | MVP del partido, Bota de Oro, Jugador de la Temporada, Balón de Oro |
| API | 7 endpoints (`create_career`, `play-match`, `resolve-event`, `advance-season`, `spin-roulette`, `accept-transfer`, `get`) |

ELBARRIO es **mucho más profundo** que Copero en simulación. Copero es más pulido en presentación y ritmo.

### 6.2 Lo que Copero tiene y ELBARRIO no

| # | Feature de Copero | Estado en ELBARRIO | Impacto |
| --- | --- | --- | --- |
| G1 | **Modos de ritmo** (1/2/3 temporadas por decisión) | No existe. `mode` es `player`/`manager` | **Alto** — es la feature identitaria de Copero |
| G2 | **Timeline de carrera completa** (edad 16→39 pre-listada, fila por temporada con club/OVR/stats) | Existe `SeasonHistory` pero solo hacia atrás, sin eje futuro | **Alto** — da sensación de "carrera" de un vistazo |
| G3 | **Celebración de trofeo a pantalla completa** con partículas y "Ver logro" | Trofeos existen, sin momento de celebración | **Alto** — es el pico emocional del juego |
| G4 | **Hitos negativos celebrados** (Descenso) | Descensos no modelados | Medio |
| G5 | **Ascensos/descensos de club** que cambian la liga del jugador | No modelado | Medio-alto |
| G6 | **Selección nacional funcional** (caps/goles acumulados, Copa América) | `caps` existe en el esquema pero **nunca se incrementa**; en el roadmap como pendiente | **Alto** |
| G7 | **Cambio de nacionalidad deportiva** (evento del abuelo) | No existe | Bajo, pero muy memorable |
| G8 | **OVR único visible** | Solo atributos granulares; **no hay OVR agregado en ningún sitio** | **Alto** — sin él no hay progresión legible |
| G9 | **Valor de mercado** | No existe | **Alto** — es el marcador principal de éxito en Copero |
| G10 | **Ilustración por evento y por rama** | Solo texto | Medio |
| G11 | **Probabilidades explícitas en la opción** ("65% +4 OVR") | Los efectos son deterministas y no se muestran | **Alto** — decisión informada vs a ciegas |
| G12 | **Fin de carrera / retiro** | No existe: la edad sube indefinidamente | **Alto** |
| G13 | Sistema de **logros/achievements** aparte de trofeos | No existe | Bajo |

### 6.3 Debilidades propias de ELBARRIO detectadas en el código

| # | Problema | Ubicación |
| --- | --- | --- |
| D1 | **Los atributos nunca cambian.** `close_season` sube reputación y resetea forma/fatiga, pero `technical`/`mental`/`physical` no evolucionan jamás. No hay crecimiento ni declive por edad, ni potencial. | `modules/simulation/season.py:348-396` |
| D2 | **`player.age += 1` sin techo.** No hay retiro ni declive; una carrera puede llegar a los 60 años. | `season.py:380` |
| D3 | **`caps` siempre 0.** El campo existe y el frontend lo muestra. | `player/factory.py:122` |
| D4 | **Catálogo de eventos corto**: 19 eventos con máximo 3 por temporada → repetición rápida. | `events/library.py` |
| D5 | Sin persistencia de usuario ni autenticación (ya en el roadmap). | — |
| D6 | Sin OVR agregado: imposible mostrar progresión en una sola cifra. | `schemas.py:127-158` |

### 6.4 Lo que ELBARRIO ya hace mejor y no debe perderse

Partido a partido con convocatoria previa, calendario multi-competición con fases y clásicos, tabla de posiciones real, contratos con años/salario/cláusula, cadenas de eventos con consecuencias diferidas, sanciones, ruleta de hitos, premios individuales, relaciones (DT, compañeros, afición, prensa, familia), estados (forma, moral, fatiga, condición, reputación, felicidad, presión).

---

## 7. Propuesta

**Tesis:** no copiar Copero. ELBARRIO ya tiene la simulación profunda que a Copero le falta; lo que le falta a ELBARRIO es **legibilidad de la progresión, ritmo elegible y cierre**. La propuesta es añadir la capa de Copero encima del motor de ELBARRIO, sin sacrificar el partido a partido.

### P1 — Ritmo de carrera elegible (`careerPace`)

Cuatro ritmos en lugar de tres, porque ELBARRIO tiene un nivel que Copero no:

| Ritmo | Unidad de avance | Público |
| --- | --- | --- |
| `match` | partido a partido (el actual) | el jugador que quiere el detalle |
| `season` | 1 temporada por decisión (≈ Intensa) | equilibrado |
| `biennial` | 2 temporadas (≈ Normal) | casual |
| `express` | 3 temporadas (≈ Exprés) | partida rápida |

El motor no cambia: los ritmos ≠ `match` ejecutan el bucle de partidos existente en batch en el servidor y devuelven un **resumen de tramo** (stats agregadas, títulos, hitos, eventos que se dispararon). Es una capa de orquestación, no una simulación paralela — evita el riesgo clásico de tener dos motores que divergen.

### P2 — OVR y valor de mercado derivados

- `overall`: función determinista de atributos ponderada por posición. **Derivada, nunca almacenada**, para que no pueda desincronizarse.
- `marketValue`: función de `overall`, edad, prestigio de liga, forma y reputación. Es el marcador emocional que Copero explota.
- Ambos entran en `SeasonSnapshot` para poder dibujar la curva histórica.

### P3 — Progresión y declive de atributos (arregla D1)

- `potential` oculto por jugador, generado en la creación.
- Crecimiento por temporada en función de minutos jugados, rating medio, edad y distancia al potencial.
- Declive físico desde ~30 (`pace`, `stamina`, `agility`, `jumping`) compensado por crecimiento mental (`composure`, `vision`, `leadership`) hasta ~34.

### P4 — Fin de carrera (arregla D2)

- Ventana de retiro 33-40, con probabilidad creciente según declive, minutos y lesiones; retiro forzado a los 40.
- Evento explícito de decisión "Retirarse / Un año más" cuando la probabilidad supera un umbral.
- Pantalla final: palmarés, curva de OVR, mapa de clubes, totales de club y selección, veredicto de carrera.

### P5 — Selección nacional (arregla D3, cierra el roadmap)

- Convocatoria según reputación, OVR relativo y minutos.
- `caps`/`goals` internacionales acumulados.
- Torneos de selección cada 2 años (continental) y cada 4 (mundial), con trofeos propios.
- Evento de nacionalidad alternativa al estilo del "abuelo".

### P6 — Timeline de carrera (G2)

Componente que sustituye/envuelve a `SeasonHistory`: eje de edad completo desde la edad inicial hasta 39, filas pasadas con club/OVR/PJ/Gls/Ast, fila actual resaltada, futuras en `?`. Badges por fila: trofeo, descenso, ascenso, préstamo, lesión grave.

### P7 — Momento de celebración (G3, G4)

Overlay bloqueante al cerrar temporada cuando hay hito: trofeo (dorado, partículas), descenso (rojo), ascenso (verde), premio individual. Encolable si hay varios. Es barato de implementar y es lo que más eleva la percepción del juego.

### P8 — Decisiones con probabilidad explícita (G11)

Extender `EventChoice` con `outcomes: [{weight, label, effects}]` y renderizar "65% +4 OVR / 35% −3 OVR" en la tarjeta. Mantener compatibilidad: si un `choice` no declara `outcomes`, se aplica `effects` como hoy (determinista).

### P9 — Ascensos y descensos (G5)

Si el club termina en zona de descenso, baja de división y arrastra al jugador (o dispara ventana de traspaso). Se apoya en `build_league_table`, que ya existe.

### P10 — Ampliar el catálogo de eventos (D4)

De 19 a 50+, con las categorías nuevas que Copero muestra y ELBARRIO no cubre: formación/estudios, concentración extra, cambio de nacionalidad, regreso de préstamo, debut, capitanía, renovación, testimonio, lesión de larga duración.

---

## 8. Arquitectura propuesta

Sin romper la estructura actual. Módulos nuevos en gris:

```
backend/src/app/modules/
├── career/service.py          + orquesta el ritmo (pace)
├── pacing/                    ★ NUEVO
│   ├── engine.py                 avanza N temporadas ejecutando el motor real
│   └── summary.py                agrega el resumen de tramo
├── player/
│   ├── factory.py             + genera `potential`
│   ├── rating.py              ★ NUEVO  overall(position, attrs)
│   ├── valuation.py           ★ NUEVO  marketValue(...)
│   └── progression.py         ★ NUEVO  crecimiento y declive por temporada
├── national/                  ★ NUEVO
│   ├── selection.py              convocatoria y caps
│   └── tournaments.py            continental / mundial
├── retirement/                ★ NUEVO
│   └── service.py                probabilidad, decisión y resumen final
├── simulation/season.py       + ascensos/descensos, engancha progression
├── events/library.py          + outcomes probabilísticos, +30 eventos
└── milestones/                ★ NUEVO
    └── service.py                cola de hitos celebrables
```

**Contrato API (aditivo, sin romper clientes):**

- `CreateCareerPayload.pace: "match" | "season" | "biennial" | "express" = "match"`
- `POST /careers/{id}/advance-chunk` → avanza un tramo completo según el ritmo, devuelve `CareerSession` + `ChunkSummary`
- `Player.overall: int`, `Player.marketValue: float`, `Player.potential` (oculto al cliente)
- `CareerSession.pendingMilestones: list[Milestone]` — cola de celebraciones
- `CareerSession.retirementOffer: RetirementOffer | None`
- `EventChoice.outcomes: list[WeightedOutcome]` (opcional)
- `SeasonSnapshot.overall`, `.marketValue`, `.leaguePosition`, `.nationalCaps`

**Frontend:**

```
frontend/src/modules/
├── creation/steps/PaceStep.tsx        ★ elegir ritmo
├── career/
│   ├── CareerTimeline.tsx             ★ eje 16→39
│   ├── MilestoneOverlay.tsx           ★ celebración
│   ├── ChunkSummaryPanel.tsx          ★ resumen de tramo (ritmos no-match)
│   ├── NationalTeamPanel.tsx          ★ selección
│   ├── RetirementScreen.tsx           ★ cierre de carrera
│   └── EventPanel.tsx                 + probabilidades por opción
```

**Invariantes de diseño a respetar:**

1. Un solo motor de simulación. Los ritmos son batching, nunca una simulación alternativa.
2. `overall` y `marketValue` derivados en cada respuesta, jamás persistidos como fuente de verdad.
3. Toda feature nueva debe funcionar en los cuatro ritmos.
4. El modo `match` sigue siendo el modo por defecto y de referencia para los tests.

---

## 9. Plan de implementación

Por fases, cada una entregable y testeable de forma independiente.

### Fase 1 — Legibilidad de la progresión (base de todo lo demás)
1. `player/rating.py`: `overall` por posición + tests de rango y monotonía.
2. `player/valuation.py`: `marketValue` + tests.
3. Exponer ambos en `Player` y `SeasonSnapshot`.
4. Frontend: OVR y valor en `PlayerCard`, curva en `SeasonHistory`.

### Fase 2 — Progresión real y retiro (arregla D1 y D2)
5. `potential` en `factory.py`.
6. `player/progression.py` enganchado en `close_season`.
7. `retirement/service.py` + `RetirementOffer` + endpoint de decisión.
8. `RetirementScreen.tsx` con palmarés y veredicto.
9. Tests: una carrera completa 16→retiro produce curva creciente-decreciente y termina.

### Fase 3 — Momento y timeline (el salto de percepción)
10. `milestones/service.py` + cola `pendingMilestones`.
11. `MilestoneOverlay.tsx` (trofeo / descenso / ascenso / premio).
12. `CareerTimeline.tsx` con eje completo y badges.
13. Ascensos y descensos en `season.py`.

### Fase 4 — Ritmo elegible (la feature de Copero)
14. `pacing/engine.py` + `pacing/summary.py`.
15. `POST /advance-chunk` y `pace` en la creación.
16. `PaceStep.tsx` y `ChunkSummaryPanel.tsx`.
17. Tests: las cuatro velocidades sobre la misma semilla producen carreras coherentes entre sí.

### Fase 5 — Selección nacional (cierra el roadmap)
18. `national/selection.py` (convocatoria, caps).
19. `national/tournaments.py` (continental y mundial, trofeos).
20. `NationalTeamPanel.tsx`; evento de nacionalidad alternativa.

### Fase 6 — Contenido y decisión informada
21. `outcomes` probabilísticos en `EventChoice` + render de porcentajes.
22. Ampliar la librería a 50+ eventos.
23. Ilustración por evento y rama (opcional, mejora de presentación).

**Orden recomendado:** 1 → 2 → 3 → 4 → 5 → 6. Las fases 1-3 son las que más elevan el juego con menos riesgo; la 4 es la que aporta la identidad de Copero; la 5 cierra un pendiente ya declarado del roadmap.

---

## 10. Verificabilidad

Toda conclusión de este informe se puede comprobar sin releer los 14 MB:

```bash
# regenerar CLEAN/ y CORPUS/ desde RAW
python3 research/copero/tools/clean.py   # (script usado en esta investigación)

# trofeos y hitos (solo viven en HTML)
rg -o 'aria-label="[^"]+"' research/copero/RAW/*/carrera_*/*_estado.html \
  | grep -Ei 'copa|liga|premier|descenso|cup|coppa'

# probabilidades de eventos
rg -o 'aria-label="[^"]*%[^"]*"' research/copero/RAW/*/carrera_*/*.html

# ejes de edad por modo
grep -oE '^[0-9]{2}$' research/copero/CLEAN/expres/carrera_1/008_estado.md | sort -nu
```
