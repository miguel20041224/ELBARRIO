# ELBARRIO

**ELBARRIO** is a football career simulator where every match, contract, transfer, scandal, award, and career decision can change the player’s story.

The project is still in active development, but the current version already includes a playable career loop with player creation, club selection, match-by-match progression, events, roulette outcomes, transfers, awards, and competition-aware fixtures.

## What is playable now

- Create a player with identity, country, position, physical profile, preferred foot, and starting league.
- Start at a contextual club based on age, league, and club level.
- Play the season match by match instead of simulating everything at once.
- Face real clubs from the selected league catalog.
- See fixture context: league, cup, continental competition, stage, venue, and clásicos.
- Resolve career and life events with persistent consequences.
- Trigger event chains with delayed follow-ups.
- Spin roulette moments at career and season milestones.
- Receive transfer offers based on reputation, performance, age, and club fit.
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
│   │   │   └── transfers/  Transfer window logic
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

## Validation

```bash
cd backend
export PATH="$HOME/.local/bin:$PATH"
poetry run pytest
```

```bash
cd frontend
npm run build
```

Current verified status:

- Backend tests: `29 passed`
- Frontend production build: passing

## Current roadmap

- [x] Player creation and core career session
- [x] Club and league catalog
- [x] Match-by-match season progression
- [x] Event system with consequences and follow-up chains
- [x] Roulette milestone outcomes
- [x] Transfer windows with contextual offers
- [x] Competition-aware fixtures for league, domestic cup, and continental matches
- [ ] League tables and trophies decided by real standings
- [ ] Contract clock, clauses, renewals, free agency, and loans
- [ ] National team competitions
- [ ] Expanded event library
- [ ] Expanded awards system
- [ ] Authentication, persistent accounts, and deployment pipeline

## Design direction

ELBARRIO is built around one principle: the career should feel earned.

A small club can have a miracle season. A superstar can get trapped by a bad contract. A great run can open Europe. A bad choice can damage the coach relationship, press image, or fitness. The goal is not only to calculate stats, but to create a football story that reacts to the player’s path.
