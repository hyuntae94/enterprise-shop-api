"""Product service — catalog CRUD with caching."""

from __future__ import annotations

import json

from app.core.exceptions import ConflictError, NotFoundError
from app.db.redis import get_redis
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate

_CACHE_TTL = 60  # seconds


class ProductService:
    def __init__(self, products: ProductRepository) -> None:
        self.products = products

    async def get(self, product_id: int) -> Product:
        product = await self.products.get(product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return product

    async def create(self, data: ProductCreate) -> Product:
        if await self.products.get_by(sku=data.sku):
            raise ConflictError(f"SKU {data.sku} already exists")
        product = Product(**data.model_dump())
        await self.products.add(product)
        await self._invalidate_list_cache()
        return product

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.get(product_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        await self.products.session.flush()
        await self._invalidate_list_cache()
        return product

    async def search(
        self, *, query: str | None, active_only: bool, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        # Read-through cache for the first page of the unfiltered catalog —
        # the hottest, most cacheable query.
        cacheable = query is None and offset == 0
        cache_key = f"products:list:{active_only}:{limit}"
        if cacheable:
            cached = await self._cache_get(cache_key)
            if cached is not None:
                return cached
        result = await self.products.search(
            query=query, active_only=active_only, offset=offset, limit=limit
        )
        if cacheable:
            await self._cache_set(cache_key, result)
        return result

    # --- cache helpers ----------------------------------------------------
    async def _cache_get(self, key: str) -> tuple[list[Product], int] | None:
        try:
            raw = await get_redis().get(key)
        except Exception:  # noqa: BLE001
            return None
        if not raw:
            return None
        payload = json.loads(raw)
        ids = payload["ids"]
        # Re-hydrate ORM objects by id to keep them session-attached.
        items = [p for pid in ids if (p := await self.products.get(pid))]
        return items, payload["total"]

    async def _cache_set(self, key: str, result: tuple[list[Product], int]) -> None:
        items, total = result
        try:
            await get_redis().set(
                key,
                json.dumps({"ids": [p.id for p in items], "total": total}),
                ex=_CACHE_TTL,
            )
        except Exception:  # noqa: BLE001
            pass

    async def _invalidate_list_cache(self) -> None:
        try:
            redis = get_redis()
            async for key in redis.scan_iter("products:list:*"):
                await redis.delete(key)
        except Exception:  # noqa: BLE001
            pass
