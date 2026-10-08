---
title: Performance checklist
description: The five-point FastAPI performance checklist from the talk, as interactive checkboxes that remember your progress in this browser, with the matching demo for each point.
---

# Performance checklist

::: tip In one sentence
Five things to check before you trust a FastAPI service under real concurrency. Each one maps to a demo with captured before-and-after numbers.
:::

Tick items as you go. Progress is saved in this browser's local storage only. Nothing is sent anywhere, and the page works without it.

## 1. Event loop hygiene

<Checklist>
<ChecklistItem id="cl1-no-sync">No synchronous I/O (`requests`, blocking file or DB drivers, `time.sleep`) inside any `async def` route or dependency.</ChecklistItem>
<ChecklistItem id="cl1-bridge">If you must call a sync library you cannot replace yet, wrap it in `loop.run_in_executor(...)` as a migration bridge, not a permanent fix.</ChecklistItem>
<ChecklistItem id="cl1-verify">Verify with `py-spy record` under concurrent load, or `PYTHONASYNCIODEBUG=1`, and watch for "Executing ... took X seconds" warnings.</ChecklistItem>
</Checklist>

Demo: [AP1](/anti-patterns/ap1-blocking-event-loop). Three concurrent requests: **3.05 s** blocking against **1.04 s** async.

## 2. Dependency lifecycle

<Checklist>
<ChecklistItem id="cl2-lifespan">Expensive objects (DB engines, HTTP clients, config) are created once, in the app lifespan, and handed out through `yield`-based `Depends()`. Never rebuilt per request.</ChecklistItem>
<ChecklistItem id="cl2-annotated">Use `Annotated[T, Depends(get_x)]` for shared singletons. Reserve `lru_cache` for pure, cheap factories.</ChecklistItem>
<ChecklistItem id="cl2-verify">Verify with a latency benchmark comparing the dependency's endpoint against a lifespan-singleton equivalent.</ChecklistItem>
</Checklist>

Demo: [AP2](/anti-patterns/ap2-di-lifecycle). **17.5 ms** against **1.7 ms** mean, about 10×, from rebuilding an engine per request.

## 3. ORM loading strategy

<Checklist>
<ChecklistItem id="cl3-eager">Every relationship accessed in a response path is eager-loaded (`selectinload` or `joinedload`) in the query that fetches the parent. Never touched lazily inside a loop.</ChecklistItem>
<ChecklistItem id="cl3-raise">Consider `lazy="raise"` on relationships in async models, so an accidental lazy touch fails loudly in development instead of degrading silently in production.</ChecklistItem>
<ChecklistItem id="cl3-verify">Verify with `echo=True` and a query counter: one extra query per eager-loaded relationship, not one per row.</ChecklistItem>
</Checklist>

Demo: [AP3](/anti-patterns/ap3-lazy-loading). Plain attribute access crashes with `MissingGreenlet`. `awaitable_attrs` works but costs **6 queries against 2** for five orders.

## 4. Pydantic usage

<Checklist>
<ChecklistItem id="cl4-from-attributes">Validate directly from ORM objects with `ConfigDict(from_attributes=True)`. No manual dict construction, and no `model_dump()` followed by `model_validate()` round-trips.</ChecklistItem>
<ChecklistItem id="cl4-skip">For data that never crosses a process or API boundary, skip Pydantic entirely. A `dataclass` or `TypedDict` is enough.</ChecklistItem>
<ChecklistItem id="cl4-verify">Verify with `cProfile` over a realistic batch size. Look at the function-call count, not just wall time.</ChecklistItem>
</Checklist>

Demo: [AP4](/anti-patterns/ap4-pydantic-overhead). About **1.9×** slower and about **1.8×** more function calls, from a redundant validation round-trip.

## 5. Connection pool sizing

<Checklist>
<ChecklistItem id="cl5-size">`pool_size` and `max_overflow` are sized for your expected concurrency, not the driver's tutorial defaults (`pool_size=5, max_overflow=10`).</ChecklistItem>
<ChecklistItem id="cl5-timeout">`pool_timeout` is a deliberate choice. You know what "the pool is exhausted" looks like for your users.</ChecklistItem>
<ChecklistItem id="cl5-verify">Verify with a locust run at realistic concurrency. Watch for `sqlalchemy.exc.TimeoutError: QueuePool limit ... reached`.</ChecklistItem>
</Checklist>

Demo: [AP5](/anti-patterns/ap5-pool-starvation). Same load, same code: **2.1% failures at 47.8 req/s** with the undersized pool, against **0% failures at 179.3 req/s** with the tuned pool.

## Profiling toolkit

| Tool | Use it for | Command |
|---|---|---|
| `py-spy` | Zero-instrumentation sampling profiler, flame graphs | `py-spy record --pid <PID> -o out.svg` |
| `asyncio` debug mode | Catching blocking calls inside `async def` | `PYTHONASYNCIODEBUG=1 python app.py` |
| `cProfile` and `pstats` | Function-level CPU cost, for example Pydantic overhead | `python -m cProfile -o out.prof script.py` |
| SQLAlchemy `echo=True` | Seeing every SQL statement and the query counts | `create_async_engine(url, echo=True)` |
| `locust` | Realistic concurrent load, pool and timeout behaviour | `locust --headless -u 50 -r 10 -t 30s` |

More detail is on the [profiling toolkit page](/reference/profiling-toolkit).

## Related

- [Anti-pattern overview](/anti-patterns/)
- [Benchmarks](/reference/benchmarks)
- [Glossary](/reference/glossary)
