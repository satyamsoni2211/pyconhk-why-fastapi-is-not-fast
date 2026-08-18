"""Seed the Orders API demo database with realistic volume.

Run inside the app container so DATABASE_URL resolves to the compose `db`
service:

    docker compose exec app uv run python scripts/seed_data.py
"""

import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from faker import Faker
from sqlalchemy import text

from app.config import get_settings
from app.db import build_engine, build_sessionmaker
from app.models import Base, Customer, Order, OrderItem

N_CUSTOMERS = 200
N_ORDERS = 2000
MAX_ITEMS_PER_ORDER = 5

fake = Faker()


async def main() -> None:
    settings = get_settings()
    engine = build_engine(settings)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = build_sessionmaker(engine)
    async with sessionmaker() as session:
        existing = await session.execute(text("SELECT count(*) FROM customer"))
        if existing.scalar_one() > 0:
            print("Data already seeded, skipping. (drop volumes to reseed)")
            await engine.dispose()
            return

        customers = [
            Customer(name=fake.name(), email=fake.unique.email()) for _ in range(N_CUSTOMERS)
        ]
        session.add_all(customers)
        await session.flush()

        for _ in range(N_ORDERS):
            order = Order(
                customer_id=random.choice(customers).id,
                status=random.choice(["pending", "paid", "shipped", "delivered"]),
            )
            session.add(order)
            await session.flush()

            for _ in range(random.randint(1, MAX_ITEMS_PER_ORDER)):
                session.add(
                    OrderItem(
                        order_id=order.id,
                        sku=fake.bothify(text="SKU-####??"),
                        quantity=random.randint(1, 4),
                        unit_price=round(random.uniform(5, 250), 2),
                    )
                )

        await session.commit()

    async with sessionmaker() as count_session:
        result = await count_session.execute(text("SELECT count(*) FROM order_item"))
        print(f"Seeded {N_CUSTOMERS} customers, {N_ORDERS} orders, {result.scalar_one()} order items")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
