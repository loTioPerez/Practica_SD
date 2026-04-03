"""Esquema de claves Redis para compras, asientos e idempotencia."""


class KeySchema:
    """Genera claves Redis consistentes para todo el sistema."""

    # ---- Unnumbered ----
    UNNUMBERED_AVAILABLE = "tickets:unnumbered:available"

    # ---- Numbered ----
    NUMBERED_AVAILABLE = "tickets:numbered:available"

    @staticmethod
    def seat_status(seat_id: int) -> str:
        """Clave para el estado de un asiento: tickets:numbered:{id}:status"""
        return f"tickets:numbered:{seat_id}:status"

    @staticmethod
    def request(request_id: str) -> str:
        """Clave de idempotencia: requests:{request_id}"""
        return f"requests:{request_id}"

    @staticmethod
    def client_purchases(client_id: str) -> str:
        """Historial de compras de un cliente: purchases:{client_id}"""
        return f"purchases:{client_id}"
