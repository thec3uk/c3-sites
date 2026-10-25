# Phase 4 M2: contact form, redirects and sitemap

## Goal
The `/share-your-story/` contact form submits to Netlify Forms with live's validation and thank-you behaviour. `dist/_redirects` holds every myc3 redirect, and `dist/sitemap.xml` lists every page.

## Read first
- Next: `slices/ContactForm/index.js`, `slices/ContactForm/model.json`, `public/__forms.html`, the redirect branch of `pages/[uid].js`
- c3-sites: Phase 3's contact form (`themes/main/templates/slices/` and `themes/main/static/js/site.js`), `pages/redirects.py`, the sitemap view, `tests/test_redirects.py`

## Facts
- The form name comes from the slice's `form_name`, defaulting to `contact`. The fields are `name`, `email`, `category` (a select filled from the slice items, required only when there are items), `subject`, `message` and `consent` (a checkbox, sent as `yes`/`no`). All are required, and email is format-checked.
- Next posts url-encoded data to `/__forms.html` only because a server-rendered Next page can't be detected by Netlify. A static build can carry the form in the page itself.
- Netlify only accepts a form it found in the deployed static HTML. That means `data-netlify="true"`, a hidden `form-name` input and a honeypot field must be in the built page.

## Tasks
1. Contact form template: plain HTML that works without JS (it posts, and Netlify shows its default success page). Enhance it with Alpine, reusing Phase 3's approach: client-side validation with Next's error messages, a `fetch` POST to `/`, and `thank_you_message` swapped in on success. Don't carry over `__forms.html`. Write tests on the rendered HTML (Netlify attributes, `form-name`, honeypot, fields, categories) and a browser test (marked `browser`) with the network mocked.
2. Redirects: generate `_redirects` for myc3 with the existing redirect code, selected by tag `domain:myc3.life`. Keep the safety rules (no whitespace or control characters; targets http(s) or `/`-relative, not `//` or `/\`). Where a redirect shadows a page (today `/alpha/`), the page wins and the build logs it. Test the myc3 rule count against fixture documents, plus the shadowing case.
3. Sitemap: `sitemap.xml` for myc3 with the same rules as main (every built page, canonical trailing-slash URLs, no 404).

## Exit checks
- `uv run pytest` green; the three builds succeed.
- The built `/share-your-story/` form passes Netlify's form detection rules (check against Netlify's Forms docs and note the URL in the commit).
- `dist/_redirects` for myc3 has one rule per valid redirect, plus uppercase twins as on main. Any skipped redirects are listed in the commit message with their reason.

## Out of scope
Netlify form notifications (Andy, in the Netlify UI, at cutover).
