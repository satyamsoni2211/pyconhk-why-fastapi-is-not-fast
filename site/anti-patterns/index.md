---
title: Anti-patterns overview
description: The five FastAPI anti-patterns from the talk at a glance, with the headline measurement for each and how to read a pattern page.
---

# Anti-patterns overview

::: tip In one sentence
Five patterns that look fine in code review and a single curl, and only hurt under concurrency. Each has a bad endpoint, a good endpoint, and measured evidence.
:::

## The five at a glance

| # | Anti-pattern | Bad endpoint or symptom | Headline measurement | Environment |
|---|---|---|---|---|
| [AP1](/anti-patterns/ap1-blocking-event-loop) | Blocking the event loop | `GET /demo/ap1/bad` | 3.046 s bad vs 1.040 s good, 3 concurrent requests | Postgres capture |
| [AP2](/anti-patterns/ap2-di-lifecycle) | Dependency injection lifecycle misuse | `GET /demo/ap2/bad` | 17.48 ms vs 1.73 ms mean, about 10× | Postgres capture |
| [AP3](/anti-patterns/ap3-lazy-loading) | Lazy loading in async | `GET /demo/ap3/bad-crash`, `bad-n1` | `MissingGreenlet`, and 6 queries vs 2 for five orders | Postgres capture |
| [AP4](/anti-patterns/ap4-pydantic-overhead) | Pydantic validation overhead | `GET /demo/ap4/bad` | About 1.9× slower, about 1.8× more function calls | Postgres capture |
| [AP5](/anti-patterns/ap5-pool-starvation) | Connection pool starvation | `GET /demo/ap5/query` under `POOL_MODE=bad` | 2.1% failures at 47.8 req/s vs 0% at 179.3 req/s | Postgres capture |

::: info How to read the environment column
**Postgres capture** is the committed output from the Docker setup, which the talk uses. The DEMO_GUIDE also gives SQLite expectations for the same demos; those are labelled "expected" wherever they appear on the site. See [Benchmarks](/reference/benchmarks).
:::

## What the five have in common

- Each one is a per-request or per-process decision that is cheap to write and expensive to run.
- Each one passes unit tests and a single-request smoke test.
- Each one is fixed by a small code change, and each fix comes with a number you can reproduce.

## How every pattern page is laid out

Every AP page uses the same sections, in the same order, so you can jump to what you need:

1. **In one sentence**: the whole idea in a single line.
2. **What goes wrong**: the mechanism, with a diagram or timeline.
3. **The bad code**: a real excerpt from the router, with the bad lines highlighted.
4. **The good code**: the matching excerpt.
5. **Try it**: commands and the expected output.
6. **Measured evidence**: the captured numbers, labelled with their environment.
7. **How to detect it**: a tool, a command, and what to look for in your own service.
8. **Checklist**: the matching items from the performance checklist.
9. **Talking points**: what to say, and what not to demo live.
10. **Related** and previous or next links.

## Suggested reading order

Read in order if you are new. The patterns build on each other:

1. **AP1** introduces what `async def` does and does not do.
2. **AP2** is about the objects you create once and share.
3. **AP3** is about what the ORM does when you touch data inside async code.
4. **AP4** is about the data you pass around once it has been loaded.
5. **AP5** is about the limit on how many database connections you can hold at once.

Then read the [performance checklist](/reference/checklist). It is the same five points in a form you can use on your own service.

## Related

- [Performance checklist](/reference/checklist)
- [Benchmarks](/reference/benchmarks)
- [Demo runbook](/demo/)
