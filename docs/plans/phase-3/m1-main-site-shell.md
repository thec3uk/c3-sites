# Phase 3 M1: main site shell

## Goal
`just build main` produces a `dist/` whose pages have the live site's layout: nav, announcement banner, footer, SEO tags, 404 page and web manifest. Slice styling is M2.

## Read first
- c3-sites: `config/settings/sites/academy.py`, `templates/base.html`, `themes/academy/` (the pattern to copy), `pages/content.py`, `scripts/build.sh`
- Gatsby: `src/components/layout.tsx`, `layout.css`, `nav/` (not `nav/search/`), `announcement.tsx`, `footer/`, `SEO.tsx`, `src/pages/404.tsx`, `tailwind.config.js`, `gatsby-config.js` (manifest, umami), `static/`

## Tasks
1. Add `config/settings/sites/main.py`: name `main`, domain `thec3.uk`, theme `main`, `prismic_tags=("domain:thec3.uk",)`, `page_types=("page",)`, Umami id `ee3c430d-e2d2-4256-973e-7c0be0223d63`, src `https://analytics.thec3.uk/script.js`. Test like `tests/test_sites.py`.
2. Create `themes/main/`: port `tailwind.config.js` (Tailwind 3) and `layout.css` into `themes/main/css/site.css` as v4 `@theme` tokens and plain CSS. Copy only the fonts and images the templates use into `themes/main/static/`. Put `favicon.ico` in `themes/main/public/`.
3. Layout: don't create `themes/main/templates/base.html`. Theme templates are found before shared ones, so it would shadow the shared base, and `{% extends "base.html" %}` inside it would load itself. Instead create `themes/main/templates/layout.html` that extends `base.html` and adds the nav, banner and footer around the page content, and override `pages/page.html` in the theme to extend `layout.html`. Add blocks to the shared `base.html` only if needed, without changing Academy's output (Academy tests must still pass).
4. Nav: the 6 hard-coded links in `nav/menu.tsx` and the logo linking to `/`. Mobile menu (Gatsby issue #55 says it is broken; this is the required behaviour): below the `lg` breakpoint a menu button opens a full-screen panel with the logo and the same 6 links, using the markup in Gatsby `nav/index.tsx`. It closes on the button, a link click or Escape; focus moves into the panel when it opens and back to the button when it closes; body scroll is locked while open. Use Alpine JS from a CDN with an exact version.
5. Banner: `notification_banner` document via `site_document("notification_banner")`. Show only when `active == "yes"`. Dismissal is remembered in `localStorage` key `NOTIFICATIONBAR` with the same `{message, closed}` shape as Gatsby, using Alpine. Test both active and inactive.
6. Footer: `static_footer` document, each `link_list` slice a titled list of `link_title`/`link_url`, plus "Charity number: 1132699".
7. SEO: match `SEO.tsx` (title format, description, canonical, Open Graph, Twitter) using the page's `seo_title`, `seo_description`, `seo_image` with `site_config` as fallback. Test the fallback.
8. 404: a distill URL writing `404.html` (Netlify serves it for missing paths) for every site, with a themed template for main. The view returns status 404, so register it with `distill_status_codes=(404,)`; distill fails the build on any other status by default. Test it renders.
9. Manifest: a static `manifest.webmanifest` in `themes/main/public/` with the values from `gatsby-config.js`, linked from base.

## Exit checks
- `uv run pytest` green; `just build main` and `just build academy` both succeed.
- `dist/` for main has an `index.html` for every page `site_pages()` returns (40 on 25 Oct 2026), plus `404.html`.
- Playwright test at 390px: the menu opens, closes on the button, a link and Escape, and focus returns to the button.
- Serve `dist/` locally and compare `/` and `/about/` with https://thec3.uk at 1440px and 390px with Playwright screenshots: nav, banner (when active), footer match. Save screenshots under `docs/plans/phase-3/evidence/m1/`.

## Out of scope
Slice templates (M2), forms (M3), redirects and sitemap (M4), search.
