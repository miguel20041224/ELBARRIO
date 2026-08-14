# ELBARRIO

**ELBARRIO** is a football career simulator about earning a player story one match at a time: create a player, join a club, fight for minutes, react to events, chase trophies, and navigate contracts, transfers, awards, and career-defining roulette moments.

The current build is already playable as a match-by-match career loop. It is not just a generic season simulator: fixtures have context, the coach previews your role before matches, standings decide league outcomes, and contract state changes what transfer paths are realistic.

## What is playable now

- Create a player with identity, country, position, body profile, preferred foot, league, and team selection.
- Progress through a career match by match instead of simulating the whole season at once.
- Review the pre-match convocatoria/team-selection preview: starter, substitute, or bench chance, coach message, expected minutes, and selection factors.
- Play fixtures with context: league, domestic cup, continental competition, stage, venue, and clásicos.
- Track league table standings, with league trophies decided from the table.
- Move through contract-aware transfer windows:
  - contract years tick down by season,
  - multi-year contracts block normal offers,
  - elite seasons can trigger release-clause offers,
  - expiring contracts and free-agent windows create different paths,
  - renewals and low-minute loan reasons exist in the transfer flow.
- Spin roulette moments at career and season milestones.
- Resolve events with chains, delayed consequences, and lasting career effects.
- Earn team trophies and individual awards.

## Tech stack

| Area | Stack |
| --- | --- |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, Zustand, React Router |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite for local development, PostgreSQL-ready through Docker Compose |
| Tooling | Poetry, npm, Docker Compose, pytest |

## Project structure

```txt
ELBARRIO/
├── backend/
│   ├── src/app/
│   │   ├── api/            FastAPI routes
│   │   ├── models/         SQLAlchemy models
│   │   ├── modules/
│   │   │   ├── awards/     Individual award logic
│   │   │   ├── career/     Career session orchestration
│   │   │   ├── clubs/      League and club catalog
│   │   │   ├── decisions/  Event effect engine
│   │   │   ├── events/     Event library, chains, selector
│   │   │   ├── player/     Player factory and stat generation
│   │   │   ├── roulette/   Roulette milestone outcomes
│   │   │   ├── simulation/ Match and season simulation
│   │   │   └── transfers/  Contract-aware transfer window logic
│   │   └── schemas.py      Shared API schemas
│   └── tests/              Backend regression tests
├── frontend/
│   └── src/
│       ├── api/            API client
│       ├── data/           Static creation data
│       ├── modules/        UI feature modules
│       ├── store/          Zustand stores
│       └── types/          Frontend game types
└── docker-compose.yml
```

## Run locally

### Backend

```bash
cd backend
export PATH="$HOME/.local/bin:$PATH"
poetry install
poetry run uvicorn app.main:app --reload --app-dir src
```

Backend API: <http://localhost:8000>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend app: <http://localhost:5173>

## Run with Docker

```bash
docker compose up --build
```

This starts the frontend, backend, and PostgreSQL service together.


## Deployment

### Backend on Render or Railway

Deploy the backend as a Docker service from `backend/Dockerfile`. The image uses Python 3.14 to match `backend/pyproject.toml`, installs the locked Poetry dependencies, and then installs `psycopg[binary]` because the application uses SQLAlchemy's synchronous `create_engine` for PostgreSQL.

Required backend environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

Notes:

- Health check path: `/health`
- Render and Railway provide `PORT`; the Docker command uses `${PORT:-8000}`.
- `CORS_ORIGINS` must contain the exact frontend origin only, not `/api` or another path.
- Use the `postgresql+psycopg://` URL scheme in production. If a host gives you `postgresql://...`, change only the scheme to `postgresql+psycopg://...` so SQLAlchemy uses the synchronous psycopg driver installed by the Docker image.

### Frontend on Vercel

Set this Vercel environment variable for the frontend project:

```env
VITE_API_URL=https://<backend-host>/api
```

After Vercel gives you the production frontend URL, add that origin to the backend `CORS_ORIGINS` value and redeploy the backend if needed.

## Validation

```bash
cd frontend
npm run build
```

```bash
cd backend
export PATH="$HOME/.local/bin:$PATH"
poetry install
poetry run pytest
```

Current verified status for this session:

- Frontend production build: passing.
- Backend tests: present, but not claimed as passing in this session because local backend dependencies were not installed here.

## Current roadmap

- [x] Player creation and core career session
- [x] League and team selection during player creation
- [x] Match-by-match season progression
- [x] Pre-match convocatoria/team-selection preview
- [x] Fixture context for league, cup, continental matches, stages, venues, and clásicos
- [x] League table standings and league trophies decided from the table
- [x] Event system with consequences and follow-up chains
- [x] Roulette outcomes at career and season milestones
- [x] Contract-aware transfer windows, renewals, release clauses, free agency, and loan reasons
- [x] Team trophies and individual awards
- [ ] National team competitions
- [ ] Expanded event library
- [ ] Authentication, persistent accounts, and deployment pipeline

## Design direction

ELBARRIO is built around one principle: the career should feel earned.

A small club can have a miracle season. A young player can sit on the bench until the coach trusts him. A superstar can get trapped by a bad contract unless a release clause appears. A great run can open Europe. A bad choice can damage the coach relationship, press image, happiness, or fitness. The goal is not only to calculate stats, but to create a football story that reacts to the player’s path.
