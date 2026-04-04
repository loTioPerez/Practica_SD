"""Declaracion de colas y exchanges para RabbitMQ."""

from __future__ import annotations

from pika.adapters.blocking_connection import BlockingChannel

from ....shared.logger import get_logger

logger = get_logger(__name__)

# Nombres de colas
PURCHASE_QUEUE = "purchase_requests"
RESULT_EXCHANGE = "purchase_results"
RESULT_EXCHANGE_TYPE = "direct"


def setup_queues(channel: BlockingChannel) -> None:
    """Declara las colas y exchanges necesarios."""
    # Cola principal de peticiones de compra
    channel.queue_declare(queue=PURCHASE_QUEUE, durable=True)
    logger.info("Cola '%s' declarada.", PURCHASE_QUEUE)

    # Exchange para enviar resultados de vuelta
    channel.exchange_declare(
        exchange=RESULT_EXCHANGE,
        exchange_type=RESULT_EXCHANGE_TYPE,
        durable=True,
    )
    logger.info("Exchange '%s' declarado.", RESULT_EXCHANGE)


def declare_reply_queue(channel: BlockingChannel, reply_queue: str) -> None:
    """Declara una cola de respuesta temporal para un gateway."""
    channel.queue_declare(queue=reply_queue, durable=False, auto_delete=True)
    channel.queue_bind(
        queue=reply_queue,
        exchange=RESULT_EXCHANGE,
        routing_key=reply_queue,
    )
    logger.info("Cola de respuesta '%s' declarada y enlazada.", reply_queue)
