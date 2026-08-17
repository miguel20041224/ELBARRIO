# Despliegue y variables de entorno

ELBARRIO son dos servicios independientes que hablan por HTTP **cross-origin**:

| Servicio | Dónde vive | Qué necesita saber |
| --- | --- | --- |
| Frontend (React + Vite) | Vercel | la URL absoluta del backend |
| Backend (FastAPI) | Render | qué orígenes acepta por CORS |

No hay proxy en ninguna capa. El frontend siempre llama al backend por su URL
absoluta, en desarrollo igual que en producción, así que un fallo de CORS
aparece en la primera prueba local y no en el despliegue.

---

## Variables por entorno

### Backend

| Variable | Obligatoria | Desarrollo | Producción (Render) |
| --- | --- | --- | --- |
| `ENVIRONMENT` | no | `development` (por defecto) | `production` |
| `DATABASE_URL` | en producción sí | `sqlite:///./elbarrio.db` (por defecto) | cadena de la base de Render, tal cual |
| `CORS_ORIGINS` | en producción sí | por defecto ya cubre `localhost:5173` y `localhost:4173` | `https://tu-app.vercel.app` |
| `CORS_ORIGIN_REGEX` | no | — | `^https://elbarrio-[a-z0-9-]+\.vercel\.app$` para los previews |
| `CORS_ALLOW_CREDENTIALS` | no | `false` | `false` |
| `PORT` | no | — | la inyecta Render; el `Dockerfile` la respeta |

### Frontend

| Variable | Obligatoria | Desarrollo | Producción (Vercel) |
| --- | --- | --- | --- |
| `VITE_API_URL` | **sí** | `http://localhost:8000/api` (ya en `frontend/.env.development`) | `https://tu-api.onrender.com/api` |
| `VITE_API_TIMEOUT_MS` | no | `60000` | `60000` (el plan free de Render tarda ~50 s en despertar) |

Las variables `VITE_*` se **incrustan en el bundle durante el build**, no se leen
en tiempo de ejecución. Cambiarlas exige volver a desplegar el frontend.

---

## Formatos aceptados en `CORS_ORIGINS`

El panel de Render solo ofrece un campo de texto por variable, así que se admiten
las cuatro formas:

```sh
CORS_ORIGINS=https://elbarrio.vercel.app
CORS_ORIGINS=https://elbarrio.vercel.app,https://www.elbarrio.com
CORS_ORIGINS=["https://elbarrio.vercel.app"]
CORS_ORIGINS=*                     # solo para depurar, nunca permanente
```

Reglas:

- El origen es **esquema + host + puerto**, sin ruta ni barra final.
  `https://app.vercel.app` sirve; `https://app.vercel.app/` y `app.vercel.app` no
  (el segundo hace fallar el arranque a propósito, con el motivo en el log).
- El navegador compara el origen carácter a carácter: `https://www.midominio.com`
  y `https://midominio.com` son orígenes distintos. Si usás los dos, poné los dos.
- Los dominios de preview de Vercel cambian en cada commit; para esos está
  `CORS_ORIGIN_REGEX`, no `CORS_ORIGINS`.

---

## Esquema de `DATABASE_URL`

Pegá la cadena tal cual la entrega el proveedor. El backend normaliza el esquema
al arrancar, porque hay dos formas de romper el despliegue con una cadena válida:

| Lo que te dan | Qué usa el backend | Por qué |
| --- | --- | --- |
| `postgres://…` | `postgresql+psycopg://…` | SQLAlchemy 2.0 eliminó el alias `postgres` |
| `postgresql://…` | `postgresql+psycopg://…` | a secas busca `psycopg2`, y la imagen instala `psycopg` (v3) |
| `postgresql+psycopg://…` | igual | ya es el driver correcto |
| `postgresql+asyncpg://…` | igual | driver explícito: se respeta, aunque el motor es síncrono |

El log de arranque imprime el esquema efectivo, así que se ve de un vistazo cuál
quedó.

---

## Desplegar el backend en Render

Con el blueprint (`render.yaml` en la raíz):

1. Render Dashboard → **New** → **Blueprint** → apuntar a este repositorio.
2. Render crea el servicio `elbarrio-api` y la base `elbarrio-db`, e inyecta
   `DATABASE_URL` sola.
3. Rellenar a mano `CORS_ORIGINS` (y `CORS_ORIGIN_REGEX` si querés previews).
   Como todavía no existe el dominio de Vercel, se puede dejar para después del
   primer deploy del frontend.

Manualmente, sin blueprint: servicio web tipo Docker, `dockerfilePath`
`./backend/Dockerfile`, `dockerContext` `./backend`, health check en `/health`,
y las variables de la tabla de arriba.

### Comprobar que arrancó bien

