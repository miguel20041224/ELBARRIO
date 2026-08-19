from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CareerSessionModel(Base):
    __tablename__ = "career_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    current_season: Mapped[int] = mapped_column(Integer, default=1)
    pending_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pending_event_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    events_resolved_total: Mapped[int] = mapped_column(Integer, default=0)
    player_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    history: Mapped[list] = mapped_column(JSON, default=list)
    pending_chains: Mapped[list] = mapped_column(JSON, default=list)
    season_progress: Mapped[dict] = mapped_column(JSON, default=dict)
    pending_roulette: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pending_transfer_window: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pending_retirement: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __mapper_args__ = {"version_id_col": version}
