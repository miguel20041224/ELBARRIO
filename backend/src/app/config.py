import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


def _parse_origins(raw: object) -> list[str]:
    """Acepta los formatos que un panel de deploy permite escribir.

    Render, Railway y Fly exponen un único campo de texto por variable, así que
    ``CORS_ORIGINS=https://mi-app.vercel.app`` es lo que cualquiera escribe. El
    decodificador JSON por defecto de pydantic-settings rompe el arranque con ese
    valor, de modo que aquí se admiten las cuatro formas razonables:

    - lista de Python (valor por defecto en código)
    - JSON: ``["https://a.com", "https://b.com"]``
    - separado por comas: ``https://a.com,https://b.com``
    - origen único: ``https://a.com``
    """
    if isinstance(raw, (list, tuple)):
        candidates = [str(item) for item in raw]
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"CORS_ORIGINS parece JSON pero no se pudo leer: {exc}. "
                    'Usá una lista JSON válida o separá los orígenes con comas.'
                ) from exc
            if not isinstance(decoded, list):
                raise ValueError("CORS_ORIGINS en JSON debe ser una lista de cadenas.")
            candidates = [str(item) for item in decoded]
        else:
            candidates = text.split(",")
    else:
        raise ValueError(f"CORS_ORIGINS no admite el tipo {type(raw).__name__}.")

    origins: list[str] = []
    for candidate in candidates:
        origin = candidate.strip().rstrip("/")
        if not origin:
            continue
        if origin != "*" and "://" not in origin:
            raise ValueError(
                f"Origen CORS inválido: {origin!r}. Incluí el esquema, por ejemplo "
                "https://mi-app.vercel.app"
            )
        if origin not in origins:
            origins.append(origin)
    return origins


def _normalize_database_url(raw: str) -> str:
    """Deja la cadena de conexión en el esquema que esta imagen sabe usar.

    Dos problemas distintos, ambos rompen el arranque en Render:

    - Render y Heroku entregan ``postgres://``, alias que SQLAlchemy 2.0 eliminó.
    - ``postgresql://`` a secas hace que SQLAlchemy busque ``psycopg2``, pero la
      imagen instala ``psycopg`` (v3), así que hay que pedirlo por nombre.

    Un driver escrito a mano (``postgresql+asyncpg://``, por ejemplo) se respeta:
    si alguien lo puso explícitamente, sabe lo que hace.
    """
    text = raw.strip()
    for prefix in ("postgres://", "postgresql://"):
        if text.startswith(prefix):
            return "postgresql+psycopg://" + text[len(prefix) :]
    return text


class Settings(BaseSettings):
    app_name: str = "ELBARRIO API"
    environment: str = "development"
    database_url: str = "sqlite:///./elbarrio.db"

    cors_origins: Annotated[list[str], NoDecode] = DEFAULT_CORS_ORIGINS
    # Los despliegues de preview de Vercel generan un dominio distinto por commit
    # (elbarrio-git-rama-usuario.vercel.app), imposible de enumerar de antemano.
    cors_origin_regex: str | None = None
    # La API no usa cookies ni cabecera Authorization: mantenerlo en False evita
    # el modo credenciales de CORS, que además prohíbe el comodín de origen.
    cors_allow_credentials: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _validate_cors_origins(cls, raw: object) -> list[str]:
        return _parse_origins(raw)

    @field_validator("database_url", mode="before")
    @classmethod
    def _validate_database_url(cls, raw: object) -> str:
        return _normalize_database_url(str(raw))

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


settings = Settings()
