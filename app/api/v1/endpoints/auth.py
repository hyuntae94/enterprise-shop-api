"""Authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_service
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

AuthDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, service: AuthDep) -> UserRead:
    user = await service.register(data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(data: LoginRequest, service: AuthDep) -> TokenPair:
    """JSON login. Returns an access/refresh token pair."""
    user = await service.authenticate(data.email, data.password)
    return service.issue_tokens(user)


@router.post("/token", response_model=TokenPair, include_in_schema=False)
async def login_oauth_form(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], service: AuthDep
) -> TokenPair:
    """OAuth2 password-flow endpoint so Swagger's *Authorize* button works."""
    user = await service.authenticate(form.username, form.password)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, service: AuthDep) -> TokenPair:
    return await service.refresh(data.refresh_token)
