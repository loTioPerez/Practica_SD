"""Implementacion Redis de los repositorios usando WATCH/MULTI/EXEC."""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import redis
from redis import WatchError

from ....core.domain.enums import (
    PurchaseStatus,
    RejectionReason,
    SeatStatus,
    TicketType,
)
from ....core.domain.models import PurchaseResult, SeatInfo
from ....core.ports.idempotency_repository import IdempotencyRepository
from ....core.ports.inventory_repository import InventoryRepository
from ....core.ports.result_repository import ResultRepository
from ....shared.logger import get_logger
from ....shared.serialization import purchase_result_to_dict
from .key_schema import KeySchema

logger = get_logger(__name__)

_MAX_RETRIES = 5


class RedisInventoryRepository(InventoryRepository):
    """Repositorio de inventario respaldado por Redis con transacciones optimistas."""

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    # ---- compra no numerada (WATCH/MULTI/EXEC) ----

    def buy_unnumbered(self, client_id: str, request_id: str) -> PurchaseResult:
        counter_key = KeySchema.unnumbered_counter()
        idemp_key = KeySchema.idempotency(request_id)

        for attempt in range(_MAX_RETRIES):
            try:
                with self._client.pipeline() as pipe:
                    pipe.watch(counter_key, idemp_key)

                    # idempotencia
                    existing = pipe.get(idemp_key)
                    if existing is not None:
                        stored = json.loads(existing)
                        return PurchaseResult(
                            status=PurchaseStatus(stored["status"]),
                            request_id=request_id,
                            client_id=stored.get("client_id", client_id),
                            reason=stored.get("reason", "ok"),
                            ticket_type=stored.get("ticket_type"),
                            remaining=stored.get("remaining"),
                            duplicate=True,
                        )

                    available = int(pipe.get(counter_key) or 0)
                    if available <= 0:
                        return PurchaseResult.rejected(
                            request_id=request_id,
                            client_id=client_id,
                            reason=RejectionReason.SOLD_OUT,
                            ticket_type=TicketType.UNNUMBERED,
                        )

                    pipe.multi()
                    pipe.decr(counter_key)
                    new_remaining = available - 1

                    result = PurchaseResult.accepted(
                        request_id=request_id,
                        client_id=client_id,
                        ticket_type=TicketType.UNNUMBERED,
                        remaining=new_remaining,
                    )
                    result_dict = purchase_result_to_dict(result)
                    pipe.set(idemp_key, json.dumps(result_dict))
                    pipe.rpush(
                        KeySchema.client_purchases(client_id),
                        json.dumps(result_dict),
                    )
                    pipe.execute()
                    return result

            except WatchError:
                logger.debug(
                    "WatchError en buy_unnumbered intento %d/%d",
                    attempt + 1, _MAX_RETRIES,
                )
                continue

        return PurchaseResult.rejected(
            request_id=request_id,
            client_id=client_id,
            reason=RejectionReason.SOLD_OUT,
            ticket_type=TicketType.UNNUMBERED,
        )

    # ---- compra numerada (WATCH/MULTI/EXEC) ----

    def buy_numbered(self, client_id: str, seat_id: int, request_id: str) -> PurchaseResult:
        seat_key = KeySchema.numbered_seat(seat_id)
        idemp_key = KeySchema.idempotency(request_id)
        available_set_key = KeySchema.numbered_available_set()

        for attempt in range(_MAX_RETRIES):
            try:
                with self._client.pipeline() as pipe:
                    pipe.watch(seat_key, idemp_key)

                    # idempotencia
                    existing = pipe.get(idemp_key)
                    if existing is not None:
                        stored = json.loads(existing)
                        return PurchaseResult(
                            status=PurchaseStatus(stored["status"]),
                            request_id=request_id,
                            client_id=stored.get("client_id", client_id),
                            reason=stored.get("reason", "ok"),
                            ticket_type=stored.get("ticket_type"),
                            seat_id=stored.get("seat_id"),
                            duplicate=True,
                        )

                    seat_data = pipe.get(seat_key)
                    if seat_data is None:
                        return PurchaseResult.rejected(
                            request_id=request_id,
                            client_id=client_id,
                            reason=RejectionReason.INVALID_SEAT,
                            ticket_type=TicketType.NUMBERED,
                            seat_id=seat_id,
                        )

                    seat_info = json.loads(seat_data)
                    if seat_info.get("status") == SeatStatus.SOLD.value:
                        return PurchaseResult.rejected(
                            request_id=request_id,
                            client_id=client_id,
                            reason=RejectionReason.SEAT_ALREADY_SOLD,
                            ticket_type=TicketType.NUMBERED,
                            seat_id=seat_id,
                        )

                    pipe.multi()
                    seat_info_new = {
                        "seat_id": seat_id,
                        "status": SeatStatus.SOLD.value,
                        "owner": client_id,
                    }
                    pipe.set(seat_key, json.dumps(seat_info_new))
                    pipe.srem(available_set_key, str(seat_id))

                    result = PurchaseResult.accepted(
                        request_id=request_id,
                        client_id=client_id,
                        ticket_type=TicketType.NUMBERED,
                        seat_id=seat_id,
                    )
                    result_dict = purchase_result_to_dict(result)
                    pipe.set(idemp_key, json.dumps(result_dict))
                    pipe.rpush(
                        KeySchema.client_purchases(client_id),
                        json.dumps(result_dict),
                    )
                    pipe.execute()
                    return result

            except WatchError:
                logger.debug(
                    "WatchError en buy_numbered intento %d/%d",
                    attempt + 1, _MAX_RETRIES,
                )
                continue

        return PurchaseResult.rejected(
            request_id=request_id,
            client_id=client_id,
            reason=RejectionReason.SEAT_ALREADY_SOLD,
            ticket_type=TicketType.NUMBERED,
            seat_id=seat_id,
        )

    # ---- consultas ----

    def get_available_count(self, ticket_type: str) -> int:
        if ticket_type == TicketType.UNNUMBERED.value:
            val = self._client.get(KeySchema.unnumbered_counter())
            return int(val) if val is not None else 0
        elif ticket_type == TicketType.NUMBERED.value:
            return self._client.scard(KeySchema.numbered_available_set())
        return 0

    def get_seat_status(self, seat_id: int) -> SeatInfo:
        data = self._client.get(KeySchema.numbered_seat(seat_id))
        if data is None:
            return SeatInfo(seat_id=seat_id, status=SeatStatus.AVAILABLE.value)
        info = json.loads(data)
        return SeatInfo(
            seat_id=seat_id,
            status=info.get("status", SeatStatus.AVAILABLE.value),
            owner=info.get("owner"),
        )

    # ---- inicializacion / reset ----

    def initialize(self, ticket_type: str, total_tickets: int) -> None:
        if ticket_type in ("unnumbered", "all"):
            self._client.set(KeySchema.unnumbered_counter(), total_tickets)
            logger.info("Inventario unnumbered inicializado: %d", total_tickets)

        if ticket_type in ("numbered", "all"):
            pipe = self._client.pipeline()
            for seat_id in range(1, total_tickets + 1):
                seat_data = json.dumps({
                    "seat_id": seat_id,
                    "status": SeatStatus.AVAILABLE.value,
                    "owner": None,
                })
                pipe.set(KeySchema.numbered_seat(seat_id), seat_data)
                pipe.sadd(KeySchema.numbered_available_set(), str(seat_id))
                if seat_id % 5000 == 0:
                    pipe.execute()
                    pipe = self._client.pipeline()
            pipe.execute()
            logger.info("Inventario numbered inicializado: %d asientos", total_tickets)

    def reset(self, ticket_type: str, total_tickets: int) -> None:
        if ticket_type == "all":
            # Borra todas las claves del sistema
            cursor = 0
            while True:
                cursor, keys = self._client.scan(
                    cursor=cursor, match=KeySchema.all_keys_pattern(), count=1000,
                )
                if keys:
                    self._client.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Estado Redis reseteado completamente.")
        elif ticket_type == "unnumbered":
            self._client.delete(KeySchema.unnumbered_counter())
        elif ticket_type == "numbered":
            self._client.delete(KeySchema.numbered_available_set())
            cursor = 0
            while True:
                cursor, keys = self._client.scan(
                    cursor=cursor, match=f"{KeySchema.PREFIX}:numbered:seat:*", count=1000,
                )
                if keys:
                    self._client.delete(*keys)
                if cursor == 0:
                    break


class RedisIdempotencyRepository(IdempotencyRepository):
    """Repositorio de idempotencia respaldado por Redis."""

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def request_exists(self, request_id: str) -> bool:
        return self._client.exists(KeySchema.idempotency(request_id)) > 0

    def get_request_result(self, request_id: str) -> Optional[dict[str, Any]]:
        raw = self._client.get(KeySchema.idempotency(request_id))
        if raw is None:
            return None
        return json.loads(raw)

    def store_result(self, request_id: str, result: dict[str, Any]) -> None:
        self._client.set(KeySchema.idempotency(request_id), json.dumps(result))


class RedisResultRepository(ResultRepository):
    """Repositorio de historial de compras respaldado por Redis."""

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def store_purchase(self, client_id: str, result: dict[str, Any]) -> None:
        self._client.rpush(
            KeySchema.client_purchases(client_id), json.dumps(result),
        )

    def get_client_purchases(self, client_id: str) -> list[dict[str, Any]]:
        raw_list = self._client.lrange(KeySchema.client_purchases(client_id), 0, -1)
        return [json.loads(item) for item in raw_list]
