"""Pruebas unitarias exhaustivas de la logica de nucleo del sistema."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from concert_ticketing.core.domain.enums import (
    PurchaseStatus,
    RejectionReason,
    SeatStatus,
    TicketType,
)
from concert_ticketing.core.domain.models import PurchaseRequest, PurchaseResult, SeatInfo
from concert_ticketing.core.services.validation_service import (
    parse_numbered_line,
    parse_unnumbered_line,
    validate_client_id,
    validate_request_id,
    validate_seat_id,
)
from concert_ticketing.shared.constants import TOTAL_TICKETS
from concert_ticketing.shared.exceptions import InvalidInputError
from concert_ticketing.shared.serialization import purchase_result_to_dict


class TestEnums(unittest.TestCase):
    def test_ticket_type_values(self) -> None:
        self.assertEqual(TicketType.UNNUMBERED.value, "unnumbered")
        self.assertEqual(TicketType.NUMBERED.value, "numbered")

    def test_purchase_status_values(self) -> None:
        self.assertEqual(PurchaseStatus.ACCEPTED.value, "ACCEPTED")
        self.assertEqual(PurchaseStatus.REJECTED.value, "REJECTED")

    def test_rejection_reasons(self) -> None:
        self.assertEqual(RejectionReason.SOLD_OUT.value, "sold_out")
        self.assertEqual(RejectionReason.SEAT_ALREADY_SOLD.value, "seat_already_sold")
        self.assertEqual(RejectionReason.DUPLICATE_REQUEST.value, "duplicate_request")

    def test_seat_status(self) -> None:
        self.assertEqual(SeatStatus.AVAILABLE.value, "available")
        self.assertEqual(SeatStatus.SOLD.value, "sold")


class TestPurchaseResult(unittest.TestCase):
    def test_accepted_result(self) -> None:
        r = PurchaseResult.accepted(
            request_id="r1", client_id="c1",
            ticket_type=TicketType.UNNUMBERED, remaining=100,
        )
        self.assertTrue(r.success)
        self.assertEqual(r.status, PurchaseStatus.ACCEPTED)
        self.assertEqual(r.reason, "ok")
        self.assertFalse(r.duplicate)

    def test_rejected_result(self) -> None:
        r = PurchaseResult.rejected(
            request_id="r2", client_id="c2",
            reason=RejectionReason.SOLD_OUT,
            ticket_type=TicketType.UNNUMBERED,
        )
        self.assertFalse(r.success)
        self.assertEqual(r.status, PurchaseStatus.REJECTED)
        self.assertEqual(r.reason, "sold_out")

    def test_accepted_with_seat(self) -> None:
        r = PurchaseResult.accepted(
            request_id="r3", client_id="c3",
            ticket_type=TicketType.NUMBERED, seat_id=42,
        )
        self.assertEqual(r.seat_id, 42)
        self.assertEqual(r.ticket_type, "numbered")

    def test_duplicate_flag(self) -> None:
        r = PurchaseResult.accepted(
            request_id="r4", client_id="c4",
            ticket_type=TicketType.UNNUMBERED,
            duplicate=True,
        )
        self.assertTrue(r.duplicate)


class TestSeatInfo(unittest.TestCase):
    def test_defaults(self) -> None:
        info = SeatInfo(seat_id=1, status="available")
        self.assertIsNone(info.owner)

    def test_with_owner(self) -> None:
        info = SeatInfo(seat_id=5, status="sold", owner="c10")
        self.assertEqual(info.owner, "c10")


class TestPurchaseRequest(unittest.TestCase):
    def test_without_seat(self) -> None:
        req = PurchaseRequest(client_id="c1", request_id="r1")
        self.assertIsNone(req.seat_id)

    def test_with_seat(self) -> None:
        req = PurchaseRequest(client_id="c1", request_id="r1", seat_id=10)
        self.assertEqual(req.seat_id, 10)


class TestValidationService(unittest.TestCase):
    def test_valid_client_id(self) -> None:
        self.assertTrue(validate_client_id("client1"))

    def test_empty_client_id(self) -> None:
        self.assertFalse(validate_client_id(""))

    def test_valid_request_id(self) -> None:
        self.assertTrue(validate_request_id("req-1"))

    def test_empty_request_id(self) -> None:
        self.assertFalse(validate_request_id(""))

    def test_valid_seat_id(self) -> None:
        self.assertTrue(validate_seat_id(1))
        self.assertTrue(validate_seat_id(TOTAL_TICKETS))

    def test_invalid_seat_id_zero(self) -> None:
        self.assertFalse(validate_seat_id(0))

    def test_invalid_seat_id_negative(self) -> None:
        self.assertFalse(validate_seat_id(-1))

    def test_invalid_seat_id_too_large(self) -> None:
        self.assertFalse(validate_seat_id(TOTAL_TICKETS + 1))


class TestBenchmarkParsing(unittest.TestCase):
    def test_parse_unnumbered_line(self) -> None:
        result = parse_unnumbered_line("BUY client1 req1")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("client1", "req1"))

    def test_parse_numbered_line(self) -> None:
        result = parse_numbered_line("BUY client1 42 req1")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("client1", 42, "req1"))

    def test_unnumbered_rejects_numbered(self) -> None:
        result = parse_unnumbered_line("BUY client1 42 req1")
        self.assertIsNone(result)

    def test_numbered_rejects_unnumbered(self) -> None:
        result = parse_numbered_line("BUY client1 req1")
        self.assertIsNone(result)


class TestSerialization(unittest.TestCase):
    def test_purchase_result_to_dict(self) -> None:
        r = PurchaseResult.accepted(
            request_id="r1", client_id="c1",
            ticket_type=TicketType.UNNUMBERED, remaining=99,
        )
        d = purchase_result_to_dict(r)
        self.assertEqual(d["status"], "ACCEPTED")
        self.assertEqual(d["request_id"], "r1")
        self.assertEqual(d["remaining"], 99)
        self.assertFalse(d["duplicate"])


if __name__ == "__main__":
    unittest.main()
