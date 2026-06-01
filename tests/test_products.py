"""Product catalog tests: public reads, role-gated writes, search & paging."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def _create_product(client, **overrides):
    payload = {
        "sku": "SKU-1",
        "name": "Widget",
        "price": "9.99",
        "stock": 5,
        **overrides,
    }
    return await client.post("/api/v1/products", json=payload)


async def test_create_requires_staff(client):
    # No auth override → treated as anonymous → 401.
    r = await _create_product(client)
    assert r.status_code == 401


async def test_admin_can_create_and_list(client, as_admin):
    r = await _create_product(client, sku="SKU-ABC", name="Gadget")
    assert r.status_code == 201, r.text
    assert r.json()["sku"] == "SKU-ABC"

    r = await client.get("/api/v1/products")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Gadget"


async def test_duplicate_sku_conflicts(client, as_admin):
    assert (await _create_product(client, sku="DUP")).status_code == 201
    r = await _create_product(client, sku="DUP", name="Other")
    assert r.status_code == 409


async def test_search_by_name(client, as_admin):
    await _create_product(client, sku="A", name="Red Shoes")
    await _create_product(client, sku="B", name="Blue Hat")

    r = await client.get("/api/v1/products", params={"q": "shoes"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1 and items[0]["name"] == "Red Shoes"


async def test_get_missing_product_returns_404(client):
    r = await client.get("/api/v1/products/9999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"
