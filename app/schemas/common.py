"""Shared schema building blocks."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for schemas read out of ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    """Offset pagination query parameters."""

    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    """A paginated response envelope."""

    items: list[T]
    total: int
    page: int
    size: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PageParams) -> Page[T]:
        return cls(items=items, total=total, page=params.page, size=params.size)
