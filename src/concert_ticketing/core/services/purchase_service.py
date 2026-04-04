"""Servicio principal para orquestar compras y devolver resultados."""

from __future__ import annotations

from typing import Any

from ...shared.constants import TOTAL_TICKETS
from ...shared.exceptions import InvalidInputError
from ..domain.enums import TicketType
from ..domain.models import PurchaseResult, SeatInfo
from ..ports.idempotency_repository import IdempotencyRepository
from ..ports.inventory_repository import InventoryRepository
from ..ports.result_repository import ResultRepository
from .idempotency_service import IdempotencyService
from .numbered_service import NumberedService
from .unnumbered_service import UnnumberedService
from .validation_service import (
    validate_client_id,
    validate_request_id,
    validate_seat_id,
)


class PurchaseService:
    """Orquesta las operaciones principales del sistema de compra."""

    def __init__(
        self,
        inventory: InventoryRepository,
        idempotency: IdempotencyRepository | None = None,
        results: ResultRepository | None = None,
    ) -> None:
        self._inventory = inventory
        self._unnumbered_service = UnnumberedService(inventory)
        self._numbered_service = NumberedService(inventory)
        self._idempotency_service = (
            IdempotencyService(idempotency) if idempotency is not None else None
        )
        self._result_repository = results

    def buy_unnumbered(self, client_id: str, request_id: str) -> PurchaseResult:
        """Compra una entrada no numerada."""
        self._validate_common_input(client_id, request_id)
        return self._unnumbered_service.buy(client_id, request_id)

    def buy_numbered(
        self,
        client_id: str,
        seat_id: int,
        request_id: str,
    ) -> PurchaseResult:
        """Compra una entrada numerada."""
        self._validate_common_input(client_id, request_id)
        if not validate_seat_id(seat_id):
            raise InvalidInputError(f"seat_id invalido: {seat_id}")
        return self._numbered_service.buy(client_id, seat_id, request_id)

    def get_request_result(self, request_id: str) -> dict[str, Any] | None:
        """Consulta el resultado guardado para un request_id."""
        if not validate_request_id(request_id):
            raise InvalidInputError("request_id invalido")
        if self._idempotency_service is None:
            return None
        return self._idempotency_service.get_result(request_id)

    def get_available_count(self, ticket_type: str | TicketType) -> int:
        """Consulta el numero de entradas disponibles."""
        normalized = self._normalize_ticket_type(ticket_type)
        return self._inventory.get_available_count(normalized)

    def get_seat_status(self, seat_id: int) -> SeatInfo:
        """Consulta el estado de un asiento numerado."""
        if not validate_seat_id(seat_id):
            raise InvalidInputError(f"seat_id invalido: {seat_id}")
        return self._numbered_service.seat_status(seat_id)

    def get_client_purchases(self, client_id: str) -> list[dict[str, Any]]:
        """Retorna el historial de compras de un cliente."""
        if not validate_client_id(client_id):
            raise InvalidInputError("client_id invalido")
        if self._result_repository is None:
            return []
        return self._result_repository.get_client_purchases(client_id)

    def initialize(
        self,
        ticket_type: str | TicketType,
        total_tickets: int = TOTAL_TICKETS,
    ) -> None:
        """Inicializa el inventario en Redis."""
        normalized = self._normalize_ticket_type(ticket_type)
        self._validate_total_tickets(total_tickets)
        self._inventory.initialize(normalized, total_tickets)

    def reset(self, ticket_type: str = "all", total_tickets: int = TOTAL_TICKETS) -> None:
        """Resetea el estado del inventario."""
        if ticket_type not in ("unnumbered", "numbered", "all"):
            raise InvalidInputError(f"ticket_type invalido: {ticket_type}")
        self._validate_total_tickets(total_tickets)
        self._inventory.reset(ticket_type, total_tickets)

    @staticmethod
    def _validate_total_tickets(total_tickets: int) -> None:
        if not isinstance(total_tickets, int) or total_tickets <= 0:
            raise InvalidInputError("total_tickets debe ser un entero positivo")

    @staticmethod
    def _normalize_ticket_type(ticket_type: str | TicketType) -> str:
        if isinstance(ticket_type, TicketType):
            return ticket_type.value
        if ticket_type in (TicketType.UNNUMBERED.value, TicketType.NUMBERED.value):
            return ticket_type
        raise InvalidInputError(f"ticket_type invalido: {ticket_type}")

    @staticmethod
    def _validate_common_input(client_id: str, request_id: str) -> None:
        if not validate_client_id(client_id):
            raise InvalidInputError("client_id invalido")
        if not validate_request_id(request_id):
            raise InvalidInputError("request_id invalido")
