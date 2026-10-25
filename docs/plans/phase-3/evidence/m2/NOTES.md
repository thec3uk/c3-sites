# Phase 3 M2: local vs live, slices

Screenshots taken 25 Oct 2026 with plain Playwright (default user agent) by `screenshots.py`. Each page is shot at 1440 and 390 wide: `<page>-<width>-live.jpg` (https://thec3.uk) and `<page>-<width>-local.jpg` (`dist/` from `just build main`).

## Page set

`page_set.py` searches `site_pages()` for the smallest set of pages that together use every slice variation on thec3.uk. That's 12 variations on 40 pages. The smallest cover is 7 pages, and 4 different 7-page sets would do. The script picked the one with the fewest slices:

| Page | Variations |
|---|---|
| /acceptable-use/ | header/textOnlyHero, text, quick_links_block, social_links_block |
| /belief/ | header/heroWithImage, text, media/default |
| /contact/ | header/heroWithCustomComponent (contact_form) |
| /impact/ | header/heroWithImage (full bleed), text, quick/social links, card/imageCard |
| /kids/ | header/heroWithImage, card/default, faq_section |
| /room-hire/ | header/heroWithImage, text, quick/social links, button/default-slice |
| /subscribe/ | card/newsletterLocationSlice |

Four variations in the brief's list are on no thec3.uk page: header/default-slice (renders nothing), media/blockImage, footer/default-slice and contact_form/default-slice. Tests render the real samples of all four (`tests/test_main_slices.py`).

All 14 local screenshots are the same height as their live pair, to the pixel. A pixel diff finds differences only inside photos (different image sizes and resampling) and in the contact form's select arrow.

## Port bugs fixed (each has a test)

1. Rich text that holds image blocks (the /room-hire/ text slices) printed as a Python list. Image blocks have no `spans`, so the source didn't recognise the field as rich text.
2. FAQ dividers sat under each question. Tailwind 4's `divide-y` borders the bottom of items, where v3 bordered the top. The template now uses explicit top borders.
3. Image cards were 360px tall, not 400px. M1's custom `min-h-90` (25rem) lost to v4's built-in `min-h-90` (22.5rem); v4's `min-h-100` is 25rem.
4. Newsletter card: the label-to-input gap was 4px short. v4's `space-y-1` puts its margin on the inline label, where it has no effect. The button gap was 8px too big, because v4's `space-y-3` no longer overrides the button's `mt-2`.
5. Social links: at mobile widths the icons were 4px off. v4's `space-x-2` spaced the icon even while its label was hidden.
6. An image card with no image ("Working with Business" on /impact/) rendered as a white card. Live renders it as an empty cell.

## Kept as live, for Andy to decide

These are bugs or quirks in the Gatsby site that show on live. M2 reproduces them for parity. Each is a one-line template change if you'd rather fix them.

- **Text slice titles never show.** Gatsby's query never fetched the `title` field. Six text slices have one: four on /visionandvalues/ ("Why are we called C3 Church?", "Our Beliefs", ...), /join-us/ ("How to apply for roles") and /values/.
- **FAQ title never shows.** Gatsby's query renamed it to `faqTitle`, but the component reads `title`. "Kids Church FAQ's" is missing on /kids/.
- **The newsletter button says "Subscribe"**, hard-coded. The card's `ctaTitle` ("Sign me up Scotty") is never used.
- **The /subscribe/ card is wrapped in `layout.Main` twice**, which doubles its margins on desktop. Reproduced.
- **A card with no colour** falls back to Gatsby's "teal", which has no classes, so it shows unfilled with a shadow.

## Deliberate differences

- **Alt text**: we use Prismic's alt text, or `alt=""` when it's empty. Gatsby filled empty alts with "Needs an alt text", "An Image needing an alt text" or "No Alt provided please email hello@thec3.uk". Most thec3.uk images have no alt in Prismic, which is worth fixing at the source.
- **Images** are imgix URLs at Gatsby's breakpoints (750, 1080, 1366, 1920) with layout-based `sizes`. Live's srcsets went up to the original width, as much as 7952px.
- **The FAQ** uses `<details>`/`<summary>`, so it works without JS and the answers are in the HTML. Live used a Headless UI button, and its answers only appear once opened.
- **The contact form category** is a native `<select>` (styled by the forms plugin) instead of Headless UI's listbox. M2 only renders the form: it has no Netlify attributes and no hidden `email_recipient`/`category_name` fields. The Send button is shown disabled and pale, as live shows it before the form is valid. Submission and validation are M3's.
- **The newsletter form** has no action. Mailchimp is M3's.
- **Slice anchor ids** such as `id="text$4a80…"` aren't emitted.
- **Empty elements** that render nothing are left out: an empty eyebrow `<h3>`, and the empty prose `<div>` on cards with no content.
- **Internal links** end in `/` (README URL decision). Rich-text external links get `rel="noopener"` (from the existing models) where live has `noreferrer`.
- **Slices with no Gatsby component**: media/blockImage renders like media/default. footer/default-slice and contact_form/default-slice fall back to the shared default templates, where Gatsby's SliceZone rendered nothing. None of them is on a thec3.uk page.
