---
title: Start here
description: What the workshop is, who it is for, what you need, and how to use this documentation site.
---

# Start here

::: tip In one sentence
This is a hands-on workshop on five ways a FastAPI service becomes slow in ways that only show up under real concurrency, each with a runnable bad and good version and measured evidence.
:::

The site accompanies the PyCon Hong Kong 2026 talk **"Why Your FastAPI Is Not Fast: A Deep Dive into Hidden Bottlenecks"**. The talk is about what happens *inside* your route handlers and dependencies. Each claim is backed by code you can run and by output captured from real runs.

## What the workshop is

The core is a small "Orders API" built with FastAPI, SQLAlchemy 2.0 async, and a payment gateway stand-in. It implements five anti-patterns on purpose:

| # | Anti-pattern | The symptom |
|---|---|---|
| AP1 | Blocking the event loop | Concurrent requests run one after another |
| AP2 | Dependency-injection lifecycle misuse | Every request pays for a new engine and client |
| AP3 | SQLAlchemy lazy loading in async | A crash, or one query per row (N+1) |
| AP4 | Pydantic validation overhead | The same data is validated twice |
| AP5 | Connection pool starvation | Requests time out waiting for a connection |

Each anti-pattern has a `bad` and a `good` endpoint on the same live service, so you can compare them without restarting anything. The exception is AP5, where the pool size is fixed when the process starts.

## Who it is for

- Python engineers who run FastAPI in production or are about to.
- Anyone who has seen a "fast" async service behave badly under load and wants to know why.
- Presenters who want a reproducible demo for their own team.

You do not need prior async expertise, but you should be comfortable reading Python and running a shell command.

## What you need

| Requirement | Needed for |
|---|---|
| Python 3.12 or newer | The Orders API (`requires-python` in `orders-api-demo/pyproject.toml`) |
| [uv](https://docs.astral.sh/uv/) | Installing dependencies and running scripts |
| Docker | Only the Postgres mode, which produces the headline numbers |
| `curl` | Trying the endpoints |

The SQLite mode needs no Docker. See [Setup](/guide/setup).

## How to use this site

- **Guide**: this section. Setup, architecture, and the baseline API.
- **[Anti-patterns](/anti-patterns/)**: one page per pattern, in the same order each time: the summary, what goes wrong, the bad code, the good code, how to try it, the measured evidence, how to detect it, a checklist, and talking points.
- **[Demo](/demo/)**: the runbook for presenting or rehearsing the talk, with commands, expected output, and what to do when something breaks.
- **[Reference](/reference/checklist)**: the checklist, every captured benchmark, profiling tools, endpoints, FAQ, and glossary.

Use the search box in the top bar to find any endpoint, command, or term.

::: info Numbers come from two environments
Every measured number on this site is labelled with where it came from. **Postgres capture** means the committed output from the Docker setup, which the talk uses. **SQLite local** means a run on a laptop with the SQLite default. The two differ, and the page explains why. See [Benchmarks](/reference/benchmarks).
:::

## Choose your path

- **5 minutes**: read the [performance checklist](/reference/checklist).
- **30 minutes**: read the [anti-pattern pages](/anti-patterns/), comparing bad and good code.
- **An evening**: follow [Setup](/guide/setup), then [Running the demos](/demo/running-the-demos).

## Repository map

The repository has three layers. This site documents the third one, and links into the other two.

| Path | What it is |
|---|---|
| `orders-api-demo/` | The runnable FastAPI Orders API, tests, benchmark captures, and scripts |
| `talk/` | Slides (`slides.md`, `slides.pdf`), the presenter guide, and flame-graph assets |
| `site/` | This documentation site |

## Related

- [Setup](/guide/setup): install, run, and verify
- [Architecture](/guide/architecture): the domain model and how the pairs are wired
- [Anti-pattern overview](/anti-patterns/)
- [About the talk](/about)
