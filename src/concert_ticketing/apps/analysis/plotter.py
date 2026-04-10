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
        fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

        for ax, latencies, label, color in [
            (axes[0], direct_latencies, "Direct", COLORS["direct"]),
            (axes[1], indirect_latencies, "Indirect", COLORS["indirect"]),
        ]:
            if latencies:
                display = self._prepare_latency_display(latencies)
                display_latencies = display["latencies"]
                display_limit = display["x_limit"]

                n_bins = min(40, max(18, int(np.sqrt(len(display_latencies)) // 2)))
                bins = np.linspace(0, display_limit, n_bins)
                ax.hist(
                    display_latencies,
                    bins=bins,
                    color=color,
                    alpha=0.75,
                    edgecolor="white",
                    linewidth=0.5,
                )

                for pval, plabel, ls in [
                    (display["p50"], "P50", "--"),
                    (display["p95"], "P95", "-."),
                    (display["p99"], "P99", ":"),
                ]:
                    ax.axvline(
                        pval,
                        color="red",
                        linestyle=ls,
                        linewidth=1.5,
                        label=f"{plabel}: {pval:.1f}ms",
                    )

                ax.set_xlim(0, display_limit * 1.02)
                if display["truncated"] > 0:
                    ax.text(
                        0.98,
                        0.80,
                        f"Mostrando hasta {display_limit:.0f}ms\n"
                        f"Outliers ocultos: {display['truncated']}",
                        transform=ax.transAxes,
                        ha="right",
                        va="top",
                        fontsize=8,
                        bbox={
                            "boxstyle": "round,pad=0.25",
                            "facecolor": "white",
                            "edgecolor": "#cccccc",
                            "alpha": 0.85,
                        },
                    )

            ax.set_title(f"{label}", fontsize=12, fontweight="bold")
            ax.set_xlabel("Latencia (ms)", fontsize=10)
            ax.yaxis.set_major_formatter(
                ticker.FuncFormatter(lambda val, _: f"{val:,.0f}")
            )
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
        all_workers: set[int] = set()
        all_throughputs: list[float] = []
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

            series = [(worker, tp) for worker, tp in zip(workers, throughputs) if tp > 0]
            if series:
                has_data = True
                series_workers, series_tp = zip(*series)
                all_workers.update(series_workers)
                all_throughputs.extend(series_tp)
                ax.plot(
                    series_workers,
                    series_tp,
                    f"-{marker}",
                    color=color,
                    label=arch.capitalize(),
                    linewidth=2.5,
                    markersize=8,
                )
                self._annotate_line_points(ax, series_workers, series_tp, color)

        ax.set_xlabel("Numero de Workers", fontsize=12)
        ax.set_ylabel("Throughput (ops/s)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        if has_data:
            ax.legend(fontsize=11)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f"{val:,.0f}"))
        ax.grid(True, axis="y", alpha=0.35)

        if has_data:
            ax.set_xticks(sorted(all_workers))
            ax.set_xlim(min(all_workers) - 0.2, max(all_workers) + 0.2)
            ax.set_ylim(0, max(all_throughputs) * 1.18)

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
    def _annotate_line_points(
        ax: plt.Axes,
        x_values: tuple[int, ...],
        y_values: tuple[float, ...],
        color: str,
    ) -> None:
        """Anade la etiqueta del valor a cada punto de una serie."""
        for x_value, y_value in zip(x_values, y_values):
            ax.annotate(
                f"{y_value:.1f}",
                xy=(x_value, y_value),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color=color,
            )

    @staticmethod
    def _prepare_latency_display(latencies: list[float]) -> dict[str, Any]:
        """Prepara una vista util de latencias, ocultando solo outliers extremos."""
        latency_array = np.asarray(latencies, dtype=float)
        p50, p95, p99, p995 = np.percentile(latency_array, [50, 95, 99, 99.5])
        clip_limit = max(p99 * 1.2, p995 * 1.05)
        x_limit = float(min(latency_array.max(), clip_limit))
        display_latencies = latency_array[latency_array <= x_limit]

        return {
            "latencies": display_latencies,
            "x_limit": x_limit,
            "p50": float(p50),
            "p95": float(p95),
            "p99": float(p99),
            "truncated": int(len(latency_array) - len(display_latencies)),
        }

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
