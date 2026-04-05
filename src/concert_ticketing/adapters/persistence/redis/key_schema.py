"""Esquema de claves Redis para el sistema de ticketing."""

from __future__ import annotations


class KeySchema:
    """Genera las claves Redis siguiendo un esquema consistente."""

    PREFIX = "ct"

    # --- Inventario no numerado ---
    @staticmethod
    def unnumbered_counter() -> str:
        return f"{KeySchema.PREFIX}:unnumbered:available"

    # --- Inventario numerado ---
    @staticmethod
    def numbered_seat(seat_id: int) -> str:
        return f"{KeySchema.PREFIX}:numbered:seat:{seat_id}"

    @staticmethod
    def numbered_available_set() -> str:
        return f"{KeySchema.PREFIX}:numbered:available_set"

    # --- Idempotencia ---
    @staticmethod
    def idempotency(request_id: str) -> str:
        return f"{KeySchema.PREFIX}:idempotency:{request_id}"

    # --- Resultados por cliente ---
    @staticmethod
    def client_purchases(client_id: str) -> str:
        return f"{KeySchema.PREFIX}:client:{client_id}:purchases"

    # --- Claves de control ---
    @staticmethod
    def all_keys_pattern() -> str:
        return f"{KeySchema.PREFIX}:*"
