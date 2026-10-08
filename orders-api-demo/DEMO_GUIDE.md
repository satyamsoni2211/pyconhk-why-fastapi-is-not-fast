# Demo guide — running and presenting the five anti-patterns

How to run every demo in this repo, what to say, and what the audience
should see. Everything here works **without Docker** (SQLite + the bundled
mock payment gateway). Docker/Postgres notes are called out where numbers
differ.

Related docs: [`README.md`](README.md) (overview), [`CHECKLIST.md`](CHECKLIST.md)
(the five-point checklist), [`benchmarks/`](benchmarks/) (captured Postgres numbers).

---

## 0. One-time setup

```bash
cd orders-api-demo
uv sync
uv run python scripts/seed_data.py     # creates db/orders.db: 200 customers, 2000 orders, ~6000 items
```

Seeding is idempotent ("Data already seeded, skipping"). Delete `db/orders.db` to reseed.

### Start the two services (two terminals)

```bash
# Terminal 1 — mock payment gateway (stands in for go-httpbin)
uv run uvicorn mock_gateway.main:app --port 8080

# Terminal 2 — the Orders API
uv run uvicorn app.main:app --port 8000
```

Sanity check:

```bash
curl localhost:8000/health                  # {"status":"ok"}
curl localhost:8080/delay/1                 # returns after ~1s
```

Interactive docs (good for showing the endpoint list on a projector): <http://localhost:8000/docs>

### Gotchas before you go on stage

| Symptom | Cause | Fix |
|---|---|---|
| Every `/demo/ap1/*` and `/demo/ap2/*` call returns 500 (`nodename nor servname provided`) | `.env` has `PAYMENT_GATEWAY_URL=http://payment-gateway:8080` (the Docker hostname) | For local runs set `PAYMENT_GATEWAY_URL=http://localhost:8080` in `.env` (or prefix the uvicorn command with it). Env vars beat `.env`. |
| `/demo/ap5/info` says `pool_mode: bad` when you wanted `good` (or vice versa) | `.env` contains `POOL_MODE=…`, read at startup | Set it explicitly: `POOL_MODE=good uv run uvicorn …` (env var wins), then confirm with `/demo/ap5/info`. |
| `Address already in use` / strange 404s on `:8000` | Another process owns the port | `lsof -nP -iTCP:8000 -sTCP:LISTEN`, or use another port and adjust URLs. |
| `.env` has `DATABASE_URL` pointing at `db:5432` | Docker config | Leave it commented out for SQLite; the default is `db/orders.db`. |

Tip: `.env` is gitignored, so edit it freely for your machine.

---

## 1. The baseline API (2 minutes — set the scene)

These endpoints are written correctly; they are the "production-shaped" service the
anti-patterns are injected into. Domain: `Customer → Order → OrderItem`.

```bash
curl "localhost:8000/orders?limit=3"                      # list recent orders
ORDER=$(curl -s "localhost:8000/orders?limit=1" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
curl localhost:8000/orders/$ORDER                          # detail with items (selectinload)

CUSTOMER=$(curl -s "localhost:8000/orders?limit=1" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['customer_id'])")
curl -X POST localhost:8000/orders -H 'content-type: application/json' \
  -d "{\"customer_id\":\"$CUSTOMER\",\"items\":[{\"sku\":\"SKU-0001AB\",\"quantity\":2,\"unit_price\":9.5}]}"
```

**Say:** "Nothing here is slow. Now I'll show five ways teams accidentally make
this exact service slow — each one has a bad and a good endpoint on the same
running process."

---

## 2. AP1 — Blocking the event loop

**Code:** [`app/routers/demo_ap1.py`](app/routers/demo_ap1.py)
**Concept:** an `async def` route that calls a synchronous library (`requests`) freezes the
*entire* server for the duration of the call. The gateway call takes 1s (`/delay/1`).

