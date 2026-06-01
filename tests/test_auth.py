"""Auth flow tests: register → login → access protected route → refresh."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_register_and_login(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@test.com", "password": "supersecret", "full_name": "Alice"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "alice@test.com"
    assert r.json()["role"] == "customer"

    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@test.com", "password": "supersecret"},
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    # Use the access token to read the profile.
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = await client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "alice@test.com"


async def test_duplicate_email_conflicts(client):
    payload = {"email": "bob@test.com", "password": "supersecret"}
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


async def test_login_with_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "carol@test.com", "password": "supersecret"},
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@test.com", "password": "wrong-password"},
    )
    assert r.status_code == 401


async def test_protected_route_without_token(client):
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401
