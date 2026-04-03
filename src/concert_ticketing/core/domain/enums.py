"""Enumeraciones del dominio: modos, estados y motivos de fallo."""

from enum import Enum


class TicketType(str, Enum):
    """Tipo de entrada: numerada o no numerada."""
    UNNUMBERED = "unnumbered"
    NUMBERED = "numbered"


class PurchaseStatus(str, Enum):
    """Estado final de una solicitud de compra."""
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RejectionReason(str, Enum):
    """Motivo por el que se rechazó una compra."""
    SOLD_OUT = "sold_out"
    SEAT_ALREADY_SOLD = "seat_already_sold"
    INVALID_SEAT = "invalid_seat"
    DUPLICATE_REQUEST = "duplicate_request"
    INVALID_INPUT = "invalid_input"


class SeatStatus(str, Enum):
    """Estado de un asiento numerado."""
    AVAILABLE = "available"
    SOLD = "sold"
