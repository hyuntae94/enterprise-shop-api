"""FastAPI dependency wiring.

This is the composition root: it turns a DB session into repositories, then
services, then resolves the authenticated user and enforces roles. Endpoints
depend only on these factories, keeping them thin.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import TokenType, decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.order import OrderService
from app.services.product import ProductService
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


# --- Service factories -----------------------------------------------------
def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(UserRepository(db))


def get_user_service(db: DbSession) -> UserService:
    return UserService(UserRepository(db))


def get_product_service(db: DbSession) -> ProductService:
    return ProductService(ProductRepository(db))


def get_order_service(db: DbSession) -> OrderService:
    return OrderService(OrderRepository(db), ProductRepository(db))


# --- Authentication --------------------------------------------------------
async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise AuthenticationError("Not authenticated")
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc
    if payload.get("type") != TokenType.ACCESS.value:
        raise AuthenticationError("Not an access token")

    user = await UserRepository(db).get(int(payload["sub"]))
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing that the current user has one of ``roles``."""

    async def _guard(user: CurrentUser) -> User:
        if user.role not in roles:
            raise PermissionDeniedError("Insufficient permissions")
        return user

    return _guard


# Convenience guards used across endpoints.
require_admin = require_roles(UserRole.ADMIN)
require_staff = require_roles(UserRole.STAFF, UserRole.ADMIN)


def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", "")
