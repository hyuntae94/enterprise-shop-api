"""Declarative base and shared mixins for all ORM models.

``Base`` derives the table name from the class name automatically and provides
common columns via mixins. Importing every model module here means Alembic's
autogenerate sees the full metadata.
"""

from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # CamelCase -> snake_case, pluralized naively (User -> users).
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name if name.endswith("s") else f"{name}s"


class TimestampMixin:
    """Adds server-managed created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


# Import models so they register on Base.metadata (used by Alembic).
from app.models import order, payment, product, user  # noqa: E402,F401
