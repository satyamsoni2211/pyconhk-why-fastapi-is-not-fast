# Presenter guide — "Why Your FastAPI Is Not Fast"

PyCon Hong Kong 2026 · Software Engineering & Platforms track
**Sat 14 Nov 2026, 14:25–14:55 HKT** (30 minutes, holds per the acceptance
mail — confirm the exact time hasn't shifted before the day)

Repo: `orders-api-demo/` in this project. Slides: [`slides.md`](slides.md) /
[`slides.pdf`](slides.pdf).

---

## 1. Pre-talk checklist

Do this the night before AND again ~30 minutes before the slot.

- [ ] Laptop charged, charger packed. AV note from the proposal: HDMI
      connection, standard projector, no special room setup needed.
- [ ] `cd orders-api-demo && docker compose down -v && docker compose up -d`
      — fresh containers, no leftover state from testing.
- [ ] `DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/orders" uv run python scripts/seed_data.py`
- [ ] Confirm `POOL_MODE=good` is currently running (`curl localhost:8000/demo/ap5/info`) — you'll switch to `bad` live for AP5 and must switch back after, or before if you demo AP5 out of order.
- [ ] `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] Terminal font size bumped up (readable from the back of the room). Two terminal tabs ready: one for the app/curl commands, one held in reserve for `docker compose logs app -f` if you want to show a live traceback.
- [ ] Slides open in presenter mode if your setup supports it; otherwise `talk/slides.pdf` open and tested for full-screen.
- [ ] Wi-Fi/network: everything runs on `localhost` — confirm you do **not** need conference Wi-Fi for the demo itself (only for showing the GitHub repo URL, which can also just be a slide).
- [ ] Screen recording backup captured beforehand (see §3 fallback plan) and accessible offline.
- [ ] Timer visible to you (phone, watch, or conference timer) — 30 minutes is tight with 5 anti-patterns.

---

## 2. Timed narration script

Total: 30:00. Matches the slide deck order.

### 0:00–2:00 — Opening hook

> "A team I worked with rewrote a payment-adjacent service from Flask to
> FastAPI. Same logic, same team, same infra. `async def` everywhere. They
> expected it to be faster. Under real production load, it was **slower**
> than the Flask service it replaced.
>
> That's not a framework problem. FastAPI is fast — but it doesn't protect
> you from yourself. Today I'm going to show you five ways to shoot
> yourself in the foot with FastAPI, each with real code, real profiling
> output, and a measured fix — from a repo you can clone and run tonight."

Slide: title → hook slide.

### 2:00–5:00 — Framing

Keep this **short** — the sibling Software-track talk covers
tracing/observability, don't duplicate it. One idea only: `async def` is
not automatically non-blocking; it's *capable of* yielding, and only does
so at an `await`. Everything today lives inside that one sentence.

### 5:00–9:00 — AP1: Blocking the event loop

- Show the `bad` code slide (`requests.get()` inside `async def`).
- **LIVE DEMO** (see §3 runbook AP1). Run bad, then good, side by side.
- Narrate while the `bad` command is running (it takes ~3s — don't stand
  in silence): "Notice this isn't 3x slower per request — it's fully
  serialized. The whole event loop is stuck for each call."
- Show the asyncio-debug slide — "asyncio will tell you this for free."
- Land the fix: async-native client, or `run_in_executor` as a bridge.

### 9:00–13:00 — AP2: Dependency injection lifecycle

- Show the bad dependency code (new engine per request).
- State the number cold: "17.5 milliseconds average, versus 1.7. Ten
  times, just from rebuilding a connection pool you already had."
- Optionally live-run `uv run python scripts/bench_ap2_di.py` if time
  allows (~2s to run) — otherwise show the captured numbers slide.
- Land the fix: build once in the lifespan, `Annotated[T, Depends(...)]`.

### 13:00–17:00 — AP3: SQLAlchemy lazy loading

- **LIVE DEMO**: `curl` the `bad-crash` endpoint first — let the room see
  a real 500 with `MissingGreenlet` in it. This is usually the biggest
  laugh/gasp moment of the talk — don't rush it.
- Then `bad-n1` and `good` — point at the echo log query counts (6 vs 2).
- Land the fix: `selectinload`, and mention `lazy="raise"` as the belt-
  and-braces model-level option (don't demo it — it would break the other
  two endpoints on purpose).

### 17:00–21:00 — AP4: Pydantic overhead

- Show the redundant round-trip code — this is the one most people
  recognize from their own codebase ("oh, we have that").
- State the numbers: "~1.9x slower, ~1.8x more function calls — from
  validating the same data twice."
- Land the fix: `from_attributes=True`, and the "skip Pydantic entirely
  for internal-only data" point — this is the one people forget.

### 21:00–25:00 — AP5: Connection pool starvation

- This is the only anti-pattern that needs a **process restart** — set
  expectations: "this one I can't toggle live in one process, because
  pool size is fixed when the engine starts. I ran this exact load twice,
  once per config, and I'm showing you the real output."
- Show the captured locust numbers slide. Read the real traceback aloud —
  `QueuePool limit of size 5 overflow 10 reached, connection timed out`.
- Land the fix: size for real concurrency, not tutorial defaults.
- **Optional live variant** if you're ahead on time (see §3 AP5 runbook)
  — otherwise stick to the captured slide, it's already real data.

### 25:00–27:00 — Checklist + toolkit recap

- One breath per checklist item, pointing at the slide, not reading it.
- Toolkit table — "every one of these is free, open source, and you saw
  all five of them used for real today."

### 27:00–28:00 — Repo CTA

> "Everything you saw — every number — is in this repo. Clone it, run
> `docker compose up`, and reproduce every single measurement yourself.
> That's the point: none of this should be trust-me-bro."

### 28:00–30:00 — Q&A

See §4 for prepared answers.

---

## 3. Live-demo runbook

Run these from `orders-api-demo/` with the stack already up
(`docker compose up -d`). Each block: **command → expected output → what
to say if it doesn't match**.

### AP1 — blocking event loop

```bash
time (for i in 1 2 3; do curl -s -o /dev/null http://localhost:8000/demo/ap1/bad & done; wait)
```
Expected: `~3.0s` total.

```bash
time (for i in 1 2 3; do curl -s -o /dev/null http://localhost:8000/demo/ap1/good & done; wait)
```
Expected: `~1.0s` total.

**Fallback if the live numbers look off** (cold container, noisy laptop):
say "the exact number moves with the machine, but the shape doesn't — bad
is always ~3x, good is always ~1x" and point at the slide's captured
numbers (3.046s / 1.040s), which are the real ones from rehearsal.

### AP2 — DI lifecycle

```bash
uv run python scripts/bench_ap2_di.py
```
Expected: `bad` mean well above `good` mean (captured: 17.48ms vs 1.73ms).
Takes ~2s to run — fine to do live if AP1 ran on time.

**Fallback:** skip the live run, show the slide's captured table directly.

### AP3 — lazy loading

```bash
curl -s "http://localhost:8000/demo/ap3/bad-crash?limit=3" | python3 -m json.tool
```
Expected: `"error_type": "MissingGreenlet"` in the response.

```bash
curl -s "http://localhost:8000/demo/ap3/bad-n1?limit=5" | python3 -m json.tool
curl -s "http://localhost:8000/demo/ap3/good?limit=5" | python3 -m json.tool
```
Expected: identical `item_counts` arrays from both — the point is they
agree on the *answer*, only the query count differs (shown on slide, not
live — the echo log is verbose, don't run it on stage).

**Fallback:** the `bad-crash` JSON response is small and always reproduces
identically — this is the safest live demo in the whole talk. If networking
is somehow broken, `benchmarks/ap3-lazy-loading/missing-greenlet-response.json`
has the exact same captured output to screenshot/paste instead.

### AP4 — Pydantic overhead

Not recommended live (the difference is milliseconds, won't read on a
projector). Show the slide's captured cProfile numbers instead. If you
want a live moment anyway:

```bash
curl -s "http://localhost:8000/demo/ap4/bad?limit=200" | python3 -m json.tool
curl -s "http://localhost:8000/demo/ap4/good?limit=200" | python3 -m json.tool
```
Expected: `elapsed_seconds` field on `bad` roughly 2x `good`'s.

### AP5 — pool starvation (advanced/optional live variant)

Only attempt this if you're comfortably on schedule — it needs a container
restart mid-demo, which is the single riskiest live moment in the talk.
The safe default is the captured slide; this is the stretch goal.

```bash
POOL_MODE=bad docker compose up -d app && sleep 3
uv run locust --headless -u 100 -r 100 -t 15s --host http://localhost:8000 \
  --csv /tmp/live-bad -f scripts/locustfile.py
```
Expected: nonzero failure count, median latency in the seconds.

```bash
POOL_MODE=good docker compose up -d app && sleep 3
uv run locust --headless -u 100 -r 100 -t 15s --host http://localhost:8000 \
  --csv /tmp/live-good -f scripts/locustfile.py
```
Expected: 0 failures, much lower median latency.

**IMPORTANT — reset after, whether or not you do this live:**
```bash
POOL_MODE=good docker compose up -d app
```
Do this even if you skip the live variant entirely, in case a rehearsal
run left `POOL_MODE=bad` active.

**Fallback:** this is why the slide numbers exist — use them. Say "I've
run this exact load test twice already so I'm not gambling 90 seconds of
a 30-minute talk on a live load test" — that's a legitimate, honest thing
to say on stage, not a cop-out.

---

## 4. Anticipated Q&A

**"Why not just use Django/DRF, it doesn't have this async footgun?"**
Django's sync ORM has its own version of every one of these — N+1 is a
Django classic, and DRF serializers have their own overhead story. The
async-specific ones (AP1, AP3-crash) are FastAPI/async-ORM specific, but
AP2, AP4, AP5 exist in some form in any framework. The point isn't
"FastAPI bad" — it's "async gives you more rope, and rope needs handling."

**"Doesn't uvloop fix the blocking event-loop problem?"**
No — uvloop makes the *loop* faster, it doesn't change the fact that a
synchronous blocking call inside a coroutine can't be interrupted. Same
anti-pattern, same fix, uvloop or not.

**"Why not just increase workers instead of fixing the pool config?"**
You can trade some of this away with more Uvicorn/Gunicorn workers — but
each worker gets its *own* pool, so you're multiplying your Postgres
connection count by worker count. At some point Postgres's own
`max_connections` becomes the wall. Pool sizing and worker count are both
levers, not substitutes for each other.

**"Isn't `lazy='raise'` a breaking change to add to an existing model?"**
Yes — treat it like any other behavior change: add it in a branch, run
your test suite, see what lights up. That's the point — it turns silent
N+1s into loud failures *in your test suite*, not in production.

**"How does this relate to the other FastAPI talk on tracing/observability today?"**
That talk is about *finding* problems in a running system over time; this
one is about specific, reproducible code-level bugs and how to fix them.
Complementary, not overlapping — start with this repo's checklist, use
their tools once you're at a scale where you need continuous visibility.

**"Is Pydantic v1 affected the same way?"**
The specific overhead numbers are v2 (pydantic-core, much faster baseline)
— v1's absolute numbers are worse, but the *shape* of the anti-pattern
(redundant round-trips, deep validators) is identical.

**"What Python/FastAPI/SQLAlchemy versions was this tested on?"**
Check `orders-api-demo/pyproject.toml` for exact floors — worth restating
the versions live since minor-version behavior (e.g. SQLAlchemy's async
error messages) does shift.

---

## 5. If something breaks on stage

- **Docker won't start / container crashed**: don't debug live. Say the
  line from §3's AP5 fallback approach — pivot straight to the captured
  slide numbers for whichever anti-pattern you're on, and keep going.
  Every single number in the deck is already real, captured data; the
  live demo is bonus texture, not the argument.
- **Wrong `POOL_MODE` mid-AP5**: if you notice `bad` requests aren't
  failing, you're probably on `good` — `curl localhost:8000/demo/ap5/info`
  to check, fix, retry once, then move to the slide if it's still wrong.
  Don't burn more than ~20 seconds on this.
- **Running over time**: cut AP4's live curl (§3) first — it's the
  optional one. If still tight, compress AP2 to "here are the numbers"
  without narrating the bench script.
