# Phase 4 M1: site shell and slices

## Goal
`just build myc3` produces a `dist/` with an `index.html` for every myc3 page, looking like live https://myc3.life at 1440px and 390px.

## Read first
- c3-sites: `config/settings/sites/` (`SiteConfig`, `main.py`), `content/prismic_client.py` (`resolve_link`), `content/sources/prismic.py`, `templates/base.html`, `themes/main/` and `themes/academy/` (the theme pattern), `scripts/build.sh`
- Next: `pages/index.js`, `pages/[uid].js` (page background image), `pages/_app.js`, `pages/_document.js`, `prismic-configuration.js` (`linkResolver`), `slices/*/index.js`, `slices/Media/fullbleed.jsx`, `styles/`, `tailwind.config.js`

## Tasks
1. Add `config/settings/sites/myc3.py`: name `myc3`, domain `myc3.life`, theme `myc3`, `prismic_tags=("domain:myc3.life",)`, `page_types=("page",)`, plus the Umami id and src from the README. Test like `tests/test_sites.py`.
2. Link resolution per site. Add a field to `SiteConfig` that selects the URL rule, so myc3 gets the README's rule (uid `myc3` is `/`; `page` and `redirect` uids are `/<uid>/`; other types are `/`) and main and Academy keep their current rule. Test both rules, including a myc3 link to `thec3.uk_about`. Main and Academy output stays byte-identical: build both before and after and `diff -r` their `dist/`.
3. Create `themes/myc3/`: port `tailwind.config.js` (Tailwind 3) colours, fonts and the typography plugin settings it uses into `themes/myc3/css/site.css` as v4 `@theme` tokens. Self-host DM Serif Display and Montserrat (the weights the CSS uses) in `themes/myc3/static/`; put `favicon.ico` in `themes/myc3/public/`.
4. Layout: `themes/myc3/templates/layout.html` extends the shared `base.html` and wraps the page in the Next page wrapper (`bg-gray-50`, full height). It sets the page's `background_image` as a CSS background when present. Override `pages/page.html` in the theme to extend it. Don't create a theme `base.html`, because it would shadow the shared one.
5. Slices: `themes/myc3/templates/slices/` for `header` (one template for all three variations), `button`, `text`, `card`, `media` (`default` full-bleed and `blockImage`), `footer` and `link`. Match the Next markup and classes. Each slice gets a test on its rendered HTML.
6. 404: the shared 404 template inside the myc3 layout (override the theme's `404.html` only if the shared one can't take the layout). Don't copy Next's default 404; M4 lists the difference.
7. `contact_form` gets a placeholder template that renders nothing; M2 replaces it. The page must still build.

## Exit checks
- `uv run pytest` green; `just build myc3`, `just build main` and `just build academy` succeed. Main and Academy `dist/` unchanged apart from intended additions (state any in the commit).
- `dist/` for myc3 has `index.html` at `/` and at `/<uid>/` for every other page that `site_pages()` returns (15 on 25 Oct 2026), plus `404.html`.
- Serve `dist/` and compare `/`, `/growth-path/` (background image), `/trustees/` (shared with thec3.uk) and `/next-steps/` with live at 1440px and 390px using Playwright screenshots. Save them under `docs/plans/phase-4/evidence/m1/`. First widen the `.gitignore` image rules from `docs/plans/phase-3/evidence/` to `docs/plans/*/evidence/`, so screenshots are never committed.

## Out of scope
The contact form (M2), redirects and sitemap (M2), schemas (M3).
