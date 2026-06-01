"""Product repository."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    model = Product

    async def search(
        self, *, query: str | None, active_only: bool, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        """Return a page of products plus the total matching count."""
        stmt = select(Product)
        count_stmt = select(func.count()).select_from(Product)
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
            count_stmt = count_stmt.where(Product.is_active.is_(True))
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(Product.name.ilike(pattern))
            count_stmt = count_stmt.where(Product.name.ilike(pattern))

        rows = (
            (await self.session.execute(stmt.order_by(Product.id).offset(offset).limit(limit)))
            .scalars()
            .all()
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        return list(rows), total

    async def get_for_update(self, product_id: int) -> Product | None:
        """Lock the row to safely decrement stock under concurrency."""
        stmt = select(Product).where(Product.id == product_id).with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()
