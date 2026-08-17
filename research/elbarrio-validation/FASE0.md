# FASE 0 — Auditoría, prueba y estabilización del modo carrera de ELBARRIO

**Fecha:** 2026-08-16 · **Alcance:** diagnóstico. No se implementó ninguna mejora P1-P10 ni cambio funcional.
**Cambios realizados en el repositorio:** únicamente instrumentación de pruebas en `research/elbarrio-validation/` (3 scripts + reportes). Cero líneas modificadas en `backend/src` y `frontend/src`.

## Cómo leer este informe

Cada hallazgo lleva dos etiquetas independientes:

| Severidad | Significado |
|---|---|
| **CRÍTICO** | Rompe un invariante del usuario, corrompe datos o pierde progreso |
| **ALTO** | Degrada gravemente la experiencia o bloquea producción |
| **MEDIO** | Comportamiento incorrecto pero tolerable a corto plazo |
| **BAJO** | Cosmético |

| Confirmación | Significado |
|---|---|
| **EJECUCIÓN** | Reproducido corriendo el sistema y midiendo el resultado |
| **CÓDIGO** | Causa raíz localizada y leída en el fuente |
| **INFERIDO** | Deducido de evidencia parcial, no reproducido aún |
| **PENDIENTE** | Falta reproducir |

Los hallazgos con **EJECUCIÓN + CÓDIGO** son los más accionables: se sabe qué pasa, dónde y por qué.

---

## 1. Arquitectura real (no la documentada)

```
┌─────────────────────── NAVEGADOR ───────────────────────┐
│  React 18 + Vite 6 + TS                                 │
│  Zustand store  ──persist──▶  localStorage               │  ◀── FUENTE DE VERDAD DE FACTO
│       │                                                  │
│       └── fetch a  /api/...  (ruta RELATIVA)             │
└──────────────────────────┬──────────────────────────────┘
                           │ dev: proxy de Vite → localhost:8000
                           │ prod: NO EXISTE reescritura
┌──────────────────────────▼──────────────────────────────┐
│  FastAPI                                                 │
│   routers/careers.py  →  modules/career/service.py       │
│                            ├── simulation/match.py       │
│                            ├── simulation/season.py      │
│                            ├── events/ · awards/         │
│                            └── transfers/ · roulette/    │
│  SQLAlchemy 2.0 sync                                     │
└──────────────────────────┬──────────────────────────────┘
                           │
              tabla ÚNICA: career_sessions
              (columnas JSON: player, history, seasonProgress, …)
              SQLite en dev · PostgreSQL en docker-compose
              SIN Alembic: solo Base.metadata.create_all
```

**Hechos relevantes que contradicen lo que se asume del sistema:**

1. **El backend es correctamente sin estado.** Toda la partida vive en una fila de `career_sessions`. Verificado destruyendo y reconstruyendo el `engine` de SQLAlchemy en caliente: el estado se recuperó byte a byte idéntico. **No hay nada en RAM que se pierda al reiniciar.**
2. **El frontend, en cambio, sí es autoritativo de facto.** Nunca hace `GET /careers/{id}` al montar. El estado que ves es el de `localStorage`.
3. **No hay migraciones.** `alembic` está en las dependencias pero no se usa. Cualquier cambio de forma del JSON rompe partidas guardadas en silencio.
4. **Una sola tabla, sin columna de versión.** No hay bloqueo optimista, ni ETag, ni `updated_at` comparable.
5. `RECENT_MATCH_LIMIT = 8` (`backend/src/app/modules/career/service.py:48`) trunca `recentMatches` a los últimos 8 partidos. **Tres subsistemas leen de esa lista truncada como si fuera el historial completo.** Es el origen de 3 bugs críticos independientes.

---

## 2. Flujo real frontend ↔ backend

Estado de la máquina, en orden de prioridad de resolución:

```
pendingRoulette → pendingTransferWindow → pendingEvent → play-match → advance-season
```

Endpoints observados en tráfico real:

| Método | Ruta | Uso real |
|---|---|---|
| POST | `/api/careers` | crear carrera |
| GET | `/api/careers/{id}` | **el frontend NUNCA lo llama** (ver B1) |
| POST | `/api/careers/{id}/play-match` | jugar 1 partido |
| POST | `/api/careers/{id}/advance-season` | cerrar temporada |
| POST | `/api/careers/{id}/events/{eid}/choose` | resolver evento |
| POST | `/api/careers/{id}/transfer` | resolver mercado |

**Todas las respuestas devuelven el objeto de carrera completo.** Eso es bueno: cada POST es una oportunidad de resincronizar. El problema es que entre POST y POST nadie sincroniza, y la UI trata su copia local como verdad.

---

## 3. Bugs confirmados

### B1 — El frontend nunca lee el estado del servidor · CRÍTICO · EJECUCIÓN + CÓDIGO

Al recargar el navegador la aplicación se hidrata desde `localStorage` y **no emite ningún `GET /careers/{id}`**. Reproducido tres veces:

