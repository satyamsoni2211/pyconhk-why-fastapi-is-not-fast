import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    sku: str
    quantity: int
    unit_price: float


class OrderCreate(BaseModel):
    customer_id: uuid.UUID
    items: list[OrderItemCreate]


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    quantity: int
    unit_price: float


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    status: str
    created_at: datetime.datetime


class OrderDetailRead(OrderRead):
    items: list[OrderItemRead]
