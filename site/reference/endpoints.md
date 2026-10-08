---
title: Endpoints
description: Every HTTP endpoint in the Orders API and the mock payment gateway, with method, path, purpose, parameters, and response shape, read from the router code.
---

# Endpoints

::: tip In one sentence
Sixteen endpoints on the Orders API and five on the mock gateway. The routers are the source of truth; this page was written from them.
:::

Interactive docs are served by FastAPI at `http://localhost:8000/docs` and the gateway at `http://localhost:8080/docs`.

## Orders API (port 8000)

### Baseline

| Method | Path | Purpose | Parameters | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness check | none | `{"status": "ok"}` |
| `POST` | `/orders` | Create an order with items | JSON body: `customer_id` (UUID), `items` (list of `sku`, `quantity`, `unit_price`) | `201`, `OrderDetailRead` |
| `GET` | `/orders` | List recent orders | `limit` (int, default `50`) | `200`, list of `OrderRead` |
| `GET` | `/orders/{order_id}` | Order detail with items | `order_id` (UUID) | `200`, `OrderDetailRead`, or `404` |

### AP1 — blocking the event loop

Each calls the gateway's `/delay/1`. Source: `app/routers/demo_ap1.py`.

| Method | Path | Purpose | Response |
|---|---|---|---|
| `GET` | `/demo/ap1/bad` | `requests.get()` inside `async def`. Blocks the loop. | `{"gateway_status": "200", "mode": "bad-blocking-requests"}` |
| `GET` | `/demo/ap1/good` | Shared `httpx.AsyncClient`, awaited | `{"gateway_status": "200", "mode": "good-httpx-async"}` |
| `GET` | `/demo/ap1/bridge` | `requests` run in `run_in_executor`, a migration bridge | `{"gateway_status": "200", "mode": "bridge-run-in-executor"}` |

### AP2 — dependency lifecycle

Source: `app/routers/demo_ap2.py`. Each runs `SELECT 1` and a `GET /get` on the gateway.

| Method | Path | Purpose | Response |
|---|---|---|---|
| `GET` | `/demo/ap2/bad` | New engine and new client per request | `{"mode": "bad-new-engine-and-client-per-request", "elapsed_seconds": <float>}` |
| `GET` | `/demo/ap2/good` | Lifespan singletons | `{"mode": "good-shared-singletons", "elapsed_seconds": <float>}` |

### AP3 — lazy loading

Source: `app/routers/demo_ap3.py`.

| Method | Path | Parameters | Purpose | Response |
|---|---|---|---|---|
| `GET` | `/demo/ap3/bad-crash` | `limit` (default `3`) | Plain `order.items` access | `500` with `error_type: "MissingGreenlet"` |
| `GET` | `/demo/ap3/bad-n1` | `limit` (default `5`) | `awaitable_attrs.items` in a loop, N+1 | `{"mode": "bad-n1-awaitable-attrs-loop", "item_counts": [...]}` |
| `GET` | `/demo/ap3/good` | `limit` (default `5`) | `selectinload(Order.items)` | `{"mode": "good-selectinload", "item_counts": [...]}` |

The `bad-crash` error body is `{"mode", "error_type", "error"}`. The `error` text is truncated to 300 characters.

### AP4 — Pydantic overhead

Source: `app/routers/demo_ap4.py`. Only the transform is timed, not the database fetch.

| Method | Path | Parameters | Purpose | Response |
|---|---|---|---|---|
| `GET` | `/demo/ap4/bad` | `limit` (default `100`) | Nested validators, dump then validate | `{"mode": "bad-nested-validators-round-trip", "n": <int>, "elapsed_seconds": <float>}` |
| `GET` | `/demo/ap4/good` | `limit` (default `100`) | `from_attributes=True`, single pass | `{"mode": "good-from-attributes-single-pass", "n": <int>, "elapsed_seconds": <float>}` |

### AP5 — pool starvation

Source: `app/routers/demo_ap5.py`.

| Method | Path | Purpose | Response |
|---|---|---|---|
| `GET` | `/demo/ap5/query` | Holds a pooled connection for about 0.3 s (Postgres, `pg_sleep`) or 0.6 s (SQLite, `asyncio.sleep`), then selects 10 orders | `{"n": <int>}` |
| `GET` | `/demo/ap5/info` | Reports the active pool profile | `{"pool_mode", "pool_size", "max_overflow", "pool_timeout", "pool_recycle"}` |

Sample `info` response for the `good` profile, using the values in `app/config.py`:

```json
{
  "pool_mode": "good",
  "pool_size": 20,
  "max_overflow": 40,
  "pool_timeout": 10,
  "pool_recycle": 1800
}
```

## Mock payment gateway (port 8080)

Source: `mock_gateway/main.py`. It is a dependency-free FastAPI app. It uses `asyncio.sleep`, so it never blocks its own loop. Delays are capped at 10 seconds.

| Method | Path | Purpose | Response |
|---|---|---|---|
| `GET` | `/health` | Liveness check | `{"status": "ok"}` |
| `GET` | `/delay/{seconds}` | Sleep, then respond. Used by AP1. | `{"delay": <float>, "url": "<request URL>"}` |
| `GET` | `/get` | Echo the query args, headers, and URL. Used by AP2. | `{"args": {...}, "headers": {...}, "url": "..."}` |
| `GET` | `/status/{code}` | Respond with the given HTTP status and no body | empty body, status `code` |
| `POST` | `/charge` | Fake payment authorisation, after a 0.2 s sleep | `{"payment_id", "status": "authorized", "amount", "currency", "order_id"}` |

`/charge` takes a JSON body with `amount` (float), `currency` (default `"USD"`), and optional `order_id`.

::: info Docker gateway
In Docker, the gateway is `go-httpbin` (`mccutchen/go-httpbin:v2.15.0`) on port 8080. The demos call only its `/delay/{n}` and `/get` routes, which the mock also provides. The mock's `POST /charge` is not called by any demo or test in this repo.
:::

## Related

- [Baseline API](/guide/baseline-api): the order endpoints with curl examples
- [Running the demos](/demo/running-the-demos): which endpoint to call in each section
- [Glossary](/reference/glossary)
