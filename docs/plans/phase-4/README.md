# Phase 4: My C3 (myc3.life) on Django

Port `myc3` (Next.js 14, server-rendered on Netlify) to c3-sites as the `myc3` site, page for page. Move the Prismic schemas out of the Next repo. Built and checked locally; no DNS, Netlify or Prismic changes.

## Order

1. [M1 site shell and slices](m1-site-shell-and-slices.md): site config, theme, home uid, all 8 slices, background images, fonts, Umami
2. [M2 form, redirects and sitemap](m2-form-redirects-sitemap.md): Netlify contact form, `_redirects`, sitemap.xml
3. [M3 schemas](m3-schemas.md): all custom types and slice models into `schemas/`, read-only `prismic_schemas diff`
4. [M4 parity check](m4-parity-check.md): every page and redirect compared with live https://myc3.life

Each milestone depends on the ones before it, except M3, which only needs the repo.

## Facts (25 Oct 2026)

- Next source, reference only: `~/c3/creative/websites/myc3`. Don't edit it.
- Pages: every `page` tagged `domain:myc3.life`, 15 today. Five are also tagged `domain:thec3.uk` (trustees, online, cambridge, team, visionandvalues); on myc3 they render with the myc3 theme.
- Slices in use: `header` (default-slice, heroWithImage, textOnlyHero), `button`, `text`, `card`, `media` (default, blockImage), `footer`, `contact_form`. `link` exists in the Next repo but no page uses it.
- Live serves 185 redirects tagged `domain:myc3.life` (307 if `permanent` is false, 308 if true).
- Umami: website id `231a1dee-01c4-422e-adbc-d253914fe38c`, src `https://analytics.myc3.life/script.js`.

## Decisions already made (25 Oct 2026)

- URLs: uid `myc3` is `/`; any other uid is `/<uid>/`. Links to other documents follow the Next resolver: `page` and `redirect` documents go to `/<uid>/`; anything else goes to `/`. The uid `thec3.uk_about` therefore becomes `/thec3.uk_about/` on myc3, as it does on live.
- Redirects honour `permanent`: 301 if true, else 302 (live's 308/307 are the same classes).
- Where a redirect and a page share a path (today only `/alpha/`), the page wins, as on the main site. Live serves the redirect instead; M4 lists each such path for Andy.
- The `header` slice renders the same markup for all three variations, as in Next.
- Not ported: Storybook, the Slice Machine simulator, Prismic previews (`pages/api/preview.js`), the `header-based-gating` Netlify plugin, and the notification banner (Next never rendered it).
- Schemas: c3-sites becomes their source of truth. Phase 4 adds a read-only diff against Prismic only; pushing schemas is a later, explicit step.
- Extra SEO tags from the shared `base.html` (title, description, canonical, Open Graph) are accepted even though live has none; M4 lists them as additions.

## Rules for every milestone

- Work in `~/c3/creative/websites/c3-sites` on `main`. Commit small; message `Phase 4 M<n>: <what>`. Never push.
- TDD: failing test first (`uv run pytest`), then code. Full suite green before each commit.
- Read Prismic only: Content API, and the Custom Types API with `PRISMIC_CUSTOM_TYPES_API_TOKEN` from `.env`, for GET requests only. Never print the token. Never write to Prismic, Netlify, DNS or GitHub.
- Don't submit real forms; mock the network in tests.
- Templates receive `Page`/`Slice` objects only (see `content/models.py`); no Prismic JSON in templates. Prismic text in HTML attributes goes through the `plain` filter.
- Tailwind v4 via `scripts/build.sh`; theme tokens go in `themes/myc3/css/site.css` under `@theme`, using `source(none)` plus explicit `@source` lines, as in the Academy theme.
- `just build myc3`, `just build main` and `just build academy` must all succeed at the end of every milestone. Main and Academy output must not change except where a milestone says so.
- Live requests use an honest user agent such as `c3-sites parity-check`.

## After Phase 4 (Andy)

- Create Netlify preview sites for `main` and `myc3` (build command and publish dir as in `netlify.toml`, `SITE` set per site) and a Prismic webhook to each site's build hook.
- On each preview, check that `/about` redirects to `/about/` and the contact form appears under Netlify Forms.
