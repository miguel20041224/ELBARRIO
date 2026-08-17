from collections.abc import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # Los proveedores gestionados cierran las conexiones ociosas sin avisar. Sin
    # pre_ping, la primera petición tras un rato de inactividad falla con
    # "server closed the connection unexpectedly".
    pool_pre_ping=not _is_sqlite,
    pool_recycle=280 if not _is_sqlite else -1,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import career  # noqa: F401 ensures models are registered

    Base.metadata.create_all(bind=engine)