- Recarga completa con el servidor en el partido 5: la UI mostraba `FECHA 2 / 28` y anunciaba *"Próximo: … vs Santa Fe"* cuando el siguiente fixture real era el partido 6. El único GET del log de red fue el que emití yo a mano desde la consola.
- **Con el backend apagado** (conexión rechazada), la app renderizó la carrera entera con normalidad: fecha, tabla de liga, convocatoria y botón "JUGAR" habilitado. Ni un indicador de carga, ni un error, ni un aviso.
- Avancé 3 partidos desde "otro dispositivo" (curl). La UI seguía en fecha 6. Al pulsar JUGAR, saltó directamente a la pantalla del evento con `PARTIDOS 4` y `1 gol`: **el usuario nunca vio el partido 7, ni su narrativa, ni el gol que marcó.** El estado se corrigió en silencio saltándose pasos.

**Este es el bug que explica el síntoma histórico de Vercel/Render.** No es que el backend pierda estado en RAM (no lo pierde, ver B7-diag): es que el frontend nunca lo pide, así que la partida parece existir mientras el `localStorage` esté vivo y parece corromperse en cuanto se abre desde otro navegador o dispositivo.

### B2 — `player.matchesPlayed` no cuadra con la suma de temporadas · CRÍTICO · EJECUCIÓN + CÓDIGO

Falla en **24 de 24 carreras**, sin excepción (invariante I03). Ejemplos: ST con 264 acumulados frente a 358 sumados; LW con 188 frente a 450.

Causa raíz exacta:

- `backend/src/app/modules/simulation/match.py:231-254` — cuando el jugador queda en el banquillo (`minutes == 0`) la función hace un `return` temprano y **nunca llega a la línea 308** (`player.matchesPlayed += 1`).
- `backend/src/app/modules/career/service.py:191` — `progress.matchesPlayed += 1` sí se incrementa siempre.
- `backend/src/app/modules/simulation/season.py:386` — el snapshot guarda `matchesPlayed=progress.matchesPlayed`.

Resultado: el contador de carrera cuenta **apariciones**, el de temporada cuenta **convocatorias**. Con un 31,2 % de partidos en el banquillo medido, la desviación es estructural y crece cada temporada.

Visible para el usuario: la ficha del jugador decía `PARTIDOS 3` mientras la temporada decía `6 / 28`.

### B3 — Marcador y resultado incoherentes · CRÍTICO · EJECUCIÓN + CÓDIGO

8 casos en 12.174 partidos: marcador `1-0` etiquetado como empate. Narrativa literal generada por el motor:

> *"Empataron 1-0 contra Sevilla de local. Jugaste 26' entrando desde el banco, clavaste 1 gol."*

Causa raíz en `backend/src/app/modules/simulation/match.py:289-294`: cuando el jugador marca más goles que los que el simulador de marcador asignó al equipo, se sube `gf` a `goals` — pero el resultado solo se recalcula si era `"L"`. Si era `"D"`, se queda en `"D"` con el marcador ya desempatado.

### B4 — La tabla de liga se calcula sobre 8 partidos · CRÍTICO · EJECUCIÓN + CÓDIGO

`backend/src/app/modules/simulation/season.py:275-276` suma goles a favor y en contra recorriendo `progress.recentMatches`, que está truncada a 8 elementos. Medido: la tabla declaraba `PJ=30 GF=3 GC=11` cuando los partidos reales daban `PJ=30 GF=40 GC=67`. Los puntos sí coincidían (22), porque se llevan en contadores aparte.

### B5 — Finales ganadas que no otorgan trofeo · CRÍTICO · EJECUCIÓN + CÓDIGO

Mismo origen: `_knockout_trophies` (`season.py:319-327`) recorre `recentMatches`. Si la final de copa cayó fuera de los últimos 8 partidos, el trofeo desaparece. 4 casos detectados (FA Cup, Copa do Brasil).

Además, y por separado: **la Champions League no tiene eliminatorias.** `season.py:169-199` genera exactamente 6 partidos de `"League phase"` y nada más. En 360 temporadas se jugaron 780 partidos de Champions, **jamás una final, cero títulos continentales**.

### B6 — Pérdida de escrituras concurrentes · CRÍTICO · EJECUCIÓN

8 peticiones `play-match` simultáneas (8 hilos, barrera de sincronización) → **8 respuestas HTTP 200 y un solo partido persistido. 7 partidos perdidos.** El usuario ve 8 narrativas con sus goles y luego se evaporan.

Causa: lectura-modificación-escritura sin bloqueo optimista ni versión de fila. `advance-season` pasó la misma prueba bajo SQLite, pero eso no lo exculpa: SQLite serializa las escrituras a nivel de fichero. **Bajo PostgreSQL el riesgo es mayor, no menor** (pendiente de reproducir).

### B18 — Un doblete es matemáticamente imposible · CRÍTICO · EJECUCIÓN + CÓDIGO

En 12.174 partidos el máximo de goles en un partido fue **1**. Distribución completa: `{0 goles: 11.627, 1 gol: 547}`. Cero dobletes, cero hat-tricks, jamás.

Causa raíz aritmética en `match.py:267-274`:

