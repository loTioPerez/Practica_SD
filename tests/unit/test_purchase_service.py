"""Pruebas unitarias del servicio principal de compra."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from concert_ticketing.core.domain.enums import PurchaseStatus, TicketType
from concert_ticketing.core.domain.models import PurchaseResult, SeatInfo
from concert_ticketing.core.services.purchase_service import PurchaseService
from concert_ticketing.shared.exceptions import InvalidInputError


class FakeInventoryRepository:
    """Doble simple para probar PurchaseService sin Redis."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def buy_unnumbered(self, client_id: str, request_id: str) -> PurchaseResult:
        self.calls.append(("buy_unnumbered", client_id, request_id))
        return PurchaseResult.accepted(
            request_id=request_id,
            client_id=client_id,
            ticket_type=TicketType.UNNUMBERED,
            remaining=19_999,
        )

    def buy_numbered(self, client_id: str, seat_id: int, request_id: str) -> PurchaseResult:
        self.calls.append(("buy_numbered", client_id, seat_id, request_id))
        return PurchaseResult.accepted(
            request_id=request_id,
            client_id=client_id,
            ticket_type=TicketType.NUMBERED,
            seat_id=seat_id,
        )

    def get_available_count(self, ticket_type: str) -> int:
        self.calls.append(("get_available_count", ticket_type))
        return 123

    def get_seat_status(self, seat_id: int) -> SeatInfo:
        self.calls.append(("get_seat_status", seat_id))
        return SeatInfo(seat_id=seat_id, status="available")

    def initialize(self, ticket_type: str, total_tickets: int) -> None:
        self.calls.append(("initialize", ticket_type, total_tickets))

    def reset(self, ticket_type: str, total_tickets: int) -> None:
        self.calls.append(("reset", ticket_type, total_tickets))


class FakeResultRepository:
    def get_client_purchases(self, client_id: str) -> list[dict]:
        return [{"request_id": "r1", "ticket_type": "unnumbered"}]


class FakeIdempotencyRepository:
    def get_request_result(self, request_id: str) -> dict | None:
        if request_id == "r1":
            return {"status": "ACCEPTED", "request_id": "r1"}
        return None

    def request_exists(self, request_id: str) -> bool:
        return request_id == "r1"


class PurchaseServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = FakeInventoryRepository()
        self.service = PurchaseService(
            inventory=self.inventory,
            results=FakeResultRepository(),
            idempotency=FakeIdempotencyRepository(),
        )

    def test_buy_unnumbered_delegates_to_inventory(self) -> None:
        result = self.service.buy_unnumbered("c1", "r1")

        self.assertEqual(result.status, PurchaseStatus.ACCEPTED)
        self.assertEqual(self.inventory.calls[0], ("buy_unnumbered", "c1", "r1"))

    def test_buy_numbered_validates_seat(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.service.buy_numbered("c1", 0, "r1")

    def test_get_available_count_accepts_enum(self) -> None:
        available = self.service.get_available_count(TicketType.UNNUMBERED)

        self.assertEqual(available, 123)
        self.assertEqual(self.inventory.calls[0], ("get_available_count", "unnumbered"))

    def test_get_client_purchases_returns_history(self) -> None:
        purchases = self.service.get_client_purchases("c1")

        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases[0]["request_id"], "r1")

    def test_get_request_result_uses_idempotency_repository(self) -> None:
        result = self.service.get_request_result("r1")

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "ACCEPTED")

    def test_initialize_and_reset_delegate_to_inventory(self) -> None:
        self.service.initialize("numbered", 20_000)
        self.service.reset("all", 20_000)

        self.assertEqual(self.inventory.calls[0], ("initialize", "numbered", 20_000))
        self.assertEqual(self.inventory.calls[1], ("reset", "all", 20_000))


if __name__ == "__main__":
    unittest.main()
