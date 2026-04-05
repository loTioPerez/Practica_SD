"""Generacion de reportes comparativos de benchmarks.

Produce reportes en formato Markdown y HTML con tablas,
graficos y analisis de resultados.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import format_duration, format_number


class BenchmarkReporter:
    """Generador de reportes comparativos de benchmarks."""

    def __init__(
        self,
        output_dir: str | Path = "benchmarks/outputs/reports",
        plots_dir: str | Path = "benchmarks/outputs/plots",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir = Path(plots_dir)

    def generate_markdown_report(
        self,
        comparison: dict[str, Any],
        scalability: dict[str, Any] | None = None,
        contention: dict[str, Any] | None = None,
        summary_table: list[dict[str, Any]] | None = None,
        generated_plots: list[str] | None = None,
    ) -> Path:
        """Genera un reporte completo en formato Markdown.

        Args:
            comparison: Datos de compare_architectures().
            scalability: Datos de analyze_scalability().
            contention: Datos de analyze_contention().
            summary_table: Tabla resumen de get_summary_table().
            generated_plots: Lista de rutas a graficos generados.

        Returns:
            Ruta al fichero MD generado.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        sections: list[str] = []

        # Header
        sections.append("# Benchmark Comparison Report")
        sections.append(f"\n> Generado: {timestamp}\n")

        # Executive Summary
        sections.append("## Executive Summary\n")
        sections.append(self._generate_executive_summary(comparison, scalability, contention))

        # Methodology
        sections.append("## Methodology\n")
        sections.append(self._generate_methodology())

        # Summary Table
        if summary_table:
            sections.append("## Summary Table\n")
            sections.append(self._generate_summary_table_md(summary_table))

        # Direct Architecture Results
        sections.append("## Direct Architecture Results\n")
        sections.append(self._generate_architecture_section_md(comparison, "direct"))

        # Indirect Architecture Results
        sections.append("## Indirect Architecture Results\n")
        sections.append(self._generate_architecture_section_md(comparison, "indirect"))

        # Comparative Analysis
        sections.append("## Comparative Analysis\n")
        sections.append(self._generate_comparative_analysis_md(comparison))

        # Scalability Analysis
        if scalability:
            sections.append("## Scalability Analysis\n")
            sections.append(self._generate_scalability_section_md(scalability))

        # Contention Analysis
        if contention:
            sections.append("## Contention Analysis\n")
            sections.append(self._generate_contention_section_md(contention))

        # Plots
        if generated_plots:
            sections.append("## Plots\n")
            sections.append(self._include_plots_md(generated_plots))

        # Conclusions
        sections.append("## Conclusions\n")
        sections.append(self._generate_conclusions(comparison, scalability, contention))

        content = "\n".join(sections)
        output_path = self.output_dir / "benchmark_report.md"
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def generate_html_report(
        self,
        comparison: dict[str, Any],
        scalability: dict[str, Any] | None = None,
        contention: dict[str, Any] | None = None,
        summary_table: list[dict[str, Any]] | None = None,
        generated_plots: list[str] | None = None,
    ) -> Path:
        """Genera un reporte completo en formato HTML.

        Returns:
            Ruta al fichero HTML generado.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        html_parts: list[str] = []
        html_parts.append(self._html_header(timestamp))

        # Executive Summary
        html_parts.append('<section id="executive-summary">')
        html_parts.append("<h2>Executive Summary</h2>")
        html_parts.append(self._md_to_html_paragraphs(
            self._generate_executive_summary(comparison, scalability, contention)
        ))
        html_parts.append("</section>")

        # Summary Table
        if summary_table:
            html_parts.append('<section id="summary-table">')
            html_parts.append("<h2>Summary Table</h2>")
            html_parts.append(self._generate_summary_table_html(summary_table))
            html_parts.append("</section>")

        # Architecture Results
        for arch in ["direct", "indirect"]:
            html_parts.append(f'<section id="{arch}-results">')
            html_parts.append(f"<h2>{arch.capitalize()} Architecture Results</h2>")
            html_parts.append(self._generate_architecture_table_html(comparison, arch))
            html_parts.append("</section>")

        # Comparative Analysis
        html_parts.append('<section id="comparative">')
        html_parts.append("<h2>Comparative Analysis</h2>")
        html_parts.append(self._generate_comparative_table_html(comparison))
        html_parts.append("</section>")

        # Scalability
        if scalability:
            html_parts.append('<section id="scalability">')
            html_parts.append("<h2>Scalability Analysis</h2>")
            html_parts.append(self._generate_scalability_table_html(scalability))
            html_parts.append("</section>")

        # Contention
        if contention:
            html_parts.append('<section id="contention">')
            html_parts.append("<h2>Contention Analysis</h2>")
            html_parts.append(self._generate_contention_table_html(contention))
            html_parts.append("</section>")

        # Plots
        if generated_plots:
            html_parts.append('<section id="plots">')
            html_parts.append("<h2>Plots</h2>")
            html_parts.append(self._include_plots_html(generated_plots))
            html_parts.append("</section>")

        # Conclusions
        html_parts.append('<section id="conclusions">')
        html_parts.append("<h2>Conclusions</h2>")
        html_parts.append(self._md_to_html_paragraphs(
            self._generate_conclusions(comparison, scalability, contention)
        ))
        html_parts.append("</section>")

        html_parts.append(self._html_footer())

        content = "\n".join(html_parts)
        output_path = self.output_dir / "benchmark_report.html"
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def generate_summary_table(
        self,
        summary_table: list[dict[str, Any]],
        filename: str = "summary_table.json",
    ) -> Path:
        """Guarda la tabla resumen como JSON."""
        output_path = self.output_dir / filename
        output_path.write_text(
            json.dumps(summary_table, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return output_path

    # ---- Secciones Markdown ----

    def _generate_executive_summary(
        self,
        comparison: dict[str, Any],
        scalability: dict[str, Any] | None,
        contention: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []
        lines.append("### Key Findings\n")

        # Analizar throughput
        best_arch = ""
        max_tp_ratio = 0
        for bench_name, data in comparison.items():
            ratio = data.get("throughput_ratio")
            if ratio and ratio > max_tp_ratio:
                max_tp_ratio = ratio

        if max_tp_ratio > 1:
            lines.append(f"- **Direct architecture** achieves up to **{max_tp_ratio:.1f}x** higher throughput than indirect.")
            best_arch = "direct"
        elif max_tp_ratio > 0:
            lines.append(f"- **Indirect architecture** achieves up to **{1/max_tp_ratio:.1f}x** higher throughput than direct.")
            best_arch = "indirect"
        else:
            lines.append("- No comparative throughput data available.")

        # Numero de benchmarks
        n_benchmarks = len(comparison)
        lines.append(f"- **{n_benchmarks}** benchmark scenarios evaluated.")

        # Escalabilidad
        if scalability:
            for arch in ["direct", "indirect"]:
                arch_data = scalability.get(arch, {})
                if len(arch_data) >= 2:
                    workers = sorted(arch_data.keys())
                    first_tp = arch_data[workers[0]].get("throughput", 0)
                    last_tp = arch_data[workers[-1]].get("throughput", 0)
                    if first_tp > 0:
                        speedup = last_tp / first_tp
                        lines.append(
                            f"- **{arch.capitalize()}** scales from {workers[0]} to {workers[-1]} "
                            f"workers with **{speedup:.1f}x** speedup."
                        )

        # Contencion
        if contention:
            for arch in ["direct", "indirect"]:
                deg = contention.get(arch, {}).get("throughput_degradation_pct", 0)
                if deg > 0:
                    lines.append(
                        f"- **{arch.capitalize()}** shows **{deg:.1f}%** throughput degradation under high contention."
                    )

        lines.append("")
        lines.append("### Recommendations\n")
        if best_arch == "direct":
            lines.append("- Use **direct architecture** for lowest latency and highest throughput.")
            lines.append("- Consider **indirect architecture** for decoupling and fault tolerance.")
        elif best_arch == "indirect":
            lines.append("- **Indirect architecture** provides better throughput in tested scenarios.")
            lines.append("- **Direct architecture** may still be preferred for simplicity.")
        else:
            lines.append("- Run benchmarks to generate comparative data and recommendations.")

        return "\n".join(lines)

    def _generate_methodology(self) -> str:
        return """### Test Setup

