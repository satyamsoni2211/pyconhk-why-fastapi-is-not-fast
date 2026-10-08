"""Mock payment gateway for the Orders API demos.

A tiny, dependency-free stand-in for the external payment gateway the Orders
API talks to. It exposes the httpbin-compatible subset the demos use, so it
can replace the go-httpbin container when Docker isn't available:

    uv run uvicorn mock_gateway.main:app --port 8080

- `GET /delay/{seconds}`  responds after sleeping (AP1 — slow gateway call)
- `GET /get`              instant echo (AP2 — cheap call, per-request client cost)
- `GET /status/{code}`    responds with the given HTTP status
- `POST /charge`          fake payment authorisation (~0.2s)

The gateway itself uses `asyncio.sleep`, so it never blocks its own event
loop: concurrent callers each wait ~`seconds`, which is what makes the
blocking-vs-async difference in the Orders API visible.
"""

import asyncio
import uuid

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

MAX_DELAY_SECONDS = 10.0

app = FastAPI(title="Mock payment gateway")


class ChargeRequest(BaseModel):
    amount: float
    currency: str = "USD"
    order_id: str | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/delay/{seconds}")
async def delay(seconds: float, request: Request) -> dict:
    await asyncio.sleep(max(0.0, min(seconds, MAX_DELAY_SECONDS)))
    return {"delay": seconds, "url": str(request.url)}


@app.get("/get")
async def get(request: Request) -> dict:
    return {
        "args": dict(request.query_params),
        "headers": dict(request.headers),
        "url": str(request.url),
    }


@app.get("/status/{code}")
async def status(code: int) -> Response:
    return Response(status_code=code)


@app.post("/charge")
async def charge(payload: ChargeRequest) -> dict:
    await asyncio.sleep(0.2)
    return {
        "payment_id": str(uuid.uuid4()),
        "status": "authorized",
        "amount": payload.amount,
        "currency": payload.currency,
        "order_id": payload.order_id,
    }
