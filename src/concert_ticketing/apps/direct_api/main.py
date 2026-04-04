"""Punto de entrada ejecutable para la API REST directa."""

from __future__ import annotations

import os

from concert_ticketing.adapters.api.rest.app_factory import create_app


def main() -> None:
    """Arranca la API REST directa con Uvicorn."""
    import uvicorn

    host = os.getenv("DIRECT_API_HOST", "0.0.0.0")
    port = int(os.getenv("DIRECT_API_PORT", "8000"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
