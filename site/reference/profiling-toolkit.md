---
title: Profiling toolkit
description: When and how to use py-spy, asyncio debug mode, cProfile, SQLAlchemy echo, and locust, with the commands and scripts this repo ships for each.
---

# Profiling toolkit

::: tip In one sentence
Every tool here is free and open source. Each answers one question: where the CPU goes, whether something blocks the loop, how many calls happen, how many queries run, or how the service behaves under load.
:::

## Pick the right tool

| Question | Tool | Covers |
|---|---|---|
| Where is CPU time spent in a running process? | [py-spy](#py-spy) | AP1 |
| Which call blocks the event loop? | [asyncio debug mode](#asyncio-debug-mode) | AP1 |
| How many function calls, and what costs the most? | [cProfile and pstats](#cprofile-and-pstats) | AP4 |
| How many SQL statements run per request? | [SQLAlchemy echo](#sqlalchemy-echo) | AP3 |
| How does the service behave under concurrent load? | [locust](#locust) | AP5 |

## py-spy

A sampling profiler. It attaches to a running process and records stacks without any code change, so it is safe for a service you do not own. The output is a flame graph.

```bash
py-spy record --pid <PID> -o out.svg
```

This repo wraps it for the Docker app container. The script fires concurrent requests while it records:

```bash
./scripts/profile_pyspy.sh bad flamegraph-bad.svg
./scripts/profile_pyspy.sh good flamegraph-good.svg
```

The script takes `<bad|good|bridge>`, an output name, and an optional concurrency (default 3). It needs Docker because it uses `docker compose exec`. The captured graphs are in `benchmarks/ap1-blocking/` and `talk/assets/`.

::: tip Flame graph reading
A wide block near the top of a stack is where time was spent. For AP1 you are looking for a synchronous HTTP call inside a coroutine frame.
:::

## asyncio debug mode

Run with `PYTHONASYNCIODEBUG=1`. asyncio logs any task that holds the loop longer than its slow-callback threshold. It names the task and prints the time taken, which is the simplest way to find a blocking call.

```bash
PYTHONASYNCIODEBUG=1 uv run python scripts/asyncio_debug_demo.py
```

The script calls the gateway through both the bad and the good path. The bad path produces the warning and the good path does not.

```text
WARNING:asyncio:Executing <Task ...> took 1.056 seconds
```

Debug mode slows the loop down. Use it to find problems, not to measure them.

## cProfile and pstats

The standard-library deterministic profiler. It counts every function call, so it is a good measure of CPU work that does not depend on the machine. Read the function-call count first, then the cumulative time.

```bash
python -m cProfile -o out.prof script.py
```

This repo's script profiles the AP4 transforms over real seeded orders:

```bash
PYTHONPATH=. uv run python scripts/pydantic_cprofile_demo.py
```

To read a saved profile:

```bash
python -c "import pstats; pstats.Stats('out.prof').sort_stats('cumulative').print_stats(10)"
```

## SQLAlchemy echo

`echo=True` prints every SQL statement the engine runs. Counting the lines gives the query count, which is the fastest way to see N+1.

```python
create_async_engine(url, echo=True)
```

This repo's script runs the AP3 bad and good paths against the same data and prints the counts:

```bash
SQLALCHEMY_WARN_20=1 PYTHONPATH=. uv run python scripts/sqlalchemy_echo_demo.py
```

The log is verbose. Use it to count, not to present live. In a test, a `before_cursor_execute` listener counts queries without printing them. The repo's AP3 test does this.

## locust

A load-testing tool written in Python. It drives many concurrent users against the service and reports failures, throughput, and latency percentiles. It is the only tool here that tests the whole system, including the pool.

```bash
locust --headless -u 50 -r 10 -t 30s \
  --host http://localhost:8000 \
  --csv my-run -f scripts/locustfile.py
```

The repo's `scripts/locustfile.py` targets `/demo/ap5/query`. The `--csv` prefix writes stats, stats history, failures, and exceptions files. For interactive runs, omit `--headless` and open the web UI on port 8089.

::: info Restart between pool profiles
The AP5 pool is fixed when the process starts. Restart the app with `POOL_MODE=bad` and then `POOL_MODE=good`, running locust against each. See [AP5](/anti-patterns/ap5-pool-starvation).
:::

## Seeding the database

The profiling scripts need data. `scripts/seed_data.py` creates 200 customers, 2000 orders, and about 6000 order items. It is idempotent.

```bash
uv run python scripts/seed_data.py
```

## Related

- [Performance checklist](/reference/checklist): the toolkit table in context
- [Benchmarks](/reference/benchmarks): the captured output these tools produced
- [Glossary](/reference/glossary)
