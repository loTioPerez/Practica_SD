"""Tests unitarios para el modulo de analisis de benchmarks.

Verifica el correcto funcionamiento del analyzer, plotter, reporter y utils.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path


class TestUtils(unittest.TestCase):
    """Tests para las utilidades del modulo de analisis."""

    def test_calculate_percentiles_basic(self) -> None:
        from concert_ticketing.apps.analysis.utils import calculate_percentiles

        data = list(range(1, 101))  # 1 a 100
        result = calculate_percentiles(data, [50, 95, 99])

        self.assertIn("p50", result)
        self.assertIn("p95", result)
        self.assertIn("p99", result)
        # P50 deberia estar alrededor de 50
        self.assertAlmostEqual(result["p50"], 50.0, delta=2.0)
        # P95 deberia estar alrededor de 95
        self.assertAlmostEqual(result["p95"], 95.0, delta=2.0)

    def test_calculate_percentiles_empty(self) -> None:
        from concert_ticketing.apps.analysis.utils import calculate_percentiles

        result = calculate_percentiles([], [50, 95, 99])
        self.assertEqual(result["p50"], 0.0)
        self.assertEqual(result["p95"], 0.0)
        self.assertEqual(result["p99"], 0.0)

    def test_calculate_percentiles_single(self) -> None:
        from concert_ticketing.apps.analysis.utils import calculate_percentiles

        result = calculate_percentiles([42.0], [50, 95, 99])
        self.assertEqual(result["p50"], 42.0)

    def test_calculate_throughput(self) -> None:
        from concert_ticketing.apps.analysis.utils import calculate_throughput

        self.assertEqual(calculate_throughput(1000, 10.0), 100.0)
        self.assertEqual(calculate_throughput(0, 10.0), 0.0)
        self.assertEqual(calculate_throughput(1000, 0.0), 0.0)

    def test_format_duration(self) -> None:
        from concert_ticketing.apps.analysis.utils import format_duration

        self.assertIn("ms", format_duration(0.5))
        self.assertIn("s", format_duration(5.0))
        self.assertIn("m", format_duration(120.0))

    def test_format_number(self) -> None:
        from concert_ticketing.apps.analysis.utils import format_number

        self.assertEqual(format_number(1000), "1,000")
        self.assertIn(".", format_number(3.14159))

    def test_safe_divide(self) -> None:
        from concert_ticketing.apps.analysis.utils import safe_divide

        self.assertEqual(safe_divide(10, 2), 5.0)
        self.assertEqual(safe_divide(10, 0), 0.0)
        self.assertEqual(safe_divide(10, 0, default=-1.0), -1.0)

    def test_extract_latencies(self) -> None:
        from concert_ticketing.apps.analysis.utils import extract_latencies

        results = [
            {"elapsed_ms": 10.5, "error": None},
            {"elapsed_ms": 20.3, "error": None},
            {"elapsed_ms": 30.0, "error": "timeout"},  # Con error -> excluido
            {"elapsed_ms": 15.0},  # Sin campo error -> incluido
        ]
        latencies = extract_latencies(results)
        self.assertEqual(len(latencies), 3)
        self.assertIn(10.5, latencies)
        self.assertIn(20.3, latencies)
        self.assertNotIn(30.0, latencies)

    def test_load_benchmark_summary(self) -> None:
        from concert_ticketing.apps.analysis.utils import load_benchmark_summary

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_summary.json", delete=False
        ) as f:
            json.dump({"throughput_ops_per_second": 1500, "total_operations": 20000}, f)
            f.flush()
            path = f.name

        try:
            result = load_benchmark_summary(path)
            self.assertEqual(result["throughput_ops_per_second"], 1500)
            self.assertEqual(result["total_operations"], 20000)
        finally:
            os.unlink(path)

    def test_load_benchmark_results(self) -> None:
        from concert_ticketing.apps.analysis.utils import load_benchmark_results

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_results.jsonl", delete=False
        ) as f:
            f.write(json.dumps({"elapsed_ms": 10.0, "http_status": 200}) + "\n")
            f.write(json.dumps({"elapsed_ms": 20.0, "http_status": 200}) + "\n")
            f.flush()
            path = f.name

        try:
            results = load_benchmark_results(path)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["elapsed_ms"], 10.0)
        finally:
            os.unlink(path)

    def test_load_all_summaries(self) -> None:
        from concert_ticketing.apps.analysis.utils import load_all_summaries

        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear ficheros de resumen
            for name in ["benchmark_unnumbered", "benchmark_numbered"]:
                path = Path(tmpdir) / f"{name}_summary.json"
                path.write_text(json.dumps(
                    {"throughput_ops_per_second": 1000, "total_operations": 100}
                ))

            summaries = load_all_summaries(tmpdir)
            self.assertEqual(len(summaries), 2)
            self.assertIn("benchmark_unnumbered", summaries)
            self.assertIn("benchmark_numbered", summaries)


class TestBenchmarkAnalyzer(unittest.TestCase):
    """Tests para el BenchmarkAnalyzer."""

    def setUp(self) -> None:
        from concert_ticketing.apps.analysis.analyzer import BenchmarkAnalyzer

        self.tmpdir = tempfile.mkdtemp()
        self.analyzer = BenchmarkAnalyzer(self.tmpdir)

    def test_empty_metrics(self) -> None:
        metrics = self.analyzer._empty_metrics()
        self.assertEqual(metrics["total_operations"], 0)
        self.assertEqual(metrics["throughput"], 0.0)
        self.assertEqual(metrics["latency_mean"], 0.0)

    def test_calculate_metrics_empty(self) -> None:
        result = self.analyzer.calculate_metrics([])
        self.assertEqual(result["total_operations"], 0)
        self.assertEqual(result["throughput"], 0.0)

    def test_calculate_metrics_with_data(self) -> None:
        results = [
            {
                "elapsed_ms": 10.0,
                "error": None,
                "response_body": {"status": "ACCEPTED", "duplicate": False},
            },
            {
                "elapsed_ms": 20.0,
                "error": None,
                "response_body": {"status": "ACCEPTED", "duplicate": False},
            },
            {
                "elapsed_ms": 30.0,
                "error": None,
                "response_body": {"status": "REJECTED", "duplicate": False, "reason": "SOLD_OUT"},
            },
            {
                "elapsed_ms": 15.0,
                "error": None,
                "response_body": {"status": "ACCEPTED", "duplicate": True},
            },
        ]

        metrics = self.analyzer.calculate_metrics(results)

        self.assertEqual(metrics["total_operations"], 4)
        self.assertEqual(metrics["accepted"], 3)
        self.assertEqual(metrics["rejected"], 1)
        self.assertEqual(metrics["duplicates"], 1)
        self.assertEqual(metrics["errors"], 0)
        self.assertGreater(metrics["latency_mean"], 0)
        self.assertGreater(metrics["throughput"], 0)
        self.assertAlmostEqual(metrics["success_rate"], 75.0)
        self.assertAlmostEqual(metrics["rejection_rate"], 25.0)

    def test_compare_architectures_with_summaries(self) -> None:
        self.analyzer.direct.summaries = {
            "test_bench": {
                "throughput_ops_per_second": 1500,
                "average_latency_ms": 10.0,
                "accepted": 100,
                "rejected": 50,
            }
        }
        self.analyzer.indirect.summaries = {
            "test_bench": {
                "throughput_ops_per_second": 1000,
                "average_latency_ms": 15.0,
                "accepted": 90,
                "rejected": 60,
            }
        }
        self.analyzer._loaded = True

        comparison = self.analyzer.compare_architectures()

        self.assertIn("test_bench", comparison)
        entry = comparison["test_bench"]
        self.assertIn("direct", entry)
        self.assertIn("indirect", entry)
        self.assertIsNotNone(entry["throughput_ratio"])
        self.assertAlmostEqual(entry["throughput_ratio"], 1.5, places=1)

    def test_get_summary_table(self) -> None:
        self.analyzer.direct.summaries = {
            "bench1": {"throughput_ops_per_second": 1000, "average_latency_ms": 10.0}
        }
        self.analyzer.indirect.summaries = {
            "bench1": {"throughput_ops_per_second": 800, "average_latency_ms": 15.0}
        }
        self.analyzer._loaded = True

        table = self.analyzer.get_summary_table()
        self.assertEqual(len(table), 2)  # direct + indirect
        archs = {row["architecture"] for row in table}
        self.assertEqual(archs, {"direct", "indirect"})


class TestBenchmarkPlotter(unittest.TestCase):
    """Tests para el BenchmarkPlotter."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def test_empty_plot_creation(self) -> None:
        from concert_ticketing.apps.analysis.plotter import BenchmarkPlotter

        plotter = BenchmarkPlotter(self.tmpdir)
        path = plotter.plot_throughput_comparison({}, filename="test_empty.png")
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)

    def test_throughput_comparison_plot(self) -> None:
        from concert_ticketing.apps.analysis.plotter import BenchmarkPlotter

        plotter = BenchmarkPlotter(self.tmpdir)
        comparison = {
            "bench_unnumbered": {
                "direct": {"throughput": 1500},
                "indirect": {"throughput": 1000},
            },
            "bench_numbered": {
                "direct": {"throughput": 1200},
                "indirect": {"throughput": 900},
            },
        }
        path = plotter.plot_throughput_comparison(comparison, filename="test_tp.png")
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)

    def test_latency_distribution_plot(self) -> None:
        from concert_ticketing.apps.analysis.plotter import BenchmarkPlotter
        import random

        plotter = BenchmarkPlotter(self.tmpdir)
        direct = [random.gauss(50, 10) for _ in range(500)]
        indirect = [random.gauss(80, 15) for _ in range(500)]

        path = plotter.plot_latency_distribution(
            direct, indirect, filename="test_lat.png"
        )
        self.assertTrue(path.exists())

    def test_scalability_plot(self) -> None:
        from concert_ticketing.apps.analysis.plotter import BenchmarkPlotter

        plotter = BenchmarkPlotter(self.tmpdir)
        scalability = {
            "direct": {
                1: {"throughput": 500},
                2: {"throughput": 900},
                4: {"throughput": 1600},
                8: {"throughput": 2800},
            },
            "indirect": {
                1: {"throughput": 400},
                2: {"throughput": 750},
                4: {"throughput": 1300},
                8: {"throughput": 2200},
            },
        }
        path = plotter.plot_scalability(scalability, filename="test_scale.png")
        self.assertTrue(path.exists())

    def test_contention_impact_plot(self) -> None:
        from concert_ticketing.apps.analysis.plotter import BenchmarkPlotter

        plotter = BenchmarkPlotter(self.tmpdir)
        contention = {
            "direct": {
                "normal": {"throughput": 1500, "latency_mean": 30},
                "hotspot": {"throughput": 800, "latency_mean": 60},
                "throughput_degradation_pct": 46.7,
            },
            "indirect": {
                "normal": {"throughput": 1000, "latency_mean": 50},
                "hotspot": {"throughput": 600, "latency_mean": 90},
                "throughput_degradation_pct": 40.0,
            },
        }
        path = plotter.plot_contention_impact(contention, filename="test_cont.png")
        self.assertTrue(path.exists())

    def test_save_all_plots(self) -> None:
        from concert_ticketing.apps.analysis.plotter import BenchmarkPlotter

        plotter = BenchmarkPlotter(self.tmpdir)
        comparison = {
            "bench_unnumbered": {
                "direct": {"throughput": 1500, "accepted": 100, "rejected": 50},
                "indirect": {"throughput": 1000, "accepted": 80, "rejected": 70},
            },
        }
        plots = plotter.save_all_plots(comparison=comparison)
        # Deberia generar al menos throughput, ticket_type y breakdown
        self.assertGreaterEqual(len(plots), 3)


