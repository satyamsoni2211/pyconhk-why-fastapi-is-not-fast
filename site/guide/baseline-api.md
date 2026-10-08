---
title: Baseline API
description: The correctly written Orders endpoints (create, list, detail) with curl examples and response shapes, taken from the router code.
---

# Baseline API

::: tip In one sentence
The baseline endpoints are the production-shaped service that the anti-patterns are injected into. Nothing here is slow; use them to set the scene.
:::

The baseline lives in `app/routers/orders.py`, mounted at `/orders`. Each handler gets a session from the lifespan-scoped sessionmaker through `Depends(get_session)`, which is the correct AP2 pattern.

## Endpoints

| Method | Path | Purpose | Status |
|---|---|---|---|
| `POST` | `/orders` | Create an order and its items | `201` |
| `GET` | `/orders` | List recent orders, newest first | `200` |
| `GET` | `/orders/{order_id}` | Order detail with items | `200`, or `404` |

`GET /orders` takes `limit` (default `50`). It orders by `created_at` descending.

`GET /orders/{order_id}` uses `selectinload(Order.items)`, so the items come from one extra query, not one per order. This is the "good" loading strategy from [AP3](/anti-patterns/ap3-lazy-loading).

## Try it

Run these after [setup](/guide/setup), from any terminal:

```bash
curl "localhost:8000/orders?limit=3"
```

Fetch the newest order's ID and its detail:

```bash
ORDER=$(curl -s "localhost:8000/orders?limit=1" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
curl localhost:8000/orders/$ORDER
```

Create an order for an existing customer:

```bash
CUSTOMER=$(curl -s "localhost:8000/orders?limit=1" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['customer_id'])")
curl -X POST localhost:8000/orders -H 'content-type: application/json' \
  -d "{\"customer_id\":\"$CUSTOMER\",\"items\":[{\"sku\":\"SKU-0001AB\",\"quantity\":2,\"unit_price\":9.5}]}"
```

::: info SKU format
The AP4 transforms validate SKUs against `^SKU-\d{4}[A-Za-z]{2}$`, for example `SKU-0001AB`. The baseline `POST` endpoint does not enforce it.
:::

## Response shapes

These come from `app/schemas.py`. Values are placeholders.

`GET /orders` returns a list of `OrderRead`:

```json
[
  {
    "id": "<uuid>",
    "customer_id": "<uuid>",
    "status": "pending",
    "created_at": "<ISO-8601 datetime>"
  }
]
```

`GET /orders/{id}` and `POST /orders` return `OrderDetailRead`, which adds `items`:

```json
{
  "id": "<uuid>",
  "customer_id": "<uuid>",
  "status": "pending",
  "created_at": "<ISO-8601 datetime>",
  "items": [
    { "id": "<uuid>", "sku": "SKU-0001AB", "quantity": 2, "unit_price": 9.5 }
  ]
}
```

A missing order returns `404` with `{"detail": "Order not found"}`.

## Related

- [Architecture](/guide/architecture): where these handlers sit in the app
- [AP3 — Lazy loading](/anti-patterns/ap3-lazy-loading): why the detail endpoint uses `selectinload`
- [Endpoints reference](/reference/endpoints): every endpoint, including the demos