```python
expected_goals = goal_rate * minute_factor * (0.6 + shot_quality * 1.4)
goals = 0
while expected_goals > 0:
    if r.random() < min(0.85, expected_goals):
        goals += 1
    expected_goals -= 1
```

El bucle se ejecuta `ceil(expected_goals)` veces. Con `goal_rate` máximo `0.42` (ST), `minute_factor ≤ 1` y `shot_quality ≤ 1`, el techo absoluto es `0.42 × 1.0 × 2.0 = 0.84 < 1`. **El bucle corre exactamente una vez, siempre.** Lo mismo ocurre con las asistencias (techo `0.54`).

Consecuencia medida: un delantero promedia **3,96 goles por temporada** y el máximo en 45 temporadas de ST fue 9. Es un techo goleador irreal para un juego de carrera.

### B26 — Ganar la semifinal otorga el trofeo · CRÍTICO · CÓDIGO

`season.py:322`:

```python
is_final = "final" in match.stageDisplay.lower() or match.stageDisplay.lower() == "final"
```

Los `stageDisplay` generados son `"Round of 16"`, `"Quarterfinal"`, `"Semifinal"`, `"Final"` (`season.py:137`). La comprobación de subcadena hace que **`"final" in "semifinal"` sea verdadero**: ganar la semifinal ya entrega la copa. La segunda mitad de la condición (`== "final"`) es código muerto.

### B19 — El backend no arranca con la variable CORS en formato natural · CRÍTICO · EJECUCIÓN + CÓDIGO

Poner `CORS_ORIGINS="https://elbarrio.vercel.app"` en el panel de Render — el formato que cualquiera escribiría — lanza `pydantic_settings.exceptions.SettingsError` y **el proceso muere al arrancar**. `cors_origins` es `list[str]`, así que pydantic-settings exige JSON: `'["https://elbarrio.vercel.app"]'`.

Y el valor por defecto (`backend/src/app/config.py:8-13`) es únicamente localhost, con `allow_credentials=True`. Un preflight desde un dominio de Vercel responde HTTP 400 *"Disallowed CORS origin"*.

### B10 — Los atributos del jugador no evolucionan al cerrar temporada · ALTO · EJECUCIÓN + CÓDIGO

En 9 de 24 carreras, `shooting`, `stamina` y `vision` eran **idénticos byte a byte tras 15 temporadas**. `close_season` (`season.py:348-390`) toca reputación, fatiga, fitness, forma y edad — ningún atributo técnico, mental ni físico. La edad final es siempre exactamente 32 (17 + 15) y **no existe retiro**.

Contraste con la referencia Copero: allí un jugador pasa de OVR 50 a 63 entre los 16 y los 19 años, y la progresión es el eje narrativo del modo.

### B11 — La tabla de liga es una proyección determinista, no una simulación · ALTO · EJECUCIÓN

Tras 5 partidos, Nacional, América, Junior y Millonarios tenían **exactamente el mismo registro**: `PJ=5 G=3 E=1 P=1 GF=10 Pts=10`. En pantalla, cinco equipos seguidos con "4 pts · DG 2". Aritméticamente imposible: si todos ganan 3 de 5, no hay suficientes derrotas en el sistema.

### B20 — Producción no puede funcionar como está montada · ALTO · EJECUCIÓN + CÓDIGO

El frontend pide rutas **relativas** (`/api/...`). En desarrollo funciona solo gracias al proxy de `frontend/vite.config.ts`. En un despliegue estático de Vercel, `/api` resuelve contra el dominio de Vercel, donde no hay nada. En el repositorio **no existen** `.env`, `vercel.json` ni `render.yaml`; solo `.env.example` con `VITE_API_URL=http://localhost:8000/api`, variable que además no se usa en el código de red.

### B24 — Los errores de red fallan en silencio absoluto · ALTO · EJECUCIÓN

Con el backend caído, pulsar "JUGAR" produce un `POST` con **HTTP 500** y en la interfaz no ocurre absolutamente nada: sin toast, sin mensaje, sin cambio de estado, sin una línea en la consola. El usuario concluye que el botón está roto.

### B25 — `play-match` bloqueado responde 200 sin hacer nada · ALTO · EJECUCIÓN

Con un evento pendiente sin resolver, `POST /play-match` devuelve **HTTP 200 y el estado sin modificar**. El cliente no puede distinguir "jugué un partido" de "no pasó nada". Debería ser un 409 con un cuerpo que explique qué falta resolver.

### B21 — Inflación de trofeos · MEDIO · EJECUCIÓN + CÓDIGO

441 trofeos en 360 temporadas: **1,23 por temporada**. Un central ganó 23 títulos en 15 temporadas. Dos causas de código: B26 (la semifinal cuenta como final) y `season.py:150` (la copa nacional genera siempre las 4 rondas fijas — nunca te eliminan antes).

### B22 — La reputación degenera a los extremos · MEDIO · EJECUCIÓN + CÓDIGO

`reputation_gain = (average_rating - 6.0) * 8 + goals * 0.5` (`season.py:373`), acumulado y recortado a [0, 100]. Como las medias de rating están comprimidas entre 5,94 y 6,25, el signo del término dominante casi nunca cambia: la reputación colapsa a 0 o se satura en 100. Un portero con 12 títulos en 15 temporadas terminó con reputación 0.

