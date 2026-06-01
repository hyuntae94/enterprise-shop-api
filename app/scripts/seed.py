"""Seed demo data: an admin user and a handful of products.

Idempotent — safe to run repeatedly.

    python -m app.scripts.seed
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from app.core.security import hash_password
from app.db.session import SessionFactory
from app.models.product import Product
from app.models.user import User, UserRole
from app.repositories.product import ProductRepository
from app.repositories.user import UserRepository

DEMO_PRODUCTS = [
    ("SKU-TEE-001", "Cotton T-Shirt", Decimal("19.90"), 100),
    ("SKU-MUG-001", "Ceramic Mug", Decimal("12.50"), 200),
    ("SKU-CAP-001", "Baseball Cap", Decimal("24.00"), 50),
]


async def seed() -> None:
    async with SessionFactory() as session:
        users = UserRepository(session)
        products = ProductRepository(session)

        if not await users.get_by_email("admin@example.com"):
            session.add(
                User(
                    email="admin@example.com",
                    hashed_password=hash_password("admin12345"),
                    full_name="Demo Admin",
                    role=UserRole.ADMIN,
                    is_verified=True,
                )
            )

        for sku, name, price, stock in DEMO_PRODUCTS:
            if not await products.get_by(sku=sku):
                session.add(Product(sku=sku, name=name, price=price, stock=stock))

        await session.commit()
    print("Seed complete. Admin: admin@example.com / admin12345")


if __name__ == "__main__":
    asyncio.run(seed())
