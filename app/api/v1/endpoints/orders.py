"""Order endpoints — checkout, view, cancel."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_order_service
from app.repositories.order import OrderRepository
from app.schemas.common import Page, PageParams
from app.schemas.order import OrderCreate, OrderRead
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate, user: CurrentUser, service: OrderServiceDep
) -> OrderRead:
    """Place an order. Reserves stock atomically; fails if any line is short."""
    order = await service.create_order(user, data)
    return OrderRead.model_validate(order)


@router.get("", response_model=Page[OrderRead])
async def list_my_orders(
    user: CurrentUser,
    service: OrderServiceDep,
    params: Annotated[PageParams, Depends()],
) -> Page[OrderRead]:
    repo: OrderRepository = service.orders
    items, total = await repo.list_for_user(
        user.id, offset=params.offset, limit=params.size
    )
    return Page.create([OrderRead.model_validate(o) for o in items], total, params)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int, user: CurrentUser, service: OrderServiceDep
) -> OrderRead:
    return OrderRead.model_validate(await service.get_for_user(order_id, user))


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int, user: CurrentUser, service: OrderServiceDep
) -> OrderRead:
    return OrderRead.model_validate(await service.cancel(order_id, user))
