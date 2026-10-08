---
title: Running the demos
description: Commands and expected output for every anti-pattern demo, condensed from DEMO_GUIDE.md, with the SQLite and Postgres expectations labelled.
---

# Running the demos

::: tip In one sentence
Start the two services, then run each section's commands and compare the output with the expected values listed here.
:::

Assumes the services are running, as set up in [Setup](/guide/setup). Commands run from `orders-api-demo/` unless noted. Every "expected" value is labelled **Postgres capture** (committed output) or **expected, SQLite** (DEMO_GUIDE guidance, not a committed capture).

## Baseline: set the scene

These endpoints are written correctly. Say so before you show the anti-patterns: "Nothing here is slow. Now I'll show five ways teams make this same service slow."

```bash
curl "localhost:8000/orders?limit=3"
ORDER=$(curl -s "localhost:8000/orders?limit=1" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
curl localhost:8000/orders/$ORDER
```

More detail is on the [baseline API page](/guide/baseline-api).

## AP1: Blocking the event loop

Endpoints: `/demo/ap1/bad`, `/demo/ap1/good`, `/demo/ap1/bridge`. Each calls the gateway's `/delay/1`.

```bash
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bad  & done; wait)
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/good & done; wait)
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bridge & done; wait)
```

**Expected, Postgres capture:** bad about 3.05 s, good about 1.04 s, bridge about 1.04 s.
**Expected, SQLite:** bad about 3.0 s, good about 1.0 s, bridge about 1.0 s.

Make it visible with the health check. Run `curl localhost:8000/demo/ap1/bad` in one terminal, and `curl localhost:8000/health` in another straight after. The health check waits for the bad call to finish. With `/good`, it answers at once.

asyncio debug mode needs only the gateway, not the app:

```bash
PYTHONASYNCIODEBUG=1 uv run python scripts/asyncio_debug_demo.py
```

It prints `Executing <Task …> took 1.0xx seconds` for the bad call, and nothing for the good one.

The py-spy flame graph needs Docker, because the script uses `docker compose exec`:

```bash
./scripts/profile_pyspy.sh bad flamegraph-bad.svg
```

Without Docker, open the captured SVGs in `talk/assets/` instead.

## AP2: DI lifecycle

Endpoints: `/demo/ap2/bad`, `/demo/ap2/good`.

```bash
curl localhost:8000/demo/ap2/bad     # {"mode":"bad-new-engine-and-client-per-request","elapsed_seconds":...}
curl localhost:8000/demo/ap2/good
BASE_URL=http://localhost:8000 uv run python scripts/bench_ap2_di.py   # 50 requests each
```

**Expected, Postgres capture:** bad mean 17.48 ms, good mean 1.73 ms, about 10×.
**Expected, SQLite:** bad about 5 to 6 ms, good about 1.3 ms, about 4×.

Say the Postgres gap out loud. SQLite understates the problem, because each fresh engine on Postgres pays a real TCP and authentication handshake.

## AP3: SQLAlchemy lazy loading

Endpoints: `/demo/ap3/bad-crash`, `/demo/ap3/bad-n1`, `/demo/ap3/good`.

```bash
curl -i "localhost:8000/demo/ap3/bad-crash?limit=3"   # 500, error_type: MissingGreenlet
curl "localhost:8000/demo/ap3/bad-n1?limit=5"
curl "localhost:8000/demo/ap3/good?limit=5"           # same item_counts as bad-n1
```

**Expected:** the crash returns HTTP 500 with `"error_type": "MissingGreenlet"`. The other two return identical `item_counts`.

To count the queries, run the echo script. It prints every statement, so do not run it on stage:

```bash
SQLALCHEMY_WARN_20=1 PYTHONPATH=. \
  DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" \
  uv run python scripts/sqlalchemy_echo_demo.py
```

**Expected** summary: `bad-n1 issued 6 queries, good issued 2 queries` for five orders. Scale with `?limit=100` to get 101 against 2.

Without Postgres, drop the `DATABASE_URL` line. The script then uses the app's configured SQLite database.

## AP4: Pydantic overhead

Endpoints: `/demo/ap4/bad`, `/demo/ap4/good`.

```bash
curl "localhost:8000/demo/ap4/bad?limit=500"
curl "localhost:8000/demo/ap4/good?limit=500"
```

Compare `elapsed_seconds`. Only the transform is timed, not the fetch.

**Expected, SQLite:** bad is about 2 to 2.7× slower, for example 5.8 ms against 2.9 ms at 500 orders.

For function-call counts:

```bash
PYTHONPATH=. uv run python scripts/pydantic_cprofile_demo.py
```

**Expected, SQLite:** about 290k calls for bad and 111k for good, about 2.6×.
**Postgres capture:** 204,481 and 116,463 calls, about 1.8×.

Not recommended live. Show the captured cProfile instead.

## AP5: Pool starvation

This one needs a restart between two runs, because the pool is fixed when the process starts. Full detail is on the [AP5 page](/anti-patterns/ap5-pool-starvation).

```bash
# --- BAD ---
POOL_MODE=bad uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"bad"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv my-run-bad -f scripts/locustfile.py

# stop the app (Ctrl-C), then --- GOOD ---
POOL_MODE=good uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"good"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv my-run-good -f scripts/locustfile.py
```

The `--csv` prefixes write to the working directory. The committed captures in `benchmarks/ap5-pool/` stay untouched.

**Expected, Postgres capture:** bad 2.1% failures at 47.8 req/s, good 0% at 179.3 req/s.
**Expected, SQLite:** bad about 40 to 45% failures at about 43 req/s, good 0% at about 97 req/s.

The interactive alternative is `uv run locust -f scripts/locustfile.py --host http://localhost:8000`, then open `http://localhost:8089` for live charts. That works well on a projector.

::: danger Reset after the run
Whether or not you did the live run, leave the stack on the good profile:

```bash
POOL_MODE=good docker compose up -d app
```

A rehearsal can leave `POOL_MODE=bad` active otherwise.
:::

## Automated proof (optional closer)

Every anti-pattern has a deterministic pytest. The suite starts the mock gateway itself if nothing listens on `PAYMENT_GATEWAY_URL`:

```bash
PAYMENT_GATEWAY_URL=http://localhost:8080 uv run pytest tests/ -v
```

**Expected:** 13 passed, in about 5 seconds.

## Related

- [Demo runbook](/demo/)
- [Troubleshooting](/demo/troubleshooting)
- [Endpoints](/reference/endpoints)
