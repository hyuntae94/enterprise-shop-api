"""User endpoints — self-service profile + admin role management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_user_service, require_admin
from app.models.user import User
from app.schemas.user import UserRead, UserRoleUpdate, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])

UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/me", response_model=UserRead)
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate, user: CurrentUser, service: UserServiceDep
) -> UserRead:
    updated = await service.update_profile(user, data)
    return UserRead.model_validate(updated)


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(require_admin)],
)
async def set_user_role(
    user_id: int, data: UserRoleUpdate, service: UserServiceDep
) -> UserRead:
    """Admin-only: change another user's role."""
    updated = await service.set_role(user_id, data.role)
    return UserRead.model_validate(updated)


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
async def read_user(user_id: int, service: UserServiceDep) -> UserRead:
    user: User = await service.get(user_id)
    return UserRead.model_validate(user)
