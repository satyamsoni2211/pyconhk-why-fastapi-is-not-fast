# Reader's Guide — "Why Your FastAPI Is Not Fast"

Welcome! This repository backs the PyCon Hong Kong 2026 talk **"Why Your
FastAPI Is Not Fast: A Deep Dive into Hidden Bottlenecks"** by Satyam Soni.
This guide tells you where everything lives, in what order to read it, and
how to get the most out of it — whether you have five minutes or a full
evening.

---

## The big picture

The repo has three layers, and everything else hangs off them:

| Path | What it is |
|---|---|
| `pycon_hk_2026_fastapi_proposal.md` | The full talk proposal — abstract, outline, and the "why" behind each anti-pattern. Best single-file overview of the talk's argument. |
| `talk/` | The presentation itself: Marp slides (`slides.md`), a rendered `slides.pdf`, a minute-by-minute `PRESENTER_GUIDE.md`, and flame-graph assets. |
| `orders-api-demo/` | The heart of the repo: a runnable FastAPI + SQLAlchemy async + PostgreSQL "Orders API" that deliberately implements all **five anti-patterns**, each with a `bad`/`good` endpoint pair and real captured benchmark evidence. |

The five anti-patterns (AP1–AP5), which structure everything:

1. **AP1 — Blocking the event loop**: sync I/O inside `async def`
2. **AP2 — DI lifecycle misuse**: rebuilding engines/clients per request
3. **AP3 — SQLAlchemy lazy loading in async**: `MissingGreenlet` crashes and silent N+1
4. **AP4 — Pydantic overhead**: redundant validate → dump round-trips
5. **AP5 — Connection pool starvation**: tutorial pool defaults under real load

You will see `ap1` … `ap5` used consistently across routers, tests, scripts,
and benchmark folders — once you know the code, everything cross-references.

---

## If you have 5 minutes

1. Read `orders-api-demo/CHECKLIST.md` — the five-point performance
   checklist with the headline before/after numbers and the profiling
   toolkit table. It is the distilled takeaway of the whole talk.
2. Skim `talk/slides.pdf` for the visuals and measured results.

## If you have 30 minutes

1. Read `orders-api-demo/README.md` top to bottom — it explains the domain
   model, the endpoint pairs, and how every benchmark was captured.
2. For each anti-pattern, open the matching pair side by side:
   - the router: `orders-api-demo/app/routers/demo_apN.py`
   - the evidence: `orders-api-demo/benchmarks/apN-*/README.md`
   Each benchmark README explains what was run, shows the real captured
   output (latency logs, SQL echo logs, cProfile dumps, locust CSVs,
   flame-graph SVGs), and interprets it.

## If you have an evening — run it yourself

Everything is reproducible. You need Docker and [uv](https://docs.astral.sh/uv/).

```bash
cd orders-api-demo
cp .env.example .env
docker compose up -d        # postgres + mock payment gateway + app
uv sync
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" \
  uv run python scripts/seed_data.py
curl http://localhost:8000/health
```

Then feel AP1 for yourself:

```bash
time (for i in 1 2 3; do curl -s -o /dev/null http://localhost:8000/demo/ap1/bad & done; wait)   # ~3.0s
time (for i in 1 2 3; do curl -s -o /dev/null http://localhost:8000/demo/ap1/good & done; wait)  # ~1.0s
```

…and watch AP3 crash for real:

```bash
curl "http://localhost:8000/demo/ap3/bad-crash?limit=3"   # MissingGreenlet
```

The README's "Reproducing every benchmark from scratch" section has the
exact commands for all five, including the py-spy flame graphs and the
locust pool-starvation runs (AP5 is the only one that needs an app restart,
via the `POOL_MODE` env var). Interactive API docs live at
`http://localhost:8000/docs`.

---

## Map of `orders-api-demo/`

```
app/
  main.py            App + lifespan — the GOOD pattern: shared engine/client singletons
  config.py          Settings, incl. the bad/good pool profiles for AP5
  db.py              Async engine/session factories + get_session dependency
  models.py          Customer → Order → OrderItem (SQLAlchemy 2.0 async)
  schemas.py         Baseline Pydantic schemas
  schemas_ap4.py     AP4's bad/good transform functions
  routers/
    orders.py        Baseline endpoints, written correctly — the reference
    demo_ap1..ap5.py One router per anti-pattern, bad/good pairs side by side
scripts/             Seeding + every profiling/benchmark script (one per AP)
benchmarks/          One folder per AP: real captured output + explanatory README
tests/               pytest suite — asserts each anti-pattern's behavior numerically
```

Reading tips:

- **Start with `app/routers/orders.py`** to see what "good" looks like as a
  baseline, then read each `demo_apN.py` to see how the bad variant differs —
  usually by only a line or two, which is exactly the point.
- **The benchmark folders are primary sources, not summaries.** Files like
  `ap1-blocking/latency-3-concurrent.txt`, `ap3-lazy-loading/echo-bad.log`,
  `ap4-pydantic/cprofile-bad.txt`, and the AP5 locust CSVs are the actual
  captured output the talk's numbers come from. Nothing is invented.
- **The tests double as documentation.** Each `tests/test_apN_*.py` asserts
  the anti-pattern numerically (e.g. query counts, latency ratios), so if
  you're unsure what a demo is supposed to prove, the test says it precisely.
- **`docs/superpowers/`** holds the design/plan documents used while building
  the repo — useful if you're curious about the construction process, safe to
  skip otherwise.

## Map of `talk/`

- `slides.md` — Marp source; `build.sh` renders it; `slides.pdf` is the
  rendered deck.
- `PRESENTER_GUIDE.md` — minute-by-minute run sheet, demo commands, and
  fallback plans; read this if you want to see how the 30 minutes are paced.
- `assets/` — the py-spy flame graphs (bad vs good) used on the AP1 slides;
  the same SVGs live in `benchmarks/ap1-blocking/`.

---

## Headline numbers (all captured, all reproducible)

| AP | Measured result |
|---|---|
| 1 | 3 concurrent requests: **3.05s** blocking vs **1.04s** async |
| 2 | Per-request engine: **17.5ms** mean vs **1.7ms** shared (~10×) |
| 3 | 5 orders: **6 queries** (lazy loop) vs **2** (`selectinload`); plus a real `MissingGreenlet` crash |
| 4 | Double validation: **~1.9× slower**, ~1.8× more function calls |
| 5 | 100 locust users: **2.1% failures @ 47.8 req/s** (default pool) vs **0% @ 179.3 req/s** (tuned) |

If you take one file away from this repo, make it `CHECKLIST.md` — run your
own FastAPI service through those five checks before you trust it under
real concurrency.
