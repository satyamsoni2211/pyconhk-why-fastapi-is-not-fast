---
title: Benchmarks
description: Every captured number from the talk in one table, with the methodology, the SQLite-versus-Postgres explanation, and links to the raw files.
---

# Benchmarks

::: tip In one sentence
The headline numbers come from a Postgres run, committed in `orders-api-demo/benchmarks/`. The SQLite numbers are a laptop run for convenience, and the two differ on purpose.
:::

## Consolidated table

Each row names its environment. **Postgres capture** is the committed output from the Docker setup. **SQLite local** is the laptop default, and where a number is guidance rather than a committed file, it is marked *expected*.

| Pattern | Metric | Bad | Good | Ratio | Environment | Source |
|---|---|---|---|---|---|---|
| AP1 | Wall clock, 3 concurrent requests | 3.046 s | 1.040 s | about 2.9× | Postgres capture | `ap1-blocking/latency-3-concurrent.txt` |
| AP1 | Wall clock, bridge (`run_in_executor`) | n/a | 1.039 s | n/a | Postgres capture | `ap1-blocking/latency-3-concurrent.txt` |
| AP1 | Wall clock, 3 concurrent requests | about 3.0 s | about 1.0 s | about 3× | SQLite, expected | DEMO_GUIDE |
| AP2 | Mean latency, 50 sequential requests | 17.48 ms | 1.73 ms | about 10× | Postgres capture | `ap2-di/latency-report.txt` |
| AP2 | Mean latency | about 5 to 6 ms | about 1.3 ms | about 4× | SQLite, expected | DEMO_GUIDE |
| AP3 | Queries for 5 orders, `echo=True` | 6 | 2 | 3× | Postgres capture | `ap3-lazy-loading/echo-bad.log`, `echo-good.log` |
| AP3 | Crash on plain attribute access | `MissingGreenlet`, HTTP 500 | n/a | n/a | Postgres capture | `ap3-lazy-loading/missing-greenlet-response.json` |
| AP4 | cProfile total time, 200 orders × 20 | 0.056 s | 0.030 s | about 1.9× | Postgres capture | `ap4-pydantic/cprofile-bad.txt`, `cprofile-good.txt` |
| AP4 | Function calls, same run | 204,481 | 116,463 | about 1.8× | Postgres capture | same |
| AP4 | Function calls | about 290k | about 111k | about 2.6× | SQLite local | working-tree capture, see note |
| AP5 | Failure rate, locust 100 users, 20 s | 2.1% (19 of 905) | 0% (0 of 3370) | n/a | Postgres capture | `ap5-pool/locust-bad_stats.csv`, `locust-good_stats.csv` |
| AP5 | Throughput | 47.8 req/s | 179.3 req/s | 3.75× | Postgres capture | same |
| AP5 | Median latency | 2200 ms | 530 ms | about 4.2× | Postgres capture | same |
| AP5 | Failure rate and throughput | about 40 to 45%, about 43 req/s | 0%, about 97 req/s | n/a | SQLite, expected | DEMO_GUIDE |

Ratios are computed from the values shown: AP2 is 17.48 ÷ 1.73, AP5 throughput is 179.3 ÷ 47.8, and so on.

## Methodology

| Pattern | How the number was produced |
|---|---|
| AP1 | Three concurrent `curl` requests to each endpoint, timed with `time`, against the dockerized app and the go-httpbin gateway. The gateway's `/delay/1` takes one second. |
| AP1 (asyncio) | `PYTHONASYNCIODEBUG=1` with `scripts/asyncio_debug_demo.py`. The log records the slow callback warning. |
| AP2 | `scripts/bench_ap2_di.py`: 50 sequential requests to each endpoint, reporting mean, p50 and p95 |
| AP3 | `scripts/sqlalchemy_echo_demo.py` with `echo=True`, counting statements for 5 orders. The test suite checks the same counts with a `before_cursor_execute` listener. |
| AP4 | `scripts/pydantic_cprofile_demo.py`: cProfile over 200 orders, repeated 20 times. Call counts are the stable comparison. |
| AP5 | `locust --headless -u 100 -r 100 -t 20s` against each pool profile, with a full app restart between profiles. |

Call counts are more useful than wall time for AP4. They are stable across machines, while timings move with the hardware and load.

## Postgres versus SQLite

The talk's numbers come from Postgres, and the difference is real.

| Effect | Postgres | SQLite |
|---|---|---|
| Engine construction (AP2) | A new TCP connection and authentication handshake each time | A local file, with no network handshake |
| Gap in AP2 | About 10× | About 4× |
| Pool exhaustion (AP5) | A real connection limit with real handshake cost | Same pool logic, but the demo holds connections longer so the starvation is reliable |
| Query count (AP3) | Identical | Identical |

The SQLite run understates AP2 and changes the AP5 shape on purpose. The demo's AP5 route holds a connection for 0.3 s on Postgres and 0.6 s on SQLite, as the code comment explains. Always label which environment a number came from when you present it.

## Note on working-tree benchmark files

Some files under `orders-api-demo/benchmarks/` were overwritten by a later local run and show as modified in git. The committed versions are the Postgres captures this page quotes. The uncommitted versions are not used for any Postgres number here.

The AP4 SQLite call counts (about 290k and 111k) come from the uncommitted working-tree cProfile files, which match the DEMO_GUIDE guidance. The AP5 working-tree CSVs show different totals from the committed capture, so they are not quoted.

## Raw files

- Committed capture folder: `orders-api-demo/benchmarks/`
- Per-pattern READMEs: `orders-api-demo/benchmarks/apN-*/README.md`
- The tests that assert the ratios: `orders-api-demo/tests/test_ap*_*.py`

## Related

- [Performance checklist](/reference/checklist)
- [Profiling toolkit](/reference/profiling-toolkit)
- [FAQ](/reference/faq)
