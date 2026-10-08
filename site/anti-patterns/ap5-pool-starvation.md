---
title: "AP5 — Connection pool starvation"
description: Tutorial pool defaults become a hard ceiling under real concurrency. Requests time out waiting for a connection while the database sits idle. Pool configs, captured locust results, and how to detect it.
---

# AP5 — Connection pool starvation

<Callout type="tip" title="In one sentence">
A pool sized with tutorial defaults is a hard ceiling on concurrent database work; once concurrency exceeds it, requests time out waiting for a connection while the database is idle.
</Callout>

## What goes wrong

Every SQLAlchemy engine has a connection pool. `pool_size` and `max_overflow` set how many connections it can open, and `pool_timeout` sets how long a request waits for one. Creating a connection to Postgres is a real TCP and authentication handshake, so the pool is a deliberate limit.

The trouble starts when requests hold connections longer than the pool can supply. Then requests queue. The pool does not fail gracefully. Once the wait exceeds `pool_timeout`, the request fails with a `TimeoutError`, even though the database has spare capacity. Failures are timeouts waiting for a connection, not database errors.

The bug is invisible at low traffic. One request works fine. It only appears when concurrency exceeds the pool's capacity, so it reaches production.

The demo cannot toggle pool sizes per request, because the pool is built when the process starts. So AP5 is shown with a **restart** between two runs of the same load test, not a bad and good endpoint pair.

<Timeline
  :total="1.2"
  unit=" s"
  caption="Schematic with the SQLite hold time of 0.6 s. Shows the queueing shape only; the measured runs are below."
  :rows="[
    { label: 'connections 1–15 · held', start: 0, end: 0.6, tone: 'info' },
    { label: 'request 16 · waiting', start: 0, end: 0.6, tone: 'warn' },
    { label: 'request 16 · querying', start: 0.6, end: 1.2, tone: 'good' },
  ]"
/>

## The bad code

Both profiles are in `orders-api-demo/app/config.py`. `POOL_MODE` selects one at process start.

::: code-group

```python [app/config.py] {3-6}
_POOL_PROFILES = {
    "bad": {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 2,
        "pool_recycle": -1,
    },
    "good": {
        "pool_size": 20,
        "max_overflow": 40,
        "pool_timeout": 10,
        "pool_recycle": 1800,
    },
}
```

:::

The engine applies those settings in `build_engine`, from `orders-api-demo/app/db.py`:

::: code-group

```python [app/db.py] {5-8}
def build_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        pool_recycle=settings.pool_recycle,
    )
```

:::

## The good code

The `good` profile is not a different endpoint. It is the same code and the same query with a larger pool. The request handler holds its connection for the whole request, so the slow query shows the pressure. From `orders-api-demo/app/routers/demo_ap5.py`:

::: code-group

```python [app/routers/demo_ap5.py] {6,12}
@router.get("/query")
async def slow_query(session: SessionDep):
    # SELECT 1 checks a connection out of the pool; it stays checked out for
    # the rest of the request, so the sleep below holds it for ~300ms.
    if session.bind.dialect.name == "postgresql":
        await session.execute(text("SELECT pg_sleep(0.3)"))
    else:
        # SQLite has no pg_sleep: hold the pooled connection explicitly. Held
        # longer than the Postgres query so the bad pool (15 conns, 2s timeout)
        # reliably starves: 100 users / (15 / 0.6s) ≈ 4s queue wait > 2s timeout.
        await session.execute(text("SELECT 1"))
        await asyncio.sleep(0.6)
```

:::

The fix is to size the pool for real concurrency, choose `pool_timeout` on purpose, and set `pool_recycle` so idle connections do not go stale. The talk's version is `pool_size=20, max_overflow=40, pool_timeout=10, pool_recycle=1800`.

## Try it

Restart the app between the two runs. The pool is fixed at process start. Use a scratch prefix for `--csv` so you do not overwrite the committed captures in `benchmarks/ap5-pool/`.

::: code-group

```bash [bad profile]
POOL_MODE=bad uv run uvicorn app.main:app --port 8000
# in a second terminal:
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"bad"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv my-run-bad -f scripts/locustfile.py
```

```bash [good profile]
# stop the bad app (Ctrl-C), then:
POOL_MODE=good uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"good"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv my-run-good -f scripts/locustfile.py
```

```bash [interactive]
uv run locust -f scripts/locustfile.py --host http://localhost:8000
# then open http://localhost:8089 for live charts
```

:::

**Expected, bad profile:** non-zero failures, and a `QueuePool` timeout in the app log:

```text
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 2.00
```

**Expected, good profile:** zero failures and a much lower median.

