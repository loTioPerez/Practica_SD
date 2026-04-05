"""Punto de entrada ejecutable para la API REST directa.

La construccion concreta de la aplicacion vive en
`concert_ticketing.adapters.api.rest.app_factory`.

El puerto se resuelve con esta prioridad:
  1. Argumento --port en línea de comandos
  2. Variable de entorno DIRECT_API_PORT
  3. Valor por defecto 8000
"""

import argparse
import os

import uvicorn

from concert_ticketing.adapters.api.rest.app_factory import create_app
from concert_ticketing.shared.config import AppConfig

app = create_app()


def _resolve_port() -> int:
    """Resuelve el puerto de escucha con prioridad: CLI > env > default."""
    parser = argparse.ArgumentParser(
        description="API REST directa del sistema de ticketing",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Puerto de escucha (default: env DIRECT_API_PORT o 8000)",
    )
    args, _ = parser.parse_known_args()

    if args.port is not None:
        return args.port

    env_port = os.getenv("DIRECT_API_PORT")
    if env_port is not None:
        try:
            return int(env_port)
        except ValueError:
            pass

    return 8000


def main() -> None:
    port = _resolve_port()
    config = AppConfig.from_env()
    uvicorn.run(
        app,
        host=config.host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
