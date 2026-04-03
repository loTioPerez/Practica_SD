"""Pruebas unitarias del parser de benchmarks."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from concert_ticketing.apps.benchmark_runner.parser import parse_benchmark_file
from concert_ticketing.core.domain.enums import TicketType


class BenchmarkParserTestCase(unittest.TestCase):
    def test_parse_unnumbered_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "bench.txt"
            file_path.write_text("BUY client1 req1\nBUY client2 req2\n", encoding="utf-8")

            operations = parse_benchmark_file(file_path)

            self.assertEqual(len(operations), 2)
            self.assertEqual(operations[0].ticket_type, TicketType.UNNUMBERED)
            self.assertEqual(operations[0].endpoint, "/buy/unnumbered")

    def test_parse_numbered_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "bench.txt"
            file_path.write_text("BUY client1 10 req1\n", encoding="utf-8")

            operations = parse_benchmark_file(file_path)

            self.assertEqual(len(operations), 1)
            self.assertEqual(operations[0].ticket_type, TicketType.NUMBERED)
            self.assertEqual(operations[0].seat_id, 10)
            self.assertEqual(operations[0].endpoint, "/buy/numbered")


if __name__ == "__main__":
    unittest.main()