The DEMO_GUIDE gives these expected values for SQLite, not captured runs: the bad profile fails about 40 to 45 percent of requests at about 43 req/s, and the good profile has 0 percent failures at about 97 req/s.

::: danger Reset the pool after rehearsal
A rehearsal can leave `POOL_MODE=bad` active. Before the talk, run `POOL_MODE=good docker compose up -d app` and confirm `/demo/ap5/info`.
:::

## Pool profiles

| `POOL_MODE` | `pool_size` | `max_overflow` | Total connections | `pool_timeout` | `pool_recycle` |
|---|---|---|---|---|---|
| `bad` | 5 | 10 | 15 | 2 s | -1 |
| `good` | 20 | 40 | 60 | 10 s | 1800 s |

## Measured evidence

Captured with `locust -u 100 -r 100 -t 20s` against the Postgres setup. The pool config was the only variable. Both runs are committed in `benchmarks/ap5-pool/`.

<StatGrid>
<StatCard value="2.1%" label="bad, failures" sub="19 of 905 requests" tone="bad" />
<StatCard value="0%" label="good, failures" sub="0 of 3370 requests" tone="good" />
<StatCard value="47.8 req/s" label="bad, throughput" sub="median 2200 ms" tone="bad" />
<StatCard value="179.3 req/s" label="good, throughput" sub="median 530 ms" tone="good" />
</StatGrid>

<BarCompare :bad="47.8" :good="179.3" unit=" req/s" :lowerIsBetter="false" caption="throughput; 179.3 ÷ 47.8 = 3.75×" />

Captured summary (`benchmarks/ap5-pool/README.md`):

| | pool config | requests served | failures | median latency | throughput |
|---|---|---|---|---|---|
| bad | 5 / +10 / 2 s timeout | 905 | 19 (2.1%) | 2200 ms | 47.8 req/s |
| good | 20 / +40 / 10 s timeout | 3370 | 0 | 530 ms | 179.3 req/s |

The 19 failures are all the same error in `benchmarks/ap5-pool/locust-bad_failures.csv`: a `500 Server Error` on `/demo/ap5/query`. The app log for each one is the pool timeout:

```text
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 2.00
```

::: info Working-tree CSVs differ from the committed captures
At the time this site was written, the locust CSVs in the working tree had been overwritten by a later local run. Their numbers differ from the committed Postgres capture above. This page quotes only the committed files. See [Benchmarks](/reference/benchmarks).
:::

## How to detect it in your own service

| Signal | Where | Meaning |
|---|---|---|
| `QueuePool limit ... reached` | Application logs | Requests are waiting for a connection, then timing out |
| `sqlalchemy.exc.TimeoutError` | Error tracking | The same, seen from the request side |
| A DB that is idle while requests fail | Database metrics | The bottleneck is the pool, not the database |
| The config values | `pool_size`, `max_overflow`, `pool_timeout` in code | Compare them with the concurrency you expect |

Rough sizing rule: the concurrent requests that hold a connection should not exceed `pool_size + max_overflow`. The DEMO_GUIDE and the code comment both work through the queue arithmetic. Also remember that each uvicorn or gunicorn worker gets its own pool. Multiply the pool by the worker count when you count Postgres connections.

## Checklist

<Checklist>
<ChecklistItem id="ap5-size">`pool_size` and `max_overflow` are sized for your expected concurrency, not the driver's tutorial defaults of `pool_size=5, max_overflow=10`.</ChecklistItem>
<ChecklistItem id="ap5-timeout">`pool_timeout` is a deliberate choice. You know what "the pool is exhausted" looks like for your users.</ChecklistItem>
<ChecklistItem id="ap5-verify">Verify with a locust run at realistic concurrency. Watch for `sqlalchemy.exc.TimeoutError: QueuePool limit ... reached`.</ChecklistItem>
</Checklist>

## Talking points

- The bug hides at low traffic. It appears only when concurrency exceeds pool capacity.
- Failures are timeouts waiting for a connection, not database errors. The database is idle while requests die.
- Size the pool from real concurrency times hold time, and make `pool_timeout` a deliberate choice.
- AP5 is the only pattern that needs a restart. Set expectations: "I can't toggle this live in one process, so I ran the same load twice and am showing you the real output."
- The live variant is a stretch goal. The captured slide is the safe default. See [Running the demos](/demo/running-the-demos#ap5-pool-starvation).

## Related

- [Setup: POOL_MODE gotcha](/guide/setup#gotchas)
- [FAQ: why not add more workers](/reference/faq)
- [Benchmarks](/reference/benchmarks)
- [Anti-pattern overview](/anti-patterns/)
