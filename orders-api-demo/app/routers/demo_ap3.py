"""Anti-pattern 3: SQLAlchemy lazy loading in an async context.

- `bad-crash`: touches `order.items` as a plain attribute — the classic sync
  lazy-load path, which needs a greenlet bridge that isn't active here, so it
  raises `MissingGreenlet`.
- `bad-n1`: uses `AsyncAttrs.awaitable_attrs.items`, which *does* work under
  `AsyncSession`, but issues one query per order (N+1) instead of crashing.
- `good`: eager-loads with `selectinload` in the original query — one extra
  query total, no per-row round trips.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Order

router = APIRouter(prefix="/demo/ap3", tags=["demo-ap3-lazy-loading"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/bad-crash")
async def lazy_attribute_access_crash(session: SessionDep, limit: int = 3):
    result = await session.execute(select(Order).limit(limit))
    orders = result.scalars().all()
    try:
        item_counts = [len(order.items) for order in orders]
    except Exception as exc:  # noqa: BLE001 - deliberately surfacing the real crash
        return JSONResponse(
            status_code=500,
            content={
                "mode": "bad-crash-sync-attribute-access",
                "error_type": type(exc).__name__,
                "error": str(exc)[:300],
            },
        )
    return {"mode": "bad-crash-sync-attribute-access", "item_counts": item_counts}


@router.get("/bad-n1")
async def lazy_load_n_plus_one(session: SessionDep, limit: int = 5):
    result = await session.execute(select(Order).limit(limit))
    orders = result.scalars().all()
    item_counts = []
    for order in orders:
        items = await order.awaitable_attrs.items  # one query PER order
        item_counts.append(len(items))
    return {"mode": "bad-n1-awaitable-attrs-loop", "item_counts": item_counts}


@router.get("/good")
async def eager_load_selectinload(session: SessionDep, limit: int = 5):
    result = await session.execute(
        select(Order).options(selectinload(Order.items)).limit(limit)
    )
    orders = result.scalars().all()
    item_counts = [len(order.items) for order in orders]
    return {"mode": "good-selectinload", "item_counts": item_counts}
