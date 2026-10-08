---
title: "AP2 — Dependency injection lifecycle misuse"
description: Building a database engine and HTTP client inside a dependency means every request pays for a new connection pool. Bad and good code, measured evidence, and how to detect it.
---

# AP2 — Dependency injection lifecycle misuse

<Callout type="tip" title="In one sentence">
Expensive objects such as the database engine and the HTTP client should be built once in the app lifespan, not inside a dependency that runs on every request.
</Callout>

## What goes wrong

`Depends()` runs its function on each request. Nothing stops you from putting `create_async_engine(...)` or `httpx.AsyncClient(...)` in that function. Each request then builds a new connection pool, opens new connections, and throws the pool away at the end.

For Postgres, the expensive part is the TCP connection and authentication handshake. The benchmark README attributes almost all of the measured overhead to that handshake. Under real concurrency the same churn also strains the database's connection limit.



## The bad code

The `bad` endpoint takes two dependencies. Each one builds its own resource on every request. This excerpt is from `orders-api-demo/app/routers/demo_ap2.py`.

::: code-group

```python [app/routers/demo_ap2.py] {3,12}
async def get_bad_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Anti-pattern: a new engine (and new pooled connection) per request."""
    engine = build_engine(get_settings())
    sessionmaker = build_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session
    await engine.dispose()


async def get_bad_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Anti-pattern: a new httpx client (new connection pool) per request."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client
```

:::

## The good code

The `good` endpoint reuses the objects created in the lifespan (`app/main.py`). The sessionmaker and the HTTP client both live on `app.state`.

::: code-group

```python [app/routers/demo_ap2.py] {3-4}
@router.get("/good")
async def good_dependency_lifecycle(
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> dict[str, str | float]:
```

```python [app/db.py] {3-4}
async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """The correct, lifespan-scoped way to hand out a DB session (Task 3/AP2 'good')."""
    async with request.app.state.sessionmaker() as session:
        yield session
```

```python [app/clients.py] {3}
async def get_http_client(request: Request) -> httpx.AsyncClient:
    """The correct way: hand out the lifespan-scoped singleton (AP2 'good')."""
    return request.app.state.http_client
```

:::

The fix is the pattern from the talk: create once in the lifespan, store on `app.state`, and hand out through `Annotated[T, Depends(...)]`.

## Try it

::: code-group

```bash [single requests]
curl localhost:8000/demo/ap2/bad     # {"mode":"bad-new-engine-and-client-per-request","elapsed_seconds":...}
curl localhost:8000/demo/ap2/good
```

```bash [benchmark, 50 each]
BASE_URL=http://localhost:8000 uv run python scripts/bench_ap2_di.py
```

:::

**Expected, Postgres capture** (`benchmarks/ap2-di/latency-report.txt`): `bad` mean about **17.48 ms**, `good` mean about **1.73 ms**.

**Expected, SQLite local** (DEMO_GUIDE, not a committed capture): `bad` about 5 to 6 ms, `good` about 1.3 ms, roughly 4×. SQLite understates the gap because a new SQLite engine has no network handshake. Say this out loud when you present with SQLite.

## Measured evidence

<StatGrid>
<StatCard value="17.48 ms" label="bad, mean" sub="new engine and client per request" tone="bad" />
<StatCard value="1.73 ms" label="good, mean" sub="lifespan singletons" tone="good" />
<StatCard value="~10×" label="ratio" sub="17.48 ÷ 1.73 = 10.1" />
<StatCard value="Postgres capture" label="environment" sub="n = 50 sequential requests each" />
</StatGrid>

<BarCompare :bad="17.48" :good="1.73" unit=" ms" caption="mean latency, 50 sequential requests each" />

Captured output (`benchmarks/ap2-di/latency-report.txt`):

```text
bad  (new engine+client per request): mean=17.48ms p50=16.82ms p95=19.52ms (n=50)
good (shared singletons)             : mean=1.73ms p50=1.59ms p95=2.56ms (n=50)

mean overhead: 15.74ms per request
```

The automated test `tests/test_ap2_di.py` asserts that `bad` stays more than 1.5× slower than `good` on every run.

## How to detect it in your own service

| Check | How | What to look for |
|---|---|---|
| Code review | Search for `create_async_engine`, `httpx.AsyncClient(`, or `build_*` calls | A constructor inside a function used with `Depends` |
| Latency benchmark | Compare an endpoint against a lifespan-singleton version, as in `scripts/bench_ap2_di.py` | A large mean gap for a trivial query |
| Connection churn | Watch connection counts on the database under load | Connections opened and closed per request |

## Checklist

<Checklist>
<ChecklistItem id="ap2-lifespan">Expensive objects (DB engines, HTTP clients, config) are created once, in the app lifespan, and handed out through `yield`-based `Depends()`.</ChecklistItem>
<ChecklistItem id="ap2-annotated">Use `Annotated[T, Depends(get_x)]` for shared singletons. Reserve `lru_cache` for pure, cheap factories.</ChecklistItem>
<ChecklistItem id="ap2-verify">Verify with a latency benchmark comparing the dependency's endpoint against a lifespan-singleton equivalent.</ChecklistItem>
</Checklist>

## Talking points

- "17.5 milliseconds average, versus 1.7. Ten times, just from rebuilding a connection pool you already had."
- The overhead is constant per request, and it also destroys connection reuse. Under load you churn sockets and can exhaust the database's `max_connections`.
- Optional live run: `scripts/bench_ap2_di.py` takes about 2 seconds. If time is short, show the captured table.

## Related

- [Architecture: how each pair is wired](/guide/architecture#how-each-pair-is-wired)
- [Benchmarks](/reference/benchmarks)
- [Checklist: dependency lifecycle](/reference/checklist)
- [Anti-pattern overview](/anti-patterns/)
