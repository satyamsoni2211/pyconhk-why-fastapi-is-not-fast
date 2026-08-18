# FastAPI performance checklist

Five things to check before you trust a FastAPI service under real
concurrency. Each one maps to a demo in this repo with real captured
before/after numbers — see `benchmarks/<name>/README.md`.

## 1. Event loop hygiene

- [ ] No synchronous I/O (`requests`, blocking file/DB drivers, `time.sleep`) inside any `async def` route or dependency.
- [ ] If you must call a sync library you can't replace yet, wrap it in `loop.run_in_executor(...)` as a migration bridge — not a permanent fix.
- [ ] Verify with: `py-spy record` under concurrent load, or `PYTHONASYNCIODEBUG=1` and watch for "Executing ... took X seconds" warnings.
- Demo: [`benchmarks/ap1-blocking/`](benchmarks/ap1-blocking/) — 3 concurrent requests: 3.05s (blocking) vs 1.04s (async).

## 2. Dependency lifecycle

- [ ] Expensive objects (DB engines, HTTP clients, config) are created **once**, in the app's lifespan, and handed out via `yield`-based `Depends()` — never rebuilt per request.
- [ ] Use `Annotated[T, Depends(get_x)]` for shared singletons; reserve `lru_cache` for pure, cheap factories.
- [ ] Verify with: a latency benchmark comparing the dependency's endpoint against a lifespan-singleton equivalent.
- Demo: [`benchmarks/ap2-di/`](benchmarks/ap2-di/) — ~10x latency overhead (17.5ms vs 1.7ms mean) from rebuilding an engine per request.

## 3. ORM loading strategy

- [ ] Every relationship you access in a response path is eager-loaded (`selectinload`/`joinedload`) in the query that fetches the parent — never touched lazily inside a loop.
- [ ] Consider `lazy="raise"` on relationships in async models so an accidental lazy touch fails loudly in dev instead of degrading silently in prod.
- [ ] Verify with: `echo=True` + a query counter — one extra query per eager-loaded relationship, not one per row.
- Demo: [`benchmarks/ap3-lazy-loading/`](benchmarks/ap3-lazy-loading/) — plain attribute access crashes with `MissingGreenlet`; `awaitable_attrs` "works" but costs N+1 queries (6 vs 2 for 5 orders).

## 4. Pydantic usage

- [ ] Validate directly from ORM objects with `ConfigDict(from_attributes=True)` — no manual dict construction, no `model_dump()` → `model_validate()` round-trips.
- [ ] For data that never crosses a process/API boundary, skip Pydantic entirely — a `dataclass` or `TypedDict` is enough.
- [ ] Verify with: `cProfile` over a realistic batch size; look at function-call count, not just wall time.
- Demo: [`benchmarks/ap4-pydantic/`](benchmarks/ap4-pydantic/) — ~1.9x slower, ~1.8x more function calls from a redundant validation round-trip.

## 5. Connection pool sizing

- [ ] `pool_size`/`max_overflow` are sized for your actual expected concurrency, not the driver's tutorial defaults (`pool_size=5, max_overflow=10`).
- [ ] `pool_timeout` is a deliberate choice, not whatever the default happens to be — know what "the pool is exhausted" looks like for your users.
- [ ] Verify with: a locust run at realistic concurrency; watch for `sqlalchemy.exc.TimeoutError: QueuePool limit ... reached`.
- Demo: [`benchmarks/ap5-pool/`](benchmarks/ap5-pool/) — same load, same code: 2.1% failures / 47.8 req/s (undersized pool) vs 0% failures / 179.3 req/s (tuned pool).

## Profiling toolkit reference

| Tool | Use it for | Command |
|---|---|---|
| `py-spy` | Zero-instrumentation sampling profiler, flame graphs | `py-spy record --pid <PID> -o out.svg` |
| `asyncio` debug mode | Catching blocking calls inside `async def` | `PYTHONASYNCIODEBUG=1 python app.py` |
| `cProfile` + `pstats` | Function-level CPU cost (e.g. Pydantic overhead) | `python -m cProfile -o out.prof script.py` |
| SQLAlchemy `echo=True` | Seeing every SQL statement + query counts | `create_async_engine(url, echo=True)` |
| `locust` | Realistic concurrent load, pool/timeout behavior | `locust --headless -u 50 -r 10 -t 30s` |
