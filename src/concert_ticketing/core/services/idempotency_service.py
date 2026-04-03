"""Coordinacion de idempotencia basada en request_id."""

from __future__ import annotations

from typing import Any, Optional

from ..ports.idempotency_repository import IdempotencyRepository


class IdempotencyService:
    """Consulta el registro de idempotencia."""

    def __init__(self, repo: IdempotencyRepository) -> None:
        self._repo = repo

    def was_processed(self, request_id: str) -> bool:
        """Indica si un request_id ya fue procesado."""
        return self._repo.request_exists(request_id)

    def get_result(self, request_id: str) -> Optional[dict[str, Any]]:
        """Retorna el resultado almacenado de un request previo."""
        return self._repo.get_request_result(request_id)