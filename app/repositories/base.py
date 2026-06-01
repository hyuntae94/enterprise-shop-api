"""Generic async repository.

Encapsulates the SQLAlchemy session so services express intent
(``repo.get(id)``) rather than query mechanics. Repositories *do not* commit;
the unit of work (request-scoped session) owns the transaction.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: Any) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def get_by(self, **filters: Any) -> ModelT | None:
        stmt = select(self.model).filter_by(**filters).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(
        self, *, offset: int = 0, limit: int = 20, **filters: Any
    ) -> list[ModelT]:
        stmt = select(self.model).filter_by(**filters).offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        return (await self.session.execute(stmt)).scalar_one()

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()  # populate PK / defaults without committing
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
