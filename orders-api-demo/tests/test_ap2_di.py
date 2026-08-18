import time


async def test_bad_dependency_is_slower_than_good(client):
    N = 10

    async def timed(path: str) -> float:
        start = time.perf_counter()
        for _ in range(N):
            resp = await client.get(path)
            assert resp.status_code == 200
        return (time.perf_counter() - start) / N

    bad_avg = await timed("/demo/ap2/bad")
    good_avg = await timed("/demo/ap2/good")

    # Rebuilding an engine (fresh asyncpg pool + connection) per request must
    # cost meaningfully more than reusing the lifespan singleton — a generous
    # 1.5x threshold keeps this from flaking on a fast/quiet machine while
    # still catching the anti-pattern.
    assert bad_avg > good_avg * 1.5, (
        f"expected bad ({bad_avg * 1000:.2f}ms) to be meaningfully slower "
        f"than good ({good_avg * 1000:.2f}ms)"
    )
