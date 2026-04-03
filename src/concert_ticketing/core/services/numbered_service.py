"""Servicio especializado para entradas numeradas y contencion por asiento."""

from __future__ import annotations

from ..domain.models import PurchaseResult, SeatInfo
from ..ports.inventory_repository import InventoryRepository


class NumberedService:
    """Encapsula la lógica específica de tickets numerados."""

    def __init__(self, inventory: InventoryRepository) -> None:
        self._inventory = inventory

    def buy(self, client_id: str, seat_id: int, request_id: str) -> PurchaseResult:
        """Ejecuta la compra atómica de un asiento concreto."""
        return self._inventory.buy_numbered(client_id, seat_id, request_id)

    def seat_status(self, seat_id: int) -> SeatInfo:
        """Estado de un asiento."""
        return self._inventory.get_seat_status(seat_id)

    def available(self) -> int:
        """Asientos numerados disponibles."""
        return self._inventory.get_available_count("numbered")