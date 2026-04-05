"""Enumeraciones del dominio de compra de entradas."""

from __future__ import annotations

from enum import Enum


class TicketType(str, Enum):
    """Tipos de entrada disponibles."""

    UNNUMBERED = "unnumbered"
    NUMBERED = "numbered"


class PurchaseStatus(str, Enum):
    """Estado de una operacion de compra."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RejectionReason(str, Enum):
    """Motivos posibles de rechazo de una compra."""

    SOLD_OUT = "sold_out"
    SEAT_ALREADY_SOLD = "seat_already_sold"
    DUPLICATE_REQUEST = "duplicate_request"
    INVALID_SEAT = "invalid_seat"
    INVALID_INPUT = "invalid_input"


class SeatStatus(str, Enum):
    """Estado de un asiento numerado."""

    AVAILABLE = "available"
    SOLD = "sold"