| Endpoint | What it does |
|---|---|
| `/demo/ap1/bad` | `requests.get()` inside `async def` — blocks the loop |
| `/demo/ap1/good` | shared `httpx.AsyncClient`, `await`ed — loop stays free |
| `/demo/ap1/bridge` | keeps `requests` but runs it in `run_in_executor` (migration stopgap) |

### Run

```bash
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bad  & done; wait)
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/good & done; wait)
time (for i in 1 2 3; do curl -s -o /dev/null localhost:8000/demo/ap1/bridge & done; wait)
```

**Expected:** bad ≈ **3.0s** (requests serialised), good ≈ **1.0s**, bridge ≈ **1.0s**.

### Make it visible

- **Health check during the block** (most dramatic): in one terminal fire `curl localhost:8000/demo/ap1/bad`, and immediately in another run `curl localhost:8000/health`. The trivial health check hangs until the bad call finishes. Repeat with `/good` — health answers instantly.
- **asyncio debug mode** (no app needed, only the gateway):
  ```bash
  PYTHONASYNCIODEBUG=1 uv run python scripts/asyncio_debug_demo.py
  ```
  Prints `Executing <Task …> took 1.0xx seconds` for the BAD call and nothing for the GOOD one.
- **py-spy flame graph** (Docker only — the script uses `docker compose exec`):
  `./scripts/profile_pyspy.sh bad flamegraph-bad.svg`. Pre-captured graphs are in
  [`benchmarks/ap1-blocking/`](benchmarks/ap1-blocking/) and `talk/assets/` — open the SVGs instead if not on Docker.

### Talking points
- Total latency is the *sum* of all blocked calls, so p99 collapses under concurrency even though each call "only" takes 1s.
- It is invisible in unit tests and single-request curl; only concurrency exposes it.
- `bridge` is a bridge, not a fix — it burns a thread-pool slot per call.
- **Checklist item 1.**

---

## 3. AP2 — Dependency-injection lifecycle

**Code:** [`app/routers/demo_ap2.py`](app/routers/demo_ap2.py), singletons in [`app/main.py`](app/main.py) lifespan
**Concept:** expensive objects (DB engine + pool, HTTP client) must be created once in the
lifespan, not inside a `Depends` that runs on every request.

| Endpoint | What it does |
|---|---|
| `/demo/ap2/bad` | builds a new SQLAlchemy engine **and** a new httpx client per request, tears them down after |
| `/demo/ap2/good` | reuses the lifespan singletons via `Depends(get_session)` / `Depends(get_http_client)` |

### Run

```bash
curl localhost:8000/demo/ap2/bad     # {"mode":"bad-new-engine-and-client-per-request","elapsed_seconds":…}
curl localhost:8000/demo/ap2/good

BASE_URL=http://localhost:8000 uv run python scripts/bench_ap2_di.py   # 50 requests each, mean/p50/p95
```

**Expected (SQLite, local):** bad ≈ 5–6 ms vs good ≈ 1.3 ms mean (~4x).
**Expected (Postgres/Docker):** ~10x (17.5 ms vs 1.7 ms, see [`benchmarks/ap2-di/`](benchmarks/ap2-di/)) —
the gap is larger there because each fresh engine pays a real TCP + auth handshake. Say this
out loud; SQLite understates the problem.

### Talking points
- The per-request cost is constant overhead *and* it destroys connection reuse — under load you also leak/churn sockets and can exhaust the DB's `max_connections`.
- Fix pattern: create in `lifespan`, store on `app.state`, hand out via a `yield`/return dependency.
- **Checklist item 2.**

---

## 4. AP3 — SQLAlchemy lazy loading in async

**Code:** [`app/routers/demo_ap3.py`](app/routers/demo_ap3.py), model in [`app/models.py`](app/models.py)
**Concept:** `Order.items` is lazy by default. In async code that is either a crash or an N+1.

