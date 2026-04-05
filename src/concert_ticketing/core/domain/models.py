"""Modelos de dominio para compras, resultados y asientos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .enums import PurchaseStatus, RejectionReason, TicketType


@dataclass(frozen=True)
class PurchaseRequest:
    """Solicitud de compra emitida por un cliente."""

    client_id: str
    request_id: str
    seat_id: Optional[int] = None


@dataclass(frozen=True)
class PurchaseResult:
    """Resultado devuelto tras procesar una solicitud de compra."""

    status: PurchaseStatus
    request_id: str
    client_id: str
    reason: str
    ticket_type: Optional[str] = None
    seat_id: Optional[int] = None
    remaining: Optional[int] = None
    duplicate: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def success(self) -> bool:
        return self.status == PurchaseStatus.ACCEPTED

    @staticmethod
    def accepted(
        request_id: str,
        client_id: str,
        ticket_type: TicketType | str,
        seat_id: Optional[int] = None,
        remaining: Optional[int] = None,
        duplicate: bool = False,
    ) -> PurchaseResult:
        tt = ticket_type.value if isinstance(ticket_type, TicketType) else ticket_type
        return PurchaseResult(
            status=PurchaseStatus.ACCEPTED,
            request_id=request_id,
            client_id=client_id,
            reason="ok",
            ticket_type=tt,
            seat_id=seat_id,
            remaining=remaining,
            duplicate=duplicate,
        )

    @staticmethod
    def rejected(
        request_id: str,
        client_id: str,
        reason: RejectionReason | str,
        ticket_type: TicketType | str | None = None,
        seat_id: Optional[int] = None,
        duplicate: bool = False,
    ) -> PurchaseResult:
        r = reason.value if isinstance(reason, RejectionReason) else reason
        tt = None
        if ticket_type is not None:
            tt = ticket_type.value if isinstance(ticket_type, TicketType) else ticket_type
        return PurchaseResult(
            status=PurchaseStatus.REJECTED,
            request_id=request_id,
            client_id=client_id,
            reason=r,
            ticket_type=tt,
            seat_id=seat_id,
            duplicate=duplicate,
        )


@dataclass(frozen=True)
class SeatInfo:
    """Informacion sobre el estado de un asiento numerado."""

    seat_id: int
    status: str
    owner: Optional[str] = None
