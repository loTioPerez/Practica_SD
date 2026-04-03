"""Middleware HTTP para trazas, errores y observabilidad basica."""

from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ....shared.exceptions import InvalidInputError, RedisConnectionError
from ....shared.logger import get_logger

logger = get_logger(__name__)


def register_middleware(app: FastAPI) -> None:
    """Registra middleware y handlers basicos para la API REST."""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[no-redef]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "%s %s -> %s (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    @app.exception_handler(InvalidInputError)
    async def handle_invalid_input(  # type: ignore[no-redef]
        request: Request,
        exc: InvalidInputError,
    ) -> JSONResponse:
        logger.warning("Entrada invalida en %s: %s", request.url.path, exc)
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(RedisConnectionError)
    async def handle_redis_error(  # type: ignore[no-redef]
        request: Request,
        exc: RedisConnectionError,
    ) -> JSONResponse:
        logger.error("Redis no disponible en %s: %s", request.url.path, exc)
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(  # type: ignore[no-redef]
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Error no controlado en %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal_error"})
