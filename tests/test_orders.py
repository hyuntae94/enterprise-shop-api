"""Order checkout tests: stock reservation, oversell protection, cancel/restock."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def _seed_product(client, stock: int = 10, sku: str = "ORD-1"):
    r = await client.post(
        "/api/v1/products",
        json={"sku": sku, "name": "Orderable", "price": "5.00", "stock": stock},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_checkout_reserves_stock(client, as_admin):
    pid = await _seed_product(client, stock=10)

    r = await client.post(
        "/api/v1/orders", json={"items": [{"product_id": pid, "quantity": 3}]}
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["status"] == "pending"
    assert order["total_amount"] == "15.00"

    # Stock decremented from 10 → 7.
    r = await client.get(f"/api/v1/products/{pid}")
    assert r.json()["stock"] == 7


async def test_oversell_is_rejected(client, as_admin):
    pid = await _seed_product(client, stock=2, sku="ORD-2")
    r = await client.post(
        "/api/v1/orders", json={"items": [{"product_id": pid, "quantity": 5}]}
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "business_rule_violation"


async def test_cancel_restocks(client, as_admin):
    pid = await _seed_product(client, stock=4, sku="ORD-3")
    order = (
        await client.post(
            "/api/v1/orders", json={"items": [{"product_id": pid, "quantity": 4}]}
        )
    ).json()

    r = await client.post(f"/api/v1/orders/{order['id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    r = await client.get(f"/api/v1/products/{pid}")
    assert r.json()["stock"] == 4
