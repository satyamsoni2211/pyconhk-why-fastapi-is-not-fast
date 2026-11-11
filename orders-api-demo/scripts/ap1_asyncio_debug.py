"""AP1: show asyncio's own debug-mode warning when a coroutine blocks the loop.

Needs only the payment-gateway service (no app process):

    uv run scripts/ap1_asyncio_debug.py

asyncio's debug mode logs "Executing <Task ...> took X.XXX seconds" for any
step that runs longer than `slow_callback_duration` without yielding. That is
exactly what a synchronous `requests.get()` inside `async def` does.

Each call runs as its own named task, so the warning prints right under the
BAD header and names `bad_blocking_call`, not `main()`.
"""

import asyncio
import logging
import time

import _common  # noqa: F401  (sets up sys.path and cwd)
import httpx
import requests

logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(name)s: %(message)s")

PAYMENT_GATEWAY_URL = _common.payment_gateway_url()
DELAY_URL = f"{PAYMENT_GATEWAY_URL}/delay/1"


async def bad_blocking_call() -> None:
    requests.get(DELAY_URL, timeout=10)


async def good_async_call(client: httpx.AsyncClient) -> None:
    await client.get(DELAY_URL)


async def run(name: str, coro) -> None:
    start = time.perf_counter()
    # A separate task means asyncio reports the slow step against this
    # task, and logs it before main() moves on to the next section.
    await asyncio.create_task(coro, name=name)
    print(f"    finished in {time.perf_counter() - start:.2f}s", flush=True)


async def main() -> None:
    loop = asyncio.get_running_loop()
    loop.slow_callback_duration = 0.1  # log anything that blocks for >100ms

    print("--- BAD: requests.get() inside async def ---", flush=True)
    await run("bad_blocking_call", bad_blocking_call())
    print("    ^ asyncio flagged the blocking call above\n", flush=True)

    # Build the client up front: creating its SSL context is itself a bit
    # of blocking work that would muddy the GOOD result.
    async with httpx.AsyncClient(timeout=10) as client:
        print("--- GOOD: httpx.AsyncClient ---", flush=True)
        await run("good_async_call", good_async_call(client))
        print("    ^ no slow-callback warning: the loop stayed free", flush=True)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