class TestBenchmarkReporter(unittest.TestCase):
    """Tests para el BenchmarkReporter."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def test_generate_markdown_report(self) -> None:
        from concert_ticketing.apps.analysis.reporter import BenchmarkReporter

        reporter = BenchmarkReporter(self.tmpdir, self.tmpdir)
        comparison = {
            "bench_test": {
                "direct": {"throughput": 1500, "latency_mean": 10, "accepted": 100, "rejected": 50},
                "indirect": {"throughput": 1000, "latency_mean": 20, "accepted": 80, "rejected": 70},
                "throughput_ratio": 1.5,
                "latency_ratio": 0.5,
            }
        }

        path = reporter.generate_markdown_report(comparison=comparison)
        self.assertTrue(path.exists())

        content = path.read_text()
        self.assertIn("Benchmark Comparison Report", content)
        self.assertIn("Executive Summary", content)
        self.assertIn("Methodology", content)
        self.assertIn("Conclusions", content)

    def test_generate_html_report(self) -> None:
        from concert_ticketing.apps.analysis.reporter import BenchmarkReporter

        reporter = BenchmarkReporter(self.tmpdir, self.tmpdir)
        comparison = {
            "bench_test": {
                "direct": {"throughput": 1500, "latency_mean": 10},
                "indirect": {"throughput": 1000, "latency_mean": 20},
                "throughput_ratio": 1.5,
            }
        }

        path = reporter.generate_html_report(comparison=comparison)
        self.assertTrue(path.exists())

        content = path.read_text()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("Benchmark Comparison Report", content)
        self.assertIn("</html>", content)

    def test_generate_summary_table_json(self) -> None:
        from concert_ticketing.apps.analysis.reporter import BenchmarkReporter

        reporter = BenchmarkReporter(self.tmpdir, self.tmpdir)
        table = [
            {"benchmark": "test", "architecture": "direct", "throughput": 1500},
            {"benchmark": "test", "architecture": "indirect", "throughput": 1000},
        ]

        path = reporter.generate_summary_table(table)
        self.assertTrue(path.exists())

        data = json.loads(path.read_text())
        self.assertEqual(len(data), 2)

    def test_report_with_all_sections(self) -> None:
        from concert_ticketing.apps.analysis.reporter import BenchmarkReporter

        reporter = BenchmarkReporter(self.tmpdir, self.tmpdir)
        comparison = {
            "bench_test": {
                "direct": {"throughput": 1500, "latency_mean": 10, "accepted": 100, "rejected": 50},
                "indirect": {"throughput": 1000, "latency_mean": 20, "accepted": 80, "rejected": 70},
                "throughput_ratio": 1.5,
                "latency_ratio": 0.5,
            }
        }
        scalability = {
            "direct": {1: {"throughput": 500}, 2: {"throughput": 900}},
            "indirect": {},
        }
        contention = {
            "direct": {
                "normal": {"throughput": 1500},
                "hotspot": {"throughput": 800},
                "throughput_degradation_pct": 46.7,
            },
            "indirect": {
                "normal": {"throughput": 1000},
                "hotspot": {"throughput": 600},
                "throughput_degradation_pct": 40.0,
            },
        }
        table = [
            {"benchmark": "test", "architecture": "direct", "throughput": 1500,
             "latency_mean": 10, "latency_p95": 25, "latency_p99": 50,
             "success_rate": 66.7, "error_rate": 0.0},
        ]

        md_path = reporter.generate_markdown_report(
            comparison, scalability, contention, table, []
        )
        self.assertTrue(md_path.exists())
        content = md_path.read_text()
        self.assertIn("Scalability", content)
        self.assertIn("Contention", content)


if __name__ == "__main__":
    unittest.main()
