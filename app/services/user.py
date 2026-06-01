"""User service — profile reads/updates and admin role management."""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def get(self, user_id: int) -> User:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.users.session.flush()
        return user

    async def set_role(self, user_id: int, role: UserRole) -> User:
        user = await self.get(user_id)
        user.role = role
        await self.users.session.flush()
        return user
