# Implementation plan — VitePress workshop site ("Why Your FastAPI Is Not Fast")

Audience of this document: the engineer (an AI model) implementing the site. Follow it
step by step. Where the plan says **verify**, actually run the command and read its output;
do not assume. Do **not** invent facts or numbers — every number on the site must come from
a file listed in §3 (Source map).

## 1. Goal and constraints

Build a documentation site for the PyCon HK 2026 workshop/talk **"Why Your FastAPI Is Not
Fast: A Deep Dive into Hidden Bottlenecks"** (speaker: Satyam Soni). It must be:

1. **Intuitive** — a first-time visitor understands what the workshop is, where to start, and
   how to run each demo within 30 seconds of landing.
2. **A reference** — detailed descriptions, real measured facts, commands, expected output,
   troubleshooting; someone should be able to come back months later and look something up.
3. **Apple-glass aesthetic** — translucent frosted panels, soft depth, generous spacing,
   SF-style typography, light + dark themes (see §5).
4. **Deployable to Vercel** as a static site.

Hard constraints:
- Tooling: **VitePress** (latest 1.x), Node ≥ 20, **npm** (a `package-lock.json` is committed).
- Site lives in a new top-level folder **`site/`** in this repo
  (`/Users/satyam_soni1/Documents/pyconhk-why-fastapi-is-not-fast/site`). Do not modify files
  outside `site/` except: (a) root `.gitignore` additions for `site/node_modules`,
  `site/.vitepress/cache`, `site/.vitepress/dist`, `site/.vercel`; (b) a short "Documentation
  site" section in `READER_GUIDE.md` pointing at `site/`.
- Do not modify `orders-api-demo/` code, benchmarks, or `talk/`. Copy/adapt content *from* them.
- No external runtime requests (no CDN fonts, no analytics, no remote images). Use a system font
  stack; everything must work offline once built.
- No new heavy dependencies. Allowed: `vitepress`, `vue` (peer), `mermaid` plugin only if you
  can verify it builds (optional; hand-written SVG/CSS diagrams are preferred).
- Do **not** run `vercel` / deploy commands. Deployment is done by the human/lead afterwards.
  You only prepare `vercel.json` and make `npm run build` succeed.
- Do not commit or push. Leave changes in the working tree.

## 2. Information architecture (sidebar + routes)

All paths are relative to `site/`. Each page needs frontmatter `title` and `description`.

```
index.md                         Home (hero + feature cards + stats + "start here" paths)
guide/
  index.md                       What this workshop is, who it's for, prerequisites, how to use this site
  setup.md                       Setup: SQLite (no Docker) and Docker/Postgres modes, env gotchas
  architecture.md                Domain model, app layout, how bad/good pairs are wired, request flow diagrams
  baseline-api.md                The correct baseline endpoints with curl examples
anti-patterns/
  index.md                       Overview table of AP1–AP5 + how to read a pattern page
  ap1-blocking-event-loop.md
  ap2-di-lifecycle.md
  ap3-lazy-loading.md
  ap4-pydantic-overhead.md
  ap5-pool-starvation.md
demo/
  index.md                       Demo runbook overview + 20-minute run of show
  running-the-demos.md           Per-AP commands and expected output (condensed from DEMO_GUIDE.md)
  troubleshooting.md             Gotchas table + "if something breaks on stage"
reference/
  checklist.md                   The 5-point performance checklist (interactive checkboxes, persisted in localStorage)
  benchmarks.md                  All captured numbers in one table + methodology + SQLite-vs-Postgres caveat
  profiling-toolkit.md           py-spy, asyncio debug, cProfile, SQLAlchemy echo, locust — when/how
  endpoints.md                   Every HTTP endpoint (API + mock gateway) with method, path, purpose, sample response
  faq.md                         Anticipated Q&A (from PRESENTER_GUIDE.md §4)
  glossary.md                    Terms: event loop, greenlet, N+1, selectinload, pool_size, max_overflow, …
about.md                         Speaker, talk abstract, links (repo, slides PDF), license
```

Sidebar groups: *Guide*, *Anti-patterns*, *Demo*, *Reference*. Top nav: Guide · Anti-patterns ·
Demo · Reference · GitHub (icon link to
`https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast`). Enable local search
(`search: { provider: 'local' }`). Enable `lastUpdated` and an "Edit this page" link pointing to the
GitHub repo path `site/<file>`. Add `outline: [2,3]`.

## 3. Source map (where every fact comes from)

Read these files completely before writing the related page. All paths from repo root.

