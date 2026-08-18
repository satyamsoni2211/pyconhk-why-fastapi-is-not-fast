"""Measure real per-request latency overhead of rebuilding DB engine + HTTP
client on every request (AP2 'bad') vs reusing lifespan singletons ('good').

Run against the live dockerized app:

    uv run python scripts/bench_ap2_di.py
"""

import statistics
import time

import httpx

BASE_URL = "http://localhost:8000"
N_REQUESTS = 50


def bench(path: str) -> list[float]:
    latencies = []
    with httpx.Client(timeout=30) as client:
        for _ in range(N_REQUESTS):
            start = time.perf_counter()
            resp = client.get(f"{BASE_URL}{path}")
            resp.raise_for_status()
            latencies.append((time.perf_counter() - start) * 1000)
    return latencies


def report(name: str, latencies: list[float]) -> None:
    latencies_sorted = sorted(latencies)
    p50 = statistics.median(latencies_sorted)
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95) - 1]
    mean = statistics.mean(latencies_sorted)
    print(f"{name}: mean={mean:.2f}ms p50={p50:.2f}ms p95={p95:.2f}ms (n={len(latencies)})")


if __name__ == "__main__":
    print(f"Firing {N_REQUESTS} sequential requests at each endpoint...\n")
    bad = bench("/demo/ap2/bad")
    good = bench("/demo/ap2/good")
    report("bad  (new engine+client per request)", bad)
    report("good (shared singletons)             ", good)
    print(f"\nmean overhead: {statistics.mean(bad) - statistics.mean(good):.2f}ms per request")
