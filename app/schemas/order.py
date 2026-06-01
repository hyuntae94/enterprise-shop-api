"""Order schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.order import OrderStatus
from app.schemas.common import ORMModel


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=1000)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(ORMModel):
    product_id: int
    unit_price: Decimal
    quantity: int


class OrderRead(ORMModel):
    id: int
    user_id: int
    status: OrderStatus
    currency: str
    total_amount: Decimal
    items: list[OrderItemRead]
    created_at: datetime
