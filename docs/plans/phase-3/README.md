# Phase 3: main site (thec3.uk) on Django

Port `new_to_church` (Gatsby 5) to c3-sites as the `main` site, with page-for-page parity, built and checked locally. No DNS, Netlify or Prismic changes.

## Order

1. [M1 site shell](m1-main-site-shell.md): site config, theme, nav, banner, footer, SEO, 404, manifest
2. [M2 slices](m2-slices-and-linked-documents.md): main-theme slice templates, linked documents (quick/social links)
3. [M3 forms](m3-forms.md): contact form (Netlify Forms), newsletter cards (Mailchimp)
4. [M4 redirects and sitemap](m4-redirects-and-sitemap.md): Prismic redirects into `_redirects`, sitemap.xml
5. [M5 parity check](m5-parity-check.md): every page compared with live thec3.uk

Each milestone depends on the ones before it.

## Decisions already made (25 Oct 2026)

- URLs stay flat `/<uid>/`; `parent_page` is not used for URLs. uid `thec3.uk` is `/`, `thec3.uk_<slug>` is `/<slug>/` (already in `resolve_link`).
- `header/default-slice` renders nothing on the main site, as in Gatsby.
- Redirects honour Prismic's `permanent` field: 301 if true, else 302.
- No search in Phase 3; Pagefind comes after cutover.
- Unused Gatsby features are not ported: map, carousel, video hero, Algolia, Prismic previews.
- Open backlog in new_to_church (10 Dependabot PRs, 2019 search PR, 2022 issues) is Andy's to close; not part of these milestones.

## Rules for every milestone

- Work in `~/c3/creative/websites/c3-sites` on `main`. Commit small; message `Phase 3 M<n>: <what>`. Never push.
- TDD: failing test first (`uv run pytest`), then code. Full suite green before each commit.
- Read Prismic only (Content API, no token needed). Never write to Prismic, Netlify, DNS or GitHub.
- Gatsby source is reference only: `~/c3/creative/websites/new_to_church`. Don't edit it.
- Templates receive `Page`/`Slice` objects only (see `content/models.py`); no Prismic JSON in templates.
- Tailwind is v4 via `scripts/build.sh`; theme tokens go in `themes/main/css/site.css` under `@theme`.
- `just build main` must succeed at the end of every milestone.
