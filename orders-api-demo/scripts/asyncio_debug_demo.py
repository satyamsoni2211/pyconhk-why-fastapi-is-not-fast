"""Show asyncio's own debug-mode warning when a coroutine blocks the loop.

Run directly against the live payment-gateway service (no app process needed):

    PYTHONASYNCIODEBUG=1 uv run python scripts/asyncio_debug_demo.py

asyncio's debug mode logs a "Executing ... took X.XXX seconds" warning for
any callback that runs longer than `slow_callback_duration` (default 0.1s)
without yielding — exactly what a synchronous `requests.get()` inside
`async def` does.
"""

import asyncio
import logging
import os

import httpx
import requests

logging.basicConfig(level=logging.WARNING)

PAYMENT_GATEWAY_URL = os.environ.get("PAYMENT_GATEWAY_URL", "http://localhost:8080")


async def bad_blocking_call() -> None:
    requests.get(f"{PAYMENT_GATEWAY_URL}/delay/1", timeout=10)


async def good_async_call() -> None:
    async with httpx.AsyncClient() as client:
        await client.get(f"{PAYMENT_GATEWAY_URL}/delay/1")


async def main() -> None:
    loop = asyncio.get_running_loop()
    loop.slow_callback_duration = 0.1  # log anything slower than 100ms

    print("--- BAD: requests.get() inside async def ---")
    await bad_blocking_call()

    print("--- GOOD: httpx.AsyncClient ---")
    await good_async_call()
    print("(no slow-callback warning expected above for the GOOD call)")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
