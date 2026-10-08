---
title: Architecture
description: The Orders API's domain model, app layout, how each bad and good pair is wired, and the request flow for each anti-pattern.
---

# Architecture

::: tip In one sentence
The baseline service is written correctly; each anti-pattern is a second endpoint that differs from the good one by only a line or two, which is the point.
:::

## Domain model

The domain is `Customer → Order → OrderItem`, defined with SQLAlchemy 2.0 async in `app/models.py`.

| Table | Columns (type notes) | Relationship |
|---|---|---|
| `customer` | `id` (UUID, PK), `name` (String 200), `email` (String 200, unique) | `orders` |
| `order` | `id` (UUID, PK), `customer_id` (FK to customer), `status` (String 30, default `pending`), `created_at` (timezone-aware datetime) | `customer`, `items` |
| `order_item` | `id` (UUID, PK), `order_id` (FK to order), `sku` (String 50), `quantity` (int), `unit_price` (Numeric 10,2) | `order` |

The base class is `Base(AsyncAttrs, DeclarativeBase)`. `AsyncAttrs` is what provides `awaitable_attrs`, used in [AP3](/anti-patterns/ap3-lazy-loading).

::: info Lazy by default, on purpose
`Order.items` uses the default `lazy="select"`. The source comments say this is deliberate, so the AP3 failure modes can be shown. The `good` path overrides it per query with `selectinload`. The model-level alternative, `lazy="raise"`, is discussed on the AP3 page.
:::

## App layout

```text
orders-api-demo/
  app/
    main.py            App, lifespan, router registration, /health
    config.py          Settings and the bad/good pool profiles
    db.py              Engine and sessionmaker factories, get_session dependency
    models.py          Customer, Order, OrderItem
    schemas.py         Baseline Pydantic schemas
    schemas_ap4.py     AP4 bad and good transforms, and the TypedDict summary
    clients.py         get_http_client dependency (the lifespan singleton)
    routers/
      orders.py        Baseline endpoints, written correctly
      demo_ap1.py      Blocking vs async vs executor bridge
      demo_ap2.py      Per-request vs shared engine and client
      demo_ap3.py      Crash, N+1, and selectinload
      demo_ap4.py      Redundant round-trip vs from_attributes
      demo_ap5.py      Slow query and pool info
  mock_gateway/main.py Stand-in for the payment gateway
  scripts/             Seeding, benchmarks, profilers, and locust
  tests/               One pytest file per anti-pattern, plus baseline tests
  benchmarks/          Captured output and an explanatory README per pattern
```

## Startup: the lifespan

`app/main.py` builds the shared objects **once**, in the FastAPI lifespan:

- the async engine, with the pool settings from `POOL_MODE`
- `Base.metadata.create_all`, which creates the tables on first start
- the sessionmaker, stored on `app.state.sessionmaker`
- one `httpx.AsyncClient(timeout=10.0)`, stored on `app.state.http_client`

On shutdown the client is closed and the engine disposed. Everything in this list is a singleton. AP2 is the anti-pattern where a route builds these objects itself instead.

## Request flow: the baseline

<svg viewBox="0 0 760 210" role="img" aria-labelledby="flow-base-title flow-base-desc" class="arch-svg">
  <title id="flow-base-title">Baseline request flow</title>
  <desc id="flow-base-desc">A client sends a request to a FastAPI route. The route receives a session from the shared sessionmaker through a dependency, which checks a connection out of the pool to Postgres or SQLite.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 z" style="fill: var(--vp-c-text-3)"/>
    </marker>
  </defs>
  <g class="arch-node">
    <rect x="8" y="78" width="120" height="54" rx="14"/>
    <text x="68" y="110" text-anchor="middle">Client</text>
  </g>
  <g class="arch-node">
    <rect x="168" y="78" width="150" height="54" rx="14"/>
    <text x="243" y="103" text-anchor="middle">FastAPI route</text>
    <text x="243" y="121" text-anchor="middle" class="arch-sub">async def</text>
  </g>
  <g class="arch-node">
    <rect x="358" y="78" width="170" height="54" rx="14"/>
    <text x="443" y="103" text-anchor="middle">get_session</text>
    <text x="443" y="121" text-anchor="middle" class="arch-sub">shared sessionmaker</text>
  </g>
  <g class="arch-node">
    <rect x="570" y="78" width="180" height="54" rx="14"/>
    <text x="660" y="103" text-anchor="middle">Pool and DB</text>
    <text x="660" y="121" text-anchor="middle" class="arch-sub">Postgres or SQLite</text>
  </g>
  <path d="M130 105 H166" class="arch-line" marker-end="url(#arrow)"/>
  <path d="M320 105 H354" class="arch-line" marker-end="url(#arrow)"/>
  <path d="M530 105 H566" class="arch-line" marker-end="url(#arrow)"/>
  <path d="M243 134 V176 H443 V136" class="arch-line dashed" marker-end="url(#arrow)"/>
  <text x="340" y="196" text-anchor="middle" class="arch-sub">the gateway client is also shared, from app.state.http_client</text>
