---
title: About
description: The speaker, the talk abstract and schedule, and the links, slides, and license for "Why Your FastAPI Is Not Fast".
---

# About

## The talk

**Why Your FastAPI Is Not Fast: A Deep Dive into Hidden Bottlenecks**

FastAPI is fast, but only if you use it correctly. The framework gives you the tools and does not protect you from yourself. The talk covers five anti-patterns that quietly erode FastAPI performance. Each one comes with real code, real profiling output, and a measured before-and-after fix, from a reproducible Orders API you can run yourself.

The talk opens with a real-world pattern: a FastAPI service, rewritten from a synchronous Flask predecessor for speed, performed worse under real concurrency. Its single-request benchmarks looked good. Production did not.

| | |
|---|---|
| Event | PyCon Hong Kong 2026 |
| Track | Software Engineering & Platforms |
| Length | 30 minutes |
| Slot | Sat 14 Nov 2026, 14:25–14:55 HKT, per the presenter guide. Confirm the time before the day. |

The talk is about what happens *inside* route handlers and dependencies. Tracing and observability are covered in the neighbouring talk in the same track.

## The speaker

**Satyam Soni** gave this talk at PyCon Hong Kong 2026. The repository is at [github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast](https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast).

## Links

| Resource | Link |
|---|---|
| Source repository | [GitHub](https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast) |
| Slides, PDF | [slides.pdf](/slides.pdf) |
| Slides, source (Marp) | [talk/slides.md](https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast/blob/main/talk/slides.md) |
| Presenter guide | [talk/PRESENTER_GUIDE.md](https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast/blob/main/talk/PRESENTER_GUIDE.md) |
| Orders API | [orders-api-demo/](https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast/tree/main/orders-api-demo) |
| Performance checklist | [orders-api-demo/CHECKLIST.md](https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast/blob/main/orders-api-demo/CHECKLIST.md) |

## License

The code is released under the **MIT License**, copyright 2026 Satyam Soni. The full text is in [`orders-api-demo/LICENSE`](https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast/blob/main/orders-api-demo/LICENSE).

## Related

- [Start here](/guide/)
- [Anti-pattern overview](/anti-patterns/)
