"""Puerto abstracto para operaciones de idempotencia."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IdempotencyRepository(ABC):
    """Interfaz para prevenir el procesamiento duplicado de requests."""

    @abstractmethod
    def request_exists(self, request_id: str) -> bool:
        """Comprueba si un request_id ya fue procesado."""

    @abstractmethod
    def get_request_result(self, request_id: str) -> Optional[dict[str, Any]]:
        """Devuelve el resultado guardado para un request_id, o None."""

    @abstractmethod
    def store_result(self, request_id: str, result: dict[str, Any]) -> None:
        """Guarda el resultado de un request_id procesado."""
