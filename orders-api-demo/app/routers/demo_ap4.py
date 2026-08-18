import time
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Order
from app.schemas_ap4 import bad_transform, good_transform

router = APIRouter(prefix="/demo/ap4", tags=["demo-ap4-pydantic-overhead"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _fetch_orders(session: AsyncSession, limit: int) -> list[Order]:
    result = await session.execute(select(Order).options(selectinload(Order.items)).limit(limit))
    return list(result.scalars().all())


@router.get("/bad")
async def bad_pydantic_overhead(session: SessionDep, limit: int = 100):
    orders = await _fetch_orders(session, limit)
    start = time.perf_counter()
    results = [bad_transform(order) for order in orders]
    elapsed = time.perf_counter() - start
    return {"mode": "bad-nested-validators-round-trip", "n": len(results), "elapsed_seconds": elapsed}


@router.get("/good")
async def good_pydantic_direct(session: SessionDep, limit: int = 100):
    orders = await _fetch_orders(session, limit)
    start = time.perf_counter()
    results = [good_transform(order) for order in orders]
    elapsed = time.perf_counter() - start
    return {"mode": "good-from-attributes-single-pass", "n": len(results), "elapsed_seconds": elapsed}
