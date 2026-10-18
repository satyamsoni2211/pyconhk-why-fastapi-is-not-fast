import { defineConfig } from 'vitepress'

// TODO: set the production hostname (e.g. https://<project>.vercel.app) before the first real deploy.
const SITE_HOSTNAME = 'https://fastapi-not-fast-workshop.vercel.app'
const SITE_URL_TITLE = 'Why Your FastAPI Is Not Fast'
const SITE_DESCRIPTION =
  'A deep dive into hidden FastAPI bottlenecks: five anti-patterns, real measurements, and runnable demos. PyCon HK 2026 workshop by Satyam Soni.'
const REPO = 'https://github.com/satyamsoni2211/pyconhk-why-fastapi-is-not-fast'

export default defineConfig({
  // README.md is for maintainers, not a published page
  srcExclude: ['README.md'],
  title: SITE_URL_TITLE,
  description: SITE_DESCRIPTION,
  lang: 'en-US',
  cleanUrls: true,
  lastUpdated: true,

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#f2f2f7', media: '(prefers-color-scheme: light)' }],
    ['meta', { name: 'theme-color', content: '#000000', media: '(prefers-color-scheme: dark)' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: SITE_URL_TITLE }],
    ['meta', { property: 'og:description', content: SITE_DESCRIPTION }],
    ['meta', { property: 'og:site_name', content: SITE_URL_TITLE }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
  ],

  markdown: {
    lineNumbers: false,
    theme: { light: 'github-light', dark: 'github-dark' },
  },

  sitemap: { hostname: SITE_HOSTNAME },

  themeConfig: {
    siteTitle: 'FastAPI Not Fast',

    nav: [
      { text: 'Guide', link: '/guide/', activeMatch: '^/guide/' },
      { text: 'Anti-patterns', link: '/anti-patterns/', activeMatch: '^/anti-patterns/' },
      { text: 'Demo', link: '/demo/', activeMatch: '^/demo/' },
      { text: 'Reference', link: '/reference/checklist', activeMatch: '^/reference/' },
      { text: 'Slides', link: '/slides/', target: '_blank' },
    ],

    sidebar: [
      {
        text: 'Guide',
        collapsed: false,
        items: [
          { text: 'Start here', link: '/guide/' },
          { text: 'Setup', link: '/guide/setup' },
          { text: 'Architecture', link: '/guide/architecture' },
          { text: 'Baseline API', link: '/guide/baseline-api' },
        ],
      },
      {
        text: 'Anti-patterns',
        collapsed: false,
        items: [
          { text: 'Overview', link: '/anti-patterns/' },
          { text: 'AP1 — Blocking the event loop', link: '/anti-patterns/ap1-blocking-event-loop' },
          { text: 'AP2 — DI lifecycle misuse', link: '/anti-patterns/ap2-di-lifecycle' },
          { text: 'AP3 — Lazy loading in async', link: '/anti-patterns/ap3-lazy-loading' },
          { text: 'AP4 — Pydantic overhead', link: '/anti-patterns/ap4-pydantic-overhead' },
          { text: 'AP5 — Pool starvation', link: '/anti-patterns/ap5-pool-starvation' },
        ],
      },
      {
        text: 'Demo',
        collapsed: false,
        items: [
          { text: 'Runbook overview', link: '/demo/' },
          { text: 'Running the demos', link: '/demo/running-the-demos' },
          { text: 'Troubleshooting', link: '/demo/troubleshooting' },
        ],
      },
      {
        text: 'Reference',
        collapsed: false,
        items: [
          { text: 'Performance checklist', link: '/reference/checklist' },
          { text: 'Benchmarks', link: '/reference/benchmarks' },
          { text: 'Profiling toolkit', link: '/reference/profiling-toolkit' },
          { text: 'Endpoints', link: '/reference/endpoints' },
          { text: 'FAQ', link: '/reference/faq' },
          { text: 'Glossary', link: '/reference/glossary' },
        ],
      },
      {
        text: 'About',
        collapsed: false,
        items: [{ text: 'Speaker, talk and license', link: '/about' }],
      },
    ],

    socialLinks: [{ icon: 'github', link: REPO }],

    search: { provider: 'local' },

    editLink: {
      pattern: `${REPO}/edit/main/site/:path`,
      text: 'Edit this page on GitHub',
    },

    lastUpdated: {
      text: 'Last updated',
    },

    outline: [2, 3],

    docFooter: { prev: 'Previous', next: 'Next' },

    footer: {
      message: 'Released under the MIT License. Speaker: Satyam Soni, PyCon Hong Kong 2026.',
      copyright: 'Copyright © 2026 Satyam Soni',
    },
  },
})
