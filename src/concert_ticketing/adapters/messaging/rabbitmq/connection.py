"""Gestion de conexiones RabbitMQ."""

from __future__ import annotations

from typing import Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from ....shared.config import AppConfig, RabbitMQConfig
from ....shared.logger import get_logger

logger = get_logger(__name__)


def create_rabbitmq_connection(
    config: Optional[RabbitMQConfig] = None,
) -> BlockingConnection:
    """Crea una conexion bloqueante a RabbitMQ."""
    if config is None:
        config = AppConfig.from_env().rabbitmq
    credentials = pika.PlainCredentials(config.user, config.password)
    params = pika.ConnectionParameters(
        host=config.host,
        port=config.port,
        virtual_host=config.vhost,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    connection = pika.BlockingConnection(params)
    logger.info("Conexion RabbitMQ establecida -> %s:%s", config.host, config.port)
    return connection


def create_channel(connection: BlockingConnection) -> BlockingChannel:
    """Crea un canal sobre una conexion existente."""
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    return channel
