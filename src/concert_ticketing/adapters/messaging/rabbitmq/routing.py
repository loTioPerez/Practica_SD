"""Logica de enrutamiento de mensajes RabbitMQ."""

from __future__ import annotations


def get_routing_key(ticket_type: str) -> str:
    """Genera la routing key basada en el tipo de ticket.

    Actualmente se usa una sola cola, pero esta funcion permite
    extender a multiples colas por tipo en el futuro.
    """
    from .queue_setup import PURCHASE_QUEUE

    return PURCHASE_QUEUE
