# AP4 — Pydantic validation overhead: captured evidence

Endpoints: `GET /demo/ap4/bad` (manual dict construction, chained
`field_validator`s, `model_dump()`→`model_validate()` redundant round-trip),
`GET /demo/ap4/good` (`ConfigDict(from_attributes=True)`, single pass
directly from the ORM object).

## Real cProfile capture — 200 real seeded orders x 20 repeats (4000 calls)

| | Total time | Function calls |
|---|---|---|
| **bad** | 0.056s | 204,481 |
| **good** | 0.030s | 116,463 |

~1.9x slower, ~1.8x more function calls — entirely from the redundant
`model_validate()` → `model_dump()` → `model_validate()` round-trip and the
extra per-field validator chain running twice.

Full pstats output: [`cprofile-bad.txt`](cprofile-bad.txt) / [`cprofile-good.txt`](cprofile-good.txt)
Reproduce: `PYTHONPATH=. uv run python scripts/pydantic_cprofile_demo.py`

## Real single-request HTTP timing, 200 orders

```
bad:  elapsed_seconds = 0.00326
good: elapsed_seconds = 0.00142
```

Reproduce: `curl "http://localhost:8000/demo/ap4/bad?limit=200"` / `.../good?limit=200`

## Automated regression test

[`tests/test_ap4_pydantic.py`](../../tests/test_ap4_pydantic.py) asserts
identical output counts (correctness) and that `bad` stays meaningfully
slower than `good` (>1.3x) on every run.

## The fix

- `ConfigDict(from_attributes=True)` validating straight from the ORM object — no manual dict, no round-trip.
- For data that never leaves the process (`InternalOrderSummary` in [`app/schemas_ap4.py`](../../app/schemas_ap4.py)), skip Pydantic entirely and use a `TypedDict`.
