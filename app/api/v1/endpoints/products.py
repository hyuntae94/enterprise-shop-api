"""Product catalog endpoints. Reads are public; writes require staff/admin."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_product_service, require_staff
from app.schemas.common import Page, PageParams
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])

ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


@router.get("", response_model=Page[ProductRead])
async def list_products(
    service: ProductServiceDep,
    params: Annotated[PageParams, Depends()],
    q: Annotated[str | None, Query(description="Search by name")] = None,
    active_only: bool = True,
) -> Page[ProductRead]:
    items, total = await service.search(
        query=q, active_only=active_only, offset=params.offset, limit=params.size
    )
    return Page.create([ProductRead.model_validate(p) for p in items], total, params)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, service: ProductServiceDep) -> ProductRead:
    return ProductRead.model_validate(await service.get(product_id))


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def create_product(
    data: ProductCreate, service: ProductServiceDep
) -> ProductRead:
    return ProductRead.model_validate(await service.create(data))


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(require_staff)],
)
async def update_product(
    product_id: int, data: ProductUpdate, service: ProductServiceDep
) -> ProductRead:
    return ProductRead.model_validate(await service.update(product_id, data))
