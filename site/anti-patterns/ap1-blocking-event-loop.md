---
title: "AP1 — Blocking the event loop"
description: A synchronous HTTP call inside an async def route freezes the whole event loop. Bad and good code, timeline, measured evidence, and how to detect it.
---

# AP1 — Blocking the event loop

<Callout type="tip" title="In one sentence">
A synchronous call inside <code>async def</code> holds the single event-loop thread for its whole duration, so every other request waits, even though each call only takes one second.
</Callout>

## What goes wrong

FastAPI runs your `async def` routes on one event-loop thread. The loop switches between coroutines only at an `await`. A synchronous call such as `requests.get()` does not yield. It holds the thread until the gateway answers.

The Orders API calls a payment gateway, which is a slow I/O dependency. The demo gateway sleeps for one second on `/delay/1`. With three concurrent requests, the blocking version finishes them one after another. The async version overlaps them.

<Timeline
  :total="3"
  caption="Schematic. Each bar is one 1 s gateway call. Not to scale with the measured runs below."
  :rows="[
    { label: 'bad · request 1', start: 0, end: 1, tone: 'bad' },
    { label: 'bad · request 2', start: 1, end: 2, tone: 'bad' },
    { label: 'bad · request 3', start: 2, end: 3, tone: 'bad' },
    { label: 'good · request 1', start: 0, end: 1, tone: 'good' },
    { label: 'good · request 2', start: 0, end: 1, tone: 'good' },
    { label: 'good · request 3', start: 0, end: 1, tone: 'good' },
  ]"
/>

Blocking is invisible in unit tests and in a single `curl`. It only appears under concurrency, which is why it reaches production.

## The bad code

The `bad` route is `async def`, but it calls `requests`, which is synchronous. This excerpt is from `orders-api-demo/app/routers/demo_ap1.py`.

::: code-group

```python [app/routers/demo_ap1.py] {5}
@router.get("/bad")
async def blocking_call(request: Request) -> dict[str, str]:
    """`async def`, but `requests.get()` blocks the whole event loop for 1s."""
    settings = get_settings()
    resp = requests.get(f"{settings.payment_gateway_url}/delay/1", timeout=10)
    return {"gateway_status": str(resp.status_code), "mode": "bad-blocking-requests"}
```

:::

## The good code

The `good` route uses the shared `httpx.AsyncClient` from the lifespan and awaits it. The loop is free while the request is in flight.

::: code-group

```python [app/routers/demo_ap1.py] {6}
@router.get("/good")
async def async_call(request: Request) -> dict[str, str]:
    """Same call via the shared httpx.AsyncClient — yields the event loop while waiting."""
    client: httpx.AsyncClient = request.app.state.http_client
    settings = get_settings()
    resp = await client.get(f"{settings.payment_gateway_url}/delay/1")
    return {"gateway_status": str(resp.status_code), "mode": "good-httpx-async"}
```

:::

The `bridge` route keeps `requests` but moves it into `run_in_executor`. It is a migration bridge, not a fix. It still uses one thread-pool slot per call.

## Try it

Run these with the Orders API and the gateway running. See [Setup](/guide/setup).

::: code-group

```bash [bad]
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bad & done; wait)
```

```bash [good]
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/good & done; wait)
```

```bash [bridge]
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bridge & done; wait)
```

:::

**Expected** (Postgres capture, Docker gateway): `bad` about **3.0 s**, `good` about **1.0 s**, `bridge` about **1.0 s**.

For the most dramatic version, run `curl localhost:8000/demo/ap1/bad` in one terminal and `curl localhost:8000/health` in another right after. The health check waits until the bad call finishes. Repeat with `/good` and it answers at once.

## Measured evidence

<StatGrid>
<StatCard value="3.046 s" label="bad, 3 concurrent" sub="serialised" tone="bad" />
<StatCard value="1.040 s" label="good, 3 concurrent" sub="overlapping" tone="good" />
<StatCard value="1.039 s" label="bridge, 3 concurrent" sub="run_in_executor" tone="good" />
<StatCard value="Postgres capture" label="environment" sub="Docker gateway, go-httpbin" />
</StatGrid>

Captured output (`benchmarks/ap1-blocking/latency-3-concurrent.txt`):

```text
=== BAD (requests.get() inside async def) ===
real: 3.046s total   (~1s x 3, fully serialized — the event loop is blocked
                       for the duration of each synchronous call)

=== GOOD (httpx.AsyncClient) ===
real: 1.040s total   (~1s total — all 3 requests run concurrently)
```

asyncio's debug mode also flags the blocking call (`benchmarks/ap1-blocking/asyncio-debug.log`):

```text
WARNING:asyncio:Executing <Task ...> took 1.056 seconds
```

The `good` path produces no such warning.

::: details Flame graphs, bad vs good
<BadGood>
<template #bad>

![py-spy flame graph of the bad AP1 path, showing time spent in blocking requests calls](/assets/ap1-flamegraph-bad.svg)

Flame graph of the bad path, sampled with py-spy during concurrent requests (`talk/assets/ap1-flamegraph-bad.svg`). Open the SVG to zoom in.

</template>
<template #good>

![py-spy flame graph of the good AP1 path, showing time spent awaiting the async client](/assets/ap1-flamegraph-good.svg)

Flame graph of the good path, from the same kind of run (`talk/assets/ap1-flamegraph-good.svg`).

</template>
</BadGood>
:::

## How to detect it in your own service

| Tool | Command | What to look for |
|---|---|---|
| asyncio debug mode | `PYTHONASYNCIODEBUG=1 python app.py` | `Executing <Task ...> took X seconds` warnings |
| py-spy | `py-spy record --pid <PID> -o out.svg` under concurrent load | A wide synchronous HTTP or DB frame inside an `async` route |
| A health check | `curl /health` while a slow route runs | Health hangs, which means the loop is blocked |

Grep for the usual suspects inside `async def` functions: `requests.`, `time.sleep`, and synchronous file or database drivers.

## Checklist

<Checklist>
<ChecklistItem id="ap1-no-sync-io">No synchronous I/O (`requests`, blocking file or DB drivers, `time.sleep`) inside any `async def` route or dependency.</ChecklistItem>
<ChecklistItem id="ap1-bridge">If you must call a sync library you cannot replace yet, wrap it in `loop.run_in_executor(...)` as a migration bridge, not a permanent fix.</ChecklistItem>
<ChecklistItem id="ap1-verify">Verify with `py-spy record` under concurrent load, or `PYTHONASYNCIODEBUG=1` and watch for "Executing ... took X seconds" warnings.</ChecklistItem>
</Checklist>

## Talking points

- Total latency is the sum of all blocked calls. p99 collapses under concurrency even though each call "only" takes one second.
- `bridge` is a bridge, not a fix. It spends a thread-pool slot on every call.
- uvloop does not fix this. It makes the loop faster but cannot interrupt a blocking call. See the [FAQ](/reference/faq).
- Live, the bad run takes about 3 seconds. Narrate while it runs, so the room does not sit in silence.

## Related

- [Anti-pattern overview](/anti-patterns/)
- [Architecture: AP1 request flow](/guide/architecture#request-flow-for-ap1)
- [Benchmarks](/reference/benchmarks)
- [Running the demos: AP1](/demo/running-the-demos#ap1-blocking-the-event-loop)
