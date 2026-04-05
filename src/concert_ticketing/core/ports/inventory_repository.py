"""Puerto abstracto para operaciones de inventario."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..domain.models import PurchaseResult, SeatInfo


class InventoryRepository(ABC):
    """Interfaz que desacopla la logica de negocio de la persistencia."""

    @abstractmethod
    def buy_unnumbered(self, client_id: str, request_id: str) -> PurchaseResult:
        """Intenta comprar una entrada general (no numerada)."""

    @abstractmethod
    def buy_numbered(self, client_id: str, seat_id: int, request_id: str) -> PurchaseResult:
        """Intenta comprar un asiento numerado concreto."""

    @abstractmethod
    def get_available_count(self, ticket_type: str) -> int:
        """Devuelve el numero de entradas disponibles para un tipo."""

    @abstractmethod
    def get_seat_status(self, seat_id: int) -> SeatInfo:
        """Devuelve el estado de un asiento numerado."""

    @abstractmethod
    def initialize(self, ticket_type: str, total_tickets: int) -> None:
        """Inicializa el inventario con la cantidad indicada."""

    @abstractmethod
    def reset(self, ticket_type: str, total_tickets: int) -> None:
        """Resetea el inventario."""
