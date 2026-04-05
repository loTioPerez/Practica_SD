"""Calculos de throughput por arquitectura, escenario y numero de workers.

Re-exporta funcionalidades de utilidades de analisis.
"""

from __future__ import annotations

from concert_ticketing.apps.analysis.utils import (
    calculate_throughput,
    safe_divide,
)

__all__ = ["calculate_throughput", "safe_divide"]
