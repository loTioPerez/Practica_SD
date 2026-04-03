"""Servicio especializado para entradas no numeradas."""

from __future__ import annotations

from ..domain.models import PurchaseResult
from ..ports.inventory_repository import InventoryRepository


class UnnumberedService:
    """Encapsula la lógica específica de tickets sin numerar."""

    def __init__(self, inventory: InventoryRepository) -> None:
        self._inventory = inventory

    def buy(self, client_id: str, request_id: str) -> PurchaseResult:
        """Ejecuta la compra atómica de un ticket no numerado."""
        return self._inventory.buy_unnumbered(client_id, request_id)

    def available(self) -> int:
        """Tickets no numerados disponibles."""
        return self._inventory.get_available_count("unnumbered")