---
title: Setup
description: Run the Orders API either with SQLite and no Docker, or with Docker and Postgres for the headline numbers. Includes the environment gotchas.
---

# Setup

::: tip In one sentence
Pick SQLite for the fastest start with no Docker, or Docker and Postgres to reproduce the captured headline numbers; both run the same code.
:::

You will run two processes: the **payment gateway** stand-in, and the **Orders API**. The Orders API calls the gateway in AP1 and AP2.

## Choose a mode

| | SQLite (no Docker) | Docker and Postgres |
|---|---|---|
| Database | `db/orders.db`, a local file | Postgres 16 in a container |
| Gateway | `mock_gateway/` (bundled) | `go-httpbin` in a container |
| Use it for | Trying every demo quickly | The numbers in the talk and [benchmarks](/reference/benchmarks) |
| Relative numbers | AP2 gap is smaller (about 4×) | AP2 gap is about 10× |

The SQLite gap is smaller because a new SQLite engine has no network handshake. See [Benchmarks](/reference/benchmarks) for the full explanation.

## Mode 1: SQLite, no Docker

Run these from `orders-api-demo/`. You need [uv](https://docs.astral.sh/uv/).

```bash
cd orders-api-demo
uv sync
uv run python scripts/seed_data.py     # creates db/orders.db
```

Seeding is idempotent. It prints "Data already seeded, skipping" on a second run. Delete `db/orders.db` to reseed. The seed creates 200 customers, 2000 orders, and about 6000 order items.

Start the two services in two terminals:

::: code-group

```bash [Terminal 1: gateway]
uv run uvicorn mock_gateway.main:app --port 8080
```

```bash [Terminal 2: Orders API]
uv run uvicorn app.main:app --port 8000
```

:::

Check both services:

```bash
curl localhost:8000/health    # {"status":"ok"}
curl localhost:8080/health    # {"status":"ok"}
```

Expected output:

```json
{"status":"ok"}
```

## Mode 2: Docker and Postgres

This mode matches the captured Postgres numbers. Docker and [uv](https://docs.astral.sh/uv/) are required.

```bash
cd orders-api-demo
cp .env.example .env
docker compose up -d          # postgres:16, go-httpbin gateway, and the app
uv sync                       # local venv for running scripts and tests on the host

DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" \
  uv run python scripts/seed_data.py

curl http://localhost:8000/health
curl "http://localhost:8000/orders?limit=5"
```

The compose file starts three services:

| Service | Image | Host port |
|---|---|---|
| `db` | `postgres:16` | 5432 |
| `payment-gateway` | `mccutchen/go-httpbin:v2.15.0` | 8080 |
| `app` | built from `orders-api-demo/Dockerfile` | 8000 |

Interactive API docs are at `http://localhost:8000/docs` once the app is running.

::: warning Docker-only commands
`scripts/profile_pyspy.sh` runs `docker compose exec`, so it only works in this mode. The flame graphs in `benchmarks/` were produced this way.
:::

## Configuration

Settings are read in `app/config.py` through `pydantic-settings`. Environment variables override `.env`.

| Variable | Default in code | `.env.example` | Meaning |
|---|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///<repo>/orders-api-demo/db/orders.db` | `postgresql+asyncpg://postgres:postgres@db:5432/orders` | SQLAlchemy URL |
| `PAYMENT_GATEWAY_URL` | `http://localhost:8080` | `http://payment-gateway:8080` | Base URL for the gateway |
| `POOL_MODE` | `good` | `good` | Pool profile, `bad` or `good`, read at process start |

The pool profiles are fixed in code:

| `POOL_MODE` | `pool_size` | `max_overflow` | `pool_timeout` | `pool_recycle` |
|---|---|---|---|---|
| `bad` | 5 | 10 | 2 s | -1 |
| `good` | 20 | 40 | 10 s | 1800 |

## Gotchas

These are the problems people hit first. Read them before you start.

::: danger PAYMENT_GATEWAY_URL points at the Docker hostname
If your `.env` contains `PAYMENT_GATEWAY_URL=http://payment-gateway:8080`, every `/demo/ap1/*` and `/demo/ap2/*` call returns HTTP 500 with `nodename nor servname provided` when you run locally. The hostname only resolves inside Docker.

**Fix:** for local runs, set `PAYMENT_GATEWAY_URL=http://localhost:8080` in `.env`, or prefix the command. Environment variables beat `.env`:

```bash
PAYMENT_GATEWAY_URL=http://localhost:8080 uv run uvicorn app.main:app --port 8000
```
:::

::: warning POOL_MODE is read once, at startup
`/demo/ap5/info` reports the pool that the process actually started with. If it says `bad` when you wanted `good`, the `.env` value won, or an earlier process is still running.

**Fix:** set the variable on the command and confirm:

```bash
POOL_MODE=good uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info
```
:::

::: warning DATABASE_URL pointing at db:5432 breaks SQLite
A `.env` with the Docker `DATABASE_URL` will not work outside Docker. Comment it out for SQLite; the default is `db/orders.db`.
:::

::: tip Port already in use
`Address already in use`, or strange 404s on port 8000, means another process owns the port.

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Stop that process, or run uvicorn on another port and adjust the URLs.
:::

`.env` is gitignored, so edit it freely for your machine.

## Verify the setup

Run the automated tests. They start the mock gateway themselves if nothing is listening on `PAYMENT_GATEWAY_URL`.

```bash
PAYMENT_GATEWAY_URL=http://localhost:8080 uv run pytest tests/ -v
```

Expected: **13 passed** (about 5 seconds). If your `.env` still has the Docker hostname, the export above overrides it.

Then run the first demo:

```bash
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bad & done; wait)
```

Expected: about **3.0 s** in the SQLite mode with the local gateway. The [AP1 page](/anti-patterns/ap1-blocking-event-loop) shows the captured Postgres run.

## Related

- [Architecture](/guide/architecture): what each file does
- [Baseline API](/guide/baseline-api): the correct endpoints, with curl examples
- [Running the demos](/demo/running-the-demos): every demo, in order
- [Troubleshooting](/demo/troubleshooting): what to do when something breaks
