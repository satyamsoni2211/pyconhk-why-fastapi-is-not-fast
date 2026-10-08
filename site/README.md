---
title: Site maintainers README
description: How to run, build, and deploy the documentation site. Not published; excluded from the VitePress build.
---

# Documentation site

The VitePress site for "Why Your FastAPI Is Not Fast". It documents the Orders API demo in `../orders-api-demo/` and the talk material in `../talk/`.

## Run locally

Requires Node 20 or newer. The lockfile is committed, so use `npm ci`.

```bash
cd site
npm ci
npm run dev        # http://localhost:5173
```

## Build and preview

```bash
npm run build      # writes .vitepress/dist; fails on dead internal links
npm run preview    # serves the built output locally
```

## Layout

| Path | What it is |
|---|---|
| `.vitepress/config.ts` | Site config: nav, sidebar, search, edit links, sitemap |
| `.vitepress/theme/` | Theme extension: `index.ts`, `style.css`, and Vue components in `components/` |
| `index.md` | Home page |
| `guide/`, `anti-patterns/`, `demo/`, `reference/`, `about.md` | Content pages |
| `public/` | Static files copied as-is: `favicon.svg`, `slides.pdf`, and the AP1 flame graphs under `assets/` |
| `vercel.json` | Vercel build and header settings |

## Content rules

- Every number must trace to a file in the repo. Label each one with its environment: **Postgres capture** (committed output) or **SQLite local** / *expected* (DEMO_GUIDE guidance).
- Pages use the `title` and `description` frontmatter fields.
- Code excerpts are copied from the routers, and line highlights match the excerpt. Keep excerpts short.
- Filenames on code blocks come from a single-tab `::: code-group`, because plain fences do not render a title in this VitePress version.
- No external requests: no CDN fonts, no analytics, no remote images. The site uses a system font stack.

## Deploying to Vercel

Deployment is a manual step. Do not run `vercel` from the repo without the owner's go-ahead.

1. In the Vercel project settings, set **Root Directory** to `site`. The build will not find `package.json` otherwise.
2. The framework is detected from `vercel.json` as `vitepress`. Install uses `npm ci`, build uses `npm run build`, and the output directory is `.vitepress/dist`.
3. Set the production hostname in `.vitepress/config.ts`, replacing the placeholder value of `SITE_HOSTNAME`, so the sitemap has real URLs.
4. Confirm that `package-lock.json` is committed, since `npm ci` needs it.

## Editing the numbers

The measured figures are in the source files listed in `anti-patterns/index.md` and `reference/benchmarks.md`. When you change a number on a page, change the committed capture it comes from first, or record the new run in `orders-api-demo/benchmarks/`.
