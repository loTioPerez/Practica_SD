"""Analizador de resultados de benchmarks comparativos.

Clase principal que carga, procesa y compara resultados de benchmarks
entre arquitecturas directa e indirecta.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .utils import (
    calculate_percentiles,
    calculate_throughput,
    extract_latencies,
    load_all_results,
    load_all_summaries,
    safe_divide,
)


@dataclass
class ArchitectureResults:
    """Resultados agregados de una arquitectura."""

    name: str
    summaries: dict[str, dict[str, Any]] = field(default_factory=dict)
    results: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


class BenchmarkAnalyzer:
    """Analizador principal de benchmarks comparativos.

    Carga resultados de ambas arquitecturas y genera metricas,
    comparativas y analisis de escalabilidad.
    """

    def __init__(self, base_output_dir: str | Path = "benchmarks/outputs") -> None:
        self.base_dir = Path(base_output_dir)
        self.direct = ArchitectureResults(name="direct")
        self.indirect = ArchitectureResults(name="indirect")
        self._loaded = False

    def load_results(self, path: str | Path | None = None) -> None:
        """Carga resultados de benchmarks desde el directorio especificado.

        Args:
            path: Ruta base de outputs. Si None, usa self.base_dir.
        """
        base = Path(path) if path else self.base_dir

        direct_dir = base / "direct"
        indirect_dir = base / "indirect"

        if direct_dir.exists():
            self.direct.summaries = load_all_summaries(direct_dir)
            self.direct.results = load_all_results(direct_dir)

        if indirect_dir.exists():
            self.indirect.summaries = load_all_summaries(indirect_dir)
            self.indirect.results = load_all_results(indirect_dir)

        self._loaded = True

    def calculate_metrics(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Calcula metricas detalladas a partir de resultados individuales.

        Args:
            results: Lista de resultados individuales de benchmark.

        Returns:
            Diccionario con metricas calculadas.
        """
        if not results:
            return self._empty_metrics()

        latencies = extract_latencies(results)
        total_ops = len(results)

        # Contar resultados por tipo
        accepted = sum(
            1 for r in results
            if r.get("response_body", {}) and r["response_body"].get("status") == "ACCEPTED"
        )
        rejected = sum(
            1 for r in results
            if r.get("response_body", {}) and r["response_body"].get("status") == "REJECTED"
        )
        duplicates = sum(
            1 for r in results
            if r.get("response_body", {}) and r["response_body"].get("duplicate") is True
        )
        errors = sum(1 for r in results if r.get("error") is not None)

        # Tiempos
        elapsed_values = [r["elapsed_ms"] for r in results if "elapsed_ms" in r]
        total_time_ms = max(elapsed_values) if elapsed_values else 0.0
        total_time_s = total_time_ms / 1000.0

        # Percentiles
        percentile_data = calculate_percentiles(latencies, [50, 95, 99])

        return {
            "total_operations": total_ops,
            "total_time_seconds": round(total_time_s, 4),
            "throughput": calculate_throughput(total_ops, total_time_s),
            "latency_mean": round(statistics.mean(latencies), 4) if latencies else 0.0,
            "latency_std": round(statistics.stdev(latencies), 4) if len(latencies) > 1 else 0.0,
            "latency_min": round(min(latencies), 4) if latencies else 0.0,
            "latency_max": round(max(latencies), 4) if latencies else 0.0,
            "latency_p50": percentile_data["p50"],
            "latency_p95": percentile_data["p95"],
            "latency_p99": percentile_data["p99"],
            "success_rate": round(safe_divide(accepted, total_ops) * 100, 2),
            "rejection_rate": round(safe_divide(rejected, total_ops) * 100, 2),
            "duplicate_rate": round(safe_divide(duplicates, total_ops) * 100, 2),
            "error_rate": round(safe_divide(errors, total_ops) * 100, 2),
            "accepted": accepted,
            "rejected": rejected,
            "duplicates": duplicates,
            "errors": errors,
        }

    def compare_architectures(self) -> dict[str, Any]:
        """Compara rendimiento entre arquitectura directa e indirecta.

        Returns:
            Diccionario con comparativa por cada benchmark comun.
        """
        comparison: dict[str, Any] = {}

        # Metricas directas desde summaries
        for bench_name in set(self.direct.summaries.keys()) | set(self.indirect.summaries.keys()):
            entry: dict[str, Any] = {"benchmark": bench_name}

            direct_summary = self.direct.summaries.get(bench_name, {})
            indirect_summary = self.indirect.summaries.get(bench_name, {})

            # Metricas detalladas desde results si estan disponibles
            direct_results = self.direct.results.get(bench_name, [])
            indirect_results = self.indirect.results.get(bench_name, [])

            if direct_results:
                entry["direct"] = self._merge_summary_metrics(
                    self.calculate_metrics(direct_results),
                    direct_summary,
                )
            elif direct_summary:
                entry["direct"] = direct_summary
            else:
                entry["direct"] = self._empty_metrics()

            if indirect_results:
                entry["indirect"] = self._merge_summary_metrics(
                    self.calculate_metrics(indirect_results),
                    indirect_summary,
                )
            elif indirect_summary:
                entry["indirect"] = indirect_summary
            else:
                entry["indirect"] = self._empty_metrics()

            # Calcular ratios
            d_tp = entry["direct"].get("throughput", entry["direct"].get("throughput_ops_per_second", 0))
            i_tp = entry["indirect"].get("throughput", entry["indirect"].get("throughput_ops_per_second", 0))
            entry["throughput_ratio"] = round(safe_divide(d_tp, i_tp), 4) if i_tp else None

            d_lat = entry["direct"].get("latency_mean", entry["direct"].get("average_latency_ms", 0))
            i_lat = entry["indirect"].get("latency_mean", entry["indirect"].get("average_latency_ms", 0))
            entry["latency_ratio"] = round(safe_divide(d_lat, i_lat), 4) if i_lat else None

            comparison[bench_name] = entry

        return comparison

    @staticmethod
    def _merge_summary_metrics(
        calculated_metrics: dict[str, Any],
        summary_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Combina metricas calculadas con metricas agregadas del summary.

        Los resultados individuales sirven para percentiles y tasas, pero el
        throughput correcto debe salir del tiempo total real del benchmark
        almacenado en el summary.
        """
        merged = dict(calculated_metrics)
        if summary_metrics:
            if "total_time_seconds" in summary_metrics:
                merged["total_time_seconds"] = summary_metrics["total_time_seconds"]
            if "throughput_ops_per_second" in summary_metrics:
                merged["throughput"] = summary_metrics["throughput_ops_per_second"]
                merged["throughput_ops_per_second"] = summary_metrics["throughput_ops_per_second"]
        return merged

    def analyze_scalability(
        self,
        scalability_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Analiza escalabilidad a partir de resultados con distintos workers.

        Args:
            scalability_dir: Directorio con resultados de escalabilidad.
                            Espera subdirectorios workers_1, workers_2, etc.

        Returns:
            Diccionario con datos de escalabilidad por arquitectura.
        """
        base = Path(scalability_dir) if scalability_dir else self.base_dir / "comparative"
        scalability: dict[str, Any] = {"direct": {}, "indirect": {}}

        for arch in ["direct", "indirect"]:
            worker_data: dict[int, dict[str, Any]] = {}
            for workers_dir in sorted(base.glob(f"workers_*/{arch}")):
                try:
                    num_workers = int(workers_dir.parent.name.split("_")[1])
                except (IndexError, ValueError):
                    continue

                summaries = load_all_summaries(workers_dir)
                results = load_all_results(workers_dir)

                all_results: list[dict[str, Any]] = []
                for result_list in results.values():
                    all_results.extend(result_list)

                metrics = self.calculate_metrics(all_results) if all_results else {}
                if summaries:
                    if metrics:
                        # Ajustar tiempo/throughput al valor agregado real del summary.
                        summary_time_values = [
                            s.get("total_time_seconds", 0) for s in summaries.values()
                            if s.get("total_time_seconds", 0)
                        ]
                        summary_tp_values = [
                            s.get("throughput_ops_per_second", 0) for s in summaries.values()
                            if s.get("throughput_ops_per_second", 0)
                        ]
                        if summary_time_values:
                            metrics["total_time_seconds"] = round(
                                statistics.mean(summary_time_values), 4
                            )
                        if summary_tp_values:
                            metrics["throughput"] = round(
                                statistics.mean(summary_tp_values), 4
                            )
                    # Agregar throughput promedio de summaries
                    avg_tp = statistics.mean(
                        s.get("throughput_ops_per_second", 0) for s in summaries.values()
                    )
                    metrics["avg_throughput_from_summaries"] = round(avg_tp, 4)

                worker_data[num_workers] = metrics

            scalability[arch] = dict(sorted(worker_data.items()))

        return scalability

    def analyze_contention(
        self,
        normal_dir: str | Path | None = None,
        hotspot_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Analiza el impacto de la contencion en el rendimiento.

        Args:
            normal_dir: Directorio con resultados normales.
            hotspot_dir: Directorio con resultados de alta contencion.

        Returns:
            Diccionario con comparativa normal vs alta contencion.
        """
        base = self.base_dir
        normal_base = Path(normal_dir) if normal_dir else base / "comparative" / "normal"
        hotspot_base = Path(hotspot_dir) if hotspot_dir else base / "comparative" / "hotspot"

        contention: dict[str, Any] = {}

        for arch in ["direct", "indirect"]:
            arch_data: dict[str, Any] = {}

            normal_results_all: list[dict[str, Any]] = []
            hotspot_results_all: list[dict[str, Any]] = []

            normal_arch = normal_base / arch
            hotspot_arch = hotspot_base / arch

            if normal_arch.exists():
                normal_summaries = load_all_summaries(normal_arch)
                for result_list in load_all_results(normal_arch).values():
                    normal_results_all.extend(result_list)
            else:
                normal_summaries = {}
            if hotspot_arch.exists():
                hotspot_summaries = load_all_summaries(hotspot_arch)
                for result_list in load_all_results(hotspot_arch).values():
                    hotspot_results_all.extend(result_list)
            else:
                hotspot_summaries = {}

            normal_metrics = self.calculate_metrics(normal_results_all)
            hotspot_metrics = self.calculate_metrics(hotspot_results_all)

            arch_data["normal"] = self._merge_summary_metrics(
                normal_metrics,
                next(iter(normal_summaries.values()), {}),
            )
            arch_data["hotspot"] = self._merge_summary_metrics(
                hotspot_metrics,
                next(iter(hotspot_summaries.values()), {}),
            )

            # Calcular degradacion
            normal_tp = arch_data["normal"].get("throughput", 0)
            hotspot_tp = arch_data["hotspot"].get("throughput", 0)
            if normal_tp > 0:
                arch_data["throughput_degradation_pct"] = round(
                    (1 - safe_divide(hotspot_tp, normal_tp)) * 100, 2
                )
            else:
                arch_data["throughput_degradation_pct"] = 0.0

            contention[arch] = arch_data

        return contention

    def get_summary_table(self) -> list[dict[str, Any]]:
        """Genera una tabla resumen con las metricas clave de cada benchmark.

        Returns:
            Lista de diccionarios, uno por fila de la tabla.
        """
        rows: list[dict[str, Any]] = []
        comparison = self.compare_architectures()

        for bench_name, data in comparison.items():
            for arch in ["direct", "indirect"]:
                arch_data = data.get(arch, {})
                rows.append({
                    "benchmark": bench_name,
                    "architecture": arch,
                    "throughput": arch_data.get("throughput", arch_data.get("throughput_ops_per_second", 0)),
                    "latency_mean": arch_data.get("latency_mean", arch_data.get("average_latency_ms", 0)),
                    "latency_p95": arch_data.get("latency_p95", 0),
                    "latency_p99": arch_data.get("latency_p99", 0),
                    "success_rate": arch_data.get("success_rate", 0),
                    "error_rate": arch_data.get("error_rate", 0),
                    "accepted": arch_data.get("accepted", 0),
                    "rejected": arch_data.get("rejected", 0),
                })

        return rows

    @staticmethod
    def _empty_metrics() -> dict[str, Any]:
        """Retorna un diccionario de metricas vacio."""
        return {
            "total_operations": 0,
            "total_time_seconds": 0.0,
            "throughput": 0.0,
            "latency_mean": 0.0,
            "latency_std": 0.0,
            "latency_min": 0.0,
            "latency_max": 0.0,
            "latency_p50": 0.0,
            "latency_p95": 0.0,
            "latency_p99": 0.0,
            "success_rate": 0.0,
            "rejection_rate": 0.0,
            "duplicate_rate": 0.0,
            "error_rate": 0.0,
            "accepted": 0,
            "rejected": 0,
            "duplicates": 0,
            "errors": 0,
        }
