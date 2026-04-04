"""Worker que consume peticiones de RabbitMQ y las procesa con PurchaseService."""

from __future__ import annotations

import signal
import sys
from typing import Any

import pika
from pika.spec import BasicProperties

from concert_ticketing.adapters.messaging.rabbitmq.connection import (
    create_channel,
    create_rabbitmq_connection,
)
from concert_ticketing.adapters.messaging.rabbitmq.consumer import RabbitMQConsumer
from concert_ticketing.adapters.messaging.rabbitmq.queue_setup import setup_queues
from concert_ticketing.adapters.persistence.redis.connection import create_redis_client
from concert_ticketing.adapters.persistence.redis.repositories import (
    RedisIdempotencyRepository,
    RedisInventoryRepository,
    RedisResultRepository,
)
from concert_ticketing.core.services.purchase_service import PurchaseService
from concert_ticketing.shared.config import AppConfig
from concert_ticketing.shared.logger import get_logger
from concert_ticketing.shared.serialization import purchase_result_to_dict

logger = get_logger(__name__)


class PurchaseProcessor:
    """Procesa mensajes de compra usando el PurchaseService."""

    def __init__(self, service: PurchaseService) -> None:
        self._service = service

    def process_message(
        self,
        request_data: dict[str, Any],
        properties: BasicProperties,
    ) -> dict[str, Any]:
        """Procesa un mensaje de compra y devuelve el resultado."""
        ticket_type = request_data.get("ticket_type", "unnumbered")
        client_id = request_data["client_id"]
        request_id = request_data["request_id"]

        try:
            if ticket_type == "numbered":
                seat_id = int(request_data["seat_id"])
                result = self._service.buy_numbered(client_id, seat_id, request_id)
            else:
                result = self._service.buy_unnumbered(client_id, request_id)

            return purchase_result_to_dict(result)

        except Exception as exc:
            logger.exception(
                "Error procesando request_id=%s: %s", request_id, exc,
            )
            return {
                "status": "REJECTED",
                "request_id": request_id,
                "client_id": client_id,
                "reason": "internal_error",
                "duplicate": False,
            }


def build_service(config: AppConfig) -> PurchaseService:
    """Construye PurchaseService conectado a Redis."""
    client = create_redis_client(config.redis)
    return PurchaseService(
        inventory=RedisInventoryRepository(client),
        idempotency=RedisIdempotencyRepository(client),
        results=RedisResultRepository(client),
    )


def main() -> None:
    """Punto de entrada del worker."""
    config = AppConfig.from_env()
    service = build_service(config)
    processor = PurchaseProcessor(service)

    connection = create_rabbitmq_connection(config.rabbitmq)
    channel = create_channel(connection)
    setup_queues(channel)

    consumer = RabbitMQConsumer(channel)

    def handle_signal(signum: int, frame: Any) -> None:
        logger.info("Señal recibida (%s), cerrando worker...", signum)
        try:
            channel.stop_consuming()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger.info("Worker iniciado. Consumiendo peticiones de compra...")
    consumer.consume(processor.process_message)


if __name__ == "__main__":
    main()
