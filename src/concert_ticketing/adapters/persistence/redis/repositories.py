"""Repositorios Redis para inventario, idempotencia y resultados.

Implementación 100% Python usando WATCH/MULTI/EXEC (optimistic locking)
para garantizar atomicidad sin scripts Lua.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import redis as redis_lib
from redis.exceptions import WatchError

from ....core.domain.enums import PurchaseStatus, TicketType
from ....core.domain.models import PurchaseResult, SeatInfo
from ....core.ports.inventory_repository import InventoryRepository
from ....core.ports.idempotency_repository import IdempotencyRepository
from ....core.ports.result_repository import ResultRepository
from ....shared.logger import get_logger

from .key_schema import KeySchema

logger = get_logger(__name__)

# Límite de reintentos para evitar bucles infinitos
MAX_RETRIES = 100


class RedisInventoryRepository(InventoryRepository):
    """Implementación Redis del repositorio de inventario.

    Todas las operaciones de compra usan WATCH/MULTI/EXEC (optimistic locking)
    para garantizar atomicidad y consistencia bajo concurrencia.
    """

    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client

    # ---- Compras atómicas ----

    def buy_unnumbered(self, client_id: str, request_id: str) -> PurchaseResult:
        """Compra atómica de ticket no numerado via WATCH/MULTI/EXEC.

        1. WATCH sobre la clave de idempotencia y el contador de disponibles.
        2. Si ya existe el request_id, devuelve resultado previo (duplicado).
        3. Si hay tickets disponibles, decrementa atómicamente.
        4. Registra compra en hash de idempotencia e historial del cliente.
        """
        now = datetime.now(timezone.utc).isoformat()
        request_key = KeySchema.request(request_id)
        avail_key = KeySchema.UNNUMBERED_AVAILABLE
        purchases_key = KeySchema.client_purchases(client_id)

        for attempt in range(MAX_RETRIES):
            try:
                pipe = self._client.pipeline()
                pipe.watch(request_key, avail_key)

                # Verificar idempotencia
                existing = pipe.exists(request_key)
                if existing:
                    prev_data = pipe.hgetall(request_key)
                    pipe.unwatch()
                    prev_status = prev_data.get("status", "ACCEPTED")
                    return PurchaseResult(
                        status=PurchaseStatus(prev_status),
                        request_id=request_id,
                        client_id=client_id,
                        reason="duplicate_request",
                        ticket_type=TicketType.UNNUMBERED,
                        duplicate=True,
                    )

                # Verificar disponibilidad
                available = int(pipe.get(avail_key) or 0)

                if available <= 0:
                    # Registrar rechazo para idempotencia
                    pipe.multi()
                    pipe.hset(request_key, mapping={
                        "status": "REJECTED",
                        "reason": "sold_out",
                        "client_id": client_id,
                        "request_id": request_id,
                        "timestamp": now,
                    })
                    pipe.execute()
                    return PurchaseResult(
                        status=PurchaseStatus.REJECTED,
                        request_id=request_id,
                        client_id=client_id,
                        reason="sold_out",
                        ticket_type=TicketType.UNNUMBERED,
                        remaining=0,
                        duplicate=False,
                    )

                # Compra exitosa: decrementar y registrar
                pipe.multi()
                pipe.decr(avail_key)
                pipe.hset(request_key, mapping={
                    "status": "ACCEPTED",
                    "reason": "ok",
                    "client_id": client_id,
                    "request_id": request_id,
                    "ticket_type": "unnumbered",
                    "timestamp": now,
                })
                pipe.rpush(purchases_key, json.dumps({
                    "request_id": request_id,
                    "ticket_type": "unnumbered",
                    "timestamp": now,
                }))
                results = pipe.execute()
                new_count = results[0]  # resultado del DECR

                return PurchaseResult(
                    status=PurchaseStatus.ACCEPTED,
                    request_id=request_id,
                    client_id=client_id,
                    reason="ok",
                    ticket_type=TicketType.UNNUMBERED,
                    remaining=new_count,
                    duplicate=False,
                )

            except WatchError:
                logger.debug(
                    "WatchError en buy_unnumbered (intento %d), reintentando...",
                    attempt + 1,
                )
                continue

        raise RuntimeError(
            f"buy_unnumbered: máximo de reintentos ({MAX_RETRIES}) alcanzado"
        )

    def buy_numbered(
        self, client_id: str, seat_id: int, request_id: str
    ) -> PurchaseResult:
        """Compra atómica de ticket numerado via WATCH/MULTI/EXEC.

        1. WATCH sobre clave del asiento, idempotencia y contador.
        2. Si ya existe el request_id, devuelve resultado previo (duplicado).
        3. Si el asiento existe y está disponible, lo marca como vendido.
        4. Registra compra en hash de idempotencia e historial del cliente.
        """
        now = datetime.now(timezone.utc).isoformat()
        seat_key = KeySchema.seat_status(seat_id)
        request_key = KeySchema.request(request_id)
        purchases_key = KeySchema.client_purchases(client_id)
        avail_key = KeySchema.NUMBERED_AVAILABLE

        for attempt in range(MAX_RETRIES):
            try:
                pipe = self._client.pipeline()
                pipe.watch(request_key, seat_key, avail_key)

                # Verificar idempotencia
                existing = pipe.exists(request_key)
                if existing:
                    prev_data = pipe.hgetall(request_key)
                    pipe.unwatch()
                    prev_status = prev_data.get("status", "ACCEPTED")
                    return PurchaseResult(
                        status=PurchaseStatus(prev_status),
                        request_id=request_id,
                        client_id=client_id,
                        reason="duplicate_request",
                        ticket_type=TicketType.NUMBERED,
                        seat_id=seat_id,
                        duplicate=True,
                    )

                # Verificar que el asiento existe
                status = pipe.get(seat_key)
                if status is None:
                    pipe.multi()
                    pipe.hset(request_key, mapping={
                        "status": "REJECTED",
                        "reason": "invalid_seat",
                        "client_id": client_id,
                        "seat_id": str(seat_id),
                        "request_id": request_id,
                        "timestamp": now,
                    })
                    pipe.execute()
                    return PurchaseResult(
                        status=PurchaseStatus.REJECTED,
                        request_id=request_id,
                        client_id=client_id,
                        reason="invalid_seat",
                        ticket_type=TicketType.NUMBERED,
                        seat_id=seat_id,
                        duplicate=False,
                    )

                # Verificar que el asiento está disponible
                if status != "available":
                    pipe.multi()
                    pipe.hset(request_key, mapping={
                        "status": "REJECTED",
                        "reason": "seat_already_sold",
                        "client_id": client_id,
                        "seat_id": str(seat_id),
                        "request_id": request_id,
                        "timestamp": now,
                    })
                    pipe.execute()
                    return PurchaseResult(
                        status=PurchaseStatus.REJECTED,
                        request_id=request_id,
                        client_id=client_id,
                        reason="seat_already_sold",
                        ticket_type=TicketType.NUMBERED,
                        seat_id=seat_id,
                        duplicate=False,
                    )

                # Compra exitosa: marcar asiento como vendido
                pipe.multi()
                pipe.set(seat_key, f"sold:{client_id}")
                pipe.decr(avail_key)
                pipe.hset(request_key, mapping={
                    "status": "ACCEPTED",
                    "reason": "ok",
                    "client_id": client_id,
                    "seat_id": str(seat_id),
                    "request_id": request_id,
                    "ticket_type": "numbered",
                    "timestamp": now,
                })
                pipe.rpush(purchases_key, json.dumps({
                    "request_id": request_id,
                    "ticket_type": "numbered",
                    "seat_id": seat_id,
                    "timestamp": now,
                }))
                pipe.execute()

                return PurchaseResult(
                    status=PurchaseStatus.ACCEPTED,
                    request_id=request_id,
                    client_id=client_id,
                    reason="ok",
                    ticket_type=TicketType.NUMBERED,
                    seat_id=seat_id,
                    duplicate=False,
                )

            except WatchError:
                logger.debug(
                    "WatchError en buy_numbered seat=%d (intento %d), reintentando...",
                    seat_id, attempt + 1,
                )
                continue

        raise RuntimeError(
            f"buy_numbered: máximo de reintentos ({MAX_RETRIES}) alcanzado"
        )

    # ---- Consultas ----

    def get_available_count(self, ticket_type: str) -> int:
        """Tickets disponibles leyendo el contador atómico."""
        if ticket_type == "unnumbered":
            key = KeySchema.UNNUMBERED_AVAILABLE
        else:
            key = KeySchema.NUMBERED_AVAILABLE

        val = self._client.get(key)
        return int(val) if val is not None else 0

    def get_seat_status(self, seat_id: int) -> SeatInfo:
        """Estado de un asiento numerado."""
        key = KeySchema.seat_status(seat_id)
        raw = self._client.get(key)
        if raw is None:
            return SeatInfo(seat_id=seat_id, status="unknown")
        if raw == "available":
            return SeatInfo(seat_id=seat_id, status="available")
        # Formato: "sold:<client_id>"
        owner = raw.split(":", 1)[1] if ":" in raw else None
        return SeatInfo(seat_id=seat_id, status="sold", owner=owner)

    # ---- Gestión del sistema ----

    def initialize(self, ticket_type: str, total_tickets: int) -> None:
        """Inicializa el inventario usando pipelines de Redis (sin Lua).

        Para unnumbered: establece el contador de tickets disponibles.
        Para numbered: crea cada asiento como 'available' y el contador total.
        """
        pipe = self._client.pipeline()
        if ticket_type == "unnumbered":
            pipe.set(KeySchema.UNNUMBERED_AVAILABLE, total_tickets)
        elif ticket_type == "numbered":
            for seat_id in range(1, total_tickets + 1):
                pipe.set(KeySchema.seat_status(seat_id), "available")
            pipe.set(KeySchema.NUMBERED_AVAILABLE, total_tickets)
        else:
            raise ValueError(f"Tipo de ticket inválido: {ticket_type}")
        pipe.execute()
        logger.info(
            "Sistema inicializado: type=%s total=%d", ticket_type, total_tickets
        )

    def reset(self, ticket_type: str, total_tickets: int) -> None:
        """Resetea todo el estado del sistema usando SCAN + pipelines.

        Borra claves de idempotencia (requests:*), historial (purchases:*)
        y claves de inventario según el tipo de ticket.
        """
        # Borrar claves de idempotencia y compras con SCAN
        for pattern in ("requests:*", "purchases:*"):
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor, match=pattern, count=1000)
                if keys:
                    self._client.delete(*keys)
                if cursor == 0:
                    break

        # Borrar claves de inventario
        pipe = self._client.pipeline()
        if ticket_type in ("unnumbered", "all"):
            pipe.delete(KeySchema.UNNUMBERED_AVAILABLE)
        if ticket_type in ("numbered", "all"):
            for seat_id in range(1, total_tickets + 1):
                pipe.delete(KeySchema.seat_status(seat_id))
            pipe.delete(KeySchema.NUMBERED_AVAILABLE)
        pipe.execute()
        logger.info("Sistema reseteado: type=%s", ticket_type)


class RedisIdempotencyRepository(IdempotencyRepository):
    """Consulta de idempotencia sobre las claves requests:{id} de Redis."""

    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client

    def get_request_result(self, request_id: str) -> Optional[dict[str, Any]]:
        """Retorna todos los campos del hash de idempotencia."""
        key = KeySchema.request(request_id)
        data = self._client.hgetall(key)
        return data if data else None

    def request_exists(self, request_id: str) -> bool:
        """Comprueba si un request_id ya fue registrado."""
        return bool(self._client.exists(KeySchema.request(request_id)))


class RedisResultRepository(ResultRepository):
    """Consulta del historial de compras de un cliente."""

    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client

    def get_client_purchases(self, client_id: str) -> list[dict[str, Any]]:
        """Lista JSON-deserializada de compras del cliente."""
        key = KeySchema.client_purchases(client_id)
        raw_list = self._client.lrange(key, 0, -1)
        return [json.loads(item) for item in raw_list] if raw_list else []
