---
title: Demo runbook
description: How to present or rehearse the five anti-pattern demos, including the 20-minute run of show, the rehearsal checklist, and a segment-by-segment timing table.
---

# Demo runbook

::: tip In one sentence
Run each anti-pattern once in the order below, with the services already up, and keep the captured numbers ready as a fallback for every live step.
:::

This runbook is for presenting or rehearsing the talk. The commands are repeated with expected output in [Running the demos](/demo/running-the-demos). If a live step misbehaves, see [Troubleshooting](/demo/troubleshooting).

## Before you start

<Checklist title="Rehearsal checklist">
<ChecklistItem id="demo-gateway-url">`PAYMENT_GATEWAY_URL` resolves locally for the mode you are running. For SQLite run, use `http://localhost:8080`. See the [gotchas](/guide/setup#gotchas).</ChecklistItem>
<ChecklistItem id="demo-both-up">Both services are up: the Orders API on port 8000 and the gateway on port 8080. `curl localhost:8000/health` returns `{"status":"ok"}`.</ChecklistItem>
<ChecklistItem id="demo-pool">`curl localhost:8000/demo/ap5/info` shows the pool mode you expect.</ChecklistItem>
<ChecklistItem id="demo-seeded">The database is seeded. `curl "localhost:8000/orders?limit=1"` returns rows.</ChecklistItem>
<ChecklistItem id="demo-warm">Each anti-pattern has been run once beforehand, so imports are warm and timings are clean.</ChecklistItem>
<ChecklistItem id="demo-fallback">The captured fallbacks are open: `benchmarks/*` and `talk/assets/*.svg`.</ChecklistItem>
</Checklist>

## Run of show: 20 minutes

The DEMO_GUIDE gives a 20-minute run of show. The talk itself is 30 minutes, with the rest of the time spent on framing, the checklist, and Q&A.

| Minutes | Segment | Action |
|---|---|---|
| 0 to 2 | Baseline | `make baseline`, and show `/docs` |
| 2 to 6 | AP1 | `make ap1`: three concurrent calls per endpoint, with the health-check probe. Then `make ap1-debug`. |
| 6 to 9 | AP2 | `make ap2-bench`. Say Postgres is about 10×. |
| 9 to 13 | AP3 | `make ap3-bad-crash` for the 500, then `make ap3-echo` for query counts |
| 13 to 16 | AP4 | `make ap4`, then the cProfile call counts (`make ap4-profile`) |
| 16 to 19 | AP5 | `make ap5-bad`, `make ap5-load`, `make ap5-good`, `make ap5-load`. Show the timeout traceback. |
| 19 to 20 | Wrap | The [performance checklist](/reference/checklist) |

## Talk timing: 30 minutes

The presenter guide paces the 30-minute slot in segments. The live demos sit inside these windows.

| Time | Segment | Live demo |
|---|---|---|
| 0:00 to 2:00 | Opening hook | None |
| 2:00 to 5:00 | Framing: what `async` buys you | None |
| 5:00 to 9:00 | AP1 | Bad and good, side by side |
| 9:00 to 13:00 | AP2 | Optional: `make ap2-bench` (about 2 s) |
| 13:00 to 17:00 | AP3 | `bad-crash` first, then `bad-n1` and `good` |
| 17:00 to 21:00 | AP4 | Not live. Show the captured cProfile. |
| 21:00 to 25:00 | AP5 | Captured slide by default. Live variant only if ahead on time. |
| 25:00 to 27:00 | Checklist and toolkit | None |
| 27:00 to 28:00 | Repo call to action | None |
| 28:00 to 30:00 | Q&A | None. See the [FAQ](/reference/faq). |

::: warning Cut order when running over time
Cut AP4's live `curl` first, since it is optional. If time is still tight, compress AP2 to "here are the numbers" without narrating the benchmark script.
:::

## The five demos at a glance

| Pattern | Live step | Fallback if the live step fails |
|---|---|---|
| [AP1](/anti-patterns/ap1-blocking-event-loop) | `make ap1-bad`, then `make ap1-good` | Captured 3.046 s and 1.040 s |
| [AP2](/anti-patterns/ap2-di-lifecycle) | `make ap2-bench` | Captured 17.48 ms and 1.73 ms table |
| [AP3](/anti-patterns/ap3-lazy-loading) | `make ap3-bad-crash` (500 response) | `missing-greenlet-response.json`, the safest demo |
| [AP4](/anti-patterns/ap4-pydantic-overhead) | Optional `make ap4` | Captured cProfile counts |
| [AP5](/anti-patterns/ap5-pool-starvation) | `make ap5-bad` / `make ap5-good`, optional | Captured locust tables and the traceback |

## Related

- [Running the demos](/demo/running-the-demos): commands and expected output for every step
- [Troubleshooting](/demo/troubleshooting): gotchas and what to do on stage
- [Setup](/guide/setup)
