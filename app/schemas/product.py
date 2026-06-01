"""Product schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import ORMModel


class ProductBase(ORMModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    stock: int = Field(ge=0)


class ProductCreate(ProductBase):
    sku: str = Field(min_length=1, max_length=64)


class ProductUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductRead(ProductBase):
    id: int
    sku: str
    is_active: bool
    created_at: datetime
