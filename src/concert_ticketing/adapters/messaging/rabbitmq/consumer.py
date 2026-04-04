"""Consumer de mensajes de compra desde RabbitMQ."""

from __future__ import annotations

from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from ....shared.logger import get_logger
from .queue_setup import PURCHASE_QUEUE
from .serializer import deserialize_request

logger = get_logger(__name__)


class RabbitMQConsumer:
    """Consume peticiones de compra de la cola principal de RabbitMQ."""

    def __init__(self, channel: BlockingChannel) -> None:
        self._channel = channel

    def consume(
        self,
        callback: Callable[[dict, BasicProperties], dict],
    ) -> None:
        """Inicia el consumo bloqueante de mensajes.

        El callback recibe (request_data_dict, properties) y devuelve
        un dict con el resultado de la compra.
        """

        def on_message(
            ch: BlockingChannel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
        ) -> None:
            try:
                request_data = deserialize_request(body)
                logger.info(
                    "Mensaje recibido: request_id=%s",
                    request_data.get("request_id", "unknown"),
                )
                result = callback(request_data, properties)

                # Si hay reply_to, enviamos el resultado de vuelta
                if properties.reply_to:
                    from .serializer import serialize_result
                    from .queue_setup import RESULT_EXCHANGE

                    ch.basic_publish(
                        exchange=RESULT_EXCHANGE,
                        routing_key=properties.reply_to,
                        body=serialize_result(result),
                        properties=pika.BasicProperties(
                            correlation_id=properties.correlation_id,
                            content_type="application/json",
                        ),
                    )

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception:
                logger.exception("Error procesando mensaje")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self._channel.basic_consume(
            queue=PURCHASE_QUEUE,
            on_message_callback=on_message,
            auto_ack=False,
        )

        logger.info("Consumiendo de '%s'. Esperando mensajes...", PURCHASE_QUEUE)
        self._channel.start_consuming()
