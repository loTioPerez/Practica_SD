"""Logica de idempotencia: deteccion de requests duplicados."""

from __future__ import annotations

from typing import Any, Optional

from ..ports.idempotency_repository import IdempotencyRepository


class IdempotencyService:
    """Consulta el repositorio de idempotencia para prevenir duplicados."""

    def __init__(self, repository: IdempotencyRepository) -> None:
        self._repo = repository

    def exists(self, request_id: str) -> bool:
        """Comprueba si un request ya fue procesado."""
        return self._repo.request_exists(request_id)

    def get_result(self, request_id: str) -> Optional[dict[str, Any]]:
        """Devuelve el resultado almacenado de un request, o None."""
        return self._repo.get_request_result(request_id)

    def store(self, request_id: str, result: dict[str, Any]) -> None:
        """Guarda el resultado de un request procesado."""
        self._repo.store_result(request_id, result)
