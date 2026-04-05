"""Gateway indirecto: recibe peticiones HTTP y las publica en RabbitMQ.

El resultado se obtiene esperando en una cola de respuesta temporal
(patron RPC asíncrono con reply queues).

Incluye retry logic para manejar RabbitMQ no disponible al arrancar.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Optional

import pika
import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

from concert_ticketing.adapters.messaging.rabbitmq.connection import (
    create_channel,
    create_rabbitmq_connection,
)
from concert_ticketing.adapters.messaging.rabbitmq.publisher import RabbitMQPublisher
from concert_ticketing.adapters.messaging.rabbitmq.queue_setup import (
    RESULT_EXCHANGE,
    declare_reply_queue,
    setup_queues,
)
from concert_ticketing.adapters.messaging.rabbitmq.serializer import deserialize_result
from concert_ticketing.adapters.persistence.redis.connection import create_redis_client
from concert_ticketing.adapters.persistence.redis.repositories import (
    RedisIdempotencyRepository,
    RedisResultRepository,
)
from concert_ticketing.shared.config import AppConfig
from concert_ticketing.shared.health import check_rabbitmq_health, check_redis_health
from concert_ticketing.shared.logger import get_logger

logger = get_logger(__name__)

# ---- Constantes de retry ----
MAX_RETRIES = 10
RETRY_BASE_DELAY = 2  # segundos (back-off exponencial: 2, 4, 8, ...)
RETRY_MAX_DELAY = 30  # tope de espera entre reintentos

# ---- Estado global del gateway ----

_config: AppConfig | None = None
_pending_responses: dict[str, dict[str, Any]] = {}
_response_events: dict[str, threading.Event] = {}
_lock = threading.Lock()

REPLY_QUEUE = f"reply_{uuid.uuid4().hex[:12]}"
RESPONSE_TIMEOUT = 30  # segundos

# Conexiones (se inicializan con retry en _init_connections)
_publisher: RabbitMQPublisher | None = None
_idempotency_repo: RedisIdempotencyRepository | None = None
_result_repo: RedisResultRepository | None = None
_ready = False


def _wait_and_connect_rabbitmq(rmq_config):
    """Intenta conectar a RabbitMQ con reintentos y back-off exponencial."""
    delay = RETRY_BASE_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = create_rabbitmq_connection(rmq_config)
            logger.info(
                "Conexión RabbitMQ establecida (intento %d/%d)",
                attempt, MAX_RETRIES,
            )
            return conn
        except Exception as exc:
            if attempt == MAX_RETRIES:
                logger.error(
                    "No se pudo conectar a RabbitMQ tras %d intentos: %s",
                    MAX_RETRIES, exc,
                )
                raise
            logger.warning(
                "RabbitMQ no disponible (intento %d/%d): %s — reintentando en %ds...",
                attempt, MAX_RETRIES, exc, delay,
            )
            time.sleep(delay)
            delay = min(delay * 2, RETRY_MAX_DELAY)


# ---- Hilo consumidor de respuestas ----


def _reply_consumer_thread(rmq_config) -> None:
    """Hilo dedicado a consumir respuestas del worker (con retry)."""
    while True:
        try:
            conn = _wait_and_connect_rabbitmq(rmq_config)
            ch = create_channel(conn)
            declare_reply_queue(ch, REPLY_QUEUE)

            def on_reply(
                ch: Any, method: Any, properties: pika.BasicProperties, body: bytes
            ) -> None:
                cid = properties.correlation_id
                if cid:
                    result = deserialize_result(body)
                    with _lock:
                        _pending_responses[cid] = result
                        event = _response_events.get(cid)
                    if event:
                        event.set()
                ch.basic_ack(delivery_tag=method.delivery_tag)

            ch.basic_consume(
                queue=REPLY_QUEUE, on_message_callback=on_reply, auto_ack=False
            )
            logger.info("Hilo consumidor de respuestas iniciado en '%s'", REPLY_QUEUE)
            ch.start_consuming()
        except Exception:
            logger.exception(
                "Error en hilo consumidor de respuestas — reconectando en 5s..."
            )
            time.sleep(5)


# ---- Inicializacion con retry ----


def _init_connections() -> None:
    """Inicializa conexiones a RabbitMQ y Redis con retry logic."""
    global _config, _publisher, _idempotency_repo, _result_repo, _ready

    _config = AppConfig.from_env()

    # RabbitMQ con retry
    logger.info("Conectando a RabbitMQ...")
    rmq_conn = _wait_and_connect_rabbitmq(_config.rabbitmq)
    rmq_channel = create_channel(rmq_conn)
    setup_queues(rmq_channel)
    _publisher = RabbitMQPublisher(rmq_channel)

    # Redis
    logger.info("Conectando a Redis...")
    redis_client = create_redis_client(_config.redis)
    _idempotency_repo = RedisIdempotencyRepository(redis_client)
    _result_repo = RedisResultRepository(redis_client)

    # Arrancar hilo de respuestas
    reply_thread = threading.Thread(
        target=_reply_consumer_thread, args=(_config.rabbitmq,), daemon=True,
    )
    reply_thread.start()

    _ready = True
    logger.info("Gateway indirecto inicializado correctamente")


# Ejecutar inicialización
try:
    _init_connections()
except Exception:
    logger.exception(
        "FATAL: No se pudo inicializar el gateway. "
        "Verifica que Redis y RabbitMQ estén corriendo."
    )
    # La app arrancará pero devolverá 503 en las peticiones

# ---- FastAPI App ----

app = FastAPI(
    title="Concert Ticketing Indirect Gateway",
    version="0.1.0",
    description="Gateway indirecto que publica en RabbitMQ y espera respuesta.",
)


def _wait_for_result(correlation_id: str) -> Optional[dict[str, Any]]:
    """Espera la respuesta del worker con timeout."""
    event = threading.Event()
    with _lock:
        _response_events[correlation_id] = event

    event.wait(timeout=RESPONSE_TIMEOUT)

    with _lock:
        _response_events.pop(correlation_id, None)
        return _pending_responses.pop(correlation_id, None)


def _publish_and_wait(request_data: dict[str, Any]) -> JSONResponse:
    """Publica en RabbitMQ y espera la respuesta del worker."""
    if not _ready or _publisher is None:
        return JSONResponse(
            status_code=503,
            content={"detail": "Gateway no inicializado. RabbitMQ/Redis no disponible."},
        )

    correlation_id = request_data.get("request_id", uuid.uuid4().hex)

    try:
        _publisher.publish_purchase_request(
            request_data=request_data,
            reply_queue=REPLY_QUEUE,
            correlation_id=correlation_id,
        )
    except Exception as exc:
        logger.exception("Error publicando en RabbitMQ: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Error de conexión con RabbitMQ"},
        )

    result = _wait_for_result(correlation_id)
    if result is None:
        return JSONResponse(
            status_code=504,
            content={"detail": "timeout esperando respuesta del worker"},
        )

    # Determinar codigo HTTP
    status = result.get("status", "")
    reason = result.get("reason", "")
    duplicate = result.get("duplicate", False)

    if duplicate or status == "ACCEPTED":
        http_code = 200
    elif reason in ("sold_out", "seat_already_sold"):
        http_code = 409
    elif reason in ("invalid_seat", "invalid_input"):
        http_code = 400
    else:
        http_code = 400

    return JSONResponse(status_code=http_code, content=result)


@app.get("/health")
def health_check() -> dict:
    if _config is None:
        return {"status": "not_initialized", "detail": "Gateway no inicializado"}

    redis_h = check_redis_health(
        host=_config.redis.host, port=_config.redis.port, db=_config.redis.db,
    )
    rmq_h = check_rabbitmq_health(
        host=_config.rabbitmq.host, port=_config.rabbitmq.port,
        user=_config.rabbitmq.user, password=_config.rabbitmq.password,
    )
    healthy = redis_h.healthy and rmq_h.healthy and _ready
    return {
        "status": "ok" if healthy else "degraded",
        "gateway_ready": _ready,
        "redis_healthy": redis_h.healthy,
        "redis_detail": redis_h.detail,
        "rabbitmq_healthy": rmq_h.healthy,
        "rabbitmq_detail": rmq_h.detail,
    }


@app.post("/buy/unnumbered")
def buy_unnumbered(payload: dict) -> JSONResponse:
    """Publica compra no numerada en RabbitMQ."""
    request_data = {
        "ticket_type": "unnumbered",
        "client_id": payload["client_id"],
        "request_id": payload["request_id"],
    }
    return _publish_and_wait(request_data)


@app.post("/buy/numbered")
def buy_numbered(payload: dict) -> JSONResponse:
    """Publica compra numerada en RabbitMQ."""
    request_data = {
        "ticket_type": "numbered",
        "client_id": payload["client_id"],
        "seat_id": payload["seat_id"],
        "request_id": payload["request_id"],
    }
    return _publish_and_wait(request_data)


@app.get("/results/{request_id}")
@app.get("/requests/{request_id}")
def get_request_result(request_id: str) -> dict:
    """Consulta resultado almacenado en Redis."""
    if _idempotency_repo is None:
        return {"request_id": request_id, "found": False, "error": "Gateway no inicializado"}
    result = _idempotency_repo.get_request_result(request_id)
    return {
        "request_id": request_id,
        "found": result is not None,
        "result": result,
    }


@app.get("/clients/{client_id}/purchases")
def get_client_purchases(client_id: str) -> dict:
    """Historial de compras de un cliente."""
    if _result_repo is None:
        return {"client_id": client_id, "purchases": [], "error": "Gateway no inicializado"}
    purchases = _result_repo.get_client_purchases(client_id)
    return {"client_id": client_id, "purchases": purchases}


def main() -> None:
    cfg = _config or AppConfig.from_env()
    uvicorn.run(
        "concert_ticketing.apps.indirect_gateway.main:app",
        host=cfg.host,
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    main()
