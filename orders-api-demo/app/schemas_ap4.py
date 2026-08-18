"""Anti-pattern 4: Pydantic validation overhead.

`bad_transform` mimics what shows up in real middleware/serializer layers:
manual dict construction from an ORM object, deep nested `field_validator`
chains, then a `model_dump()` -> `model_validate()` round-trip that re-runs
every validator a second time for no reason.

`good_transform` validates directly from the ORM object once
(`from_attributes=True`, no manual dict, no round-trip). `internal_summary`
shows the further step of skipping Pydantic entirely for data that never
leaves the process boundary.
"""

import re
import uuid
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

SKU_RE = re.compile(r"^SKU-\d{4}[A-Za-z]{2}$")
ALLOWED_STATUSES = {"pending", "paid", "shipped", "delivered"}


# ---- BAD: deeply nested, chained validators, manual dict construction ----


class BadOrderItem(BaseModel):
    id: str
    sku: str
    quantity: int
    unit_price: float

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        if not SKU_RE.fullmatch(v):
            raise ValueError(f"invalid sku format: {v}")
        return v.upper()

    @field_validator("unit_price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        # Simulates a common "just to be safe" validator: round-trip through
        # string formatting to normalize precision.
        return float(f"{v:.2f}")


class BadOrder(BaseModel):
    id: str
    customer_id: str
    status: str
    items: list[BadOrderItem]

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"invalid status: {v}")
        return v


def bad_transform(order) -> dict:
    raw = {
        "id": str(order.id),
        "customer_id": str(order.customer_id),
        "status": order.status,
        "items": [
            {
                "id": str(item.id),
                "sku": item.sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in order.items
        ],
    }
    validated = BadOrder.model_validate(raw)
    dumped = validated.model_dump()  # round-trip #1
    revalidated = BadOrder.model_validate(dumped)  # round-trip #2 — redundant
    return revalidated.model_dump()


# ---- GOOD: from_attributes, single pass, no manual dict ----


class GoodOrderItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    quantity: int
    unit_price: float


class GoodOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    status: str
    items: list[GoodOrderItem]


def good_transform(order) -> dict:
    validated = GoodOrder.model_validate(order)
    return validated.model_dump(mode="json")


class InternalOrderSummary(TypedDict):
    order_id: str
    item_count: int
    total: float


def internal_summary(order) -> InternalOrderSummary:
    """Internal-only data never crossing a process boundary: skip Pydantic."""
    return InternalOrderSummary(
        order_id=str(order.id),
        item_count=len(order.items),
        total=sum(item.quantity * float(item.unit_price) for item in order.items),
    )
