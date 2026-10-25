# Phase 3 M5: page-by-page parity check

## Goal
A report that compares every main-site page built locally with live https://thec3.uk, so Andy can decide on cutover.

## Tasks
1. A script under `scripts/` (not shipped in `dist/`) that serves `dist/`, and for every page in `site_pages()` takes Playwright screenshots of local and live at 1440px and 390px and records HTTP status, `<title>`, meta description, canonical and the list of link targets on both.
2. Also check every generated redirect against live: same status code class and same target.
3. Write `docs/plans/phase-3/evidence/m5/REPORT.md`: a table of pages with a status and notes. Status: **match** = no visible difference; **minor** = only spacing or font rendering differs; **differs** = content, links or layout differ. Include the redirect comparison, and anything the live site has that the build lacks. Link screenshots.
4. Fix port bugs (in the earlier milestones' files, with a test each). Content or design differences (the live content or styling itself) are not changed; list them in the report for Andy.

## Exit checks
- Report covers all pages and all redirects.
- `uv run pytest` green, `just build main` succeeds.

## Out of scope
Creating the Netlify preview site, DNS, Cloudflare and Netlify forms settings: Andy's cutover steps.
