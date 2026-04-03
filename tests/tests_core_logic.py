"""Tests de FASE 1: Core Logic & Persistencia.

Estos tests verifican correctness del sistema de tickets:
- Compra unnumbered hasta agotar (exactamente 20,000)
- Compra numbered con concurrencia simulada
- Idempotencia (mismo request_id no se procesa dos veces)
- Rechazo cuando no hay tickets
- Asientos duplicados rechazados

Implementación 100% Python (sin Lua) usando WATCH/MULTI/EXEC.
"""

import json
import sys
import os
import concurrent.futures
from pathlib import Path

import pytest

# Asegurar que src está en el path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concert_ticketing.shared.config import RedisConfig, AppConfig
from concert_ticketing.shared.constants import TOTAL_TICKETS
from concert_ticketing.shared.exceptions import InvalidInputError
from concert_ticketing.core.domain.enums import PurchaseStatus, TicketType
from concert_ticketing.core.domain.models import PurchaseResult, PurchaseRequest
from concert_ticketing.adapters.persistence.redis.connection import create_redis_client
from concert_ticketing.adapters.persistence.redis.repositories import (
    RedisInventoryRepository,
    RedisIdempotencyRepository,
    RedisResultRepository,
)
from concert_ticketing.core.services.purchase_service import PurchaseService


# ---- Fixtures ----

@pytest.fixture(scope="module")
def redis_client():
    """Cliente Redis conectado (usa DB 1 para tests)."""
    cfg = RedisConfig(db=1)
    client = create_redis_client(cfg)
    yield client
    client.flushdb()
    client.close()


@pytest.fixture(scope="module")
def inventory(redis_client):
    return RedisInventoryRepository(redis_client)


@pytest.fixture(scope="module")
def idempotency_repo(redis_client):
    return RedisIdempotencyRepository(redis_client)


@pytest.fixture(scope="module")
def result_repo(redis_client):
    return RedisResultRepository(redis_client)


@pytest.fixture(scope="module")
def service(inventory, idempotency_repo, result_repo):
    return PurchaseService(inventory, idempotency_repo, result_repo)


# ---- Tests Unnumbered ----

class TestUnnumbered:
    """Tests para tickets no numerados."""

    SMALL_TOTAL = 100  # Usamos 100 para tests rápidos

    def test_buy_all_unnumbered(self, service, redis_client):
        """Exactamente SMALL_TOTAL compras exitosas, luego todas rechazadas."""
        redis_client.flushdb()
        service.initialize_system("unnumbered", self.SMALL_TOTAL)

        accepted = 0
        rejected = 0

        # Comprar todos
        for i in range(self.SMALL_TOTAL + 50):
            result = service.buy_unnumbered_ticket(
                client_id=f"user{i:05d}",
                request_id=f"req_un_{i:05d}",
            )
            if result.success:
                accepted += 1
            else:
                rejected += 1

        assert accepted == self.SMALL_TOTAL, f"Esperado {self.SMALL_TOTAL} aceptados, got {accepted}"
        assert rejected == 50, f"Esperado 50 rechazados, got {rejected}"

        # Verificar contador
        remaining = service.get_available_count("unnumbered")
        assert remaining == 0

    def test_rejection_reason_sold_out(self, service, redis_client):
        """Tras agotarse, el motivo debe ser 'sold_out'."""
        redis_client.flushdb()
        service.initialize_system("unnumbered", 1)
        service.buy_unnumbered_ticket("alice", "req_first")

        result = service.buy_unnumbered_ticket("bob", "req_second")
        assert result.status == PurchaseStatus.REJECTED
        assert result.reason == "sold_out"

    def test_unnumbered_idempotency(self, service, redis_client):
        """Mismo request_id retorna resultado anterior sin doble-gasto."""
        redis_client.flushdb()
        service.initialize_system("unnumbered", 10)

        r1 = service.buy_unnumbered_ticket("alice", "req_idem_1")
        r2 = service.buy_unnumbered_ticket("alice", "req_idem_1")

        assert r1.success is True
        assert r2.success is True  # mismo resultado
        assert r2.duplicate is True

        # Solo se consumió 1 ticket
        assert service.get_available_count("unnumbered") == 9


# ---- Tests Numbered ----