### B23 — Detalles de interfaz · BAJO/MEDIO · EJECUCIÓN

- El indicador de pasos va uno por detrás (muestra "2. ORIGEN" estando en el paso 3, POSICIÓN).
- La Serie A se dibuja con 6 estrellas; todas las demás ligas con 5.
- Texto sin traducir: `"#10 · Pie right"`.
- El contador de partidos arranca en `FECHA 0 / 28`.
- El botón "Siguiente" se deshabilita sin decir por qué.

---

## 4. Bugs potenciales (no confirmados)

| ID | Sev. | Descripción | Estado |
|---|---|---|---|
| P1 | CRÍTICO | Pérdida de escrituras en `advance-season` bajo PostgreSQL. La prueba pasó en SQLite, que serializa por fichero; en Postgres con varios workers de uvicorn la ventana de carrera es real. | PENDIENTE |
| P2 | ALTO | Ausencia total de migraciones. Cualquier cambio de forma de los JSON rompe las partidas guardadas sin error visible: pydantic rellenará con defaults. | INFERIDO |
| P3 | ALTO | Cold start de Render (30-60 s en el plan gratuito) contra un `fetch` sin timeout ni reintento: el primer clic tras la inactividad cae en B24 (fallo mudo). | INFERIDO |
| P4 | MEDIO | Dos pestañas abiertas con la misma carrera: cada una con su `localStorage`, gana la última que escriba. Es B1 amplificado. | PENDIENTE |
| P5 | MEDIO | `allow_credentials=True` con `allow_methods=["*"]` es innecesariamente permisivo para una API sin cookies. | CÓDIGO |

---

## 5. Resultados de las simulaciones

**24 carreras × 15 temporadas = 360 temporadas, 12.174 partidos, 0 errores de ejecución, 0 bloqueos.** Perfiles: ST, CAM, CM, CB, GK, LW, CDM, RB, arrancando en 6 ligas distintas.

El motor **no se rompe**: no lanza excepciones, no se atasca, no produce estados imposibles de continuar. Los problemas son de corrección, no de estabilidad.

### Distribución por posición (media por temporada, 45 temporadas cada una)

| Pos | Goles | Asist. | Minutos | Partidos | Rating |
|---|---|---|---|---|---|
| ST | 3,96 | 2,64 | 1249 | 28,8 | 6,25 |
| LW | 3,38 | 3,82 | 1391 | 33,7 | 6,17 |
| CAM | 2,82 | 5,89 | 1503 | 36,7 | 6,24 |
| CM | 0,69 | 2,58 | 1037 | 32,3 | 6,06 |
| CDM | 0,60 | 1,49 | 1318 | 36,0 | 6,03 |
| RB | 0,36 | 1,11 | 1256 | 34,8 | 6,01 |
| CB | 0,33 | 0,18 | 793 | 35,1 | 5,96 |
| GK | 0,02 | 0,02 | 1118 | 33,2 | 5,94 |

**La jerarquía posicional es correcta** — es lo que se esperaría de un motor de fútbol. Los problemas son de escala y de dispersión:

- **Los totales son demasiado bajos**: 3,96 goles por temporada para un delantero, techo histórico de 9.
- **Los ratings están comprimidos** en una banda de 0,31 puntos entre el mejor y el peor perfil. No hay diferenciación perceptible.
- **CB genera 0,18 asistencias por temporada** — prácticamente nunca participa en el juego ofensivo.

### Resultados de partido

| | | |
|---|---|---|
| Victorias | 6.221 | 51,1 % |
| Derrotas | 4.711 | 38,7 % |
| **Empates** | **1.242** | **10,2 %** |

El 10,2 % de empates es irreal (en ligas reales ronda el 25 %). Marcadores más frecuentes: `2-1`, `3-0`, `3-1`, `2-0` — el motor produce partidos con demasiados goles y demasiado pocos empates.

**31,2 % de los partidos en el banquillo** con 0 minutos. Es una cifra alta y, combinada con B2, es la causa directa del descuadre de partidos.

---

## 6. Diagnóstico de goles y estadísticas

Esta era la preocupación central. El resultado es **mejor de lo temido en acumulación y peor de lo temido en generación**.

### Lo que está bien

| Invariante | Resultado |
|---|---|
| `career.total_goals == Σ goles de todas las temporadas` | ✅ **360/360 temporadas** |
| `career.total_assists == Σ asistencias históricas` | ✅ **360/360** |
| `season.goals == Σ goles de los partidos de la temporada` | ✅ **12.174/12.174 partidos** |
| `match.goals <= match.goalsFor` | ✅ sin excepciones |
| Las estadísticas acumuladas nunca decrecen | ✅ |
| Una llamada a `play-match` avanza exactamente 1 partido | ✅ (secuencialmente) |
| Una llamada a `advance-season` añade 1 snapshot y +1 edad | ✅ |

**El bug histórico de acumulación de goles no está presente.** Los goles y las asistencias cuadran perfectamente en los tres niveles (partido → temporada → carrera). Esto lo verifiqué sin asumir nada: recalculé cada suma desde los partidos individuales.

