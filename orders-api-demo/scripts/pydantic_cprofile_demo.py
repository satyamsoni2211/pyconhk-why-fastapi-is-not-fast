"""cProfile bad_transform vs good_transform over real seeded orders.

    PYTHONPATH=. uv run python scripts/pydantic_cprofile_demo.py
"""

import asyncio
import cProfile
import os
import pstats
from io import StringIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import selectinload

from app.db import build_sessionmaker
from app.models import Order
from app.schemas_ap4 import bad_transform, good_transform

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/orders"
)
N_ORDERS = 200
N_REPEATS = 20  # amplify so cProfile has enough signal to be meaningful


async def fetch_orders() -> list[Order]:
    engine = create_async_engine(DATABASE_URL)
    sessionmaker = build_sessionmaker(engine)
    async with sessionmaker() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.items)).limit(N_ORDERS)
        )
        orders = list(result.scalars().all())
    await engine.dispose()
    return orders


def profile_transform(name: str, fn, orders: list[Order]) -> str:
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(N_REPEATS):
        for order in orders:
            fn(order)
    profiler.disable()

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stream.write(f"=== {name}: {N_ORDERS} orders x {N_REPEATS} repeats ===\n")
    stats.print_stats(10)
    return stream.getvalue()


async def main() -> None:
    orders = await fetch_orders()
    print(f"Loaded {len(orders)} orders with items for profiling.\n")

    bad_report = profile_transform("BAD (nested validators + round-trip)", bad_transform, orders)
    good_report = profile_transform("GOOD (from_attributes, single pass)", good_transform, orders)

    print(bad_report)
    print(good_report)

    with open("benchmarks/ap4-pydantic/cprofile-bad.txt", "w") as f:
        f.write(bad_report)
    with open("benchmarks/ap4-pydantic/cprofile-good.txt", "w") as f:
        f.write(good_report)


if __name__ == "__main__":
    asyncio.run(main())
