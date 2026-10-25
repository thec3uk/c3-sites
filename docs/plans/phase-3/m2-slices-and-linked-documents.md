# Phase 3 M2: main-theme slices and linked documents

## Goal
Every slice variation used on thec3.uk renders like the live site, including quick-links and social-links blocks, which need the content of another Prismic document.

## Read first
- c3-sites: `content/models.py`, `content/sources/prismic.py`, `pages/templatetags/slices.py`, `templates/slices/` (shared defaults), `tests/test_default_slices.py`, `tests/fixtures/slice_samples.json`
- Gatsby: `src/slices/` and `src/components/` for each slice; `components/quickLinks.tsx`, `socialLinks.tsx`, `aside.tsx`

## Slice variations in real use (25 Oct 2026)
button/default-slice x41 · card/default x106 · card/imageCard x5 · card/newsletterLocationSlice x1 · contact_form/default-slice x1 · faq_section/default x1 · footer/default-slice x4 · header/default-slice x10 · header/heroWithCustomComponent x1 (componentName `contact_form`) · header/heroWithImage x26 · header/textOnlyHero x13 · media/blockImage x4 · media/default x6 · quick_links_block/default x13 · social_links_block/default x14 · text/default x50

## Tasks
1. Linked documents. Document links currently become a URL string, and links to uid-less documents (quick-links, social-links) become `""`. Change the source layer so a Document link becomes a `Link`: a `str` subclass (so `{{ link }}` still prints the URL and existing tests hold) that also carries the target document's `id` and `type`. Add a template filter `linked_document` that returns the converted `Page` for a `Link` from `site_documents()`, or `None`. Tests first, using the real quick-links and social-links documents saved as fixtures.
2. Main-theme templates in `themes/main/templates/slices/`, one per type, or per variation where markup differs (`slices/<type>/<variation>.html`). Port classes from the Gatsby components. `header/default-slice` renders nothing (decided). Layout wrappers (Gatsby `layout.Aside`, `Main`, full bleed) belong in these templates.
3. Social links: a social-links document has `instagramUrl`, `facebookUrl`, `youtubeUrl` (any may be empty) and `title`. Quick links: `title` plus `slices` of `link` with `primary.title` (rich text) and `primary.url`.
4. Images through the `imgix` filter with sizes matching the Gatsby layout; `alt` from Prismic.
5. Extend `tests/test_default_slices.py` (or a sibling) to render every sample with the main theme and assert key content appears.

## Exit checks
- `uv run pytest` green; `just build main` succeeds with no missing-slice errors.
- Playwright screenshots, local vs live at 1440px and 390px, of the smallest set of pages that together use every variation above (choose them with a script over `site_pages()`, and list them in the commit message). Save under `docs/plans/phase-3/evidence/m2/`.
- Differences: fix port bugs (with a test). Content or design differences (the live content or styling itself) are not changed; list them in `evidence/m2/NOTES.md` for Andy.

## Out of scope
Form submission behaviour (M3): the contact form and newsletter card render here but needn't submit yet.
