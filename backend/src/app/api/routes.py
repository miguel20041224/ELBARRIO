from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.career import service
from app.modules.clubs.data import get_league, get_clubs_for_league
from app.schemas import (
    AcceptTransferPayload,
    CareerSession,
    CreateCareerPayload,
    ResolveEventPayload,
    ResolveRetirementPayload,
    SpinRoulettePayload,
    TeamOption,
)

router = APIRouter(prefix="/api", tags=["career"])


@router.get("/leagues/{league_id}/teams", response_model=list[TeamOption])
def list_teams(league_id: str):
    if not get_league(league_id):
        raise HTTPException(status_code=404, detail="League not found")
    return [
        TeamOption(
            id=club.id,
            name=club.name,
            shortName=club.short_name,
            city=club.city,
            prestige=club.prestige,
            nickname=club.nickname,
        )
        for club in sorted(get_clubs_for_league(league_id), key=lambda c: -c.prestige)
    ]


@router.post("/careers", response_model=CareerSession)
def create_career(payload: CreateCareerPayload, db: Session = Depends(get_db)):
    return service.create_career(payload, db)


@router.get("/careers/{session_id}", response_model=CareerSession)
def get_career(session_id: str, db: Session = Depends(get_db)):
    session = service.get_career(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Career not found")
    return session


@router.post("/careers/{session_id}/spin-roulette", response_model=CareerSession)
def spin_roulette(
    session_id: str,
    payload: SpinRoulettePayload,
    db: Session = Depends(get_db),
):
    session = service.spin_roulette(session_id, payload.outcomeId, db)
    if not session:
        raise HTTPException(status_code=404, detail="Career or roulette not found")
    return session


@router.post("/careers/{session_id}/play-match", response_model=CareerSession)
def play_match(session_id: str, db: Session = Depends(get_db)):
    session = service.play_match(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Career not found")
    return session


@router.post("/careers/{session_id}/resolve-event", response_model=CareerSession)
def resolve_event(
    session_id: str,
    payload: ResolveEventPayload,
    db: Session = Depends(get_db),
):
    session = service.resolve_event(session_id, payload.choiceId, db)
    if not session:
        raise HTTPException(
            status_code=404, detail="Career or pending event not found"
        )
    return session


@router.post("/careers/{session_id}/advance-season", response_model=CareerSession)
def advance_season(session_id: str, db: Session = Depends(get_db)):
    session = service.advance_season(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Career not found")
    return session


@router.post("/careers/{session_id}/resolve-retirement", response_model=CareerSession)
def resolve_retirement(
    session_id: str,
    payload: ResolveRetirementPayload,
    db: Session = Depends(get_db),
):
    session = service.resolve_retirement(session_id, payload.retire, db)
    if not session:
        raise HTTPException(
            status_code=404, detail="Career or pending retirement not found"
        )
    return session


@router.post("/careers/{session_id}/accept-transfer", response_model=CareerSession)
def accept_transfer(
    session_id: str,
    payload: AcceptTransferPayload,
    db: Session = Depends(get_db),
):
    session = service.accept_transfer(session_id, payload.offerId, db)
    if not session:
        raise HTTPException(
            status_code=404, detail="Career or transfer window not found"
        )
    return session
