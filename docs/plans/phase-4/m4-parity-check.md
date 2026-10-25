# Phase 4 M4: page-by-page parity check

## Goal
A report that compares every myc3 page built locally with live https://myc3.life, so Andy can decide on the preview and cutover.

## Read first
- c3-sites: `scripts/parity_check.py`, `tests/test_parity_check.py`, and `docs/plans/phase-3/evidence/m5/REPORT.md` (the format to follow)

## Tasks
1. Make `scripts/parity_check.py` work for any site: the site name and live base URL come from the site config or arguments, not constants. While in there, fix three gaps found in Phase 3:
   - Classify each page in code, with the thresholds written as constants in the script.
   - Treat a bare-domain target with and without a trailing `/` as the same target.
   - Read the old site's static folder from an argument instead of a hard-coded path.
   - Test the classifier and the redirect comparison with the network mocked.
   - Re-run the classifier on Phase 3's `docs/plans/phase-3/evidence/m5/results.json`. Pick the thresholds that reproduce the most Phase 3 labels (30 match, 10 minor, 1 differs). List any main-site page that now classifies differently in the M4 report. Don't edit Phase 3's report.
2. Run it for myc3: every page in `site_pages()` at 1440px and 390px, plus the 404 page. Record status, `<title>`, meta description, canonical and link targets on both sides. Check every generated redirect against live: same status class (301 vs 308, 302 vs 307) and same target.
3. Write `docs/plans/phase-4/evidence/m4/REPORT.md` and `results.json`. Use Phase 3's statuses (**match**, **minor**, **differs**), and include:
   - the redirect comparison;
   - every path where live serves a redirect but the build serves a page (`/alpha/` today);
   - the SEO tags the build adds over live;
   - anything live has that the build lacks.
   Screenshots stay local (git-ignored).
4. Fix port bugs in the earlier milestones' files, with a test each. Don't change content or design differences in the live content or styling itself; list them in the report for Andy.

## Exit checks
- The report covers all pages and all redirects.
- `uv run pytest` green; the three builds succeed.

## Out of scope
Creating the Netlify preview sites, DNS, and Netlify forms settings: Andy's steps (see the README).