### Lo que está mal

1. **`matchesPlayed` no cuadra en ninguna carrera** (B2). Es el único contador roto, y lo está en el 100 % de los casos.
2. **La generación de goles tiene un techo estructural de 1 por partido** (B18). Los números cuadran entre sí, pero el motor no puede producir un doblete.
3. **El marcador puede contradecir el resultado** (B3).

### Sobre las llamadas repetidas

- Repetir `GET` es puro: 6 llamadas consecutivas devolvieron respuestas idénticas. ✅
- Repetir `POST /play-match` **no es idempotente**: cada llamada juega otro partido. Es semánticamente defendible (es una acción, no una consulta), pero significa que un doble clic o un reintento de red juegan partidos de más. En la interfaz probé triple clic sobre "JUGAR": solo se emitió **una** petición, así que hay una protección en el cliente. Es la única barrera, y es del lado equivocado.
- Una recarga del navegador **no** modifica estadísticas. ✅

---

## 7. Diagnóstico de persistencia

**El backend está bien.** Esta es la conclusión más importante de esta sección y contradice la hipótesis inicial.

| Prueba | Resultado |
|---|---|
| Reconstruir el `engine` de SQLAlchemy en caliente (simula reinicio de proceso) y releer la carrera | ✅ **Estado idéntico byte a byte** |
| Recuperar carrera por ID desde un cliente nuevo | ✅ |
| Carrera inexistente | ✅ HTTP 404 correcto |
| Continuar la simulación tras el reinicio | ✅ |
| `GET` repetido | ✅ 6 respuestas idénticas |

**No hay ni un solo dato de la partida viviendo solo en RAM.** El requisito del usuario — *"la fuente de verdad debe ser persistente y recuperable"* — **ya se cumple en el backend**.

El problema de persistencia percibido es enteramente del frontend (B1): la fuente de verdad efectiva es `localStorage`, y esa sí se pierde al cambiar de navegador, de dispositivo o al limpiar los datos del sitio.

**Riesgo real pendiente:** ausencia de migraciones (P2). La forma de los JSON es un contrato implícito sin versionar.

---

## 8. Diagnóstico de clubes y competiciones

**Integridad referencial: correcta.** Ningún `club_id` persistido apunta a una entidad inexistente, en 360 temporadas con traspasos (invariante I10 limpio). Todos los `league_id` resuelven. Los traspasos mueven al jugador de forma consistente.

**Calendario: correcto en estructura.** Los fixtures se generan de forma determinista con `random.Random(f"{player.id}:{season_number}:{player.clubId}")`, lo que garantiza reproducibilidad. `snapshot.matchesPlayed == número de fixtures` se cumple siempre. Se juegan todas las competiciones del calendario (I20 limpio).

**Competiciones: el modelo está incompleto, no simplificado por error.**

| Problema | Detalle |
|---|---|
| Copa nacional sin eliminación | Siempre se generan las 4 rondas (`Round of 16` → `Final`). Nunca te eliminan antes. 68/68/68 rondas jugadas en Copa Colombia. |
| Semifinal cuenta como final | B26 |
| Champions/Libertadores sin eliminatorias | Solo 6 partidos de fase de liga. 780 partidos jugados, 0 finales, 0 títulos. |
| Tabla de liga fabricada | B11: los rivales tienen registros idénticos e imposibles. |
| Goles de la tabla sobre 8 partidos | B4 |

Ninguna de estas es una simplificación deliberada bien hecha: son piezas a medio construir. Respetando la instrucción de no simplificar el motor, lo que hace falta es **completarlo**, no recortarlo.

---

## 9. Diagnóstico Vercel / Render

El síntoma histórico ("la carrera parece depender de que el backend de Render siga vivo") tiene **tres causas independientes que se suman**:

| Capa | Problema | ID |
|---|---|---|
| Frontend | Nunca hace `GET` del estado; se hidrata de `localStorage`. Con el backend caído la app se ve perfectamente normal, y al volver salta pasos en silencio. | B1 |
| Red | Peticiones a `/api` relativo, que en dev funciona solo por el proxy de Vite. En Vercel no hay reescritura ni `vercel.json`, así que `/api` no resuelve a ningún sitio. | B20 |
| Backend | `CORS_ORIGINS` en formato natural mata el proceso al arrancar; el valor por defecto solo admite localhost. | B19 |
| UX | Los fallos de red no producen ningún mensaje. El usuario no puede saber que hay un problema de conexión. | B24 |

**Lo que NO es la causa:** el backend no guarda estado en RAM. Sobrevive a un reinicio completo con el estado intacto. Cualquier arreglo que se enfoque en "hacer que Render no se duerma" ataca el síntoma equivocado.

**Orden de arreglo para producción:** B19 (o el backend ni arranca) → B20 (o el frontend no encuentra la API) → B1 (o el estado sigue divergiendo) → B24 (o los fallos siguen siendo invisibles).

---

## 10. Invariantes formales

Los 20 invariantes están implementados y ejecutables en `research/elbarrio-validation/analyze.py`. Estado tras 360 temporadas:

