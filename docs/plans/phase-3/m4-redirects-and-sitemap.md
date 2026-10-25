# Phase 3 M4: redirects and sitemap

## Goal
The build writes every Prismic redirect for the site into `dist/_redirects` and a `sitemap.xml`, so the new site serves the same short links as live thec3.uk.

## Read first
- c3-sites: `content/audit.py` (redirect rows), `scripts/build.sh` (copies `themes/<site>/public/` into `dist/`), `themes/academy/public/_redirects`
- Gatsby: redirect creation in `gatsby-node.js`

## Facts
- Live thec3.uk serves 294 Prismic redirects (all sites; filter by the site's tags) via Gatsby's Netlify adapter, all as 301 because of `permanent || true`.
- A redirect's source is `/<uid>`; Gatsby also adds `/<UID>` uppercase. Its target is `destination`: Web/Media URL, or a Document link resolved with the site's domain.
- Decision: 301 if `permanent` is true, else 302.

## Tasks
1. A function that turns the site's redirect documents into `_redirects` lines (`/from /to 301|302`), skipping ones with no destination or a deleted target and logging each skip. Tests first with fixtures.
2. Add an uppercase `/<UID>` line for each redirect, as Gatsby did, unless Netlify's docs clearly say redirect paths match case-insensitively. If the docs don't settle it, add them (duplicates are harmless). Cite the doc page, or note it was unclear, in a code comment.
3. Write it as a distill URL (`distill_file="_redirects"`, `text/plain`). Change `scripts/build.sh` so the theme's static `public/_redirects` rules come first and the generated ones follow, instead of overwriting. Academy's output must be unchanged.
4. Rules that would be shadowed by a real page (same path) are not forced; list them in the build log.
5. `sitemap.xml` for every page via a distill URL (Django's sitemap framework is fine if it needs no database; otherwise a template). Add `Sitemap:` to a `robots.txt` in `themes/main/public/`.

## Exit checks
- `uv run pytest` green; `just build main` and `just build academy` succeed.
- Count of generated rules equals the site's redirect documents minus logged skips.
- `uv run python manage.py prismic_audit --type redirect --site main` agrees with the generated file on every source path.
