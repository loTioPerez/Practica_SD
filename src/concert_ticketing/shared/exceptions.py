"""Excepciones base del sistema de ticketing."""

from __future__ import annotations


class TicketingError(Exception):
    """Excepcion base del dominio."""


class InvalidInputError(TicketingError):
    """Entrada de usuario invalida."""


class RedisConnectionError(TicketingError):
    """Redis no disponible o error de conexion."""


class RabbitMQConnectionError(TicketingError):
    """RabbitMQ no disponible o error de conexion."""
