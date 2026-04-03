"""Rutas REST para compras, salud y consulta de resultados."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from ....core.domain.enums import RejectionReason, TicketType
from ....core.services.purchase_service import PurchaseService
from ....shared.health import check_redis_health
from ....shared.exceptions import InvalidInputError
from ....shared.serialization import purchase_result_to_dict
from .dependencies import get_app_config, get_purchase_service
from .schemas import (
    ClientPurchasesResponseSchema,
    HealthResponseSchema,
    InventoryResponseSchema,
    NumberedPurchaseRequestSchema,
    PurchaseResponseSchema,
    RequestLookupResponseSchema,
    SeatStatusResponseSchema,
    StatsResponseSchema,
    UnnumberedPurchaseRequestSchema,
)

router = APIRouter()


def _status_code_from_result(result) -> int:
    """Mapea un PurchaseResult a un codigo HTTP simple y defendible."""
    if result.duplicate:
        return 200
    if result.success:
        return 200
    if result.reason in (
        RejectionReason.SOLD_OUT.value,
        RejectionReason.SEAT_ALREADY_SOLD.value,
    ):
        return 409
    if result.reason in (
        RejectionReason.INVALID_SEAT.value,
        RejectionReason.INVALID_INPUT.value,
    ):
        return 400
    return 400


def _parse_ticket_type(ticket_type: str) -> TicketType:
    """Valida y normaliza el tipo de ticket recibido por URL."""
    try:
        return TicketType(ticket_type)
    except ValueError as exc:
        raise InvalidInputError(f"ticket_type invalido: {ticket_type}") from exc


@router.get("/health", response_model=HealthResponseSchema)
def health_check(response: Response, config=Depends(get_app_config)) -> HealthResponseSchema:
    """Comprueba el estado basico del servicio y de Redis."""
    health = check_redis_health(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
    )
    if not health.healthy:
        response.status_code = 503
    return HealthResponseSchema(
        status="ok" if health.healthy else "degraded",
        redis_healthy=health.healthy,
        redis_detail=health.detail,
    )


@router.post("/buy/unnumbered", response_model=PurchaseResponseSchema)
def buy_unnumbered(
    payload: UnnumberedPurchaseRequestSchema,
    response: Response,
    service: PurchaseService = Depends(get_purchase_service),
) -> PurchaseResponseSchema:
    """Procesa una compra no numerada."""
    result = service.buy_unnumbered(payload.client_id, payload.request_id)
    response.status_code = _status_code_from_result(result)
    return PurchaseResponseSchema(**purchase_result_to_dict(result))


@router.post("/buy/numbered", response_model=PurchaseResponseSchema)
def buy_numbered(
    payload: NumberedPurchaseRequestSchema,
    response: Response,
    service: PurchaseService = Depends(get_purchase_service),
) -> PurchaseResponseSchema:
    """Procesa una compra numerada."""
    result = service.buy_numbered(payload.client_id, payload.seat_id, payload.request_id)
    response.status_code = _status_code_from_result(result)
    return PurchaseResponseSchema(**purchase_result_to_dict(result))


@router.get("/requests/{request_id}", response_model=RequestLookupResponseSchema)
@router.get("/results/{request_id}", response_model=RequestLookupResponseSchema)
def get_request_result(
    request_id: str,
    service: PurchaseService = Depends(get_purchase_service),
) -> RequestLookupResponseSchema:
    """Consulta el resultado asociado a un request_id."""
    result = service.get_request_result(request_id)
    return RequestLookupResponseSchema(
        request_id=request_id,
        found=result is not None,
        result=result,
    )


@router.get("/stats", response_model=StatsResponseSchema)
def get_stats(
    service: PurchaseService = Depends(get_purchase_service),
) -> StatsResponseSchema:
    """Estadisticas basicas de inventario para benchmark y verificacion."""
    return StatsResponseSchema(
        unnumbered_available=service.get_available_count(TicketType.UNNUMBERED),
        numbered_available=service.get_available_count(TicketType.NUMBERED),
    )


@router.get("/inventory/{ticket_type}", response_model=InventoryResponseSchema)
def get_inventory(
    ticket_type: str,
    service: PurchaseService = Depends(get_purchase_service),
) -> InventoryResponseSchema:
    """Consulta entradas disponibles para un tipo."""
    normalized = _parse_ticket_type(ticket_type)
    return InventoryResponseSchema(
        ticket_type=normalized.value,
        available=service.get_available_count(normalized),
    )


@router.get("/seats/{seat_id}", response_model=SeatStatusResponseSchema)
def get_seat_status(
    seat_id: int,
    service: PurchaseService = Depends(get_purchase_service),
) -> SeatStatusResponseSchema:
    """Consulta el estado de un asiento numerado."""
    seat = service.get_seat_status(seat_id)
    return SeatStatusResponseSchema(
        seat_id=seat.seat_id,
        status=seat.status,
        owner=seat.owner,
    )


@router.get("/clients/{client_id}/purchases", response_model=ClientPurchasesResponseSchema)
def get_client_purchases(
    client_id: str,
    service: PurchaseService = Depends(get_purchase_service),
) -> ClientPurchasesResponseSchema:
    """Consulta el historial de compras de un cliente."""
    return ClientPurchasesResponseSchema(
        client_id=client_id,
        purchases=service.get_client_purchases(client_id),
    )
