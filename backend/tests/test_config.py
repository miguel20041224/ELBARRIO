"""Pruebas de configuración de arranque.

Cubren el fallo que impedía desplegar: `CORS_ORIGINS=https://app.vercel.app`
—el formato que se escribe en el panel de Render— rompía el arranque del proceso
porque pydantic-settings intentaba decodificarlo como JSON.
"""

import pytest
from pydantic import ValidationError

from app.config import Settings, _normalize_database_url, _parse_origins


class TestCorsOriginsParsing:
    def test_single_origin_without_json(self):
        assert _parse_origins("https://elbarrio.vercel.app") == [
            "https://elbarrio.vercel.app"
        ]

    def test_comma_separated(self):
        assert _parse_origins(
            "https://elbarrio.vercel.app,https://www.elbarrio.com"
        ) == ["https://elbarrio.vercel.app", "https://www.elbarrio.com"]

    def test_comma_separated_with_spaces(self):
        assert _parse_origins(" https://a.com , https://b.com ") == [
            "https://a.com",
            "https://b.com",
        ]

    def test_json_list_still_supported(self):
        assert _parse_origins('["https://a.com", "https://b.com"]') == [
            "https://a.com",
            "https://b.com",
        ]

    def test_python_list_default(self):
        assert _parse_origins(["https://a.com"]) == ["https://a.com"]

    def test_trailing_slash_removed(self):
        """El navegador manda el Origin sin barra final; si la configuración la
        lleva, la comparación falla y el preflight se rechaza."""
        assert _parse_origins("https://a.com/") == ["https://a.com"]

    def test_duplicates_removed_preserving_order(self):
        assert _parse_origins("https://b.com,https://a.com,https://b.com") == [
            "https://b.com",
            "https://a.com",
        ]

    def test_empty_string_yields_no_origins(self):
        assert _parse_origins("") == []
        assert _parse_origins("  ") == []

    def test_wildcard_allowed(self):
        assert _parse_origins("*") == ["*"]

    def test_origin_without_scheme_is_rejected(self):
        with pytest.raises(ValueError, match="Incluí el esquema"):
            _parse_origins("elbarrio.vercel.app")

    def test_malformed_json_gives_actionable_message(self):
        with pytest.raises(ValueError, match="parece JSON"):
            _parse_origins('["https://a.com"')


class TestSettingsFromEnvironment:
    def test_settings_boot_with_plain_origin(self, monkeypatch):
        """Reproduce el arranque en Render con la variable escrita a mano."""
        monkeypatch.setenv("CORS_ORIGINS", "https://elbarrio.vercel.app")
        settings = Settings(_env_file=None)
        assert settings.cors_origins == ["https://elbarrio.vercel.app"]

    def test_settings_boot_with_comma_separated(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "https://a.com,https://b.com")
        settings = Settings(_env_file=None)
        assert settings.cors_origins == ["https://a.com", "https://b.com"]

    def test_settings_boot_with_json(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", '["https://a.com"]')
        settings = Settings(_env_file=None)
        assert settings.cors_origins == ["https://a.com"]

    def test_invalid_origin_fails_loudly(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "elbarrio.vercel.app")
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_defaults_cover_dev_and_preview_ports(self):
        settings = Settings(_env_file=None)
        assert "http://localhost:5173" in settings.cors_origins
        assert "http://localhost:4173" in settings.cors_origins

    def test_credentials_disabled_by_default(self):
        """La API no usa cookies. Con credenciales activas, CORS prohíbe '*'."""
        assert Settings(_env_file=None).cors_allow_credentials is False

    def test_is_production_flag(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        assert Settings(_env_file=None).is_production is True


class TestDatabaseUrlNormalization:
    def test_render_postgres_scheme_is_rewritten(self):
        """Render entrega postgres://, esquema que SQLAlchemy 2.0 ya no acepta."""
        assert _normalize_database_url("postgres://u:p@host:5432/db") == (
            "postgresql+psycopg://u:p@host:5432/db"
        )

    def test_bare_postgresql_scheme_gets_the_installed_driver(self):
        """postgresql:// a secas busca psycopg2, que la imagen no instala."""
        assert _normalize_database_url("postgresql://u:p@host:5432/db") == (
            "postgresql+psycopg://u:p@host:5432/db"
        )

    def test_explicit_driver_untouched(self):
        for url in (
            "postgresql+psycopg://u:p@host:5432/db",
            "postgresql+asyncpg://u:p@host:5432/db",
        ):
            assert _normalize_database_url(url) == url

    def test_sqlite_untouched(self):
        assert _normalize_database_url("sqlite:///./elbarrio.db") == (
            "sqlite:///./elbarrio.db"
        )

    def test_settings_normalize_from_environment(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host:5432/db")
        assert Settings(_env_file=None).database_url.startswith("postgresql+psycopg://")
