"""Puerto para persistir y recuperar resultados de compra."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResultRepository(ABC):
    """Interface para consultar el historial de compras de un cliente."""

    @abstractmethod
    def get_client_purchases(self, client_id: str) -> list[dict[str, Any]]:
        """Retorna la lista de compras de un cliente."""
        ...
