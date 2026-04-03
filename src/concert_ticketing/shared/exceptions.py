"""Excepciones de dominio e infraestructura compartidas."""


class TicketingBaseError(Exception):
    """Excepción base del sistema de ticketing."""


# ---- Errores de dominio ----

class TicketNotAvailableError(TicketingBaseError):
    """No quedan tickets disponibles."""
    def __init__(self, message: str = "No hay tickets disponibles") -> None:
        super().__init__(message)


class SeatAlreadySoldError(TicketingBaseError):
    """El asiento solicitado ya fue vendido."""
    def __init__(self, seat_id: int, message: str | None = None) -> None:
        self.seat_id = seat_id
        super().__init__(message or f"El asiento {seat_id} ya fue vendido")


class DuplicateRequestError(TicketingBaseError):
    """Se detectó un request_id duplicado (idempotencia)."""
    def __init__(self, request_id: str, message: str | None = None) -> None:
        self.request_id = request_id
        super().__init__(message or f"Request {request_id} ya fue procesado")


class InvalidSeatError(TicketingBaseError):
    """El seat_id proporcionado no existe."""
    def __init__(self, seat_id: int, message: str | None = None) -> None:
        self.seat_id = seat_id
        super().__init__(message or f"Asiento {seat_id} no válido")


class InvalidInputError(TicketingBaseError):
    """Parámetros de entrada inválidos."""


# ---- Errores de infraestructura ----

class RedisConnectionError(TicketingBaseError):
    """Fallo al conectar con Redis."""


class ScriptLoadError(TicketingBaseError):
    """Fallo al cargar un script Lua en Redis."""
