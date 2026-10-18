---
layout: home
title: Why Your FastAPI Is Not Fast
description: A deep dive into five hidden FastAPI bottlenecks, with real measurements and runnable demos. PyCon Hong Kong 2026 workshop by Satyam Soni.

hero:
  name: Why Your FastAPI Is Not Fast
  text: A deep dive into hidden bottlenecks
  tagline: Five anti-patterns, real measurements, runnable demos.
  actions:
    - theme: brand
      text: Start the workshop
      link: /guide/
    - theme: alt
      text: View the checklist
      link: /reference/checklist
    - theme: alt
      text: Open the slides
      link: /slides/
      target: _blank
---

<div class="home-section">

## The five anti-patterns

FastAPI gives you the tools, but it does not protect you from yourself. Each card below is one anti-pattern from the talk, with the headline measurement from the captured Postgres runs. Each pattern has a `bad` and a `good` endpoint on the same running service.

</div>

<FeatureGrid :cols="5">

<GlassCard title="AP1 · Blocking" href="/anti-patterns/ap1-blocking-event-loop" badge="Loop">
<template #icon>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
</template>
A sync call inside <code>async def</code> freezes the whole event loop.

**3.05 s → 1.04 s** for three concurrent requests.
</GlassCard>

<GlassCard title="AP2 · DI lifecycle" href="/anti-patterns/ap2-di-lifecycle" badge="Setup">
<template #icon>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 9h6v6H9z"/></svg>
</template>
Rebuilding an engine per request pays a connection handshake every time.

**17.48 ms → 1.73 ms** mean per request.
</GlassCard>

<GlassCard title="AP3 · Lazy loading" href="/anti-patterns/ap3-lazy-loading" badge="ORM">
<template #icon>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/></svg>
</template>
Lazy loading either crashes with <code>MissingGreenlet</code> or quietly issues one query per row.

**6 → 2 queries** for five orders.
</GlassCard>

<GlassCard title="AP4 · Pydantic overhead" href="/anti-patterns/ap4-pydantic-overhead" badge="CPU">
<template #icon>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 12h6l-2-3m2 3-2 3"/><path d="M20 12h-6l2-3m-2 3 2 3"/></svg>
</template>
Validating the same data twice doubles the work.

**~1.9× slower**, ~1.8× more function calls.
</GlassCard>

<GlassCard title="AP5 · Pool starvation" href="/anti-patterns/ap5-pool-starvation" badge="Pool">
<template #icon>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z"/><path d="M4 7v10c0 1.7 3.6 3 8 3s8-1.3 8-3V7"/></svg>
</template>
A tutorial-size pool becomes a hard ceiling under real concurrency.

**2.1% → 0% failures** at 47.8 → 179.3 req/s.
</GlassCard>

</FeatureGrid>

<div class="home-section">

## At a glance

</div>

<StatGrid>
<StatCard value="5" label="Anti-patterns" sub="AP1 to AP5" />
<StatCard value="16" label="HTTP endpoints" sub="API, including /health" />
<StatCard value="13" label="Automated tests" sub="pytest, deterministic" tone="good" />
<StatCard value="0" label="Invented numbers" sub="every figure traces to a repo file" tone="good" />
</StatGrid>

<div class="home-section">

## Choose your path

Pick the time you have. The same material is organised differently for each.

</div>

<FeatureGrid :cols="3">

<GlassCard title="5 minutes" badge="Skim">
Read the five-point performance checklist. It is the distilled takeaway of the talk, with the headline before-and-after numbers.

[Open the checklist →](/reference/checklist)
</GlassCard>

<GlassCard title="30 minutes" badge="Read">
Read the five anti-pattern pages. For each one, look at the bad and good code side by side and the measured evidence.

[Read the patterns →](/anti-patterns/)
</GlassCard>

<GlassCard title="An evening" badge="Run">
Clone the repo, start the services, and reproduce every demo yourself with the SQLite setup or the Docker and Postgres setup.

[Set up and run →](/guide/setup)
</GlassCard>

</FeatureGrid>

<p class="home-footer">MIT licensed. Speaker: Satyam Soni. PyCon Hong Kong 2026, Software Engineering &amp; Platforms track.</p>

## Related

- [Start here](/guide/)
- [Anti-pattern overview](/anti-patterns/)
- [Endpoints](/reference/endpoints)
- [About the talk](/about)
