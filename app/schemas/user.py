"""User schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: int
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserUpdate(ORMModel):
    full_name: str | None = Field(default=None, max_length=255)


class UserRoleUpdate(ORMModel):
    """Admin-only role change."""

    role: UserRole
