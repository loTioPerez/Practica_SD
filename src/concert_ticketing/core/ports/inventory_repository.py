"""Puerto de acceso atómico al inventario y a la asignación de entradas."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..domain.models import PurchaseResult, SeatInfo


class InventoryRepository(ABC):
    """Interface abstracta para operaciones atómicas sobre el inventario."""

    # ---- Compras atómicas ----

    @abstractmethod
    def buy_unnumbered(self, client_id: str, request_id: str) -> PurchaseResult:
        """Compra atómica de un ticket no numerado."""
        ...

    @abstractmethod
    def buy_numbered(self, client_id: str, seat_id: int, request_id: str) -> PurchaseResult:
        """Compra atómica de un ticket numerado (asiento específico)."""
        ...

    # ---- Consultas ----

    @abstractmethod
    def get_available_count(self, ticket_type: str) -> int:
        """Retorna el número de tickets disponibles."""
        ...

    @abstractmethod
    def get_seat_status(self, seat_id: int) -> SeatInfo:
        """Retorna el estado de un asiento numerado."""
        ...

    # ---- Gestión del sistema ----

    @abstractmethod
    def initialize(self, ticket_type: str, total_tickets: int) -> None:
        """Inicializa el inventario (crear tickets/asientos)."""
        ...

    @abstractmethod
    def reset(self, ticket_type: str, total_tickets: int) -> None:
        """Resetea completamente el inventario."""
        ...
