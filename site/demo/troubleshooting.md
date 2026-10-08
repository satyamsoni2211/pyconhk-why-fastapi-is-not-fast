---
title: Troubleshooting
description: The gotchas table, what to do when a demo misbehaves, and the fallbacks to use on stage when Docker or the network fails.
---

# Troubleshooting

::: tip In one sentence
Most failures come from one of three things: the gateway hostname in `.env`, the pool mode left over from a previous run, or a port that another process already owns.
:::

## Gotchas table

| Symptom | Cause | Fix |
|---|---|---|
| Every `/demo/ap1/*` and `/demo/ap2/*` call returns 500 with `nodename nor servname provided` | `.env` has `PAYMENT_GATEWAY_URL=http://payment-gateway:8080`, the Docker hostname | For local runs set `PAYMENT_GATEWAY_URL=http://localhost:8080`, either in `.env` or on the command. Environment variables beat `.env`. |
| `/demo/ap5/info` shows `pool_mode: bad` when you wanted `good`, or the reverse | `.env` contains `POOL_MODE`, which is read at process start | Set it on the command, for example `POOL_MODE=good uv run uvicorn …`, then confirm with `/demo/ap5/info` |
| `Address already in use`, or strange 404s on `:8000` | Another process owns the port | `lsof -nP -iTCP:8000 -sTCP:LISTEN`, or use another port and change the URLs |
| `.env` has `DATABASE_URL` pointing at `db:5432` | Docker configuration | Comment it out for SQLite. The default is `db/orders.db`. |
| Locust reports failures on `good` | Pool still on `bad`, or the app was not restarted | Restart with `POOL_MODE=good`, confirm with `/demo/ap5/info`, and run again |
| `pytest` cannot reach the gateway | `PAYMENT_GATEWAY_URL` still points at the Docker hostname | `PAYMENT_GATEWAY_URL=http://localhost:8080 uv run pytest tests/ -v` |

::: tip Check before every rehearsal
Two commands catch most problems. `curl localhost:8000/health` should return `{"status":"ok"}`, and `curl localhost:8000/demo/ap5/info` should show the pool mode you expect.
:::

## If something breaks on stage

The presenter guide sets the rule: do not debug live. Every number in the deck is already captured, so the live demo is texture, not the argument.

| What broke | What to do |
|---|---|
| Docker will not start, or the container crashed | Do not debug. Say you will show the captured output, then move to the slide for the current anti-pattern. |
| Wrong `POOL_MODE` during AP5 | Check `/demo/ap5/info`, fix it, and retry once. If it is still wrong after about 20 seconds, move to the captured slide. |
| Live numbers look off, for example a cold container or a noisy laptop | "The exact number moves with the machine, but the shape doesn't. Bad is always about 3×, good is always about 1×." Then show the captured numbers, 3.046 s and 1.040 s for AP1. |
| Networking is broken | For AP3, `benchmarks/ap3-lazy-loading/missing-greenlet-response.json` holds the exact captured output. Use it to screenshot or paste. |
| Running over time | Cut AP4's live `curl` first. Then compress AP2 to "here are the numbers." |

::: info The AP5 fallback line
"I've run this exact load test twice already, so I'm not gambling 90 seconds of a 30-minute talk on a live load test." It is an honest reason, not a cop-out.
:::

## Captured fallbacks

| Pattern | Captured file |
|---|---|
| AP1 | `benchmarks/ap1-blocking/latency-3-concurrent.txt`, `asyncio-debug.log`, and the flame graphs in `talk/assets/` |
| AP2 | `benchmarks/ap2-di/latency-report.txt` |
| AP3 | `benchmarks/ap3-lazy-loading/missing-greenlet-response.json`, `echo-bad.log`, `echo-good.log` |
| AP4 | `benchmarks/ap4-pydantic/cprofile-bad.txt`, `cprofile-good.txt` |
| AP5 | `benchmarks/ap5-pool/README.md`, `pool-timeout-traceback.log`, and the locust CSVs |

## Related

- [Setup gotchas](/guide/setup#gotchas): the same problems, with setup context
- [Running the demos](/demo/running-the-demos)
- [Benchmarks](/reference/benchmarks)
