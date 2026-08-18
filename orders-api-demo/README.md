# Orders API — FastAPI performance demo

Demo repository for the PyCon Hong Kong 2026 talk **"Why Your FastAPI Is
Not Fast: A Deep Dive into Hidden Bottlenecks"**.

A small, realistic "Orders API" (FastAPI + SQLAlchemy async + asyncpg +
PostgreSQL) intentionally implements all five anti-patterns from the talk,
each with a working "bad" and "good" endpoint pair on the same running
service, plus scripts that produce real, reproducible profiling and
benchmark output — nothing in this repo's numbers is invented; every figure
under `benchmarks/` was captured by actually running these scripts.

See [`CHECKLIST.md`](CHECKLIST.md) for the five-point performance checklist
this repo demonstrates.

## Quick start

Requires Docker and [uv](https://docs.astral.sh/uv/).

```bash
git clone <this-repo-url>
cd orders-api-demo
cp .env.example .env

docker compose up -d          # postgres + mock payment gateway + app
uv sync                       # local venv, for running scripts/tests on the host

DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" \
  uv run python scripts/seed_data.py

curl http://localhost:8000/health
curl http://localhost:8000/orders?limit=5
```

Interactive API docs: http://localhost:8000/docs

## Domain model

`Customer → Order → OrderItem`, seeded with 200 customers, 2000 orders, and
~6000 order items — enough volume that N+1 queries and pool exhaustion are
visible under realistic load, not just in theory.

## Baseline endpoints

Written the *correct* way from the start — these are what "good" looks
like in production, not part of the anti-pattern demo:

- `POST /orders` — create an order with items
- `GET /orders` — list recent orders
- `GET /orders/{id}` — order detail, eager-loaded

## The five anti-pattern demos

Each pair runs on the same live service — no restarts needed except AP5,
where the pool config is fixed at process start.

| # | Anti-pattern | Endpoints | Real captured evidence |
|---|---|---|---|
| 1 | Blocking the event loop | `GET /demo/ap1/{bad,good,bridge}` | [`benchmarks/ap1-blocking/`](benchmarks/ap1-blocking/) — 3.05s vs 1.04s (3 concurrent requests) |
| 2 | Dependency injection lifecycle | `GET /demo/ap2/{bad,good}` | [`benchmarks/ap2-di/`](benchmarks/ap2-di/) — ~10x latency overhead |
| 3 | SQLAlchemy lazy loading (async) | `GET /demo/ap3/{bad-crash,bad-n1,good}` | [`benchmarks/ap3-lazy-loading/`](benchmarks/ap3-lazy-loading/) — real `MissingGreenlet` crash + 6 vs 2 queries |
| 4 | Pydantic validation overhead | `GET /demo/ap4/{bad,good}` | [`benchmarks/ap4-pydantic/`](benchmarks/ap4-pydantic/) — ~1.9x slower, ~1.8x more function calls |
| 5 | Connection pool starvation | `GET /demo/ap5/query` (+ `POOL_MODE` env) | [`benchmarks/ap5-pool/`](benchmarks/ap5-pool/) — 2.1% failures @ 47.8 req/s vs 0% @ 179.3 req/s |

Try them yourself:

```bash
# AP1 — feel the difference under concurrency
time (for i in 1 2 3; do curl -s -o /dev/null http://localhost:8000/demo/ap1/bad & done; wait)
time (for i in 1 2 3; do curl -s -o /dev/null http://localhost:8000/demo/ap1/good & done; wait)

# AP3 — watch it crash for real
curl "http://localhost:8000/demo/ap3/bad-crash?limit=3"
```

## Reproducing every benchmark from scratch

```bash
docker compose up -d
uv sync

# AP1 — py-spy flame graphs + asyncio debug-mode warning
./scripts/profile_pyspy.sh bad flamegraph-bad.svg
./scripts/profile_pyspy.sh good flamegraph-good.svg
PAYMENT_GATEWAY_URL="http://localhost:8080" PYTHONASYNCIODEBUG=1 \
  uv run python scripts/asyncio_debug_demo.py

# AP2 — DI lifecycle latency
uv run python scripts/bench_ap2_di.py

# AP3 — SQL echo + query counts
SQLALCHEMY_WARN_20=1 PYTHONPATH=. \
  DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" \
  uv run python scripts/sqlalchemy_echo_demo.py

# AP4 — cProfile
PYTHONPATH=. DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" \
  uv run python scripts/pydantic_cprofile_demo.py

# AP5 — locust, bad config then good config
POOL_MODE=bad docker compose up -d app
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv benchmarks/ap5-pool/locust-bad -f scripts/locustfile.py

POOL_MODE=good docker compose up -d app
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv benchmarks/ap5-pool/locust-good -f scripts/locustfile.py
```

## Running the automated tests

Every anti-pattern also has a fast, deterministic pytest that asserts the
same behavior numerically on every run (not just a one-off capture):

```bash
docker compose up -d db payment-gateway
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" \
PAYMENT_GATEWAY_URL="http://localhost:8080" \
  uv run pytest tests/ -v
```

## Repo layout

```
app/
  main.py            FastAPI app + lifespan (shared engine/session/http-client singletons)
  config.py          Settings, including the bad/good pool profiles for AP5
  db.py               Async engine/session factories, get_session dependency
  models.py           Customer / Order / OrderItem (SQLAlchemy 2.0 async)
  schemas.py           Baseline API's Pydantic schemas
  schemas_ap4.py        AP4's bad/good transform functions + schemas
  clients.py            Shared httpx.AsyncClient dependency
  routers/
    orders.py            Baseline create/list/detail endpoints
    demo_ap1.py..demo_ap5.py   One router per anti-pattern
scripts/                  Seeding + every profiling/benchmark script
benchmarks/                One folder per anti-pattern with real captured output + README
tests/                      pytest suite, one file per anti-pattern
```

## Toolkit

py-spy, `asyncio` debug mode, cProfile + pstats, SQLAlchemy `echo`, locust —
see [`CHECKLIST.md`](CHECKLIST.md) for what each one is for.

## License

MIT — see [`LICENSE`](LICENSE).
