"""Configuracion centralizada de logging."""

from __future__ import annotations

import logging
import os
import sys

_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """Configura el logging del proceso una sola vez."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format=_LOG_FORMAT,
        stream=sys.stdout,
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el nivel configurado por entorno."""
    level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level)
    return logging.getLogger(name)
