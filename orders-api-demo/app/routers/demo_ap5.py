"""Anti-pattern 5: connection pool starvation.

Pool size/overflow/timeout are set once at engine-creation time from
`POOL_MODE` (see `app/config.py`) — there's no per-request toggle, so this
anti-pattern is demonstrated by restarting the app process between locust
runs rather than a bad/good endpoint pair.

`/demo/ap5/query` deliberately holds its connection for ~300ms
(`pg_sleep`, or `asyncio.sleep` on SQLite) to simulate a realistic report-style query — long enough that
a too-small pool visibly starves under concurrent load within a short
locust run.
"""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import Order

router = APIRouter(prefix="/demo/ap5", tags=["demo-ap5-pool-starvation"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/query")
async def slow_query(session: SessionDep):
    # SELECT 1 checks a connection out of the pool; it stays checked out for
    # the rest of the request, so the sleep below holds it for ~300ms.
    if session.bind.dialect.name == "postgresql":
        await session.execute(text("SELECT pg_sleep(0.3)"))
    else:
        # SQLite has no pg_sleep: hold the pooled connection explicitly. Held
        # longer than the Postgres query so the bad pool (15 conns, 2s timeout)
        # reliably starves: 100 users / (15 / 0.6s) ≈ 4s queue wait > 2s timeout.
        await session.execute(text("SELECT 1"))
        await asyncio.sleep(0.6)
    result = await session.execute(select(Order).limit(10))
    return {"n": len(result.scalars().all())}


@router.get("/info")
async def pool_info():
    settings = get_settings()
    return {
        "pool_mode": settings.pool_mode,
        "pool_size": settings.pool_size,
        "max_overflow": settings.max_overflow,
        "pool_timeout": settings.pool_timeout,
        "pool_recycle": settings.pool_recycle,
    }
