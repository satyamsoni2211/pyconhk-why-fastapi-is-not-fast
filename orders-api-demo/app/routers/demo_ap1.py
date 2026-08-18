"""Anti-pattern 1: blocking the event loop.

`/delay/1` on the payment-gateway service (go-httpbin) sleeps for 1 second
before responding — standing in for a slow external payment gateway call
that a real Orders API would make while creating an order.
"""

import asyncio

import httpx
import requests
from fastapi import APIRouter, Request

from app.config import get_settings

router = APIRouter(prefix="/demo/ap1", tags=["demo-ap1-blocking-event-loop"])


@router.get("/bad")
async def blocking_call(request: Request) -> dict[str, str]:
    """`async def`, but `requests.get()` blocks the whole event loop for 1s."""
    settings = get_settings()
    resp = requests.get(f"{settings.payment_gateway_url}/delay/1", timeout=10)
    return {"gateway_status": str(resp.status_code), "mode": "bad-blocking-requests"}


@router.get("/good")
async def async_call(request: Request) -> dict[str, str]:
    """Same call via the shared httpx.AsyncClient — yields the event loop while waiting."""
    client: httpx.AsyncClient = request.app.state.http_client
    settings = get_settings()
    resp = await client.get(f"{settings.payment_gateway_url}/delay/1")
    return {"gateway_status": str(resp.status_code), "mode": "good-httpx-async"}


@router.get("/bridge")
async def executor_bridge_call(request: Request) -> dict[str, str]:
    """Migration bridge: keep using `requests`, but push it off the event loop."""
    settings = get_settings()
    loop = asyncio.get_running_loop()
    resp = await loop.run_in_executor(
        None, lambda: requests.get(f"{settings.payment_gateway_url}/delay/1", timeout=10)
    )
    return {"gateway_status": str(resp.status_code), "mode": "bridge-run-in-executor"}