class TestNumbered:
    """Tests para tickets numerados."""

    SMALL_TOTAL = 50

    def test_buy_all_numbered(self, service, redis_client):
        """Cada asiento se vende exactamente una vez."""
        redis_client.flushdb()
        service.initialize_system("numbered", self.SMALL_TOTAL)

        accepted = 0
        for seat in range(1, self.SMALL_TOTAL + 1):
            result = service.buy_numbered_ticket(
                client_id=f"user{seat:05d}",
                seat_id=seat,
                request_id=f"req_num_{seat:05d}",
            )
            assert result.success, f"Asiento {seat} debería aceptarse"
            accepted += 1

        assert accepted == self.SMALL_TOTAL

        # Verificar que todos están vendidos
        remaining = service.get_available_count("numbered")
        assert remaining == 0

    def test_seat_already_sold(self, service, redis_client):
        """Intentar comprar un asiento ya vendido falla."""
        redis_client.flushdb()
        service.initialize_system("numbered", 10)

        r1 = service.buy_numbered_ticket("alice", 5, "req_seat5_a")
        assert r1.success is True

        r2 = service.buy_numbered_ticket("bob", 5, "req_seat5_b")
        assert r2.success is False
        assert r2.reason == "seat_already_sold"

    def test_invalid_seat(self, service, redis_client):
        """Asiento fuera de rango es rechazado por validación."""
        redis_client.flushdb()
        service.initialize_system("numbered", 10)

        with pytest.raises(InvalidInputError):
            service.buy_numbered_ticket("alice", 999999, "req_invalid_seat")

    def test_numbered_idempotency(self, service, redis_client):
        """Idempotencia para compras numeradas."""
        redis_client.flushdb()
        service.initialize_system("numbered", 10)

        r1 = service.buy_numbered_ticket("alice", 3, "req_idem_num_1")
        r2 = service.buy_numbered_ticket("alice", 3, "req_idem_num_1")

        assert r1.success is True
        assert r2.success is True
        assert r2.duplicate is True
        assert service.get_available_count("numbered") == 9

    def test_seat_status(self, service, redis_client):
        """Verificar consulta de estado de asientos."""
        redis_client.flushdb()
        service.initialize_system("numbered", 10)

        info = service.get_seat_status(1)
        assert info.status == "available"

        service.buy_numbered_ticket("alice", 1, "req_status_1")
        info = service.get_seat_status(1)
        assert info.status == "sold"
        assert info.owner == "alice"


# ---- Test Concurrencia ----

class TestConcurrency:
    """Tests de concurrencia con ThreadPoolExecutor."""

    def test_unnumbered_concurrent(self, redis_client):
        """Múltiples threads comprando unnumbered no sobrevenden."""
        redis_client.flushdb()
        total = 200
        repo = RedisInventoryRepository(redis_client)
        svc = PurchaseService(repo)
        svc.initialize_system("unnumbered", total)

        num_buyers = 300

        def buy(i):
            return svc.buy_unnumbered_ticket(f"user{i}", f"conc_un_{i}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(buy, range(num_buyers)))

        accepted = sum(1 for r in results if r.success)
        rejected = sum(1 for r in results if not r.success)

        assert accepted == total, f"Exactamente {total} aceptados, got {accepted}"
        assert rejected == num_buyers - total
        assert svc.get_available_count("unnumbered") == 0

    def test_numbered_concurrent_same_seat(self, redis_client):
        """Múltiples threads compiten por el mismo asiento: exactamente 1 gana."""
        redis_client.flushdb()
        repo = RedisInventoryRepository(redis_client)
        svc = PurchaseService(repo)
        svc.initialize_system("numbered", 100)

        target_seat = 42
        num_buyers = 50

        def buy(i):
            return svc.buy_numbered_ticket(f"user{i}", target_seat, f"conc_num_{i}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(buy, range(num_buyers)))

        accepted = sum(1 for r in results if r.success)
        assert accepted == 1, f"Solo 1 comprador debe ganar, got {accepted}"


# ---- Test Full Scale (20k, skip por defecto) ----

class TestFullScale:
    """Tests a escala completa (20,000 tickets). Se saltan con -k 'not fullscale'."""

    @pytest.mark.slow
    def test_unnumbered_20k(self, redis_client):
        """20,000 compras unnumbered exitosas, el resto rechazadas."""
        redis_client.flushdb()
        repo = RedisInventoryRepository(redis_client)
        svc = PurchaseService(repo)
        svc.initialize_system("unnumbered", TOTAL_TICKETS)

        accepted = 0
        for i in range(TOTAL_TICKETS + 100):
            r = svc.buy_unnumbered_ticket(f"u{i}", f"full_un_{i}")
            if r.success:
                accepted += 1

        assert accepted == TOTAL_TICKETS
        assert svc.get_available_count("unnumbered") == 0

    @pytest.mark.slow
    def test_numbered_20k(self, redis_client):
        """20,000 asientos, cada uno vendido exactamente una vez."""
        redis_client.flushdb()
        repo = RedisInventoryRepository(redis_client)
        svc = PurchaseService(repo)
        svc.initialize_system("numbered", TOTAL_TICKETS)

        for seat in range(1, TOTAL_TICKETS + 1):
            r = svc.buy_numbered_ticket(f"u{seat}", seat, f"full_num_{seat}")
            assert r.success, f"Asiento {seat} deberia aceptarse"

        assert svc.get_available_count("numbered") == 0


# ---- Test Request Result / Client Purchases ----

class TestQueryCapabilities:
    """Tests de consulta de resultados e historial."""

    def test_request_result_lookup(self, service, redis_client, idempotency_repo):
        """Podemos consultar el resultado de un request procesado."""
        redis_client.flushdb()
        service.initialize_system("unnumbered", 5)
        service.buy_unnumbered_ticket("alice", "query_req_1")

        result = service.get_request_result("query_req_1")
        assert result is not None
        assert result["status"] == "ACCEPTED"
        assert result["client_id"] == "alice"

    def test_client_purchases_list(self, service, redis_client, result_repo):
        """Historial de compras del cliente."""
        redis_client.flushdb()
        service.initialize_system("unnumbered", 5)
        service.buy_unnumbered_ticket("alice", "hist_1")
        service.buy_unnumbered_ticket("alice", "hist_2")

        purchases = service.get_client_purchases("alice")
        assert len(purchases) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
