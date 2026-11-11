---
title: Running the demos
description: Commands and expected output for every anti-pattern demo, as make targets or plain curl, with the SQLite and Postgres expectations labelled.
---

# Running the demos

::: tip In one sentence
Start the services, then run each section's `make` target (or the plain curl commands) and compare the output with the expected values listed here.
:::

Assumes the services are running, as set up in [Setup](/guide/setup). Commands run from `orders-api-demo/`. Every "expected" value is labelled **Postgres capture** (committed output) or **expected, SQLite** (DEMO_GUIDE guidance, not a committed capture).

## Two ways to run each demo

Every section below has two tabs:

- **make**: one command per demo, from the `Makefile` in `orders-api-demo/`. The `make apN` targets call each endpoint through `scripts/demo_endpoints.py` and print bad and good results side by side. `make apN-<endpoint>` calls a single endpoint.
- **curl**: the raw requests, if you want the audience to see exactly what is sent.

Run `make` on its own to list every target. The ones used on this page:

| Demo | All endpoints | One endpoint | Profiling script |
|---|---|---|---|
| AP1 | `make ap1` | `make ap1-bad`, `ap1-good`, `ap1-bridge` | `make ap1-debug`, `make ap1-flamegraph` |
| AP2 | `make ap2` | `make ap2-bad`, `ap2-good` | `make ap2-bench` |
| AP3 | `make ap3` | `make ap3-bad-crash`, `ap3-bad-n1`, `ap3-good` | `make ap3-echo` |
| AP4 | `make ap4` | `make ap4-bad`, `ap4-good` | `make ap4-profile` |
| AP5 | `make ap5` | `make ap5-info`, `ap5-query` | `make ap5-bad`, `ap5-good`, `ap5-load`, `ap5-ui` |

## Baseline: set the scene

These endpoints are written correctly. Say so before you show the anti-patterns: "Nothing here is slow. Now I'll show five ways teams make this same service slow."

::: code-group

```bash [make]
make baseline
```

```bash [curl]
curl "localhost:8000/orders?limit=3"
ORDER=$(curl -s "localhost:8000/orders?limit=1" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
curl localhost:8000/orders/$ORDER
```

:::

More detail is on the [baseline API page](/guide/baseline-api).

## AP1: Blocking the event loop

Endpoints: `/demo/ap1/bad`, `/demo/ap1/good`, `/demo/ap1/bridge`. Each calls the gateway's `/delay/1`.

::: code-group

```bash [make]
make ap1          # all three, 3 concurrent requests each, plus a /health probe
make ap1-bad      # one endpoint: ap1-bad, ap1-good or ap1-bridge
```

```bash [curl]
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bad  & done; wait)
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/good & done; wait)
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bridge & done; wait)
```

:::

**Expected, Postgres capture:** bad about 3.05 s, good about 1.04 s, bridge about 1.04 s.
**Expected, SQLite:** bad about 3.0 s, good about 1.0 s, bridge about 1.0 s.

`make ap1` output looks like this. The `/health` column is the health-check trick: a trivial request waits for the blocking calls to finish.

```text
AP1: Blocking the event loop  (http://localhost:8000)
  GET /demo/ap1/bad                3 concurrent: total  3.06 s   /health answered in  2956.5 ms   status [200]
  GET /demo/ap1/good               3 concurrent: total  1.03 s   /health answered in     5.0 ms   status [200]
  GET /demo/ap1/bridge             3 concurrent: total  1.02 s   /health answered in     3.1 ms   status [200]
```

To show the health-check trick by hand, run `curl localhost:8000/demo/ap1/bad` in one terminal, and `curl localhost:8000/health` in another straight after. With `/good`, it answers at once.

asyncio debug mode needs only the gateway, not the app:

::: code-group

```bash [make]
make ap1-debug
```

```bash [uv]
PYTHONASYNCIODEBUG=1 uv run scripts/ap1_asyncio_debug.py
```

:::

It prints `Executing <Task name='bad_blocking_call' …> took 1.0xx seconds` under the BAD header, and nothing for the good call.

The py-spy flame graph needs Docker, because the script uses `docker compose exec`:

::: code-group

```bash [make]
make ap1-flamegraph MODE=bad
```

```bash [shell]
./scripts/ap1_pyspy_flamegraph.sh bad flamegraph-bad.svg
```

:::

Without Docker, open the captured SVGs in `talk/assets/` instead.

## AP2: DI lifecycle

Endpoints: `/demo/ap2/bad`, `/demo/ap2/good`.

::: code-group

```bash [make]
make ap2          # both, 20 requests each, server-side time
make ap2-bad      # one endpoint: ap2-bad or ap2-good
make ap2-bench    # 50 requests each, mean/p50/p95
```

```bash [curl]
curl localhost:8000/demo/ap2/bad     # {"mode":"bad-new-engine-and-client-per-request","elapsed_seconds":...}
curl localhost:8000/demo/ap2/good
uv run scripts/ap2_di_benchmark.py   # 50 requests each
```

:::

**Expected, Postgres capture:** bad mean 17.48 ms, good mean 1.73 ms, about 10×.
**Expected, SQLite:** bad about 5 to 6 ms, good about 1.3 ms, about 4×.

