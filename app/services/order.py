"""Order service — checkout with atomic stock reservation.

Demonstrates a multi-step business transaction: validate products, lock stock
rows ``FOR UPDATE`` to prevent oversells under concurrency, snapshot prices,
decrement inventory, and persist the order — all inside the request's single
transaction so it commits or rolls back as one unit.
"""

from __future__ import annotations

from app.core.exceptions import BusinessRuleError, NotFoundError, PermissionDeniedError
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User, UserRole
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import OrderCreate


class OrderService:
    def __init__(self, orders: OrderRepository, products: ProductRepository) -> None:
        self.orders = orders
        self.products = products

    async def create_order(self, user: User, data: OrderCreate) -> Order:
        # Collapse duplicate product lines into one quantity per product.
        wanted: dict[int, int] = {}
        for line in data.items:
            wanted[line.product_id] = wanted.get(line.product_id, 0) + line.quantity

        order = Order(user_id=user.id)
        for product_id, quantity in wanted.items():
            product = await self.products.get_for_update(product_id)
            if product is None or not product.is_active:
                raise NotFoundError(f"Product {product_id} not available")
            if product.stock < quantity:
                raise BusinessRuleError(
                    f"Insufficient stock for product {product_id}",
                    details={"product_id": product_id, "available": product.stock},
                )
            product.stock -= quantity
            order.items.append(
                OrderItem(
                    product_id=product.id,
                    unit_price=product.price,
                    quantity=quantity,
                )
            )
        order.recalculate_total()
        return await self.orders.add(order)

    async def get_for_user(self, order_id: int, user: User) -> Order:
        order = await self.orders.get(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        # Customers may only see their own orders; staff/admin see all.
        if order.user_id != user.id and user.role == UserRole.CUSTOMER:
            raise PermissionDeniedError("Not allowed to view this order")
        return order

    async def cancel(self, order_id: int, user: User) -> Order:
        order = await self.get_for_user(order_id, user)
        if order.status not in (OrderStatus.PENDING, OrderStatus.PAID):
            raise BusinessRuleError(f"Cannot cancel a {order.status} order")
        # Restock the reserved inventory.
        for item in order.items:
            product = await self.products.get_for_update(item.product_id)
            if product is not None:
                product.stock += item.quantity
        order.status = OrderStatus.CANCELLED
        await self.orders.session.flush()
        return order
