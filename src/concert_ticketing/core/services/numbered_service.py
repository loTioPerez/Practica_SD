"""Logica de negocio para compra de asientos numerados."""

from __future__ import annotations

from ..domain.models import PurchaseResult, SeatInfo
from ..ports.inventory_repository import InventoryRepository


class NumberedService:
    """Delega la compra numerada al repositorio de inventario."""

    def __init__(self, inventory: InventoryRepository) -> None:
        self._inventory = inventory

    def buy(self, client_id: str, seat_id: int, request_id: str) -> PurchaseResult:
        """Ejecuta la compra de un asiento numerado concreto."""
        return self._inventory.buy_numbered(client_id, seat_id, request_id)

    def seat_status(self, seat_id: int) -> SeatInfo:
        """Consulta el estado de un asiento."""
        return self._inventory.get_seat_status(seat_id)