| ID | Sev. | Invariante | Estado |
|---|---|---|---|
| I01 | CRÍTICO | `player.goals == Σ goles de temporadas cerradas` | ✅ |
| I02 | CRÍTICO | `player.assists == Σ asistencias de temporadas cerradas` | ✅ |
| I03 | CRÍTICO | `player.matchesPlayed == Σ snapshot.matchesPlayed` | ❌ **24 violaciones** |
| I04 | CRÍTICO | `snapshot.goals == Σ goles de los partidos de la temporada` | ✅ |
| I05 | CRÍTICO | `result` coincide con el marcador | ❌ **8 violaciones** |
| I06 | CRÍTICO | `match.goals <= match.goalsFor` | ✅ |
| I07 | CRÍTICO | Una llamada a `play-match` avanza exactamente 1 partido | ✅ (secuencial) / ❌ (concurrente, ver B6) |
| I08 | CRÍTICO | Una llamada a `advance-season` añade 1 snapshot y +1 edad | ✅ |
| I09 | ALTO | Las estadísticas acumuladas nunca decrecen | ✅ |
| I10 | ALTO | El club actual existe en el catálogo | ✅ |
| I11 | ALTO | No hay valores negativos en estadísticas | ✅ |
| I12 | ALTO | `progress.matchesPlayed <= progress.matchesTotal` | ✅ |
| I13 | ALTO | `snapshot.season` es estrictamente creciente sin huecos | ✅ |
| I14 | ALTO | `minutos == 0` implica `goles == 0` y `asistencias == 0` | ✅ |
| I15 | MEDIO | El rol previsto en la convocatoria coincide con los minutos reales | ✅ |
| I16 | ALTO | `snapshot.matchesPlayed == nº de fixtures de la temporada` | ✅ |
| I17 | ALTO | Los atributos evolucionan a lo largo de la carrera | ❌ **9 violaciones** |
| I18 | ALTO | La posición en la tabla es coherente con los puntos | ✅ |
| I19 | MEDIO | Cada final ganada produce un trofeo | ❌ **4 violaciones** |
| I20 | ALTO | Se juegan todas las competiciones del calendario | ✅ |

**16 de 20 limpios. 45 violaciones totales.**

Invariantes adicionales que esta auditoría demuestra necesarios y que aún no están implementados:

- **I21** (CRÍTICO): N llamadas concurrentes a `play-match` deben producir exactamente N partidos o rechazos explícitos — nunca 200 silenciosos que se pierden.
- **I22** (CRÍTICO): la tabla de liga debe calcularse sobre **todos** los partidos de la temporada, no sobre `recentMatches`.
- **I23** (ALTO): la suma de partidos jugados por todos los equipos de la tabla debe ser aritméticamente posible.
- **I24** (ALTO): un `POST` bloqueado por estado pendiente debe responder 4xx, no 200.
- **I25** (MEDIO): la distribución de goles por partido debe permitir valores ≥ 2.

---

## 11. Tests existentes

`backend/tests/test_engine.py`: **39 tests, los 39 pasan en 0,26 s.** No hay tests en el frontend.

La cobertura es buena en mecánicas puntuales (fixtures, traspasos, ruleta, eventos, premios, tabla, cierre de temporada) y **nula en exactamente las tres áreas donde están todos los bugs críticos**:

| Área | Tests existentes | Bugs que se escaparon |
|---|---|---|
| Coherencia acumulativa entre partido → temporada → carrera | 0 | B2 |
| Idempotencia y concurrencia | 0 | B6 |
| Coherencia interna de un `MatchResult` | 0 | B3, B18 |
| Ventana `recentMatches` vs historial completo | 0 | B4, B5, B26 |
| Configuración y arranque (CORS, env) | 0 | B19 |
| Frontend (cualquier cosa) | 0 | B1, B20, B24 |

Los 39 tests verifican piezas aisladas; ninguno recorre una carrera completa comprobando que los totales cuadren al final. Ese es el hueco exacto por el que pasaron B2 y B18.

---

## 12. Tests nuevos necesarios

Propuesta priorizada. **Ninguno es costoso**: la suite completa propuesta debería correr en menos de 15 segundos.

### Prioridad 1 — Invariantes de carrera (`backend/tests/test_invariants.py`)

```
test_career_totals_match_season_sums()          # I01, I02, I03 — 1 carrera de 3 temporadas
test_season_goals_match_sum_of_matches()        # I04
test_match_result_consistent_with_score()       # I05 — barrido de 500 partidos simulados
test_match_goals_never_exceed_goals_for()       # I06
test_accumulated_stats_never_decrease()         # I09
test_attributes_evolve_across_seasons()         # I17
```

### Prioridad 2 — Concurrencia e idempotencia (`backend/tests/test_concurrency.py`)

```
test_concurrent_play_match_does_not_lose_updates()   # I21 — 8 hilos, barrera
test_concurrent_advance_season_creates_one_snapshot()
test_play_match_blocked_by_pending_event_returns_409() # I24
test_get_career_is_pure()
```

### Prioridad 3 — Competiciones (`backend/tests/test_competitions.py`)

