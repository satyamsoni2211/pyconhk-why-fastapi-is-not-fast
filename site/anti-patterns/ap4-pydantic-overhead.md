---
title: "AP4 — Pydantic validation overhead"
description: Validating the same data twice, with a manual dict and a model_dump then model_validate round-trip, costs about 1.9× the time and 1.8× the function calls. Bad and good code, cProfile evidence, and how to detect it.
---

# AP4 — Pydantic validation overhead

<Callout type="tip" title="In one sentence">
Validate straight from the ORM object once with <code>from_attributes=True</code>, and skip Pydantic entirely for data that never leaves the process.
</Callout>

## What goes wrong

Pydantic v2 is fast. The problem is redundant work. Middleware and serializer layers often grow a pattern like this: build a dict by hand from the ORM object, validate it, dump it, validate the dump again, and dump again. Each validation re-runs every field validator, and each round-trip allocates new objects.

The overhead is pure CPU, and it runs on the event-loop thread. It is easy to miss in a single request, and it adds up across thousands of rows. Most people recognise the bad version from their own codebase.

## The bad code

`bad_transform` is in `orders-api-demo/app/schemas_ap4.py`. It builds a dict, validates it, dumps it, and validates it again. The second validation is the redundant one.

::: code-group

```python [app/schemas_ap4.py] {17-18}
def bad_transform(order) -> dict:
    raw = {
        "id": str(order.id),
        "customer_id": str(order.customer_id),
        "status": order.status,
        "items": [
            {
                "id": str(item.id),
                "sku": item.sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in order.items
        ],
    }
    validated = BadOrder.model_validate(raw)
    dumped = validated.model_dump()  # round-trip #1
    revalidated = BadOrder.model_validate(dumped)  # round-trip #2 — redundant
    return revalidated.model_dump()
```

:::

`BadOrder` and `BadOrderItem` have chained `field_validator`s, for example the SKU regex and a price normalisation. Those run on every validation, so the round-trip runs them twice.

## The good code

`good_transform` validates the ORM object directly, once. No manual dict, no round-trip.

::: code-group

```python [app/schemas_ap4.py] {2}
class GoodOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    status: str
    items: list[GoodOrderItem]


def good_transform(order) -> dict:
    validated = GoodOrder.model_validate(order)
    return validated.model_dump(mode="json")
```

:::

For data that never crosses a process boundary, the file also includes `internal_summary`, which returns a `TypedDict` and skips Pydantic entirely.

## Try it

::: code-group

```bash [endpoints]
curl "localhost:8000/demo/ap4/bad?limit=500"
curl "localhost:8000/demo/ap4/good?limit=500"
```

```bash [function calls]
PYTHONPATH=. uv run python scripts/pydantic_cprofile_demo.py
```

:::

Compare `elapsed_seconds`. Only the transform is timed, not the database fetch. **Expected, local SQLite** (DEMO_GUIDE): `bad` is roughly 2 to 2.7× slower than `good`, for example 5.8 ms against 2.9 ms at 500 orders.

The cProfile script prints the function-call counts. **Expected, local SQLite:** about 290k calls for `bad` and 111k for `good`.

Live, the time difference is only milliseconds, so it will not read on a projector. Show the captured numbers instead, and use the endpoints if you want a live moment.

## Measured evidence

<StatGrid>
<StatCard value="0.056 s → 0.030 s" label="cProfile total time" sub="Postgres capture, 200 orders × 20 repeats" tone="bad" />
<StatCard value="204,481 → 116,463" label="function calls" sub="Postgres capture" />
<StatCard value="~1.9×" label="slower" sub="time, bad ÷ good" tone="bad" />
<StatCard value="~290k vs 111k" label="function calls, SQLite local" sub="working-tree capture, not committed" />
</StatGrid>

<BarCompare :bad="204481" :good="116463" unit=" calls" caption="function calls, Postgres capture (committed)" />

Captured header lines (`benchmarks/ap4-pydantic/cprofile-bad.txt`, `cprofile-good.txt`):

```text
=== BAD (nested validators + round-trip): 200 orders x 20 repeats ===
204481 function calls in 0.056 seconds

=== GOOD (from_attributes, single pass): 200 orders x 20 repeats ===
116463 function calls (116319 primitive calls) in 0.030 seconds
```

The automated test `tests/test_ap4_pydantic.py` asserts identical output counts and that `bad` is more than 1.3× slower than `good`.

::: info Why call counts matter more than wall time
Wall-clock timings move with the machine. Function-call counts are stable across machines, so they make a better comparison.
:::

## How to detect it in your own service

| Tool | Command | What to look for |
|---|---|---|
| cProfile | `python -m cProfile -o out.prof script.py` | `model_validate` and `model_dump` called twice per object |
| Code review | Search for `model_dump()` followed by `model_validate(` | A round-trip with no change in between |
| Benchmark | Compare call counts over a realistic batch size | A large call count for a simple mapping |

## Checklist

<Checklist>
<ChecklistItem id="ap4-from-attributes">Validate directly from ORM objects with `ConfigDict(from_attributes=True)`. No manual dict construction and no `model_dump()` followed by `model_validate()`.</ChecklistItem>
<ChecklistItem id="ap4-skip">For data that never crosses a process or API boundary, skip Pydantic. A `dataclass` or `TypedDict` is enough.</ChecklistItem>
<ChecklistItem id="ap4-verify">Verify with cProfile over a realistic batch size, and look at the function-call count, not only wall time.</ChecklistItem>
</Checklist>

## Talking points

- Pydantic v2 is fast, but a redundant round-trip times thousands of rows is not free, and it is CPU on the event-loop thread.
- Measure call counts, not just wall time. They are stable across machines.
- The "skip Pydantic for internal data" point is the one people forget. Mention it explicitly.
- Do not demo this live. Show the captured cProfile numbers.

## Related

- [Benchmarks](/reference/benchmarks)
- [Profiling toolkit: cProfile](/reference/profiling-toolkit)
- [Checklist: Pydantic usage](/reference/checklist)
- [Anti-pattern overview](/anti-patterns/)