| Endpoint | Behaviour |
|---|---|
| `/demo/ap3/bad-crash` | plain `order.items` → **`MissingGreenlet`** (HTTP 500 with the real error) |
| `/demo/ap3/bad-n1` | `await order.awaitable_attrs.items` in a loop → works, one query **per order** |
| `/demo/ap3/good` | `selectinload(Order.items)` → one extra query total |

### Run

```bash
curl -i "localhost:8000/demo/ap3/bad-crash?limit=3"   # 500, error_type: MissingGreenlet
curl "localhost:8000/demo/ap3/bad-n1?limit=5"
curl "localhost:8000/demo/ap3/good?limit=5"           # same item_counts as bad-n1
```

### Make it visible — count the queries

```bash
PYTHONPATH=. uv run python scripts/sqlalchemy_echo_demo.py
```

Prints every SQL statement (`echo=True`) and ends with
`bad-n1 issued 6 queries, good issued 2 queries` for 5 orders (1 + N vs 1 + 1).
Scale it: `?limit=100` → 101 queries vs 2.

> The script uses `DATABASE_URL` if set, otherwise the app's configured database (SQLite by default).

### Talking points
- `bad-crash` is the *good* failure — it is loud. `bad-n1` is the dangerous one: correct output, silently slow, and each query is an `await` hop on the loop.
- Defensive option: `lazy="raise"` on the relationship so any accidental lazy touch fails in dev.
- **Checklist item 3.**

---

## 5. AP4 — Pydantic validation overhead

**Code:** [`app/routers/demo_ap4.py`](app/routers/demo_ap4.py), [`app/schemas_ap4.py`](app/schemas_ap4.py)
**Concept:** the "bad" transform builds a dict by hand, runs nested `field_validator`s, then
does `model_dump()` → `model_validate()` — validating everything twice. The "good" one uses
`from_attributes=True` once.

```bash
curl "localhost:8000/demo/ap4/bad?limit=500"
curl "localhost:8000/demo/ap4/good?limit=500"
```

Compare `elapsed_seconds` (only the transform is timed, not the DB fetch). Locally, bad is
roughly **2–2.7x** slower (e.g. 5.8 ms vs 2.9 ms at 500 orders).

### Make it visible — function-call counts

```bash
PYTHONPATH=. uv run python scripts/pydantic_cprofile_demo.py
```

Shows cProfile output for both: ~290k function calls (bad) vs ~111k (good), ≈ **2.6x** more
calls on SQLite data. Point at `bad_transform` vs `good_transform` cumulative time.
Captured Postgres run: [`benchmarks/ap4-pydantic/`](benchmarks/ap4-pydantic/) (~1.9x slower, ~1.8x calls).

### Talking points
- Pydantic v2 is fast, but "fast" × a redundant round-trip × thousands of rows is not free, and it is CPU on the event-loop thread.
- Measure *call counts*, not just wall time — they're stable across machines.
- For data that never crosses a boundary, skip Pydantic (`dataclass`/`TypedDict`).
- **Checklist item 4.**

---

## 6. AP5 — Connection-pool starvation

**Code:** [`app/routers/demo_ap5.py`](app/routers/demo_ap5.py), pool profiles in [`app/config.py`](app/config.py)
**Concept:** same code, same endpoint; only the pool config differs. The pool is fixed at
process start, so the demo **restarts the app** between runs instead of using a bad/good pair.

| `POOL_MODE` | pool_size | max_overflow | pool_timeout | total conns |
|---|---|---|---|---|
| `bad` | 5 | 10 | 2 s | 15 |
| `good` | 20 | 40 | 10 s | 60 |

`/demo/ap5/query` holds a pooled connection ~0.3 s (Postgres `pg_sleep`) / ~0.6 s (SQLite
`asyncio.sleep`, longer so starvation is reliable). `/demo/ap5/info` reports the active pool config.

### Run (restart between the two runs!)