Say the Postgres gap out loud. SQLite understates the problem, because each fresh engine on Postgres pays a real TCP and authentication handshake.

## AP3: SQLAlchemy lazy loading

Endpoints: `/demo/ap3/bad-crash`, `/demo/ap3/bad-n1`, `/demo/ap3/good`.

::: code-group

```bash [make]
make ap3                # all three, limit=5
make ap3-bad-crash      # one endpoint: ap3-bad-crash, ap3-bad-n1 or ap3-good
```

```bash [curl]
curl -i "localhost:8000/demo/ap3/bad-crash?limit=3"   # 500, error_type: MissingGreenlet
curl "localhost:8000/demo/ap3/bad-n1?limit=5"
curl "localhost:8000/demo/ap3/good?limit=5"           # same item_counts as bad-n1
```

:::

**Expected:** the crash returns HTTP 500 with `"error_type": "MissingGreenlet"`. The other two return identical `item_counts`.

To count the queries, run the echo script. It prints every statement, so do not run it on stage:

::: code-group

```bash [make]
make ap3-echo
```

```bash [uv]
uv run scripts/ap3_sqlalchemy_echo.py
```

:::

**Expected** summary: `bad-n1 issued 6 queries, good issued 2 queries` for five orders. Scale with `?limit=100` to get 101 against 2.

The script uses the same database as the app: Postgres when `.env` points at Docker (it swaps the `db` hostname for `localhost`), otherwise the local SQLite file.

## AP4: Pydantic overhead

Endpoints: `/demo/ap4/bad`, `/demo/ap4/good`.

::: code-group

```bash [make]
make ap4          # both, limit=500, median of 5 runs
make ap4-bad      # one endpoint: ap4-bad or ap4-good
```

```bash [curl]
curl "localhost:8000/demo/ap4/bad?limit=500"
curl "localhost:8000/demo/ap4/good?limit=500"
```

:::

Compare `elapsed_seconds`. Only the transform is timed, not the fetch.

**Expected, SQLite:** bad is about 2 to 2.7× slower, for example 5.8 ms against 2.9 ms at 500 orders.

For function-call counts:

::: code-group

```bash [make]
make ap4-profile
```

```bash [uv]
uv run scripts/ap4_pydantic_cprofile.py
```

:::

**Expected, SQLite:** about 290k calls for bad and 111k for good, about 2.6×.
**Postgres capture:** 204,481 and 116,463 calls, about 1.8×.

The script rewrites `benchmarks/ap4-pydantic/cprofile-*.txt`. Run `git checkout benchmarks/ap4-pydantic` to restore the committed capture.

Not recommended live. Show the captured cProfile instead.

## AP5: Pool starvation

This one needs a restart between two runs, because the pool is fixed when the process starts. Full detail is on the [AP5 page](/anti-patterns/ap5-pool-starvation).

::: code-group

```bash [make (Docker)]
make ap5-bad       # restart the app with the small pool, then fire 200 requests at once
make ap5-load      # locust, 100 users for 20 s, CSV prefix my-run-bad
make ap5-good      # restart with the large pool, same burst
make ap5-load      # locust again, CSV prefix my-run-good
```

```bash [make (local)]
make run POOL_MODE=bad     # terminal 2: start the app with the small pool
make ap5 && make ap5-load  # terminal 3
# Ctrl-C the app, then:
make run POOL_MODE=good
make ap5 && make ap5-load
```

```bash [uv]
# --- BAD ---
POOL_MODE=bad uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"bad"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv my-run-bad -f scripts/ap5_locustfile.py

# stop the app (Ctrl-C), then --- GOOD ---
POOL_MODE=good uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"good"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv my-run-good -f scripts/ap5_locustfile.py
```

:::

The `--csv` prefixes write to the working directory. The committed captures in `benchmarks/ap5-pool/` stay untouched. Change the locust run with `make ap5-load USERS=50 DURATION=30s CSV=my-prefix`.

**Expected, Postgres capture:** bad 2.1% failures at 47.8 req/s, good 0% at 179.3 req/s.
**Expected, SQLite:** bad about 40 to 45% failures at about 43 req/s, good 0% at about 97 req/s.

The interactive alternative is `make ap5-ui` (or `uv run locust -f scripts/ap5_locustfile.py --host http://localhost:8000`), then open `http://localhost:8089` for live charts. That works well on a projector.

::: danger Reset after the run
Whether or not you did the live run, leave the stack on the good profile:

```bash
make ap5-good     # or: POOL_MODE=good docker compose up -d app
```

A rehearsal can leave `POOL_MODE=bad` active otherwise.
:::

## Automated proof (optional closer)

Every anti-pattern has a deterministic pytest. The suite starts the mock gateway itself if nothing listens on `PAYMENT_GATEWAY_URL`:

::: code-group

```bash [make]
make test
```

```bash [uv]
PAYMENT_GATEWAY_URL=http://localhost:8080 uv run pytest tests/ -v
```

:::

`make test` also points `DATABASE_URL` at `localhost:5432` when your `.env` is set up for Docker.

**Expected:** 13 passed, in about 5 seconds.

## Related

- [Demo runbook](/demo/)
- [Troubleshooting](/demo/troubleshooting)
- [Endpoints](/reference/endpoints)