```
test_league_table_uses_full_season_not_recent_window()  # I22
test_league_table_matches_are_arithmetically_possible() # I23
test_semifinal_win_does_not_award_trophy()              # B26
test_cup_final_outside_recent_window_still_awards()     # B5
test_continental_competition_has_knockout_stages()
```

### Prioridad 4 — Configuración (`backend/tests/test_config.py`)

```
test_cors_origins_accepts_comma_separated_string()   # B19
test_cors_origins_accepts_single_origin()
```

### Prioridad 5 — Frontend

Actualmente cero. Lo mínimo imprescindible:

```
career store: hidrata desde el servidor al montar, no solo desde localStorage  # B1
career store: un fallo de red produce un estado de error visible               # B24
```

### Herramientas de auditoría (mantener, no convertir en CI)

Los tres scripts de `research/elbarrio-validation/` son caros (minutos) y no deben correr en cada commit. Su sitio es una ejecución manual antes de cada release:

- `runner.py` — simula N carreras completas
- `analyze.py` — verifica los 20 invariantes sobre lo simulado
- `robustness.py` — 8 pruebas de concurrencia, pureza y persistencia

---

## 13. Riesgos

| Riesgo | Sev. | Comentario |
|---|---|---|
| Arreglar B2 cambia las estadísticas de las partidas existentes | ALTO | Hay que decidir qué significa `matchesPlayed`: ¿convocatorias o apariciones? Yo recomiendo **apariciones** (es lo que un jugador entiende por "partidos jugados") y añadir `callUps` aparte. Las partidas guardadas necesitarán un recálculo. |
| Arreglar B18 desequilibra todo el balance | ALTO | Subir los goles por partido cambia trofeos, premios, reputación, valor de mercado y ofertas de traspaso en cascada. Requiere recalibrar, no solo tocar la constante. |
| Sin migraciones, cualquier cambio de esquema rompe partidas en silencio | ALTO | P2. Debería resolverse **antes** de tocar la forma de los JSON. |
| Arreglar B4/B5/B26 requiere guardar la temporada completa | MEDIO | `RECENT_MATCH_LIMIT = 8` existe por tamaño de payload. La solución es separar "historial completo persistido" de "ventana enviada al cliente", no subir el límite. |
| B6 bajo PostgreSQL no está medido | MEDIO | La prueba en SQLite no es concluyente. |
| El motor es determinista por semilla | BAJO | Es una virtud (reproducibilidad), pero significa que dos jugadores con el mismo ID y club ven el mismo calendario. |

---

## 14. Cambios concretos recomendados

Cada uno es pequeño y localizado. **No implementados** — este documento es solo el diagnóstico.

| # | Cambio | Archivo | Bug |
|---|---|---|---|
| 1 | Aceptar `CORS_ORIGINS` como cadena separada por comas (validador `field_validator` con `mode="before"`) | `backend/src/app/config.py:8` | B19 |
| 2 | Que el frontend haga `GET /careers/{id}` al montar y trate la respuesta del servidor como autoritativa | store de Zustand | B1 |
| 3 | Definir `VITE_API_URL` y usarla en la capa de red; añadir `vercel.json` con la reescritura o la URL absoluta | `frontend/` | B20 |
| 4 | Mostrar un estado de error visible cuando una petición falla | capa de red del frontend | B24 |
| 5 | Recalcular el resultado tras ajustar `gf`, en lugar de parchear solo el caso `"L"` | `match.py:289-294` | B3 |
| 6 | Contar el partido también cuando `minutes == 0`, o renombrar el contador y separar apariciones de convocatorias | `match.py:231-254` + `season.py:386` | B2 |
| 7 | Sustituir el bucle de goles por un muestreo que permita valores ≥ 2 (Poisson o binomial con más intentos) y recalibrar las tasas | `match.py:267-279` | B18 |
| 8 | Persistir el historial completo de la temporada y calcular tabla y trofeos sobre él; mantener `recentMatches` solo como ventana de presentación | `service.py:48,215` + `season.py:275,319` | B4, B5, B26 |
| 9 | Comparar el identificador de fase (`stage_id == "final"`) en vez de buscar la subcadena `"final"` | `season.py:322` | B26 |
| 10 | Eliminación real en la copa nacional (probabilidad de caer en cada ronda) | `season.py:137-160` | B21 |
| 11 | Añadir eliminatorias y final a la competición continental | `season.py:169-199` | B5 |
| 12 | Simular la tabla de liga en vez de proyectarla, o al menos garantizar coherencia aritmética | `season.py:280-306` | B11 |
| 13 | Progresión y declive de atributos en `close_season`, más retiro | `season.py:348-390` | B10 |
| 14 | Columna `version` con bloqueo optimista; devolver 409 en conflicto | modelo + `service.py` | B6 |
| 15 | Devolver 409 cuando `play-match` está bloqueado por estado pendiente | `service.py:236` | B25 |
| 16 | Subir la tasa de empates y comprimir los marcadores | `_compute_score` | §5 |
| 17 | Introducir Alembic con una migración base antes de tocar la forma de los JSON | `backend/` | P2 |

---

## 15. Orden de reparación recomendado

