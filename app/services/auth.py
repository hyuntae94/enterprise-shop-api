"""Authentication service — registration, login, token refresh.

Contains all auth business rules and is transport-agnostic (no FastAPI). It
raises domain exceptions that the API layer maps to HTTP responses.
"""

from __future__ import annotations

import jwt

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest, TokenPair


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def register(self, data: RegisterRequest) -> User:
        if await self.users.get_by_email(data.email):
            raise ConflictError("Email already registered")
        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        return await self.users.add(user)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        # Constant-ish work: verify even when user is missing to reduce the
        # signal from timing differences, then fail uniformly.
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user.id, role=user.role.value),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid refresh token") from exc
        if payload.get("type") != TokenType.REFRESH.value:
            raise AuthenticationError("Not a refresh token")
        user = await self.users.get(int(payload["sub"]))
        if user is None or not user.is_active:
            raise AuthenticationError("User no longer valid")
        return self.issue_tokens(user)
