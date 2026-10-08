---
title: FAQ
description: Answers to the questions the talk expects in Q&A, covering Django, uvloop, workers, lazy='raise', the tracing talk, Pydantic v1, and tested versions.
---

# FAQ

::: tip In one sentence
Prepared answers to the questions the presenter expects, drawn from the presenter guide. Use them as written, or adapt them to your audience.
:::

## Why not just use Django or DRF? It does not have this async footgun.

Django's synchronous ORM has its own version of every one of these. N+1 is a classic Django problem, and DRF serializers have their own overhead story.

The async-specific ones, AP1 and the crash in AP3, belong to FastAPI and async ORMs. AP2, AP4, and AP5 exist in some form in any framework. The point is not that FastAPI is bad. It is that async gives you more rope, and the rope needs handling.

## Doesn't uvloop fix the blocking event-loop problem?

No. uvloop makes the loop itself faster. It does not change the fact that a synchronous blocking call inside a coroutine cannot be interrupted. It is the same anti-pattern with the same fix, uvloop or not. See [AP1](/anti-patterns/ap1-blocking-event-loop).

## Why not just add more workers instead of fixing the pool config?

You can trade some of this away with more Uvicorn or Gunicorn workers. But each worker gets its own pool, so the number of Postgres connections is multiplied by the worker count. At some point the database's own `max_connections` becomes the limit.

Pool sizing and worker count are two levers, not substitutes for each other. See [AP5](/anti-patterns/ap5-pool-starvation).

## Isn't `lazy='raise'` a breaking change to add to an existing model?

Yes. Treat it like any other behaviour change. Add it in a branch, run your test suite, and see what lights up. That is the point: it turns silent N+1 queries into loud failures in your test suite, not in production. See [AP3](/anti-patterns/ap3-lazy-loading).

## How does this relate to the other FastAPI talk on tracing and observability?

That talk is about finding problems in a running system over time. This one is about specific, reproducible code-level bugs and how to fix them. The two are complementary, not overlapping. Start with this repo's checklist, and use the tracing talk's tools once you need continuous visibility at scale.

## Is Pydantic v1 affected the same way?

The specific overhead numbers in this talk are for Pydantic v2, whose baseline is much faster. Pydantic v1's absolute numbers are worse. The shape of the anti-pattern is the same: redundant round-trips and deep validators. See [AP4](/anti-patterns/ap4-pydantic-overhead).

## Which Python, FastAPI, and SQLAlchemy versions was this tested on?

The floors are in `orders-api-demo/pyproject.toml`:

| Dependency | Floor in `pyproject.toml` |
|---|---|
| Python | 3.12 (`requires-python`) |
| FastAPI | 0.115 (`fastapi[standard]`) |
| SQLAlchemy | 2.0.36 (`sqlalchemy[asyncio]`) |
| asyncpg | 0.30 |
| Pydantic | 2.9 |
| httpx | 0.27 |

The cProfile captures in `benchmarks/ap4-pydantic/` were recorded under CPython 3.14, as the paths in the files show. Restate the versions you run live, because minor-version behaviour does shift. SQLAlchemy's async error messages are one example.

## Do I need Docker?

No. The SQLite mode needs only `uv`. Docker is required only for the Postgres mode, which produces the headline numbers. See [Setup](/guide/setup).

## Why does SQLite show a smaller gap for AP2?

A new SQLite engine does not do a network handshake, so the cost of rebuilding it is much smaller. Postgres pays a TCP and authentication handshake every time. See [Benchmarks](/reference/benchmarks#postgres-versus-sqlite).

## Related

- [Anti-pattern overview](/anti-patterns/)
- [Demo runbook](/demo/)
- [Glossary](/reference/glossary)
