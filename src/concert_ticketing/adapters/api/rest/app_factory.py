"""Creacion de la aplicacion REST y ensamblado de dependencias."""

from __future__ import annotations

from fastapi import FastAPI

from ....shared.logger import get_logger
from .middleware import register_middleware
from .routes import router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Construye la aplicacion FastAPI de la arquitectura directa."""
    app = FastAPI(
        title="Concert Ticketing Direct API",
        version="0.1.0",
        description="API REST directa para compra y consulta de entradas.",
    )
    register_middleware(app)
    app.include_router(router)
    logger.info("Aplicacion REST creada")
    return app
