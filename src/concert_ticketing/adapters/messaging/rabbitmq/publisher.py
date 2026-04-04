"""Publisher de mensajes de compra a RabbitMQ."""

from __future__ import annotations

from typing import Any, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from ....shared.logger import get_logger
from .queue_setup import PURCHASE_QUEUE
from .serializer import serialize_request

logger = get_logger(__name__)


class RabbitMQPublisher:
    """Publica peticiones de compra en la cola de RabbitMQ."""

    def __init__(self, channel: BlockingChannel) -> None:
        self._channel = channel

    def publish_purchase_request(
        self,
        request_data: dict[str, Any],
        reply_queue: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publica una peticion de compra en la cola principal."""
        properties = pika.BasicProperties(
            delivery_mode=2,  # persistente
            content_type="application/json",
        )
        if reply_queue:
            properties.reply_to = reply_queue
        if correlation_id:
            properties.correlation_id = correlation_id

        self._channel.basic_publish(
            exchange="",
            routing_key=PURCHASE_QUEUE,
            body=serialize_request(request_data),
            properties=properties,
        )
        logger.debug(
            "Peticion publicada en '%s': %s",
            PURCHASE_QUEUE,
            request_data.get("request_id", "unknown"),
        )
