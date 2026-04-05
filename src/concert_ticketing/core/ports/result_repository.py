"""Puerto abstracto para consulta de historial de compras por cliente."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResultRepository(ABC):
    """Interfaz para almacenar y consultar resultados de compras."""

    @abstractmethod
    def store_purchase(self, client_id: str, result: dict[str, Any]) -> None:
        """Almacena un resultado de compra para un cliente."""

    @abstractmethod
    def get_client_purchases(self, client_id: str) -> list[dict[str, Any]]:
        """Devuelve el historial de compras de un cliente."""