**Bloque A — Desbloquear producción** (nada más tiene sentido si la app no funciona desplegada)

1. #1 CORS como cadena (B19)
2. #3 URL de la API en producción (B20)
3. #4 Errores de red visibles (B24)
4. #2 El frontend lee del servidor (B1)

**Bloque B — Integridad de datos** (antes de tocar el balance, que los números cuadren)

5. #17 Alembic (P2) — **primero**, para poder cambiar esquemas sin romper partidas
6. #6 `matchesPlayed` (B2)
7. #5 Marcador vs resultado (B3)
8. #14 Bloqueo optimista (B6)
9. #15 409 en acción bloqueada (B25)

**Bloque C — Competiciones** (el bloque de `recentMatches`, todo junto)

10. #8 Historial completo persistido (B4, B5, B26)
11. #9 Comparación por `stage_id` (B26)
12. #10 Eliminación real en copa (B21)
13. #11 Eliminatorias continentales (B5)
14. #12 Tabla de liga coherente (B11)

**Bloque D — Balance del motor** (lo más delicado; requiere recalibración completa)

15. #7 Goles por partido (B18)
16. #16 Empates y marcadores
17. #13 Progresión de atributos y retiro (B10)

**Después de cada bloque:** ejecutar `runner.py` + `analyze.py` sobre 24 carreras y verificar que los invariantes no han retrocedido.

**Solo cuando el Bloque D esté cerrado tiene sentido empezar con P1-P10.** Las mejoras propuestas en `research/copero/INFORME.md` asumen un motor con progresión de atributos, competiciones completas y estadísticas coherentes — tres cosas que hoy no existen.

---

## 16. Evidencia reproducible

Todo está en `research/elbarrio-validation/`.

```
research/elbarrio-validation/
├── runner.py              # simula carreras completas vía TestClient
├── analyze.py             # verifica los 20 invariantes
├── robustness.py          # 8 pruebas de concurrencia/pureza/persistencia
├── runs/                  # 16 MB de estados de carrera crudos
│   └── browser.db         # base de la sesión de navegador
└── reports/
    ├── violations.json    # 45 violaciones con carrera, temporada, partido y narrativa
    ├── distributions.json # distribuciones por posición y censo de 12.174 partidos
    └── robustness.json    # resultados T1-T8
```

**Reproducir la auditoría completa:**

```bash
cd backend && .venv/bin/python ../research/elbarrio-validation/runner.py
.venv/bin/python ../research/elbarrio-validation/analyze.py
.venv/bin/python ../research/elbarrio-validation/robustness.py
```

**Reproducir B6 (pérdida de escrituras) en aislamiento:** `robustness.py`, test T3 — 8 hilos con `threading.Barrier` contra `play-match`.

**Reproducir B1 (el frontend no lee del servidor):**

1. Arrancar backend y frontend, crear una carrera y jugar 5 partidos en la interfaz.
2. `curl -X POST http://127.0.0.1:8000/api/careers/{id}/play-match` tres veces.
3. Sin recargar, pulsar "JUGAR" en la interfaz: salta varios partidos de golpe sin mostrarlos.
4. Variante: matar el backend y recargar la página — la carrera se ve intacta y el botón sigue habilitado.

**Resultados de robustez (T1-T8):**

| Test | Qué comprueba | Resultado |
|---|---|---|
| T1 | `GET` es puro (6 llamadas) | ✅ PASA |
| T2 | `play-match` repetido | ❌ no idempotente (por diseño discutible) |
| T3 | 8 `play-match` concurrentes | ❌ **7 actualizaciones perdidas** |
| T4 | 6 `advance-season` concurrentes | ✅ pasa (bajo SQLite) |
| T5 | Persistencia tras reinicio del engine | ✅ **idéntico byte a byte** |
| T6 | Carrera inexistente | ✅ 404 |
| T7 | Cliente con estado obsoleto | ❌ sin versión ni ETag |
| T8 | Goles de la tabla vs partidos reales | ❌ **B4** |

---

## Resumen ejecutivo

**El motor no está roto: está incompleto y mal conectado.** Corrió 12.174 partidos sin una sola excepción y respeta 16 de 20 invariantes, incluidos los de acumulación de goles y asistencias que eran la principal preocupación.

Los tres problemas de fondo son:

1. **El frontend ignora al servidor** (B1). Es el origen del misterio de Vercel/Render. El backend persiste correctamente; nadie le pregunta.
2. **`recentMatches` truncada a 8 se usa como historial completo** en tres sitios distintos, generando tres bugs críticos independientes (B4, B5, B26).
3. **El motor de goles tiene un techo aritmético de 1 gol por partido** (B18), lo que hace que ninguna carrera pueda resultar memorable.

Los cuatro invariantes que fallan tienen causa raíz localizada en el código, con archivo y línea. Ninguno requiere un rediseño: son entre 3 y 20 líneas cada uno, salvo el rebalanceo del bloque D.

**Recomendación:** ejecutar los bloques A-D en orden antes de abrir P1-P10. El bloque A es de un día y desbloquea producción; el bloque B garantiza que los números no mientan; C y D construyen la base que P1-P10 da por supuesta.
