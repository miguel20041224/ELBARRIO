# ELBARRIO Backend

FastAPI backend for ELBARRIO.

## Runtime

- Python: `>=3.14`
- App entrypoint: `app.main:app`
- Health check: `GET /health`
- API base path used by the frontend: `/api`

## Local development

```bash
cd backend
export PATH="$HOME/.local/bin:$PATH"
poetry install
poetry run uvicorn app.main:app --reload --app-dir src
```

Default local API URL: <http://localhost:8000>

## Production Docker image

The backend image uses `python:3.14-slim` to match `pyproject.toml` and starts Uvicorn on the platform-provided `PORT` value, falling back to `8000`:

```bash
docker build -t elbarrio-backend ./backend
docker run --rm -p 8000:8000 \
  -e DATABASE_URL='postgresql+psycopg://user:password@host:5432/dbname' \
  -e CORS_ORIGINS='["https://your-frontend.vercel.app"]' \
  elbarrio-backend
```

The image installs `psycopg[binary]` after the locked Poetry dependencies. This is intentional: the application uses SQLAlchemy's synchronous `create_engine`, so production PostgreSQL URLs need a synchronous driver. The existing lock file only includes `asyncpg`, which is async-only.

Use the `postgresql+psycopg://` URL scheme for production. If Render, Railway, or another provider gives you `postgresql://...`, change only the scheme to `postgresql+psycopg://...` before setting `DATABASE_URL`.

## Deploy to Render

1. Create a PostgreSQL database in Render.
2. Create a new Web Service from this repository.
3. Set the root directory to `backend`.
4. Use Docker as the runtime.
5. Set the health check path to `/health`.
6. Add environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

Render provides `PORT`; the Docker command already honors it.

Important: if Render gives you a `postgresql://...` database URL, set `DATABASE_URL` as `postgresql+psycopg://...` instead so SQLAlchemy uses the installed synchronous driver.

## Deploy to Railway

1. Create a Railway project and add a PostgreSQL service.
2. Add the backend service from this repository.
3. Configure the service to build from `backend/Dockerfile` or set the root directory to `backend`.
4. Set the health check path to `/health`.
5. Add environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

Railway provides `PORT`; the Docker command already honors it.

Important: if Railway gives you a `postgresql://...` database URL, set `DATABASE_URL` as `postgresql+psycopg://...` instead so SQLAlchemy uses the installed synchronous driver.

## CORS and frontend configuration

The backend only accepts browser requests from origins listed in `CORS_ORIGINS`. For production, include the exact Vercel frontend origin, for example:

```env
CORS_ORIGINS=["https://elbarrio.vercel.app"]
```

Do not include paths in CORS origins. Use only scheme, host, and optional port.

For the Vercel frontend, set `VITE_API_URL` to the backend API URL:

```env
VITE_API_URL=https://<backend-host>/api
```
