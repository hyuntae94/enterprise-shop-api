"""Order repository."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order

    async def list_for_user(
        self, user_id: int, *, offset: int, limit: int
    ) -> tuple[list[Order], int]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        total = (
            await self.session.execute(
                select(func.count()).select_from(Order).where(Order.user_id == user_id)
            )
        ).scalar_one()
        return list(rows), total
