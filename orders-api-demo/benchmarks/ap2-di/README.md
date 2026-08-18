# AP2 — Dependency injection lifecycle misuse: captured evidence

Endpoints: `GET /demo/ap2/bad` (new SQLAlchemy engine + new httpx client
built inside the dependency on every request), `GET /demo/ap2/good` (both
pulled from the `app.state` singletons created once in the lifespan).

## Real measured latency, 50 sequential requests each

```
bad  (new engine+client per request): mean=17.48ms p50=16.82ms p95=19.52ms (n=50)
good (shared singletons)             : mean=1.73ms  p50=1.59ms  p95=2.56ms  (n=50)

mean overhead: 15.74ms per request  (~10x)
```

Full output: [`latency-report.txt`](latency-report.txt)
Reproduce: `docker compose up -d && uv run python scripts/bench_ap2_di.py`

That ~16ms is almost entirely the fresh asyncpg connection handshake +
Postgres auth the "bad" path pays on every single request — at any real
concurrency this either serializes on connection setup or exhausts the
database's own connection limit long before your app's pool would.

## Automated regression test

[`tests/test_ap2_di.py`](../../tests/test_ap2_di.py) asserts `bad` stays
meaningfully slower than `good` (>1.5x) on every test run.

## The fix

- `yield`-based dependency (`app/db.py:get_session`) pulling `request.app.state.sessionmaker`, created once in `app/main.py`'s lifespan.
- `app/clients.py:get_http_client` returning the lifespan-scoped `httpx.AsyncClient` via `Annotated[..., Depends(...)]`.
