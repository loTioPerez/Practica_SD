"""Generacion de graficas para la memoria y la comparativa final.

Este modulo re-exporta las funcionalidades del modulo de analisis
principal en apps/analysis/plotter.py para compatibilidad.
"""

from __future__ import annotations

from concert_ticketing.apps.analysis.plotter import (
    COLORS,
    BenchmarkPlotter,
)

__all__ = ["BenchmarkPlotter", "COLORS"]
