import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as career_router
from app.config import DEFAULT_CORS_ORIGINS, Settings, settings
from app.database import init_db
from app.modules.career.service import ActionBlockedError, ConcurrentModificationError

logger = logging.getLogger("elbarrio")


def _configure_logging() -> None:
    """Engancha el logger de la app a la salida de uvicorn.

    Uvicorn instala sus propios handlers y deja el logger raíz en WARNING, así
    que los `info` de arranque se perderían justo donde más falta hacen: en los
    logs del servidor desplegado.
    """
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return
    uvicorn_logger = logging.getLogger("uvicorn")
    if uvicorn_logger.handlers:
        logger.handlers = uvicorn_logger.handlers
        logger.propagate = False
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False


def _log_startup_config(config: Settings) -> None:
    """Deja rastro de la configuración efectiva de red al arrancar.

    Sin esto, un despliegue con el CORS mal puesto falla en el navegador del
    usuario y no deja ninguna pista en los logs del servidor.
    """
    logger.info("ELBARRIO API arrancando | entorno=%s", config.environment)
    logger.info("CORS origins permitidos: %s", config.cors_origins or "(ninguno)")
    if config.cors_origin_regex:
        logger.info("CORS origin regex: %s", config.cors_origin_regex)
    logger.info("CORS allow_credentials: %s", config.cors_allow_credentials)

    scheme = config.database_url.split("://", 1)[0] if "://" in config.database_url else "?"
    logger.info("Base de datos: %s", scheme)

    if config.is_production:
        if config.cors_origins == DEFAULT_CORS_ORIGINS and not config.cors_origin_regex:
            logger.warning(
                "CORS_ORIGINS sigue en el valor por defecto (localhost) con ENVIRONMENT=%s. "
                "El frontend desplegado recibirá HTTP 400 en el preflight. "
                "Definí CORS_ORIGINS con el dominio real.",
                config.environment,
            )
        if config.database_url.startswith("sqlite"):
            logger.warning(
                "DATABASE_URL apunta a SQLite en producción. En un disco efímero "
                "(Render sin volumen persistente) las carreras se pierden en cada redeploy."
            )


def create_app(config: Settings | None = None) -> FastAPI:
    """Construye la aplicación.

    Recibe la configuración por parámetro para que las pruebas puedan levantar la
    app real con orígenes CORS de producción sin tocar variables de entorno del
    proceso.
    """
    config = config or settings

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        _configure_logging()
        _log_startup_config(config)
        init_db()
        yield

    application = FastAPI(title=config.app_name, lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_origin_regex=config.cors_origin_regex,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(career_router)

    @application.exception_handler(ActionBlockedError)
    def handle_action_blocked(_: Request, exc: ActionBlockedError):
        return JSONResponse(
            status_code=409,
            content={"detail": "La carrera tiene una acción pendiente por resolver.", "reason": exc.reason},
        )

    @application.exception_handler(ConcurrentModificationError)
    def handle_concurrent_modification(_: Request, exc: ConcurrentModificationError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @application.get("/health")
    def health():
        """Sonda de salud. Render la usa como health check del servicio."""
        payload = {
            "status": "ok",
            "app": config.app_name,
            "environment": config.environment,
        }
        if not config.is_production:
            # Fuera de producción se devuelve la configuración de red efectiva:
            # es la forma más rápida de saber por qué el navegador rechaza una
            # respuesta. En producción no se expone.
            payload["corsOrigins"] = config.cors_origins
            payload["corsOriginRegex"] = config.cors_origin_regex
        return payload

    return application


app = create_app()