```bash
# --- BAD ---
POOL_MODE=bad uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"bad"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv benchmarks/ap5-pool/locust-bad -f scripts/locustfile.py

# stop the app (Ctrl-C), then --- GOOD ---
POOL_MODE=good uv run uvicorn app.main:app --port 8000
curl localhost:8000/demo/ap5/info          # confirm "pool_mode":"good"
uv run locust --headless -u 100 -r 100 -t 20s --host http://localhost:8000 \
  --csv benchmarks/ap5-pool/locust-good -f scripts/locustfile.py
```

(The `--csv` flags overwrite the captured Postgres results in `benchmarks/ap5-pool/`; drop
them or point at another prefix like `/tmp/locust-bad` if you want to keep those.)

**Expected (SQLite, 100 users, 15 s):** bad ≈ **40–45 % failures**, ~43 req/s; good **0 %**, ~97 req/s.
**Captured (Postgres):** 2.1 % failures @ 47.8 req/s vs 0 % @ 179.3 req/s.

Interactive alternative: `uv run locust -f scripts/locustfile.py --host http://localhost:8000`
and open <http://localhost:8089> for live charts — good for a projector.

In the bad run the app log shows:
`sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 2.00`
(a saved example is in [`benchmarks/ap5-pool/pool-timeout-traceback.log`](benchmarks/ap5-pool/pool-timeout-traceback.log)).

### Talking points
- The bug is *invisible at low traffic*: one request works fine. It only appears at concurrency > pool capacity.
- Failures are timeouts waiting for a connection, not DB errors — the DB is idle while requests die.
- Size pools from real expected concurrency × hold time; make `pool_timeout` a deliberate choice.
- **Checklist item 5.**

---

## 7. Automated proof (optional closer)

Every anti-pattern has a deterministic pytest asserting the same behaviour. The suite starts
the mock gateway itself if nothing is listening on `PAYMENT_GATEWAY_URL`:

```bash
PAYMENT_GATEWAY_URL=http://localhost:8080 uv run pytest tests/ -v
```

Expect 13 passed (~5 s). If your `.env` still has the Docker hostname, export the variable as
above so it overrides it.

---

## 8. Suggested 20-minute run of show

| Min | Segment | Action |
|---|---|---|
| 0–2 | Baseline | Section 1; show `/docs` |
| 2–6 | AP1 | 3× concurrent bad vs good; health-check-hangs trick; asyncio debug output |
| 6–9 | AP2 | `bench_ap2_di.py`; mention Postgres is ~10x |
| 9–13 | AP3 | Show the 500, then query counts script |
| 13–16 | AP4 | `curl` both, then cProfile call counts |
| 16–19 | AP5 | Restart in `bad`, locust, restart in `good`, locust; show timeout traceback |
| 19–20 | Wrap | [`CHECKLIST.md`](CHECKLIST.md) |

**Rehearsal checklist**
- [ ] `PAYMENT_GATEWAY_URL` resolves locally (see gotchas) and both servers are up.
- [ ] `curl localhost:8000/demo/ap5/info` shows the mode you expect.
- [ ] DB seeded (`curl "localhost:8000/orders?limit=1"` returns rows).
- [ ] Run each AP once beforehand to warm imports so timings are clean.
- [ ] Have `benchmarks/*` and `talk/assets/*.svg` open as a fallback if live numbers misbehave.

## 9. Docker / Postgres mode (for the headline numbers)

```bash
cp .env.example .env          # DATABASE_URL=…@db:5432, PAYMENT_GATEWAY_URL=http://payment-gateway:8080
docker compose up -d
docker compose exec app uv run python scripts/seed_data.py
POOL_MODE=bad docker compose up -d app    # AP5: recreate the app with a different pool mode
```

Use this mode for AP2's ~10x gap, the py-spy flame graphs (`scripts/profile_pyspy.sh`), and
the Postgres AP5 numbers. The scripts under `scripts/` use `DATABASE_URL` if set, otherwise the app's configured database; from the host
use `DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders"`.
