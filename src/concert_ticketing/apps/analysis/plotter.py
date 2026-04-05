"""Generacion de graficos comparativos de benchmarks.

Produce graficos de throughput, latencia, escalabilidad,
comparacion por tipo de ticket y analisis de contencion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Backend sin GUI
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# Paleta de colores consistente
COLORS = {
    "direct": "#2196F3",       # Azul
    "indirect": "#FF9800",     # Naranja
    "unnumbered": "#4CAF50",   # Verde
    "numbered": "#E91E63",     # Rosa
    "normal": "#00BCD4",       # Cyan
    "hotspot": "#F44336",      # Rojo
    "ideal": "#9E9E9E",        # Gris
}

FIGSIZE_STANDARD = (10, 6)
FIGSIZE_WIDE = (12, 6)
FIGSIZE_TALL = (10, 8)


class BenchmarkPlotter:
    """Generador de graficos comparativos de benchmarks."""

    def __init__(self, output_dir: str | Path = "benchmarks/outputs/plots") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_plots: list[str] = []
        plt.style.use("seaborn-v0_8-whitegrid")

    def plot_throughput_comparison(
        self,
        comparison: dict[str, Any],
        title: str = "Throughput: Direct vs Indirect",
        filename: str = "throughput_comparison.png",
    ) -> Path:
        """Grafico de barras comparando throughput entre arquitecturas.

        Args:
            comparison: Datos de compare_architectures().
            title: Titulo del grafico.
            filename: Nombre del fichero de salida.

        Returns:
            Ruta al fichero generado.
        """
        benchmarks = list(comparison.keys())
        if not benchmarks:
            return self._empty_plot(filename, title)

        direct_tp = []
        indirect_tp = []

        for name in benchmarks:
            d = comparison[name].get("direct", {})
            i = comparison[name].get("indirect", {})
            direct_tp.append(
                d.get("throughput", d.get("throughput_ops_per_second", 0))
            )
            indirect_tp.append(
                i.get("throughput", i.get("throughput_ops_per_second", 0))
            )

        x = np.arange(len(benchmarks))
        width = 0.35

        fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
        bars1 = ax.bar(x - width / 2, direct_tp, width, label="Direct",
                       color=COLORS["direct"], edgecolor="white", linewidth=0.5)
        bars2 = ax.bar(x + width / 2, indirect_tp, width, label="Indirect",
                       color=COLORS["indirect"], edgecolor="white", linewidth=0.5)

        ax.set_xlabel("Benchmark", fontsize=12)
        ax.set_ylabel("Throughput (ops/s)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self._format_labels(benchmarks), rotation=15, ha="right")
        ax.legend(fontsize=11)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f"{val:,.0f}"))

        # Etiquetas sobre barras
        self._add_bar_labels(ax, bars1)
        self._add_bar_labels(ax, bars2)

        fig.tight_layout()
        return self._save(fig, filename)

    def plot_latency_distribution(
        self,
        direct_latencies: list[float],
        indirect_latencies: list[float],
        title: str = "Distribucion de Latencia",
        filename: str = "latency_distribution.png",
    ) -> Path:
        """Histograma de distribucion de latencias por arquitectura.

        Args:
            direct_latencies: Latencias en ms de arquitectura directa.
            indirect_latencies: Latencias en ms de arquitectura indirecta.
            title: Titulo del grafico.
            filename: Nombre del fichero de salida.

        Returns:
            Ruta al fichero generado.
        """
        fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE, sharey=True)

        for ax, latencies, label, color in [
            (axes[0], direct_latencies, "Direct", COLORS["direct"]),
            (axes[1], indirect_latencies, "Indirect", COLORS["indirect"]),
        ]:
            if latencies:
                n_bins = min(50, max(10, len(latencies) // 100))
                ax.hist(latencies, bins=n_bins, color=color, alpha=0.7,
                        edgecolor="white", linewidth=0.5)

                # Lineas de percentiles
                if len(latencies) >= 2:
                    import statistics
                    quantiles = statistics.quantiles(latencies, n=100)
                    p50 = quantiles[49] if len(quantiles) > 49 else latencies[0]
                    p95 = quantiles[94] if len(quantiles) > 94 else latencies[-1]
                    p99 = quantiles[98] if len(quantiles) > 98 else latencies[-1]

                    for pval, plabel, ls in [
                        (p50, "P50", "--"), (p95, "P95", "-."), (p99, "P99", ":")
                    ]:
                        ax.axvline(pval, color="red", linestyle=ls, linewidth=1.5,
                                   label=f"{plabel}: {pval:.1f}ms")

            ax.set_title(f"{label}", fontsize=12, fontweight="bold")
            ax.set_xlabel("Latencia (ms)", fontsize=10)
            ax.legend(fontsize=9)

        axes[0].set_ylabel("Frecuencia", fontsize=10)
        fig.suptitle(title, fontsize=14, fontweight="bold")
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_scalability(
        self,
        scalability_data: dict[str, Any],
        title: str = "Escalabilidad: Throughput vs Workers",
        filename: str = "scalability.png",
    ) -> Path:
        """Grafico de lineas de escalabilidad (throughput vs workers).

        Args:
            scalability_data: Datos de analyze_scalability().
            title: Titulo del grafico.
            filename: Nombre del fichero de salida.

        Returns:
            Ruta al fichero generado.
        """
        fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)

        has_data = False
        for arch, color, marker in [
            ("direct", COLORS["direct"], "o"),
            ("indirect", COLORS["indirect"], "s"),
        ]:
            arch_data = scalability_data.get(arch, {})
            if not arch_data:
                continue

            workers = sorted(arch_data.keys())
            throughputs = [
                arch_data[w].get("throughput", arch_data[w].get("avg_throughput_from_summaries", 0))
                for w in workers
            ]

            if any(t > 0 for t in throughputs):
                has_data = True
                ax.plot(workers, throughputs, f"-{marker}", color=color,
                       label=arch.capitalize(), linewidth=2, markersize=8)

        if has_data:
            # Linea de escalamiento ideal
            all_workers = set()
            for arch_data in scalability_data.values():
                if isinstance(arch_data, dict):
                    all_workers.update(arch_data.keys())
            if all_workers:
                workers_sorted = sorted(all_workers)
                min_workers = workers_sorted[0]
                # Usar el throughput mas alto del worker minimo como base
                base_tp = 0
                for arch_data in scalability_data.values():
                    if isinstance(arch_data, dict) and min_workers in arch_data:
                        tp = arch_data[min_workers].get(
                            "throughput",
                            arch_data[min_workers].get("avg_throughput_from_summaries", 0)
                        )
                        base_tp = max(base_tp, tp)

                if base_tp > 0:
                    ideal = [base_tp * (w / min_workers) for w in workers_sorted]
                    ax.plot(workers_sorted, ideal, "--", color=COLORS["ideal"],
                           label="Escalado ideal", linewidth=1.5, alpha=0.7)

        ax.set_xlabel("Numero de Workers", fontsize=12)
        ax.set_ylabel("Throughput (ops/s)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.legend(fontsize=11)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f"{val:,.0f}"))

        if has_data:
            ax.set_xticks(sorted(all_workers))

        fig.tight_layout()
        return self._save(fig, filename)

    def plot_ticket_type_comparison(
        self,
        comparison: dict[str, Any],
        title: str = "Comparacion: Unnumbered vs Numbered",
        filename: str = "ticket_type_comparison.png",
    ) -> Path:
        """Grafico comparativo de rendimiento por tipo de ticket.

        Args:
            comparison: Datos de compare_architectures() con benchmarks
                       que contengan 'unnumbered' y 'numbered' en el nombre.
            title: Titulo del grafico.
            filename: Nombre del fichero de salida.

        Returns:
            Ruta al fichero generado.
        """
        # Clasificar benchmarks por tipo
        unnumbered_benchmarks = {
            k: v for k, v in comparison.items() if "unnumbered" in k.lower()
        }
        numbered_benchmarks = {
            k: v for k, v in comparison.items() if "numbered" in k.lower() and "unnumbered" not in k.lower()
        }

        fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

        # Throughput por tipo de ticket
        ax = axes[0]
        categories = ["Direct", "Indirect"]

        unnumbered_tp = [0.0, 0.0]
        numbered_tp = [0.0, 0.0]

        for bench_data in unnumbered_benchmarks.values():
            for i, arch in enumerate(["direct", "indirect"]):
                d = bench_data.get(arch, {})
                tp = d.get("throughput", d.get("throughput_ops_per_second", 0))
                unnumbered_tp[i] = max(unnumbered_tp[i], tp)

        for bench_data in numbered_benchmarks.values():
            for i, arch in enumerate(["direct", "indirect"]):
                d = bench_data.get(arch, {})
                tp = d.get("throughput", d.get("throughput_ops_per_second", 0))
                numbered_tp[i] = max(numbered_tp[i], tp)

        x = np.arange(len(categories))
        width = 0.35

        ax.bar(x - width / 2, unnumbered_tp, width, label="Unnumbered",
               color=COLORS["unnumbered"], edgecolor="white")
        ax.bar(x + width / 2, numbered_tp, width, label="Numbered",
               color=COLORS["numbered"], edgecolor="white")

        ax.set_ylabel("Throughput (ops/s)", fontsize=10)
        ax.set_title("Throughput por Tipo", fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend(fontsize=10)

        # Latencia por tipo de ticket
        ax = axes[1]
        unnumbered_lat = [0.0, 0.0]
        numbered_lat = [0.0, 0.0]

        for bench_data in unnumbered_benchmarks.values():
            for i, arch in enumerate(["direct", "indirect"]):
                d = bench_data.get(arch, {})
                lat = d.get("latency_mean", d.get("average_latency_ms", 0))
                unnumbered_lat[i] = max(unnumbered_lat[i], lat)

        for bench_data in numbered_benchmarks.values():
            for i, arch in enumerate(["direct", "indirect"]):
                d = bench_data.get(arch, {})
                lat = d.get("latency_mean", d.get("average_latency_ms", 0))
                numbered_lat[i] = max(numbered_lat[i], lat)

        ax.bar(x - width / 2, unnumbered_lat, width, label="Unnumbered",
               color=COLORS["unnumbered"], edgecolor="white")
        ax.bar(x + width / 2, numbered_lat, width, label="Numbered",
               color=COLORS["numbered"], edgecolor="white")

        ax.set_ylabel("Latencia Media (ms)", fontsize=10)
        ax.set_title("Latencia por Tipo", fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend(fontsize=10)

        fig.suptitle(title, fontsize=14, fontweight="bold")
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_contention_impact(
        self,
        contention_data: dict[str, Any],
        title: str = "Impacto de Contencion en Rendimiento",
        filename: str = "contention_impact.png",
    ) -> Path:
        """Grafico comparativo de rendimiento normal vs alta contencion.

        Args:
            contention_data: Datos de analyze_contention().
            title: Titulo del grafico.
            filename: Nombre del fichero de salida.

        Returns:
            Ruta al fichero generado.
        """
        fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

        architectures = ["direct", "indirect"]

        # Throughput: normal vs hotspot
        ax = axes[0]
        x = np.arange(len(architectures))
        width = 0.35

        normal_tp = []
        hotspot_tp = []
        for arch in architectures:
            arch_data = contention_data.get(arch, {})
            normal_tp.append(arch_data.get("normal", {}).get("throughput", 0))
            hotspot_tp.append(arch_data.get("hotspot", {}).get("throughput", 0))

        ax.bar(x - width / 2, normal_tp, width, label="Normal",
               color=COLORS["normal"], edgecolor="white")
        ax.bar(x + width / 2, hotspot_tp, width, label="Hotspot",
               color=COLORS["hotspot"], edgecolor="white")

        ax.set_ylabel("Throughput (ops/s)", fontsize=10)
        ax.set_title("Throughput: Normal vs Hotspot", fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([a.capitalize() for a in architectures])
        ax.legend(fontsize=10)

        # Latencia media: normal vs hotspot
        ax = axes[1]
        normal_lat = []
        hotspot_lat = []
        for arch in architectures:
            arch_data = contention_data.get(arch, {})
            normal_lat.append(arch_data.get("normal", {}).get("latency_mean", 0))
            hotspot_lat.append(arch_data.get("hotspot", {}).get("latency_mean", 0))

        ax.bar(x - width / 2, normal_lat, width, label="Normal",
               color=COLORS["normal"], edgecolor="white")
        ax.bar(x + width / 2, hotspot_lat, width, label="Hotspot",
               color=COLORS["hotspot"], edgecolor="white")

        ax.set_ylabel("Latencia Media (ms)", fontsize=10)
        ax.set_title("Latencia: Normal vs Hotspot", fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([a.capitalize() for a in architectures])
        ax.legend(fontsize=10)

        # Anotaciones de degradacion
        for idx, arch in enumerate(architectures):
            degradation = contention_data.get(arch, {}).get("throughput_degradation_pct", 0)
            if degradation != 0:
                ax_first = axes[0]
                ax_first.annotate(
                    f"{degradation:+.1f}%",
                    xy=(x[idx] + width / 2, hotspot_tp[idx]),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=9,
                    fontweight="bold",
                    color="red" if degradation > 0 else "green",
                )

        fig.suptitle(title, fontsize=14, fontweight="bold")
        fig.tight_layout()
        return self._save(fig, filename)

    def plot_success_failure_breakdown(
        self,
        comparison: dict[str, Any],
        title: str = "Desglose de Resultados",
        filename: str = "success_failure_breakdown.png",
    ) -> Path:
        """Grafico de barras apiladas con desglose de operaciones.

        Args:
            comparison: Datos de compare_architectures().
            title: Titulo del grafico.
            filename: Nombre del fichero de salida.

        Returns:
            Ruta al fichero generado.
        """
        fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)

        labels: list[str] = []
        accepted_vals: list[int] = []
        rejected_vals: list[int] = []
        duplicate_vals: list[int] = []
        error_vals: list[int] = []

        for bench_name, data in comparison.items():
            for arch in ["direct", "indirect"]:
                arch_data = data.get(arch, {})
                labels.append(f"{self._short_name(bench_name)}\n({arch.capitalize()})")
                accepted_vals.append(arch_data.get("accepted", 0))
                rejected_vals.append(arch_data.get("rejected", 0))
                duplicate_vals.append(arch_data.get("duplicates", 0))
                error_vals.append(arch_data.get("errors", arch_data.get("transport_errors", 0)))

        if not labels:
            return self._empty_plot(filename, title)

        x = np.arange(len(labels))
        width = 0.6

        ax.bar(x, accepted_vals, width, label="Aceptadas", color="#4CAF50")
        ax.bar(x, rejected_vals, width, bottom=accepted_vals, label="Rechazadas", color="#FFC107")

        bottom2 = [a + r for a, r in zip(accepted_vals, rejected_vals)]
        ax.bar(x, duplicate_vals, width, bottom=bottom2, label="Duplicadas", color="#FF9800")

        bottom3 = [b + d for b, d in zip(bottom2, duplicate_vals)]
        ax.bar(x, error_vals, width, bottom=bottom3, label="Errores", color="#F44336")

        ax.set_ylabel("Numero de Operaciones", fontsize=10)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.legend(fontsize=10)

        fig.tight_layout()
        return self._save(fig, filename)

    def save_all_plots(
        self,
        comparison: dict[str, Any],
        scalability_data: dict[str, Any] | None = None,
        contention_data: dict[str, Any] | None = None,
        direct_latencies: list[float] | None = None,
        indirect_latencies: list[float] | None = None,
    ) -> list[Path]:
        """Genera y guarda todos los graficos disponibles.

        Returns:
            Lista de rutas a los ficheros generados.
        """
        plots: list[Path] = []

        # 1. Throughput comparison
        plots.append(self.plot_throughput_comparison(comparison))

        # 2. Latency distribution
        if direct_latencies or indirect_latencies:
            plots.append(self.plot_latency_distribution(
                direct_latencies or [],
                indirect_latencies or [],
            ))

        # 3. Scalability
        if scalability_data:
            plots.append(self.plot_scalability(scalability_data))

        # 4. Ticket type comparison
        plots.append(self.plot_ticket_type_comparison(comparison))

        # 5. Contention impact
        if contention_data:
            plots.append(self.plot_contention_impact(contention_data))

        # 6. Success/failure breakdown
        plots.append(self.plot_success_failure_breakdown(comparison))

        return plots

    # ---- Helpers privados ----

    def _save(self, fig: plt.Figure, filename: str) -> Path:
        """Guarda figura y cierra."""
        path = self.output_dir / filename
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.generated_plots.append(str(path))
        return path

    def _empty_plot(self, filename: str, title: str) -> Path:
        """Genera un grafico vacio con mensaje."""
        fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
        ax.text(0.5, 0.5, "No hay datos disponibles",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=14, color="gray")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_axis_off()
        fig.tight_layout()
        return self._save(fig, filename)

    @staticmethod
    def _add_bar_labels(ax: plt.Axes, bars: Any) -> None:
        """Anade etiquetas de valor sobre las barras."""
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(
                    f"{height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center", va="bottom",
                    fontsize=8,
                )

    @staticmethod
    def _format_labels(labels: list[str]) -> list[str]:
        """Formatea etiquetas de benchmarks para mejor lectura."""
        formatted = []
        for label in labels:
            label = label.replace("benchmark_", "").replace("_", " ").title()
            formatted.append(label)
        return formatted

    @staticmethod
    def _short_name(name: str) -> str:
        """Acorta nombres de benchmarks."""
        return name.replace("benchmark_", "").replace("_", " ").title()
