"""Inicializa el estado base de Redis para desarrollo local."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from concert_ticketing.core.services.purchase_service import PurchaseService
from concert_ticketing.adapters.persistence.redis.connection import create_redis_client
from concert_ticketing.adapters.persistence.redis.repositories import (
    RedisIdempotencyRepository,
    RedisInventoryRepository,
    RedisResultRepository,
)
from concert_ticketing.shared.constants import TOTAL_TICKETS


def build_service() -> PurchaseService:
    """Construye PurchaseService contra Redis local."""
    client = create_redis_client()
    return PurchaseService(
        inventory=RedisInventoryRepository(client),
        idempotency=RedisIdempotencyRepository(client),
        results=RedisResultRepository(client),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicializa el estado local en Redis.")
    parser.add_argument(
        "--ticket-type",
        default="all",
        choices=["unnumbered", "numbered", "all"],
        help="Tipo de inventario a resetear e inicializar.",
    )
    parser.add_argument(
        "--total-tickets",
        type=int,
        default=TOTAL_TICKETS,
        help="Numero total de entradas a crear.",
    )
    args = parser.parse_args()

    service = build_service()
    service.reset(args.ticket_type, args.total_tickets)
    if args.ticket_type in ("unnumbered", "all"):
        service.initialize("unnumbered", args.total_tickets)
    if args.ticket_type in ("numbered", "all"):
        service.initialize("numbered", args.total_tickets)

    print(
        f"Estado local inicializado: ticket_type={args.ticket_type} "
        f"total_tickets={args.total_tickets}"
    )


if __name__ == "__main__":
    main()
