"""Pruebas unitarias del reporting de benchmark."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from concert_ticketing.apps.benchmark_runner.reporting import (
    BenchmarkRequestResult,
    build_summary,
    write_results,
    write_summary,
)


class BenchmarkReportingTestCase(unittest.TestCase):
    def test_build_summary_counts_statuses(self) -> None:
        results = [
            BenchmarkRequestResult(
                line_number=1,
                endpoint="/buy/unnumbered",
                request_id="r1",
                client_id="c1",
                ticket_type="unnumbered",
                seat_id=None,
                http_status=200,
                elapsed_ms=10.0,
                response_body={"status": "ACCEPTED", "reason": "ok", "duplicate": False},
            ),
            BenchmarkRequestResult(
                line_number=2,
                endpoint="/buy/unnumbered",
                request_id="r2",
                client_id="c2",
                ticket_type="unnumbered",
                seat_id=None,
                http_status=409,
                elapsed_ms=12.0,
                response_body={"status": "REJECTED", "reason": "sold_out", "duplicate": False},
            ),
        ]

        summary = build_summary(results, total_seconds=2.0)

        self.assertEqual(summary["total_operations"], 2)
        self.assertEqual(summary["accepted"], 1)
        self.assertEqual(summary["rejected"], 1)
        self.assertIn(200, summary["http_status_counts"])
        self.assertIn("sold_out", summary["reason_counts"])

    def test_write_summary_and_results(self) -> None:
        result = BenchmarkRequestResult(
            line_number=1,
            endpoint="/buy/numbered",
            request_id="r1",
            client_id="c1",
            ticket_type="numbered",
            seat_id=5,
            http_status=200,
            elapsed_ms=11.5,
            response_body={"status": "ACCEPTED", "reason": "ok", "duplicate": False},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            summary_path = Path(temp_dir) / "summary.json"
            results_path = Path(temp_dir) / "results.jsonl"

            write_summary(summary_path, {"total_operations": 1})
            write_results(results_path, [result])

            self.assertTrue(summary_path.exists())
            self.assertTrue(results_path.exists())


if __name__ == "__main__":
    unittest.main()
