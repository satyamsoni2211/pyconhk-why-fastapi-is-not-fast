"""Anti-pattern 2: dependency injection lifecycle misuse.

The "bad" dependency builds a brand-new SQLAlchemy engine (fresh connection
pool, fresh TCP handshake + auth to Postgres) and a brand-new httpx client on
*every request*, then tears them down. The "good" dependency reuses the
lifespan-scoped singletons created once in `app.main.lifespan`.
"""

import time
from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import get_http_client
from app.config import get_settings
from app.db import build_engine, build_sessionmaker, get_session

router = APIRouter(prefix="/demo/ap2", tags=["demo-ap2-dependency-injection"])


async def get_bad_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Anti-pattern: a new engine (and new pooled connection) per request."""
    engine = build_engine(get_settings())
    sessionmaker = build_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session
    await engine.dispose()


async def get_bad_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Anti-pattern: a new httpx client (new connection pool) per request."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client


@router.get("/bad")
async def bad_dependency_lifecycle(
    session: Annotated[AsyncSession, Depends(get_bad_db_session)],
    client: Annotated[httpx.AsyncClient, Depends(get_bad_http_client)],
) -> dict[str, str | float]:
    start = time.perf_counter()
    settings = get_settings()
    await session.execute(text("SELECT 1"))
    await client.get(f"{settings.payment_gateway_url}/get")
    elapsed = time.perf_counter() - start
    return {"mode": "bad-new-engine-and-client-per-request", "elapsed_seconds": elapsed}


@router.get("/good")
async def good_dependency_lifecycle(
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> dict[str, str | float]:
    start = time.perf_counter()
    settings = get_settings()
    await session.execute(text("SELECT 1"))
    await client.get(f"{settings.payment_gateway_url}/get")
    elapsed = time.perf_counter() - start
    return {"mode": "good-shared-singletons", "elapsed_seconds": elapsed}
