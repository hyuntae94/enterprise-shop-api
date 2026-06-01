"""Pytest fixtures: an isolated in-memory SQLite DB and an async test client.

Each test runs against a fresh schema with the ``get_db`` dependency overridden
to the test session, so tests never touch Postgres or Redis.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.user import User, UserRole

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session() -> AsyncIterator:
    engine = create_async_engine(TEST_DB_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def app(db_session):  # type: ignore[no-untyped-def]
    application = create_app()

    async def _override_get_db():
        # Reuse the test session; don't commit/dispose (fixture owns it).
        yield db_session

    application.dependency_overrides[get_db] = _override_get_db
    return application


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:  # type: ignore[no-untyped-def]
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
async def admin_user(db_session) -> User:  # type: ignore[no-untyped-def]
    from app.core.security import hash_password

    user = User(
        email="admin@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def as_admin(app, admin_user):  # type: ignore[no-untyped-def]
    """Override auth so requests are made as the admin user."""

    async def _override():
        return admin_user

    app.dependency_overrides[get_current_user] = _override
    return admin_user
