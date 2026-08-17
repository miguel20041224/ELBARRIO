"""Smoke tests del flujo de red frontend → backend.

Levantan la aplicación real (`create_app`) con la configuración CORS que tendría
en producción y comprueban lo que el navegador comprueba: preflight, cabecera
`Access-Control-Allow-Origin` en la respuesta, y que un origen ajeno no la
recibe. Son la red de seguridad del despliegue Vercel + Render.
"""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DEFAULT_CORS_ORIGINS, Settings
from app.database import Base, get_db
from app.main import _log_startup_config, create_app

FRONTEND = "https://elbarrio.vercel.app"
PREVIEW = "https://elbarrio-git-fix-cors-miguel.vercel.app"
STRANGER = "https://sitio-ajeno.example"
PREVIEW_REGEX = r"^https://elbarrio-[a-z0-9-]+\.vercel\.app$"


def make_settings(**overrides) -> Settings:
    base = dict(
        environment="production",
        database_url="sqlite://",
        cors_origins=FRONTEND,
        cors_origin_regex=PREVIEW_REGEX,
        _env_file=None,
    )
    base.update(overrides)
    return Settings(**base)


@pytest.fixture
def client() -> TestClient:
    """Cliente contra la app real, con una base en memoria."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    app = create_app(make_settings())

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Sin `with`: no se ejecuta el lifespan, que crearía el fichero SQLite real.
    return TestClient(app)


DRAFT = {
    "mode": "player",
    "draft": {
        "firstName": "Diego",
        "lastName": "Rodriguez",
        "birthCountry": "AR",
        "startingLeague": "col-primera-a",
        "position": "CAM",
        "shirtNumber": 10,
        "preferredFoot": "left",
        "age": 19,
        "height": 175,
        "weight": 70,
    },
}


class TestPreflight:
    def test_allowed_origin_gets_preflight_approval(self, client):
        response = client.options(
            "/api/careers",
            headers={
                "Origin": FRONTEND,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == FRONTEND

    def test_vercel_preview_domain_matches_regex(self, client):
        """Cada commit genera un dominio de preview distinto, imposible de listar."""
        response = client.options(
            "/api/careers",
            headers={
                "Origin": PREVIEW,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == PREVIEW

    def test_unknown_origin_is_rejected(self, client):
        response = client.options(
            "/api/careers",
            headers={
                "Origin": STRANGER,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in response.headers

    def test_get_career_preflight_is_approved(self, client):
        """El endpoint que el frontend llama al montar la pantalla de carrera."""
        response = client.options(
            "/api/careers/cualquiera",
            headers={
                "Origin": FRONTEND,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == FRONTEND


class TestActualRequests:
    def test_health_is_reachable(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_hides_cors_config_in_production(self, client):
        assert "corsOrigins" not in client.get("/health").json()

    def test_health_exposes_cors_config_outside_production(self):
        app = create_app(make_settings(environment="development"))
        body = TestClient(app).get("/health").json()
        assert body["corsOrigins"] == [FRONTEND]
        assert body["corsOriginRegex"] == PREVIEW_REGEX

    def test_create_and_get_career_from_the_frontend_origin(self, client):
        """Recorrido completo: crear carrera y releerla, como hace el navegador."""
        created = client.post("/api/careers", json=DRAFT, headers={"Origin": FRONTEND})
        assert created.status_code == 200
        assert created.headers["access-control-allow-origin"] == FRONTEND

        session_id = created.json()["id"]
        fetched = client.get(f"/api/careers/{session_id}", headers={"Origin": FRONTEND})
        assert fetched.status_code == 200
        assert fetched.headers["access-control-allow-origin"] == FRONTEND
        assert fetched.json()["id"] == session_id

    def test_response_to_unknown_origin_has_no_cors_header(self, client):
        """El servidor responde, pero el navegador descarta el cuerpo sin la cabecera."""
        response = client.get("/health", headers={"Origin": STRANGER})
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers

    def test_missing_career_returns_404(self, client):
        """El frontend distingue 404 (carrera borrada) de fallo de red."""
        response = client.get("/api/careers/no-existe", headers={"Origin": FRONTEND})
        assert response.status_code == 404

    def test_no_credentials_header_by_default(self, client):
        """Sin cookies no hay motivo para activar el modo credenciales de CORS."""
        response = client.get("/health", headers={"Origin": FRONTEND})
        assert "access-control-allow-credentials" not in response.headers


class TestStartupLogging:
    def test_logs_effective_cors_configuration(self, caplog):
        with caplog.at_level(logging.INFO, logger="elbarrio"):
            _log_startup_config(make_settings())
        assert FRONTEND in caplog.text
        assert "entorno=production" in caplog.text

    def test_warns_when_production_still_points_at_localhost(self, caplog):
        """El fallo más probable del despliegue: olvidar CORS_ORIGINS en Render."""
        config = make_settings(
            cors_origins=DEFAULT_CORS_ORIGINS, cors_origin_regex=None
        )
        with caplog.at_level(logging.WARNING, logger="elbarrio"):
            _log_startup_config(config)
        assert "CORS_ORIGINS sigue en el valor por defecto" in caplog.text

    def test_warns_about_sqlite_in_production(self, caplog):
        with caplog.at_level(logging.WARNING, logger="elbarrio"):
            _log_startup_config(make_settings(database_url="sqlite:///./elbarrio.db"))
        assert "SQLite en producción" in caplog.text

    def test_no_warnings_with_correct_production_config(self, caplog):
        config = make_settings(database_url="postgresql://u:p@host:5432/db")
        with caplog.at_level(logging.WARNING, logger="elbarrio"):
            _log_startup_config(config)
        assert caplog.text == ""