</svg>

The baseline routes in `app/routers/orders.py` use `Annotated[AsyncSession, Depends(get_session)]`, and `get_session` hands out a session from `request.app.state.sessionmaker`. The detail endpoint eager-loads items with `selectinload`. See [Baseline API](/guide/baseline-api).

## How each pair is wired

Every pair runs on the same process. The table shows what differs between `bad` and `good`.

| Pattern | Bad path | Good path | Where the difference lives |
|---|---|---|---|
| AP1 | `requests.get()` inside `async def` | shared `httpx.AsyncClient`, awaited | `app/routers/demo_ap1.py` |
| AP2 | new engine and new client per request | `get_session` and `get_http_client` singletons | `app/routers/demo_ap2.py` |
| AP3 | plain `order.items`, or `awaitable_attrs` in a loop | `selectinload(Order.items)` in the query | `app/routers/demo_ap3.py` |
| AP4 | dict, nested validators, `model_dump` then `model_validate` | `from_attributes=True` once | `app/schemas_ap4.py`, `app/routers/demo_ap4.py` |
| AP5 | pool fixed at `POOL_MODE=bad` | pool fixed at `POOL_MODE=good` | `app/config.py`, restart between runs |

## Request flow for AP1

The blocking call stops the event loop. Both requests below are on one loop thread.

<svg viewBox="0 0 760 230" role="img" aria-labelledby="flow-ap1-title flow-ap1-desc" class="arch-svg">
  <title id="flow-ap1-title">AP1 timeline, bad and good</title>
  <desc id="flow-ap1-desc">Bad path: three requests run one after another, about 1 second each. Good path: the three requests overlap and finish together after about 1 second.</desc>
  <text x="10" y="24" class="arch-sub">bad: requests.get() blocks the loop</text>
  <rect x="150" y="34" width="200" height="22" rx="8" class="bar-bad"/>
  <rect x="350" y="34" width="200" height="22" rx="8" class="bar-bad"/>
  <rect x="550" y="34" width="200" height="22" rx="8" class="bar-bad"/>
  <text x="150" y="30" class="arch-sub" dy="-4">request 1</text>
  <text x="10" y="82" class="arch-sub">good: awaited, so the loop is free</text>
  <rect x="150" y="92" width="600" height="22" rx="8" class="bar-good"/>
  <text x="150" y="132" class="arch-sub">request 1, request 2 and request 3 overlap in the same window</text>
  <rect x="150" y="150" width="600" height="22" rx="8" class="bar-good"/>
  <rect x="150" y="180" width="600" height="22" rx="8" class="bar-good"/>
  <line x1="150" y1="210" x2="750" y2="210" class="arch-axis"/>
  <text x="150" y="226" class="arch-sub">0 s</text>
  <text x="750" y="226" text-anchor="end" class="arch-sub">about 3 s</text>
</svg>

This timeline is schematic. The measured values are on the [AP1 page](/anti-patterns/ap1-blocking-event-loop).

## Related

- [Baseline API](/guide/baseline-api)
- [AP1 — Blocking the event loop](/anti-patterns/ap1-blocking-event-loop)
- [Endpoints reference](/reference/endpoints)
