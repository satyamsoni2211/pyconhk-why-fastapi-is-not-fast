---
title: "AP3 — SQLAlchemy lazy loading in async"
description: Touching a lazy relationship in async SQLAlchemy either crashes with MissingGreenlet or silently issues one query per row. Bad and good code, query counts, and how to detect it.
---

# AP3 — SQLAlchemy lazy loading in async

<Callout type="tip" title="In one sentence">
In async code, a lazy relationship either crashes with <code>MissingGreenlet</code> or quietly runs one query per row; eager-load it in the query that fetches the parent.
</Callout>

## What goes wrong

`Order.items` is a relationship that loads lazily by default. In synchronous SQLAlchemy, reading `order.items` runs a query on the spot. In async SQLAlchemy that query needs an `await`, and a plain attribute access cannot await. There are two failure modes.

**Failure mode 1: it crashes.** Plain attribute access raises `MissingGreenlet`. It is loud, so it is the easier one to catch.

**Failure mode 2: it works, and costs N+1.** `await order.awaitable_attrs.items` does work, but it runs one query per order. Five orders means six queries: one for the orders and one for each order's items. The results are identical, so code review does not catch it.

The fix is to eager-load the relationship in the query that fetches the parent. That turns N+1 into two queries, whatever the row count.

## The bad code

Both bad endpoints are in `orders-api-demo/app/routers/demo_ap3.py`. The crash endpoint catches the exception on purpose and returns it as JSON. The excerpt below shows the core lines, with the error response elided.

::: code-group

```python [app/routers/demo_ap3.py] {6}
@router.get("/bad-crash")
async def lazy_attribute_access_crash(session: SessionDep, limit: int = 3):
    result = await session.execute(select(Order).limit(limit))
    orders = result.scalars().all()
    try:
        item_counts = [len(order.items) for order in orders]  # plain attribute access
    except Exception as exc:  # noqa: BLE001 - deliberately surfacing the real crash
        # ... returns a 500 JSON body with error_type and error ...
```

```python [app/routers/demo_ap3.py] {7}
@router.get("/bad-n1")
async def lazy_load_n_plus_one(session: SessionDep, limit: int = 5):
    result = await session.execute(select(Order).limit(limit))
    orders = result.scalars().all()
    item_counts = []
    for order in orders:
        items = await order.awaitable_attrs.items  # one query PER order
        item_counts.append(len(items))
    return {"mode": "bad-n1-awaitable-attrs-loop", "item_counts": item_counts}
```

:::

## The good code

The `good` endpoint asks for the items in the same query that fetches the orders:

::: code-group

```python [app/routers/demo_ap3.py] {3-4}
@router.get("/good")
async def eager_load_selectinload(session: SessionDep, limit: int = 5):
    result = await session.execute(
        select(Order).options(selectinload(Order.items)).limit(limit)
    )
    orders = result.scalars().all()
    item_counts = [len(order.items) for order in orders]
    return {"mode": "good-selectinload", "item_counts": item_counts}
```

:::

<BadGood>
<template #bad>

**`/demo/ap3/bad-crash`** raises `MissingGreenlet` and returns HTTP 500.

**`/demo/ap3/bad-n1`** works, but issues one query per order.

</template>
<template #good>

**`/demo/ap3/good`** issues one extra batched query for all the items, no matter how many orders.

</template>
</BadGood>

## Try it

::: code-group

```bash [crash]
curl -i "localhost:8000/demo/ap3/bad-crash?limit=3"
```

```bash [N+1 vs eager]
curl "localhost:8000/demo/ap3/bad-n1?limit=5"
curl "localhost:8000/demo/ap3/good?limit=5"
```

```bash [count the queries]
PYTHONPATH=. uv run python scripts/sqlalchemy_echo_demo.py
```

:::

**Expected for the crash:** HTTP 500 with `"error_type": "MissingGreenlet"`.

**Expected for N+1 and eager:** identical `item_counts` arrays from both endpoints. Only the query count differs.

**Expected from the echo script** (the last line of the captured log): `bad-n1 issued 6 queries, good issued 2 queries` for five orders. Scaling `?limit=100` gives 101 queries against 2, from the 1 + N arithmetic.

The echo log is verbose. Run the script to count, not to present live.

## Measured evidence

<StatGrid>
<StatCard value="MissingGreenlet" label="bad-crash" sub="HTTP 500, captured" tone="bad" />
<StatCard value="6" label="queries, bad-n1" sub="1 for orders + 5, one per order" tone="bad" />
<StatCard value="2" label="queries, good" sub="1 for orders + 1 batched IN (...)" tone="good" />
<StatCard value="Postgres capture" label="environment" sub="echo=True, 5 orders" />
</StatGrid>

<BarCompare :bad="6" :good="2" unit=" queries" caption="five orders, echo=True, Postgres capture" />

The captured crash response (`benchmarks/ap3-lazy-loading/missing-greenlet-response.json`):

```json
{
    "mode": "bad-crash-sync-attribute-access",
    "error_type": "MissingGreenlet",
    "error": "greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place? (Background on this error at: https://sqlalche.me/e/20/xd2s)"
}
```

The captured `echo-good.log` ends with the summary line that compares the two runs:

```text
=== SUMMARY: bad-n1 issued 6 queries, good issued 2 queries ===
```

The good log shows the single `IN (...)` query for the five order IDs. The bad log shows one `SELECT ... FROM order_item WHERE ... = $1` per order.

Both paths return the same counts. The automated test `tests/test_ap3_lazy_loading.py` asserts all three behaviours with a `before_cursor_execute` query counter.

## How to detect it in your own service

| Tool | Command or method | What to look for |
|---|---|---|
| `echo=True` | `create_async_engine(url, echo=True)` in a test or script | Many near-identical `SELECT` statements, one per row |
| Query counter | `before_cursor_execute` event listener in a test | The count grows with the number of rows |
| Tests | `lazy="raise"` on the relationship | Any accidental lazy touch fails the test run |
| Crash logs | Search for `MissingGreenlet` | A lazy attribute read in an async route |

## Checklist

<Checklist>
<ChecklistItem id="ap3-eager">Every relationship accessed in a response path is eager-loaded (`selectinload` or `joinedload`) in the query that fetches the parent, never touched lazily inside a loop.</ChecklistItem>
<ChecklistItem id="ap3-raise">Consider `lazy="raise"` on relationships in async models, so an accidental lazy touch fails loudly in development.</ChecklistItem>
<ChecklistItem id="ap3-verify">Verify with `echo=True` and a query counter: one extra query per eager-loaded relationship, not one per row.</ChecklistItem>
</Checklist>

## Talking points

- `bad-crash` is the good failure. It is loud, so it is safe to show live. It is the most reliable demo in the talk.
- `bad-n1` is the dangerous one. The answer is correct, it is silently slow, and each query is an `await` hop on the loop.
- `lazy="raise"` is the belt-and-braces option. Do not demo it live, because it would break the other two endpoints on purpose. Adding it to an existing model is a behaviour change: try it in a branch and run the tests.

## Related

- [Baseline API: the eager-loaded detail endpoint](/guide/baseline-api)
- [Glossary: N+1, greenlet, selectinload](/reference/glossary)
- [Benchmarks](/reference/benchmarks)
- [Anti-pattern overview](/anti-patterns/)
