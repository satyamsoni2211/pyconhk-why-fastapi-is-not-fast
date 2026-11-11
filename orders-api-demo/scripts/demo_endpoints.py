"""Call the demo endpoints for one anti-pattern and print a short comparison.

A scripted version of the curl commands in DEMO_GUIDE.md. Needs the app
running on BASE_URL (default http://localhost:8000).

    uv run scripts/demo_endpoints.py ap1            # every endpoint for AP1
    uv run scripts/demo_endpoints.py ap1 bad        # one endpoint
    uv run scripts/demo_endpoints.py --list         # show all choices

Or through the Makefile: `make ap1`, `make ap1-bad`, ...
"""

import argparse
import asyncio
import statistics
import sys
import time

import _common
import httpx

BASE_URL = _common.base_url()


def ms(seconds: float) -> str:
    return f"{seconds * 1000:7.1f} ms"


# --- AP1: blocking the event loop -----------------------------------------
AP1_CONCURRENCY = 3


async def ap1(client: httpx.AsyncClient, variant: str) -> None:
    """Fire 3 requests at once, and check /health while they are in flight."""
    path = f"/demo/ap1/{variant}"

    async def one() -> int:
        return (await client.get(path)).status_code

    async def health_probe() -> float:
        await asyncio.sleep(0.1)  # let the slow requests start first
        start = time.perf_counter()
        await client.get("/health")
        return time.perf_counter() - start

    start = time.perf_counter()
    *codes, health = await asyncio.gather(*(one() for _ in range(AP1_CONCURRENCY)), health_probe())
    total = time.perf_counter() - start
    print(
        f"  GET {path:<28} {AP1_CONCURRENCY} concurrent: total {total:5.2f} s"
        f"   /health answered in {ms(health)}   status {sorted(set(codes))}"
    )


# --- AP2: DI lifecycle ------------------------------------------------------
AP2_REQUESTS = 20


async def ap2(client: httpx.AsyncClient, variant: str) -> None:
    """Sequential requests; report the server-side time each one took."""
    path = f"/demo/ap2/{variant}"
    server = []
    for _ in range(AP2_REQUESTS):
        resp = await client.get(path)
        resp.raise_for_status()
        server.append(resp.json()["elapsed_seconds"])
    print(
        f"  GET {path:<28} {AP2_REQUESTS} requests: mean {ms(statistics.mean(server))}"
        f"   p50 {ms(statistics.median(server))}   (server-side)"
    )


# --- AP3: lazy loading ------------------------------------------------------
AP3_LIMIT = 5


async def ap3(client: httpx.AsyncClient, variant: str) -> None:
    path = f"/demo/ap3/{variant}"
    start = time.perf_counter()
    resp = await client.get(path, params={"limit": AP3_LIMIT})
    took = time.perf_counter() - start
    body = resp.json()
    detail = (
        f"error_type={body.get('error_type')}"
        if resp.status_code >= 400
        else f"item_counts={body.get('item_counts')}"
    )
    print(f"  GET {path + f'?limit={AP3_LIMIT}':<28} HTTP {resp.status_code}  {ms(took)}   {detail}")


# --- AP4: Pydantic overhead -------------------------------------------------
AP4_LIMIT = 500
AP4_REPEATS = 5


async def ap4(client: httpx.AsyncClient, variant: str) -> None:
    """Median of a few runs of the server-timed transform."""
    path = f"/demo/ap4/{variant}"
    times = []
    for _ in range(AP4_REPEATS):
        resp = await client.get(path, params={"limit": AP4_LIMIT})
        resp.raise_for_status()
        body = resp.json()
        times.append(body["elapsed_seconds"])
    print(
        f"  GET {path + f'?limit={AP4_LIMIT}':<28} {body['n']} orders: transform median "
        f"{ms(statistics.median(times))} over {AP4_REPEATS} runs"
    )


# --- AP5: pool starvation ---------------------------------------------------
AP5_BURST = 200


async def ap5(client: httpx.AsyncClient, variant: str) -> None:
    if variant == "info":
        info = (await client.get("/demo/ap5/info")).json()
        print(
            f"  GET {'/demo/ap5/info':<28} pool_mode={info['pool_mode']} "
            f"pool_size={info['pool_size']} max_overflow={info['max_overflow']} "
            f"pool_timeout={info['pool_timeout']}s"
        )
        return

    async def one() -> tuple[int, float]:
        start = time.perf_counter()
        try:
            code = (await client.get("/demo/ap5/query")).status_code
        except httpx.HTTPError:
            code = 0
        return code, time.perf_counter() - start

    start = time.perf_counter()
    results = await asyncio.gather(*(one() for _ in range(AP5_BURST)))
    total = time.perf_counter() - start
    failed = sum(1 for code, _ in results if code != 200)
    worst = max(t for _, t in results)
    print(
        f"  GET {'/demo/ap5/query':<28} {AP5_BURST} at once: {failed} failed "
        f"({failed / AP5_BURST:.0%})   slowest {worst:4.2f} s   total {total:4.2f} s"
    )


DEMOS = {
    "ap1": (ap1, ["bad", "good", "bridge"], "Blocking the event loop"),
    "ap2": (ap2, ["bad", "good"], "DI lifecycle"),
    "ap3": (ap3, ["bad-crash", "bad-n1", "good"], "Lazy loading"),
    "ap4": (ap4, ["bad", "good"], "Pydantic overhead"),
    "ap5": (ap5, ["info", "query"], "Pool starvation (restart with POOL_MODE to compare)"),
}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("demo", nargs="?", choices=DEMOS)
    parser.add_argument("variant", nargs="?", help="one endpoint; omit to run them all")
    parser.add_argument("--list", action="store_true", help="list demos and endpoints")
    args = parser.parse_args()

    if args.list or not args.demo:
        for name, (_, variants, title) in DEMOS.items():
            print(f"{name}  {title}: {', '.join(variants)}")
        return

    fn, variants, title = DEMOS[args.demo]
    if args.variant and args.variant not in variants:
        parser.error(f"{args.demo} endpoints are: {', '.join(variants)}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        try:
            await client.get("/health")
        except httpx.ConnectError:
            sys.exit(f"App is not reachable at {BASE_URL}. Start it with `make up` or `make run`.")

        print(f"{args.demo.upper()}: {title}  ({BASE_URL})")
        for variant in [args.variant] if args.variant else variants:
            await fn(client, variant)


if __name__ == "__main__":
    asyncio.run(main())
