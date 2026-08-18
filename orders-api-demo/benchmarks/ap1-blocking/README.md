# AP1 — Blocking the event loop: captured evidence

Endpoints: `GET /demo/ap1/bad` (`requests.get()` inside `async def`),
`GET /demo/ap1/good` (`httpx.AsyncClient`), `GET /demo/ap1/bridge`
(`run_in_executor` migration bridge). All three call `payment-gateway`'s
`/delay/1` (go-httpbin), standing in for a slow external payment API.

## Real measured latency, 3 concurrent requests

| Endpoint | Wall-clock (3 concurrent) | What it shows |
|---|---|---|
| `bad` | **3.046s** | Fully serialized — the sync call blocks the whole event loop each time |
| `good` | **1.040s** | Concurrent — all 3 requests overlap |
| `bridge` | **1.039s** | Concurrent — `run_in_executor` frees the loop too |

Full output: [`latency-3-concurrent.txt`](latency-3-concurrent.txt)
Reproduce: `docker compose up -d && ./scripts/profile_pyspy.sh bad` (see script for the raw curl loop)

## asyncio debug-mode slow-callback warning

Captured via `PYTHONASYNCIODEBUG=1 uv run python scripts/asyncio_debug_demo.py`:

```
WARNING:asyncio:Executing <Task ...> took 1.056 seconds
```

— logged only for the `bad` path. The `good` (httpx.AsyncClient) path produces
no warning at all, because it yields control back to the loop while waiting.
Full output: [`asyncio-debug.log`](asyncio-debug.log)

## py-spy flame graphs

[`flamegraph-bad.svg`](flamegraph-bad.svg) / [`flamegraph-good.svg`](flamegraph-good.svg)
— captured with `py-spy record --pid 1 --duration 5 --rate 200` against the
dockerized app process while firing concurrent requests at each endpoint.
Reproduce: `./scripts/profile_pyspy.sh <bad|good> <output.svg>`

## Automated regression test

[`tests/test_ap1_blocking.py`](../../tests/test_ap1_blocking.py) asserts the
same serialized-vs-concurrent behavior numerically on every test run, so this
isn't just a one-off demo capture.