Los logs de Render tienen que mostrar la configuración de red efectiva:

```txt
INFO:     ELBARRIO API arrancando | entorno=production
INFO:     CORS origins permitidos: ['https://elbarrio.vercel.app']
INFO:     CORS origin regex: ^https://elbarrio-[a-z0-9-]+\.vercel\.app$
INFO:     CORS allow_credentials: False
INFO:     Base de datos: postgresql+psycopg
INFO:     Application startup complete.
```

Si aparece `WARNING: CORS_ORIGINS sigue en el valor por defecto (localhost)`, el
frontend desplegado va a recibir un error de CORS en cuanto cargue.

Si aparece `WARNING: DATABASE_URL apunta a SQLite en producción`, las carreras se
borran en cada redeploy: el disco de Render es efímero salvo que montes un
volumen.

---

## Desplegar el frontend en Vercel

1. Importar el repositorio, con **Root Directory** = `frontend`.
2. `frontend/vercel.json` ya define framework, build, `outputDirectory` y el
   rewrite de SPA (sin él, recargar `/career` devuelve 404).
3. Definir `VITE_API_URL` en Settings → Environment Variables, con `/api` al
   final: `https://elbarrio-api.onrender.com/api`.
4. Desplegar.

Si falta `VITE_API_URL`, el build **falla a propósito** con el motivo en los logs
de Vercel, en vez de generar un bundle roto que solo se nota en el navegador del
usuario.

### Orden recomendado la primera vez

El frontend necesita la URL del backend y el backend necesita el dominio del
frontend, así que:

1. Desplegar el backend (`CORS_ORIGINS` puede quedar vacío de momento).
2. Desplegar el frontend con `VITE_API_URL` apuntando al backend.
3. Volver a Render, poner `CORS_ORIGINS` con el dominio de Vercel y esperar el
   reinicio.
4. Ejecutar el smoke test (abajo).

---

## Verificar el despliegue

```sh
./scripts/smoke-network.sh https://elbarrio-api.onrender.com https://elbarrio.vercel.app
```

Comprueba salud, preflight desde el frontend, rechazo de un origen ajeno, crear y
releer una carrera, y el 404 de una carrera inexistente. Crea una carrera de
prueba; no borra nada.

---

## Desarrollo local

```sh
# backend (puerto 8000)
cd backend
poetry install
poetry run uvicorn app.main:app --reload --app-dir src

# frontend (puerto 5173)
cd frontend
npm install
npm run dev
```

`frontend/.env.development` ya apunta a `http://localhost:8000/api` y los
orígenes por defecto del backend ya incluyen `localhost:5173`, así que no hace
falta configurar nada. Como no hay proxy, el navegador hace CORS de verdad
también en local.

Fuera de producción, `GET /health` devuelve la configuración CORS efectiva —
la forma más rápida de ver por qué el navegador rechaza una respuesta:

```sh
curl -s http://localhost:8000/health
```

Para probar el build de producción tal cual sale a Vercel:

```sh
cd frontend
VITE_API_URL=http://localhost:8000/api npm run build
npx vite preview --port 4173
```

`localhost:4173` también está en los orígenes permitidos por defecto.

Con Docker Compose (Postgres incluido):

```sh
docker compose up --build
```

---

## Fallos frecuentes

| Síntoma | Causa | Arreglo |
| --- | --- | --- |
| `blocked by CORS policy` en la consola del navegador | el dominio de Vercel no está en `CORS_ORIGINS` | añadirlo en Render (sin barra final) |
| Falla solo en los previews de Vercel | cada preview tiene dominio propio | definir `CORS_ORIGIN_REGEX` |
| El proceso no arranca en Render | `CORS_ORIGINS` mal escrito | el log dice qué origen y por qué |
| Peticiones a `localhost:8000` desde producción | se desplegó un build sin `VITE_API_URL` | definirla en Vercel y volver a desplegar |
| Recargar `/career` da 404 en Vercel | falta el rewrite de SPA | usar `frontend/vercel.json` |
| Las carreras desaparecen tras un redeploy | SQLite en disco efímero | usar la base Postgres de Render |
| La primera petición tarda ~50 s | el plan free de Render duerme el servicio | esperar; el cliente aguanta 60 s |
| `NoSuchModuleError: postgres` | Render entrega `postgres://` | ya se reescribe solo a `postgresql+psycopg://` |
| `ModuleNotFoundError: psycopg2` | `postgresql://` a secas pide un driver que no está instalado | ya se reescribe solo; si aparece, alguien forzó `+psycopg2` a mano |
| `server closed the connection unexpectedly` en la primera petición tras un rato | Postgres gestionado corta las conexiones ociosas | ya cubierto con `pool_pre_ping` y `pool_recycle=280` |
