"""Modelos principales del dominio: peticiones, resultados y datos de compra."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .enums import PurchaseStatus, RejectionReason, TicketType


@dataclass(frozen=True)
class PurchaseRequest:
    """Solicitud de compra de una entrada."""
    client_id: str
    request_id: str
    ticket_type: TicketType
    seat_id: Optional[int] = None  # Solo para numbered

    def __post_init__(self) -> None:
        if self.ticket_type == TicketType.NUMBERED and self.seat_id is None:
            raise ValueError("seat_id es obligatorio para tickets numerados")


@dataclass(frozen=True)
class PurchaseResult:
    """Resultado de una operación de compra."""
    status: PurchaseStatus
    request_id: str
    client_id: str
    reason: str = "ok"
    ticket_type: Optional[TicketType] = None
    seat_id: Optional[int] = None
    remaining: Optional[int] = None
    duplicate: bool = False

    @property
    def success(self) -> bool:
        """Indica si la compra fue exitosa."""
        return self.status == PurchaseStatus.ACCEPTED

    @staticmethod
    def accepted(
        request_id: str,
        client_id: str,
        ticket_type: TicketType,
        seat_id: Optional[int] = None,
        remaining: Optional[int] = None,
        duplicate: bool = False,
    ) -> PurchaseResult:
        """Crea un resultado exitoso."""
        return PurchaseResult(
            status=PurchaseStatus.ACCEPTED,
            request_id=request_id,
            client_id=client_id,
            reason="ok",
            ticket_type=ticket_type,
            seat_id=seat_id,
            remaining=remaining,
            duplicate=duplicate,
        )

    @staticmethod
    def rejected(
        request_id: str,
        client_id: str,
        reason: str,
        ticket_type: Optional[TicketType] = None,
        seat_id: Optional[int] = None,
        duplicate: bool = False,
    ) -> PurchaseResult:
        """Crea un resultado de rechazo."""
        return PurchaseResult(
            status=PurchaseStatus.REJECTED,
            request_id=request_id,
            client_id=client_id,
            reason=reason,
            ticket_type=ticket_type,
            seat_id=seat_id,
            duplicate=duplicate,
        )


@dataclass(frozen=True)
class SeatInfo:
    """Información sobre el estado de un asiento numerado."""
    seat_id: int
    status: str  # 'available' o 'sold:<client_id>'
    owner: Optional[str] = None  # client_id del comprador si está vendido

