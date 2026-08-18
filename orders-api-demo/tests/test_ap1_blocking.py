import asyncio
import time

N_CONCURRENT = 3


async def test_bad_endpoint_serializes_concurrent_requests(client):
    start = time.perf_counter()
    results = await asyncio.gather(*[client.get("/demo/ap1/bad") for _ in range(N_CONCURRENT)])
    elapsed = time.perf_counter() - start

    assert all(r.status_code == 200 for r in results)
    # Each call blocks the event loop for ~1s (go-httpbin /delay/1), so N
    # concurrent calls take roughly N seconds wall-clock, not ~1s.
    assert elapsed >= N_CONCURRENT * 0.9, (
        f"expected serialized blocking (~{N_CONCURRENT}s), got {elapsed:.2f}s"
    )


async def test_good_endpoint_runs_concurrently(client):
    start = time.perf_counter()
    results = await asyncio.gather(*[client.get("/demo/ap1/good") for _ in range(N_CONCURRENT)])
    elapsed = time.perf_counter() - start

    assert all(r.status_code == 200 for r in results)
    # httpx.AsyncClient yields the event loop while waiting, so N concurrent
    # calls should take roughly one delay period, not N of them.
    assert elapsed < N_CONCURRENT * 0.9, (
        f"expected concurrent execution (~1s), got {elapsed:.2f}s"
    )
