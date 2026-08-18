# AP3 — SQLAlchemy lazy loading in async: captured evidence

Endpoints: `GET /demo/ap3/bad-crash` (plain attribute access), `GET /demo/ap3/bad-n1`
(`awaitable_attrs` loop), `GET /demo/ap3/good` (`selectinload`).

## Failure mode 1: `MissingGreenlet` crash

Hitting `curl "http://localhost:8000/demo/ap3/bad-crash?limit=3"` for real
against the dockerized app returns a real 500 with:

```json
{
    "error_type": "MissingGreenlet",
    "error": "greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place? (Background on this error at: https://sqlalche.me/e/20/xd2s)"
}
```

Full response: [`missing-greenlet-response.json`](missing-greenlet-response.json)

`AsyncSession`'s lazy loading needs a greenlet bridge; a plain Python
attribute access (`order.items`) outside of that bridge can't call back into
the driver, so it fails hard instead of silently going sync.

## Failure mode 2: N+1 queries (the "silent" version)

`AsyncAttrs.awaitable_attrs.items` *does* work — but issues one query per
order. Real `echo=True` SQL log, 5 orders:

- **bad-n1**: 6 queries total (1 for the order list + 5, one per order) — [`echo-bad.log`](echo-bad.log)
- **good (selectinload)**: 2 queries total (1 for the order list + 1 batched `IN (...)` query) — [`echo-good.log`](echo-good.log)

Reproduce: `SQLALCHEMY_WARN_20=1 PYTHONPATH=. uv run python scripts/sqlalchemy_echo_demo.py`

Both paths return identical item counts (verified — see
[`tests/test_ap3_lazy_loading.py`](../../tests/test_ap3_lazy_loading.py)),
so this is purely a query-count/latency problem, not a correctness one — the
kind of bug that passes code review and only shows up under load.

## The fix, two layers

1. **Per-query**: `select(Order).options(selectinload(Order.items))` — what `good` does.
2. **Defensive, model-level**: set `lazy="raise"` on `Order.items` in `app/models.py` so any *accidental* future lazy access fails loudly and immediately in development, rather than silently degrading into N+1 in production. Not applied in this demo repo (it would break `bad-crash`/`bad-n1` on purpose), but worth calling out live as the belt-and-braces option.

## Automated regression test

[`tests/test_ap3_lazy_loading.py`](../../tests/test_ap3_lazy_loading.py)
asserts all three behaviors on every run using a real SQLAlchemy
`before_cursor_execute` query counter — not just a one-off capture.
