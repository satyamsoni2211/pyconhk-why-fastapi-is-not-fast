"""Show real SQL echo output + query counts for AP3 (lazy loading): N+1 vs
selectinload, on the same seeded data.

    SQLALCHEMY_WARN_20=1 uv run python scripts/sqlalchemy_echo_demo.py

Mirrors exactly what `/demo/ap3/bad-n1` and `/demo/ap3/good` do, but runs
directly against the DB (own engine, echo=True) so every SQL statement is
printed and counted without HTTP/log noise in between.
"""

import asyncio
import os

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import selectinload

from app.db import build_sessionmaker
from app.models import Order

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/orders"
)
LIMIT = 5


async def run_bad_n1(engine) -> int:
    count = {"n": 0}
    event.listen(engine.sync_engine, "before_cursor_execute", lambda *a: count.__setitem__("n", count["n"] + 1))

    sessionmaker = build_sessionmaker(engine)
    async with sessionmaker() as session:
        result = await session.execute(select(Order).limit(LIMIT))
        orders = result.scalars().all()
        for order in orders:
            await order.awaitable_attrs.items
    return count["n"]


async def run_good_selectinload(engine) -> int:
    count = {"n": 0}
    event.listen(engine.sync_engine, "before_cursor_execute", lambda *a: count.__setitem__("n", count["n"] + 1))

    sessionmaker = build_sessionmaker(engine)
    async with sessionmaker() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.items)).limit(LIMIT)
        )
        result.scalars().all()
    return count["n"]


async def main() -> None:
    print(f"--- BAD: awaitable_attrs.items loop over {LIMIT} orders (echo=True) ---")
    engine_bad = create_async_engine(DATABASE_URL, echo=True)
    n_bad = await run_bad_n1(engine_bad)
    await engine_bad.dispose()

    print(f"\n--- GOOD: selectinload over {LIMIT} orders (echo=True) ---")
    engine_good = create_async_engine(DATABASE_URL, echo=True)
    n_good = await run_good_selectinload(engine_good)
    await engine_good.dispose()

    print(f"\n=== SUMMARY: bad-n1 issued {n_bad} queries, good issued {n_good} queries ===")


if __name__ == "__main__":
    asyncio.run(main())
