"""Utilidades para el analisis de benchmarks.

Proporciona funciones auxiliares para calculo de percentiles,
throughput, formateo de metricas y carga de resultados.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any


def calculate_percentiles(
    data: list[float],
    percentiles: list[int] | None = None,
) -> dict[str, float]:
    """Calcula los percentiles especificados de una lista de valores.

    Args:
        data: Lista de valores numericos (e.g. latencias en ms).
        percentiles: Lista de percentiles a calcular. Por defecto [50, 95, 99].

    Returns:
        Diccionario con percentil como clave (e.g. 'p50') y valor calculado.
    """
    if percentiles is None:
        percentiles = [50, 95, 99]
    if not data:
        return {f"p{p}": 0.0 for p in percentiles}

    sorted_data = sorted(data)
    result: dict[str, float] = {}
    for p in percentiles:
        # Usar statistics.quantiles para calculo preciso
        if len(sorted_data) < 2:
            result[f"p{p}"] = round(sorted_data[0], 4)
        else:
            quantile_values = statistics.quantiles(sorted_data, n=100)
            idx = max(0, min(p - 1, len(quantile_values) - 1))
            result[f"p{p}"] = round(quantile_values[idx], 4)
    return result


def calculate_throughput(total_ops: int, total_time: float) -> float:
    """Calcula el throughput en operaciones por segundo.

    Args:
        total_ops: Numero total de operaciones.
        total_time: Tiempo total en segundos.

    Returns:
        Operaciones por segundo, 0.0 si total_time <= 0.
    """
    if total_time <= 0:
        return 0.0
    return round(total_ops / total_time, 4)


def format_duration(seconds: float) -> str:
    """Formatea una duracion en formato legible."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    remaining = seconds % 60
    return f"{minutes}m {remaining:.1f}s"


def format_number(value: float, decimals: int = 2) -> str:
    """Formatea un numero con separador de miles."""
    if isinstance(value, int) or value == int(value):
        return f"{int(value):,}"
    return f"{value:,.{decimals}f}"


def format_metrics(metrics: dict[str, Any]) -> str:
    """Formatea un diccionario de metricas para visualizacion.

    Args:
        metrics: Diccionario con las metricas a formatear.

    Returns:
        String con metricas formateadas de forma legible.
    """
    lines: list[str] = []
    for key, value in metrics.items():
        if isinstance(value, float):
            lines.append(f"  {key}: {format_number(value)}")
        elif isinstance(value, dict):
            lines.append(f"  {key}:")
            for sub_key, sub_value in value.items():
                lines.append(f"    {sub_key}: {sub_value}")
        else:
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def load_benchmark_summary(path: str | Path) -> dict[str, Any]:
    """Carga un fichero de resumen de benchmark (JSON).

    Args:
        path: Ruta al fichero JSON de resumen.

    Returns:
        Diccionario con los datos del resumen.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontro el fichero: {file_path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def load_benchmark_results(path: str | Path) -> list[dict[str, Any]]:
    """Carga un fichero de resultados individuales (JSON Lines).

    Args:
        path: Ruta al fichero JSONL de resultados.

    Returns:
        Lista de diccionarios con los resultados individuales.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontro el fichero: {file_path}")

    results: list[dict[str, Any]] = []
    for line in file_path.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            results.append(json.loads(line))
    return results


def load_all_summaries(directory: str | Path) -> dict[str, dict[str, Any]]:
    """Carga todos los ficheros de resumen de un directorio.

    Args:
        directory: Ruta al directorio con ficheros *_summary.json.

    Returns:
        Diccionario con nombre del benchmark como clave y resumen como valor.
    """
    dir_path = Path(directory)
    summaries: dict[str, dict[str, Any]] = {}

    if not dir_path.exists():
        return summaries

    for summary_file in sorted(dir_path.glob("*_summary.json")):
        name = summary_file.stem.replace("_summary", "")
        summaries[name] = load_benchmark_summary(summary_file)

    return summaries


def load_all_results(directory: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Carga todos los ficheros de resultados de un directorio.

    Args:
        directory: Ruta al directorio con ficheros *_results.jsonl.

    Returns:
        Diccionario con nombre del benchmark como clave y resultados como valor.
    """
    dir_path = Path(directory)
    all_results: dict[str, list[dict[str, Any]]] = {}

    if not dir_path.exists():
        return all_results

    for results_file in sorted(dir_path.glob("*_results.jsonl")):
        name = results_file.stem.replace("_results", "")
        all_results[name] = load_benchmark_results(results_file)

    return all_results


def extract_latencies(results: list[dict[str, Any]]) -> list[float]:
    """Extrae las latencias (elapsed_ms) de una lista de resultados."""
    return [
        r["elapsed_ms"]
        for r in results
        if "elapsed_ms" in r and r.get("error") is None
    ]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division segura que retorna default si el denominador es 0."""
    if denominator == 0:
        return default
    return numerator / denominator