| Page | Primary sources |
|---|---|
| home, guide/index, about | `READER_GUIDE.md`, `talk/slides.md` (title/abstract/incident), `orders-api-demo/README.md` |
| guide/setup | `orders-api-demo/README.md` ("Without Docker" + Quick start), `orders-api-demo/DEMO_GUIDE.md` §0 and §9, `orders-api-demo/.env.example`, `docker-compose.yml` |
| guide/architecture, baseline-api | `orders-api-demo/app/{main,config,db,models,schemas,clients}.py`, `app/routers/orders.py`, `mock_gateway/main.py` |
| anti-patterns/apN | `orders-api-demo/app/routers/demo_apN.py` (quote the real code), `app/schemas_ap4.py` for AP4, `orders-api-demo/benchmarks/apN-*/README.md` and the raw files next to it, `talk/slides.md` sections, `talk/PRESENTER_GUIDE.md`, `CHECKLIST.md`, `DEMO_GUIDE.md` |
| demo/* | `orders-api-demo/DEMO_GUIDE.md` (primary), `talk/PRESENTER_GUIDE.md` §2–§5 |
| reference/checklist | `orders-api-demo/CHECKLIST.md` |
| reference/benchmarks | all `benchmarks/*/README.md`; `DEMO_GUIDE.md` for SQLite numbers |
| reference/profiling-toolkit | `CHECKLIST.md` toolkit table, `scripts/*` |
| reference/endpoints | routers + `mock_gateway/main.py` (verify by reading the code, not guessing) |
| reference/faq | `talk/PRESENTER_GUIDE.md` §4 |

Assets: copy `talk/assets/ap1-flamegraph-bad.svg` and `ap1-flamegraph-good.svg` into
`site/public/assets/`; copy `talk/slides.pdf` to `site/public/slides.pdf`. Reference them with
absolute `/assets/...` URLs. Do not copy benchmark CSV/log files; inline the key numbers or short
excerpts in fenced code blocks, with a link to the file on GitHub
(`https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast/blob/main/<path>`).

### Facts that must appear (verify each against the source file before using)

- AP1: 3 concurrent requests — 3.05 s blocking vs 1.04 s async (Postgres/go-httpbin capture);
  local mock gateway ≈ 3.0 s vs 1.0 s; `bridge` ≈ 1.0 s.
- AP2: Postgres 17.48 ms vs 1.73 ms mean (~10×); SQLite local ≈ 5.8 ms vs 1.3 ms (~4×).
- AP3: `MissingGreenlet` on plain attribute access; N+1 = 6 queries vs 2 for 5 orders.
- AP4: cProfile — Postgres capture ~1.9× slower, ~1.8× more calls; SQLite local ≈ 290k vs 111k calls.
- AP5: Postgres capture 2.1 % failures @ 47.8 req/s vs 0 % @ 179.3 req/s; SQLite local
  ≈ 44 % @ ~43 req/s vs 0 % @ ~97 req/s. Pool profiles: bad = 5+10 conns / 2 s timeout,
  good = 20+40 / 10 s (see `app/config.py`).
- Setup gotcha: `.env` containing `PAYMENT_GATEWAY_URL=http://payment-gateway:8080` breaks local
  runs; env vars override `.env`; `POOL_MODE` is read at process start.

Always label which environment a number came from (Postgres capture vs SQLite local).

## 4. Page templates

### 4.1 Anti-pattern page (every `apN` page uses this exact section order)

1. **Frontmatter + one-line summary** (a `<Callout type="tip">` "In one sentence").
2. **What goes wrong** — plain-language explanation, 2–3 paragraphs, with a small diagram
   (`<Diagram>` or a CSS/SVG timeline).
3. **The bad code** — real excerpt from the router, fenced with line highlights and a filename
   title (`​```python [app/routers/demo_ap1.py] {3-4}`).
4. **The good code** — same format.
5. **Try it** — a `<DemoTabs>` or VitePress `::: code-group` with the exact curl/script
   commands and an "Expected" block.
6. **Measured evidence** — `<StatGrid>` (3–4 `<StatCard>`s: bad, good, ratio, environment) +
   short excerpt of the captured output.
7. **How to detect it in your own service** — tool + command + what to look for.
8. **Checklist** — the corresponding checklist bullets.
9. **Talking points / common questions** — bullets.
10. **Prev / Next** links (VitePress default `docFooter` is fine).

### 4.2 Home page (`layout: home` customised)

- Hero: name "Why Your FastAPI Is Not Fast", tagline "A deep dive into hidden bottlenecks —
  five anti-patterns, real measurements, runnable demos.", two buttons: *Start the workshop*
  (→ /guide/) and *View the checklist* (→ /reference/checklist).
- Row of 5 glass **feature cards** (AP1–AP5), each with an icon (inline SVG), a one-line hook,
  and the headline metric (e.g. "3.0 s → 1.0 s").
- A **stats strip** (`<StatGrid>`): "5 anti-patterns · 10+ live endpoints · 13 automated tests ·
  0 invented numbers".
- A **"Choose your path"** section with three glass cards: *5 minutes* (checklist),
  *30 minutes* (read the patterns), *An evening* (run everything) — taken from `READER_GUIDE.md`.
- Footer line: licence + speaker.

## 5. Visual design spec — Apple "liquid glass" aesthetic

Implement via custom theme extension: `site/.vitepress/theme/index.ts` (extends
`DefaultTheme`), `site/.vitepress/theme/style.css`, and components in
`site/.vitepress/theme/components/`. Keep VitePress's layout/accessibility; restyle with CSS
variables rather than replacing the layout wholesale.

### 5.1 Design tokens (define on `:root`; override in `.dark`)

```css
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
               "Inter", "Segoe UI", system-ui, sans-serif;
  --font-mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;

  /* brand */
  --accent: #0a84ff;           /* iOS blue */
  --accent-2: #5e5ce6;         /* indigo */
  --good: #30d158;             /* green */
  --bad: #ff453a;              /* red */
  --warn: #ff9f0a;             /* orange */

  /* surfaces */
  --bg: #f2f2f7;
  --glass-bg: rgba(255, 255, 255, 0.55);
  --glass-bg-strong: rgba(255, 255, 255, 0.78);
  --glass-border: rgba(255, 255, 255, 0.65);
  --glass-hairline: rgba(60, 60, 67, 0.12);
  --glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.12), inset 0 1px 0 rgba(255,255,255,0.8);
  --glass-blur: saturate(180%) blur(24px);
  --radius-lg: 22px; --radius-md: 14px; --radius-sm: 10px;
}
.dark {
  --bg: #000;
  --glass-bg: rgba(44, 44, 46, 0.55);
  --glass-bg-strong: rgba(58, 58, 60, 0.75);
  --glass-border: rgba(255, 255, 255, 0.14);
  --glass-hairline: rgba(235, 235, 245, 0.16);
  --glass-shadow: 0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.12);
}
```

### 5.2 Rules

- **Background**: page `background: var(--bg)` plus a fixed, blurred "aurora" layer behind
  content (3–4 large radial gradients in blue/indigo/teal/pink, ~35 % opacity in light, ~25 %
  in dark, `filter: blur(60px)`, `position: fixed; inset: 0; z-index: -1; pointer-events: none`).
  This gives the glass something to blur. Provide `@media (prefers-reduced-motion: reduce)` to
  disable any animation (a very slow 40 s gradient drift is allowed, nothing faster).
- **Glass surface mixin** (apply to nav bar, sidebar, doc containers, cards, callouts, code
  blocks, search modal, outline): `background: var(--glass-bg); backdrop-filter:
  var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); border: 1px solid
  var(--glass-border); box-shadow: var(--glass-shadow); border-radius: var(--radius-lg)`.
  Provide a solid fallback via `@supports not (backdrop-filter: blur(1px))` using
  `--glass-bg-strong`.
- **Navbar**: sticky, full-width glass strip with hairline bottom border; floating pill-style
  nav items; active item gets an accent-tinted glass pill.
- **Sidebar**: glass panel with rounded corners, inset from the viewport edge; active link
  has accent pill background; group titles small, uppercase, letter-spaced, secondary colour.
- **Content area**: the main doc column sits on a large glass sheet (`--glass-bg-strong`) with
  `--radius-lg`, padding ≥ 2rem (1.25rem on mobile).
- **Typography**: body 17 px / 1.7; H1 clamp(2.2rem, 5vw, 3.2rem), weight 700, letter-spacing
  −0.02em, subtle gradient text (accent → accent-2) on the hero title only; H2 with no
  bottom border, 1.8rem, weight 650; mono code 0.9em.
- **Code blocks**: glass dark panel in both themes (`rgba(20,20,24,0.72)` + blur), rounded 14 px,
  filename tab on top, copy button visible on hover, line-highlight uses accent at 18 % opacity.
- **Tables**: rounded, glass, zebra rows via `rgba(127,127,127,0.06)`, sticky header on wide
  tables, horizontal scroll wrapper on mobile.
- **Buttons / links**: primary button = accent gradient + glass sheen (inset top highlight),
  hover lifts 1 px and increases shadow; links use accent colour with 1 px underline offset 3 px.
- **Badges**: `bad` (red), `good` (green), `info` (blue), `warn` (orange) – tinted glass pills.
- **Motion**: 150–250 ms ease-out transitions on hover/focus only; respect reduced motion.
- **Focus rings**: always visible, 3 px accent at 45 % opacity (accessibility requirement).
- **Contrast**: body text must meet WCAG AA against the glass in both themes; if a glass
  surface sits over the aurora, use `--glass-bg-strong` for text-heavy areas.
- **Responsive**: must work at 375 px width with no horizontal page scroll; sidebar collapses
  to VitePress's mobile drawer (also glass).

### 5.3 Custom components (Vue SFCs, `<script setup lang="ts">`, registered globally in `theme/index.ts`)

| Component | Purpose | Props |
|---|---|---|
| `GlassCard.vue` | Generic glass card with optional icon slot, title, link | `title`, `href?`, `badge?` |
| `FeatureGrid.vue` | Responsive grid wrapper (1/2/3/5 cols) | slot |
| `StatCard.vue` / `StatGrid.vue` | Big number + label + sub-label; `tone` = good/bad/neutral | `value`, `label`, `sub?`, `tone?` |
| `Callout.vue` | tip / warning / danger / info boxes (glass, coloured left accent) | `type`, `title?` |
| `BadGood.vue` | Side-by-side two-column "Bad ❌ / Good ✅" slot panels (stack on mobile) | slots `bad`, `good` |
| `Timeline.vue` | Horizontal SVG/CSS request timeline to visualise serial vs concurrent execution (AP1) and pool queueing (AP5); data via prop array of `{label, start, end, tone}` | `rows`, `total` |
| `BarCompare.vue` | Two-bar animated comparison (bad vs good) for latency/throughput, pure CSS widths | `bad`, `good`, `unit`, `lowerIsBetter` |
| `ChecklistItem.vue` / `Checklist.vue` | Checkbox list persisted in `localStorage` (wrapped in try/catch; page must render without it) | `id`, slot |
| `CopyCommand.vue` | Single-line shell command with copy button and "Run this in: terminal N" label | `cmd`, `label?` |
| `EnvBadge.vue` | Inline pill "Postgres capture" / "SQLite local" for labelling numbers | `env` |
| `ThemeAurora.vue` | The background aurora layer, mounted via the `layout-bottom`/`layout-top` slot | – |

All components must work with no JS errors in SSR build (guard `window`/`localStorage` access
with `onMounted`/`typeof window`).

## 6. Step-by-step tasks

Do these in order; after each numbered group run the **verify** command.

### T1 — Scaffold
1. `mkdir site && cd site && npm init -y` → set `"name": "fastapi-workshop-site"`,
   `"private": true`, `"type": "module"`.
2. `npm install -D vitepress@^1` (and `vue` if npm does not auto-install the peer).
3. Scripts: `"dev": "vitepress dev"`, `"build": "vitepress build"`, `"preview": "vitepress preview"`.
4. Create `.vitepress/config.ts` with: `title`, `description`, `lang: 'en-US'`, `cleanUrls: true`,
   `lastUpdated: true`, `head` (favicon `/favicon.svg`, theme-color meta for light/dark, Open
   Graph tags), `themeConfig` (nav, sidebar per §2, socialLinks, search local, editLink,
   footer, outline, `docFooter`), `markdown: { lineNumbers: false, theme: { light: 'github-light',
   dark: 'github-dark' } }`, `sitemap: { hostname: <leave a TODO constant at top of file> }`.
5. Create a simple `public/favicon.svg` (rounded square, accent gradient, white "⚡"-like bolt path).
6. **Verify:** `npm run build` succeeds with the placeholder `index.md`.

### T2 — Theme and components
1. Create `theme/index.ts` extending default theme, importing `style.css`, registering all
   components from §5.3, and injecting `ThemeAurora` via `h(DefaultTheme.Layout, null, { 'layout-top': ... })`.
2. Write `style.css` implementing §5.1–5.2, overriding VitePress variables (`--vp-c-brand-1`,
   `--vp-c-bg`, `--vp-c-bg-soft`, `--vp-nav-bg-color`, `--vp-sidebar-bg-color`, etc.) and
   restyling `.VPNav`, `.VPSidebar`, `.VPDoc .container`, `.vp-doc table`, `div[class*='language-']`,
   `.custom-block`, `.VPLocalSearchBox`, `.VPFooter`, `.VPDocOutlineItem`.
3. Implement the components in §5.3.
4. Create a throw-away page `site/_theme-test.md` (excluded in `srcExclude`, or delete before
   finishing) exercising every component in light/dark to eyeball; delete when done.
5. **Verify:** `npm run build` passes; `npm run dev` serves; fetch the page HTML and confirm
   components render (`curl -s localhost:5173/ | grep -c glass`).

### T3 — Content: guide + reference foundations
Write `guide/*`, `reference/endpoints.md`, `reference/glossary.md`, `about.md`, `index.md`.
Rules: concise paragraphs, short sentences, tables for comparisons, every command in a
`CopyCommand` or fenced `bash` block, and an "Expected output" block where the sources have one.
Endpoints page must be generated from the actual router code (list: `/health`; `/orders`
GET/POST, `/orders/{id}`; `/demo/ap1/{bad,good,bridge}`; `/demo/ap2/{bad,good}`;
`/demo/ap3/{bad-crash,bad-n1,good}`; `/demo/ap4/{bad,good}`; `/demo/ap5/{query,info}`; mock gateway
`/health`, `/delay/{seconds}`, `/get`, `/status/{code}`, `POST /charge`) — confirm by reading the code.

### T4 — Content: five anti-pattern pages
One page each, following §4.1 exactly. Use real code excerpts copied from the routers (keep
them short, ≤ 25 lines, and correct). Include at least one visual per page:
AP1 `Timeline` (3 serial vs 3 concurrent 1 s bars); AP2 `BarCompare`; AP3 query-count
`BarCompare` (6 vs 2) + a `BadGood` of the three endpoints; AP4 `BarCompare` of function calls;
AP5 `Timeline` of requests queueing for a 15-connection pool + `StatGrid` of failures/throughput.
Add the AP1 flame graphs as two images in a `BadGood` block with captions.

### T5 — Content: demo runbook and reference
`demo/*` from `DEMO_GUIDE.md` and `PRESENTER_GUIDE.md` (run of show table, rehearsal checklist,
if-something-breaks section). `reference/checklist.md` uses the `Checklist` component,
`reference/benchmarks.md` has one consolidated table (columns: pattern, metric, bad, good, ratio,
environment) plus methodology and the SQLite-vs-Postgres explanation, `profiling-toolkit.md`,
`faq.md`.

### T6 — Cross-cutting polish
- Add `<Callout>` for every gotcha in DEMO_GUIDE §0.
- Every page ends with a "Related" list of internal links.
- Alt text on every image; `lang` attribute on code fences.
- Add `site/README.md` (how to run/build/deploy the site locally).
- Add a "Documentation site" section to `READER_GUIDE.md`.
- Update root `.gitignore`.

### T7 — Vercel configuration (no deploy)
Create `site/vercel.json`:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vitepress",
  "installCommand": "npm ci",
  "buildCommand": "npm run build",
  "outputDirectory": ".vitepress/dist",
  "cleanUrls": true,
  "headers": [
    { "source": "/assets/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] },
    { "source": "/(.*)", "headers": [
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
    ] }
  ]
}
```
Note in `site/README.md` that the Vercel project's **Root Directory must be `site`**.
Ensure `package-lock.json` is present so `npm ci` works.

## 7. Verification and acceptance criteria

Run all of these and report actual results:

1. `cd site && npm ci && npm run build` exits 0 with **no** dead-link errors (VitePress fails the
   build on dead internal links; fix, do not ignore).
2. `npm run preview` and `curl -s -o /dev/null -w '%{http_code}'` returns 200 for every route in §2.
3. A script (node or bash) walks every `.md` page and confirms: has frontmatter `title` and
   `description`; no `TODO`/`lorem`/`XXX` text remains (the sitemap hostname TODO constant is the
   only allowed exception).
4. Numbers audit: grep the pages for each number listed in §3 "Facts that must appear" and
   confirm the source file contains it. List any number on the site that you could not trace to a
   source file — there must be none.
5. Visual check with a browser tool if available (screenshots at 1440 px and 375 px, light and dark):
   glass panels visibly translucent over the aurora, no horizontal scroll at 375 px, code blocks
   readable, no overlapping text. If no browser tool exists, state that visual QA was not done.
6. Lighthouse-style sanity (manual): all images have alt, headings in order (one H1 per page),
   focus ring visible.
7. `git status` shows changes only inside `site/` plus `.gitignore` and `READER_GUIDE.md`.

## 8. Final report format (what to send back)

- Files created (tree of `site/`, 2 levels).
- Output tail of `npm run build`.
- Results of each §7 check (pass/fail, with evidence).
- Any deviations from this plan and why.
- Anything you could not verify.
