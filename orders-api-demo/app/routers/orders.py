import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Order, OrderItem
from app.schemas import OrderCreate, OrderDetailRead, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=OrderDetailRead, status_code=201)
async def create_order(payload: OrderCreate, session: SessionDep) -> Order:
    order = Order(customer_id=payload.customer_id)
    order.items = [
        OrderItem(sku=item.sku, quantity=item.quantity, unit_price=item.unit_price)
        for item in payload.items
    ]
    session.add(order)
    await session.commit()
    await session.refresh(order, attribute_names=["items"])
    return order


@router.get("", response_model=list[OrderRead])
async def list_orders(session: SessionDep, limit: int = 50) -> list[Order]:
    result = await session.execute(select(Order).order_by(Order.created_at.desc()).limit(limit))
    return list(result.scalars().all())


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order(order_id: uuid.UUID, session: SessionDep) -> Order:
    result = await session.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
