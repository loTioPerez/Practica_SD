"""Constantes compartidas entre componentes del sistema."""

# ---- Inventario ----
TOTAL_TICKETS: int = 20_000
MIN_SEAT_ID: int = 1
MAX_SEAT_ID: int = TOTAL_TICKETS

# ---- Redis defaults ----
REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379
REDIS_DB: int = 0
REDIS_DECODE_RESPONSES: bool = True

# ---- Benchmark ----
DEFAULT_CONCURRENCY: int = 50
DEFAULT_TIMEOUT_SECONDS: int = 60