- **System**: Concert Ticketing System (20,000 tickets default)
- **Architectures**: Direct (REST + NGINX) and Indirect (RabbitMQ + Workers)
- **Persistence**: Redis
- **Benchmark Tool**: Custom async HTTP benchmark runner (httpx)

### Workloads

| Workload | Description | Operations |
|----------|-------------|------------|
| Unnumbered | General admission tickets | 20,000 |
| Numbered | Specific seat purchases | 60,000 |
| Hotspot | High contention (80% to 5% of seats) | Variable |

### Configuration

- **Concurrency**: 50 concurrent requests (configurable)
- **Timeout**: 60 seconds per request
- **Workers tested**: 1, 2, 4, 8
"""

    def _generate_summary_table_md(self, table: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        lines.append("| Benchmark | Architecture | Throughput (ops/s) | Latency Mean (ms) | P95 (ms) | P99 (ms) | Success Rate | Error Rate |")
        lines.append("|-----------|-------------|-------------------|-------------------|----------|----------|-------------|------------|")

        for row in table:
            lines.append(
                f"| {row.get('benchmark', 'N/A')} "
                f"| {row.get('architecture', 'N/A')} "
                f"| {format_number(row.get('throughput', 0))} "
                f"| {format_number(row.get('latency_mean', 0))} "
                f"| {format_number(row.get('latency_p95', 0))} "
                f"| {format_number(row.get('latency_p99', 0))} "
                f"| {format_number(row.get('success_rate', 0))}% "
                f"| {format_number(row.get('error_rate', 0))}% |"
            )
        lines.append("")
        return "\n".join(lines)

    def _generate_architecture_section_md(self, comparison: dict[str, Any], arch: str) -> str:
        lines: list[str] = []

        for bench_name, data in comparison.items():
            arch_data = data.get(arch, {})
            if not arch_data:
                continue

            lines.append(f"### {bench_name}\n")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")

            tp = arch_data.get("throughput", arch_data.get("throughput_ops_per_second", 0))
            lines.append(f"| Throughput | {format_number(tp)} ops/s |")

            lat = arch_data.get("latency_mean", arch_data.get("average_latency_ms", 0))
            lines.append(f"| Latency (mean) | {format_number(lat)} ms |")

            for key in ["latency_p50", "latency_p95", "latency_p99"]:
                val = arch_data.get(key, 0)
                if val:
                    lines.append(f"| {key.replace('latency_', 'Latency ').upper()} | {format_number(val)} ms |")

            accepted = arch_data.get("accepted", 0)
            rejected = arch_data.get("rejected", 0)
            lines.append(f"| Accepted | {format_number(accepted)} |")
            lines.append(f"| Rejected | {format_number(rejected)} |")
            lines.append(f"| Success Rate | {format_number(arch_data.get('success_rate', 0))}% |")
            lines.append("")

        return "\n".join(lines)

    def _generate_comparative_analysis_md(self, comparison: dict[str, Any]) -> str:
        lines: list[str] = []
        lines.append("### Direct vs Indirect\n")
        lines.append("| Benchmark | Direct Throughput | Indirect Throughput | Ratio | Direct Latency | Indirect Latency |")
        lines.append("|-----------|------------------|--------------------|---------|-----------------|--------------------|")

        for bench_name, data in comparison.items():
            d = data.get("direct", {})
            i = data.get("indirect", {})
            d_tp = d.get("throughput", d.get("throughput_ops_per_second", 0))
            i_tp = i.get("throughput", i.get("throughput_ops_per_second", 0))
            ratio = data.get("throughput_ratio", "N/A")
            d_lat = d.get("latency_mean", d.get("average_latency_ms", 0))
            i_lat = i.get("latency_mean", i.get("average_latency_ms", 0))

            lines.append(
                f"| {bench_name} "
                f"| {format_number(d_tp)} "
                f"| {format_number(i_tp)} "
                f"| {ratio} "
                f"| {format_number(d_lat)}ms "
                f"| {format_number(i_lat)}ms |"
            )

        lines.append("")
        return "\n".join(lines)

    def _generate_scalability_section_md(self, scalability: dict[str, Any]) -> str:
        lines: list[str] = []

        for arch in ["direct", "indirect"]:
            arch_data = scalability.get(arch, {})
            if not arch_data:
                continue

            lines.append(f"### {arch.capitalize()} Scalability\n")
            lines.append("| Workers | Throughput (ops/s) | Latency Mean (ms) | Success Rate |")
            lines.append("|---------|-------------------|-------------------|-------------|")

            for workers, metrics in sorted(arch_data.items()):
                tp = metrics.get("throughput", 0)
                lat = metrics.get("latency_mean", 0)
                sr = metrics.get("success_rate", 0)
                lines.append(f"| {workers} | {format_number(tp)} | {format_number(lat)} | {format_number(sr)}% |")

            lines.append("")

        return "\n".join(lines)

    def _generate_contention_section_md(self, contention: dict[str, Any]) -> str:
        lines: list[str] = []
        lines.append("### Normal vs High Contention\n")
        lines.append("| Architecture | Scenario | Throughput (ops/s) | Latency Mean (ms) | Degradation |")
        lines.append("|-------------|----------|-------------------|-------------------|-------------|")

        for arch in ["direct", "indirect"]:
            arch_data = contention.get(arch, {})
            for scenario in ["normal", "hotspot"]:
                metrics = arch_data.get(scenario, {})
                tp = metrics.get("throughput", 0)
                lat = metrics.get("latency_mean", 0)
                lines.append(
                    f"| {arch.capitalize()} | {scenario.capitalize()} "
                    f"| {format_number(tp)} | {format_number(lat)} | - |"
                )

            deg = arch_data.get("throughput_degradation_pct", 0)
            lines.append(f"| **{arch.capitalize()}** | **Degradation** | - | - | **{deg:.1f}%** |")

        lines.append("")
        return "\n".join(lines)

    def _include_plots_md(self, plots: list[str]) -> str:
        lines: list[str] = []
        for plot_path in plots:
            name = Path(plot_path).stem.replace("_", " ").title()
            # Ruta relativa desde reports a plots
            try:
                rel_path = Path(plot_path).relative_to(self.output_dir.parent)
            except ValueError:
                rel_path = Path(plot_path)
            lines.append(f"### {name}\n")
            lines.append(f"![{name}]({rel_path})\n")
        return "\n".join(lines)

    def _generate_conclusions(
        self,
        comparison: dict[str, Any],
        scalability: dict[str, Any] | None,
        contention: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []

        lines.append("### Tradeoffs\n")
        lines.append("- **Direct Architecture**: Lower latency, simpler deployment, but tightly coupled.")
        lines.append("- **Indirect Architecture**: Better fault tolerance, decoupled components, but higher latency.\n")

        lines.append("### Best Use Cases\n")
        lines.append("- **Direct**: Low-latency requirements, simple deployments, small to medium scale.")
        lines.append("- **Indirect**: Large scale, need for fault tolerance, asynchronous processing requirements.\n")

        lines.append("### Recommendations\n")

        # Analizar datos para dar recomendaciones concretas
        direct_faster = 0
        indirect_faster = 0
        for data in comparison.values():
            ratio = data.get("throughput_ratio")
            if ratio and ratio > 1:
                direct_faster += 1
            elif ratio and ratio < 1:
                indirect_faster += 1

        if direct_faster > indirect_faster:
            lines.append(
                f"1. Direct architecture outperforms indirect in {direct_faster}/{len(comparison)} scenarios."
            )
            lines.append("2. Consider indirect architecture for production workloads requiring fault tolerance.")
        elif indirect_faster > direct_faster:
            lines.append(
                f"1. Indirect architecture outperforms direct in {indirect_faster}/{len(comparison)} scenarios."
            )
            lines.append("2. Consider direct architecture for simplicity in small deployments.")
        else:
            lines.append("1. Both architectures show comparable performance.")
            lines.append("2. Choose based on non-functional requirements (fault tolerance, simplicity).")

        lines.append("3. Scale workers based on expected load using the scalability analysis.")
        lines.append("4. Monitor contention patterns in production to detect hotspot scenarios.")

        return "\n".join(lines)

    # ---- HTML Helpers ----

    def _html_header(self, timestamp: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Comparison Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        h1 {{ color: #1565C0; border-bottom: 3px solid #1565C0; padding-bottom: 10px; }}
        h2 {{ color: #1976D2; border-bottom: 1px solid #ddd; padding-bottom: 8px; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th {{ background: #1976D2; color: white; padding: 12px 8px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px 8px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        img {{ max-width: 100%; height: auto; border-radius: 4px; margin: 10px 0; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .metric-good {{ color: #2E7D32; font-weight: bold; }}
        .metric-bad {{ color: #C62828; font-weight: bold; }}
        nav {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        nav a {{ margin-right: 15px; color: #1976D2; text-decoration: none; }}
        nav a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Benchmark Comparison Report</h1>
    <p class="timestamp">Generated: {html.escape(timestamp)}</p>
    <nav>
        <a href="#executive-summary">Summary</a>
        <a href="#summary-table">Table</a>
        <a href="#direct-results">Direct</a>
        <a href="#indirect-results">Indirect</a>
        <a href="#comparative">Comparative</a>
        <a href="#scalability">Scalability</a>
        <a href="#contention">Contention</a>
        <a href="#plots">Plots</a>
        <a href="#conclusions">Conclusions</a>
    </nav>"""

    def _html_footer(self) -> str:
        return """</body>
</html>"""

    def _generate_summary_table_html(self, table: list[dict[str, Any]]) -> str:
        rows: list[str] = []
        rows.append("<table>")
        rows.append("<tr><th>Benchmark</th><th>Architecture</th><th>Throughput (ops/s)</th>"
                    "<th>Latency Mean (ms)</th><th>P95 (ms)</th><th>P99 (ms)</th>"
                    "<th>Success Rate</th><th>Error Rate</th></tr>")

        for row in table:
            rows.append(
                f"<tr><td>{html.escape(str(row.get('benchmark', 'N/A')))}</td>"
                f"<td>{html.escape(str(row.get('architecture', 'N/A')))}</td>"
                f"<td>{format_number(row.get('throughput', 0))}</td>"
                f"<td>{format_number(row.get('latency_mean', 0))}</td>"
                f"<td>{format_number(row.get('latency_p95', 0))}</td>"
                f"<td>{format_number(row.get('latency_p99', 0))}</td>"
                f"<td>{format_number(row.get('success_rate', 0))}%</td>"
                f"<td>{format_number(row.get('error_rate', 0))}%</td></tr>"
            )

        rows.append("</table>")
        return "\n".join(rows)

    def _generate_architecture_table_html(self, comparison: dict[str, Any], arch: str) -> str:
        rows: list[str] = []
        rows.append("<table>")
        rows.append("<tr><th>Benchmark</th><th>Throughput</th><th>Latency Mean</th>"
                    "<th>P50</th><th>P95</th><th>P99</th><th>Accepted</th><th>Rejected</th></tr>")

        for bench_name, data in comparison.items():
            d = data.get(arch, {})
            tp = d.get("throughput", d.get("throughput_ops_per_second", 0))
            lat = d.get("latency_mean", d.get("average_latency_ms", 0))

            rows.append(
                f"<tr><td>{html.escape(bench_name)}</td>"
                f"<td>{format_number(tp)} ops/s</td>"
                f"<td>{format_number(lat)} ms</td>"
                f"<td>{format_number(d.get('latency_p50', 0))} ms</td>"
                f"<td>{format_number(d.get('latency_p95', 0))} ms</td>"
                f"<td>{format_number(d.get('latency_p99', 0))} ms</td>"
                f"<td>{format_number(d.get('accepted', 0))}</td>"
                f"<td>{format_number(d.get('rejected', 0))}</td></tr>"
            )

        rows.append("</table>")
        return "\n".join(rows)

    def _generate_comparative_table_html(self, comparison: dict[str, Any]) -> str:
        rows: list[str] = []
        rows.append("<table>")
        rows.append("<tr><th>Benchmark</th><th>Direct Throughput</th><th>Indirect Throughput</th>"
                    "<th>Ratio</th><th>Direct Latency</th><th>Indirect Latency</th></tr>")

        for bench_name, data in comparison.items():
            d = data.get("direct", {})
            i = data.get("indirect", {})
            d_tp = d.get("throughput", d.get("throughput_ops_per_second", 0))
            i_tp = i.get("throughput", i.get("throughput_ops_per_second", 0))
            ratio = data.get("throughput_ratio", "N/A")
            d_lat = d.get("latency_mean", d.get("average_latency_ms", 0))
            i_lat = i.get("latency_mean", i.get("average_latency_ms", 0))

            rows.append(
                f"<tr><td>{html.escape(bench_name)}</td>"
                f"<td>{format_number(d_tp)} ops/s</td>"
                f"<td>{format_number(i_tp)} ops/s</td>"
                f"<td>{ratio}</td>"
                f"<td>{format_number(d_lat)} ms</td>"
                f"<td>{format_number(i_lat)} ms</td></tr>"
            )

        rows.append("</table>")
        return "\n".join(rows)

    def _generate_scalability_table_html(self, scalability: dict[str, Any]) -> str:
        rows: list[str] = []
        for arch in ["direct", "indirect"]:
            arch_data = scalability.get(arch, {})
            if not arch_data:
                continue
            rows.append(f"<h3>{arch.capitalize()}</h3>")
            rows.append("<table>")
            rows.append("<tr><th>Workers</th><th>Throughput (ops/s)</th>"
                        "<th>Latency Mean (ms)</th><th>Success Rate</th></tr>")
            for workers, metrics in sorted(arch_data.items()):
                rows.append(
                    f"<tr><td>{workers}</td>"
                    f"<td>{format_number(metrics.get('throughput', 0))}</td>"
                    f"<td>{format_number(metrics.get('latency_mean', 0))}</td>"
                    f"<td>{format_number(metrics.get('success_rate', 0))}%</td></tr>"
                )
            rows.append("</table>")
        return "\n".join(rows)

    def _generate_contention_table_html(self, contention: dict[str, Any]) -> str:
        rows: list[str] = []
        rows.append("<table>")
        rows.append("<tr><th>Architecture</th><th>Scenario</th><th>Throughput</th>"
                    "<th>Latency Mean</th><th>Degradation</th></tr>")
        for arch in ["direct", "indirect"]:
            arch_data = contention.get(arch, {})
            for scenario in ["normal", "hotspot"]:
                metrics = arch_data.get(scenario, {})
                rows.append(
                    f"<tr><td>{arch.capitalize()}</td><td>{scenario.capitalize()}</td>"
                    f"<td>{format_number(metrics.get('throughput', 0))} ops/s</td>"
                    f"<td>{format_number(metrics.get('latency_mean', 0))} ms</td>"
                    f"<td>-</td></tr>"
                )
            deg = arch_data.get("throughput_degradation_pct", 0)
            rows.append(
                f"<tr><td><strong>{arch.capitalize()}</strong></td>"
                f"<td><strong>Degradation</strong></td>"
                f"<td>-</td><td>-</td>"
                f"<td class='metric-bad'>{deg:.1f}%</td></tr>"
            )
        rows.append("</table>")
        return "\n".join(rows)

    def _include_plots_html(self, plots: list[str]) -> str:
        rows: list[str] = []
        for plot_path in plots:
            name = Path(plot_path).stem.replace("_", " ").title()
            try:
                rel_path = Path(plot_path).relative_to(self.output_dir.parent)
            except ValueError:
                rel_path = Path(plot_path)
            rows.append(f"<h3>{html.escape(name)}</h3>")
            rows.append(f'<img src="{html.escape(str(rel_path))}" alt="{html.escape(name)}">')
        return "\n".join(rows)

    @staticmethod
    def _md_to_html_paragraphs(md_text: str) -> str:
        """Convierte texto MD basico a parrafos HTML."""
        lines = md_text.split("\n")
        html_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("### "):
                html_lines.append(f"<h3>{html.escape(stripped[4:])}</h3>")
            elif stripped.startswith("- "):
                content = stripped[2:]
                # Convertir **bold** a <strong>
                import re
                content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
                html_lines.append(f"<li>{content}</li>")
            elif stripped:
                html_lines.append(f"<p>{html.escape(stripped)}</p>")
        return "\n".join(html_lines)
