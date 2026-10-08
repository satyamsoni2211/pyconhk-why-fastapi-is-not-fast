---
title: Glossary
description: Plain-language definitions of the async, ORM, and pool terms used across the workshop, with links to where each one matters.
---

# Glossary

::: tip In one sentence
Each entry says what the term means here, then where it shows up. Terms are alphabetical.
:::

| Term | Meaning |
|---|---|
| **`async def`** | A coroutine function. It *can* yield control at an `await`, but it does not make the code inside non-blocking. A call that never awaits runs like ordinary synchronous code. See [AP1](/anti-patterns/ap1-blocking-event-loop). |
| **`awaitable_attrs`** | The `AsyncAttrs` property that lets you write `await order.awaitable_attrs.items`. It loads a relationship on demand. In a loop this issues one query per row, which is the N+1 pattern. See [AP3](/anti-patterns/ap3-lazy-loading). |
| **blocking call** | A synchronous call, such as `requests.get()` or `time.sleep()`, that holds the thread until it finishes. Inside `async def` it also stops every other coroutine on the same event loop. |
| **connection pool** | A set of open database connections that requests borrow and return. Creating a connection is expensive, so pools reuse them. The pool is a hard ceiling on concurrent database work. See [AP5](/anti-patterns/ap5-pool-starvation). |
| **`echo=True`** | A SQLAlchemy engine option that logs every SQL statement it runs. Counting the log lines gives the query count. See [Profiling toolkit](/reference/profiling-toolkit). |
| **event loop** | The single thread that runs coroutines and switches between them at `await` points. One blocked call blocks the loop for every request. See [Architecture](/guide/architecture). |
| **`from_attributes`** | A Pydantic v2 `ConfigDict` option that lets a model validate straight from an object's attributes, such as an ORM instance, without building a dict first. See [AP4](/anti-patterns/ap4-pydantic-overhead). |
| **greenlet** | A lightweight cooperative task. SQLAlchemy's async layer runs its synchronous internals inside a greenlet so it can await the driver. Touching a lazy attribute outside that bridge raises `MissingGreenlet`. See [AP3](/anti-patterns/ap3-lazy-loading). |
| **`lazy="raise"`** | A relationship option that makes any implicit load raise an error instead of querying. It is the model-level defence the talk recommends. The demo repo does not apply it, because the crash and N+1 demos need the default. See [AP3](/anti-patterns/ap3-lazy-loading). |
| **lifespan** | The FastAPI startup and shutdown hook, an `asynccontextmanager` in `app/main.py`. The demo builds the engine, sessionmaker, and HTTP client here, once. See [AP2](/anti-patterns/ap2-di-lifecycle). |
| **`max_overflow`** | How many connections a pool may open above `pool_size` during a burst. Those extra connections are closed when returned. In the bad profile it is 10. See [Setup](/guide/setup#configuration). |
| **`MissingGreenlet`** | The error raised when async-only SQLAlchemy code runs a lazy load in a synchronous context. The `/demo/ap3/bad-crash` endpoint returns it on purpose. |
| **N+1 query** | One query for the parent rows, then one more per row to fetch a child relationship. With five orders that is six queries. Eager loading turns it into two. See [AP3](/anti-patterns/ap3-lazy-loading). |
| **`pool_recycle`** | The age in seconds after which a pooled connection is replaced. It stops idle connections from going stale. The good profile uses 1800. See [AP5](/anti-patterns/ap5-pool-starvation). |
| **`pool_size`** | The number of connections the pool keeps open. The bad profile uses 5 and the good profile uses 20. See [Setup](/guide/setup#configuration). |
| **`pool_timeout`** | How long a request waits for a connection before the pool raises `TimeoutError`. The bad profile uses 2 seconds and the good profile uses 10. See [AP5](/anti-patterns/ap5-pool-starvation). |
| **`py-spy`** | A sampling profiler that attaches to a running process without code changes and records flame graphs. See [Profiling toolkit](/reference/profiling-toolkit). |
| **`QueuePool limit ... reached`** | The SQLAlchemy error text for a pool timeout, for example `QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 2.00`. It is the signature of AP5 in logs. See [Troubleshooting](/demo/troubleshooting). |
| **`run_in_executor`** | An asyncio method that runs a blocking function in a thread pool and returns an awaitable. The demo calls it a migration bridge, not a fix. See [AP1](/anti-patterns/ap1-blocking-event-loop). |
| **`selectinload`** | A SQLAlchemy loader option that fetches a relationship for all parent rows in one extra `IN (...)` query. See [AP3](/anti-patterns/ap3-lazy-loading). |
| **sessionmaker** | The factory that creates `AsyncSession` objects. The demo creates one at startup and shares it. See [AP2](/anti-patterns/ap2-di-lifecycle). |
| **`uvloop`** | A faster event loop implementation. It makes the loop faster but does not stop a blocking call from blocking it. See the [FAQ](/reference/faq). |

## Related

- [Checklist](/reference/checklist)
- [Anti-pattern overview](/anti-patterns/)
