# AP5 — Connection pool starvation: captured evidence

`GET /demo/ap5/query` holds its connection for ~300ms (`pg_sleep(0.3)`) to
simulate a realistic report-style query. Identical locust load
(`-u 100 -r 100 -t 20s`, near-instant ramp to 100 users) run twice against
the same endpoint, only the pool config differed — via a full app restart
with `POOL_MODE=bad` then `POOL_MODE=good` (pool size/overflow/timeout are
fixed at engine-creation time, so this can't be an in-process toggle).

## bad — `pool_size=5, max_overflow=10, pool_timeout=2`

```
Requests: 905   Failures: 19 (2.10%)   Median: 2200ms   Throughput: 47.8 req/s
```

Real app log traceback for every one of those failures:

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 2.00
```

Full traceback: [`pool-timeout-traceback.log`](pool-timeout-traceback.log)
Full CSV: [`locust-bad_stats.csv`](locust-bad_stats.csv) / [`locust-bad_failures.csv`](locust-bad_failures.csv)

## good — `pool_size=20, max_overflow=40, pool_timeout=10`

```
Requests: 3370   Failures: 0 (0.00%)   Median: 530ms   Throughput: 179.3 req/s
```

Full CSV: [`locust-good_stats.csv`](locust-good_stats.csv)

## Summary

| | pool config | requests served | failures | median latency | throughput |
|---|---|---|---|---|---|
| bad | 5 / +10 / 2s timeout | 905 | 19 (2.1%) | 2200ms | 47.8 req/s |
| good | 20 / +40 / 10s timeout | 3370 | 0 | 530ms | 179.3 req/s |

Same code, same query, same load — **~3.7x throughput and zero failures**
just from sizing the pool for real concurrency instead of leaving the
tutorial defaults in place.

Reproduce:
```bash
POOL_MODE=bad docker compose up -d app
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv benchmarks/ap5-pool/locust-bad -f scripts/locustfile.py

POOL_MODE=good docker compose up -d app
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv benchmarks/ap5-pool/locust-good -f scripts/locustfile.py
```

## The fix

`app/config.py`'s `_POOL_PROFILES["good"]` — larger `pool_size`/`max_overflow`
sized for actual expected concurrency, a realistic `pool_timeout`, and
`pool_recycle` set so idle connections don't go stale.
