# Phase 3 M5: thec3.uk parity check

Every main-site page built locally (`just build main`, `dist/`) compared with live https://thec3.uk on 25 Oct 2026, plus every generated redirect. Use it to decide on cutover.

## Summary

- **Pages: 41** (40 from `site_pages()` plus the 404 page). **30 match, 10 minor, 1 differs.** No page differs in visible content or layout.
- **Redirects: 242** (one per Prismic redirect document; the uppercase twins weren't requested). **All 242 have the same status class (3xx) and the same target.** 231 Location headers are byte-identical. In the other 11, live adds a `/` after a bare domain (`https://store.thec3.uk` becomes `https://store.thec3.uk/`), which is the same URL.
- **Status codes:** 100 redirects are 301 on both. 142 are 302 in the build because Prismic `permanent` is false, while live sends 301 for every redirect. That is the decided behaviour (README).
- **Two port bugs were found and fixed** (see below). The pages they affected are now pixel-identical to live.
- **Nothing blocked the check.** It used plain Playwright and httpx with the user agent `c3-sites parity-check (+https://thec3.uk)`. Requests were sequential, read-only and sent no form submissions. Umami requests were blocked on both sides so the check doesn't count as visits.

## How it was checked

`scripts/parity_check.py` (run `SITE=main uv run python scripts/parity_check.py` after `just build main`) serves `dist/` locally and does the following for each page:

- It takes full-page screenshots of live and local at 1440x900 and 390x844, after scrolling and waiting for visible images.
- It records the HTTP status, `<title>`, meta description, canonical, every `a[href]` and the visible text.
- It diffs the two screenshots pixel by pixel (a pixel differs if a channel changes by more than 48). The tables give the share of pixels that differ.

Live is requested at its own URL without the trailing slash (e.g. `/about`), which skips live's 301 from `/about/`. Raw data is in [results.json](results.json). Desktop screenshots are saved at half size (720px wide); the diff itself was done at full size. A `-diff.jpg`, which marks differing pixels in red over a faded local shot, is saved only where the heights differ or more than 0.2% of pixels differ.

Status meanings: **match** means no visible difference. **minor** means only sub-pixel spacing or photo resampling differs. **differs** means content, links or layout differ.

## Port bugs fixed in M5 (each with a failing test first)

1. **`/racial-unity/`: the hero printed "None".** The hero has one link item with no title and no link. `slices/header/_text.html` rendered `{{ item.linkTitle }}` without a default; live renders an empty link. Fix: `|default:""`. Test: `test_hero_link_with_no_title_renders_empty_not_none`. Commit 16ff0d6.
2. **`/trustees/`: cards with no content were 16px shorter than live.** M2 left out the empty `prose` div, but in Gatsby it always renders, and inside `space-y-4` it adds a 16px gap before the button. The difference added up to 16px (1440) and 64px (390) over the page. Fix: `slices/card/default.html` always renders the div. Test: `test_card_without_content_keeps_its_empty_prose_div`. Commit d670e19. (This corrects one line of the "Deliberate differences" in `evidence/m2/NOTES.md`.)

## For Andy: differences that are decided or are content

Decided earlier, recorded here and not changed:

- **Meta description fallback** (39 pages, every page without its own `seo_description`). The build uses Prismic site_config: "...based in the UK. With locations in Bury St Edmunds, Cambridge, Colchester and online!". Live uses Gatsby's hard-coded text: "...based in Cambridge, Bury St Edmunds, Colchester, England and online." Edit site_config in Prismic if you want live's wording. The title and image match.
- **Trailing slashes.** Live's canonical URLs and sitemap have no trailing slash (`https://thec3.uk/about`), and live 301s `/about/` to `/about`. The build uses `/about/` (README decision), so every canonical, sitemap URL and internal link differs only by the slash. Expect search engines to re-crawl after cutover. Check on the Netlify preview that `/about` reaches `/about/` (not verified here).
- **Redirect status:** 302 when Prismic `permanent` is false (142 redirects), where live sends 301 for all of them. If any of these should stay permanent, tick `permanent` in Prismic.
- **The mobile menu is in the HTML.** Every page has 6 more links in the DOM than live (`/about`, `/reaching`, `/shaping`, `/giving`, `/locations`, `https://prayer.thec3.uk/`). They are the mobile menu, which is in the DOM but hidden; Gatsby only mounts it when it's opened. There's no visible difference.
- `header/default-slice` renders nothing. Alt text comes from Prismic. The Gatsby quirks in `evidence/m2/NOTES.md` are kept: text-slice titles and the /kids/ FAQ title are hidden, the newsletter button says "Subscribe", and so on. Also kept from M2: native `<select>` on /contact/ and `<details>` FAQ answers on /kids/ (in the DOM, not visible until opened).
- **Empty links not reproduced.** Live has `<a href="">` with no text in the /racial-unity/ hero, and an empty `<a>` in the image cell of the image-less "Vision, Values and Core Beliefs" card on /trustees/. They're invisible, but they are keyboard tab stops with no text. The build renders the hero link without `href` and leaves out the card one.

Content issues for Andy (both live and build):

- **/colchester/: "Watch at Church Online" links to `www.church-online.uk` with no `https://`**, so browsers treat it as a relative path. It 404s on live (`/www.church-online.uk`) and will 404 on the build (`/colchester/www.church-online.uk`). Fix the link in Prismic.
- **Redirect `/kidschurch` targets `/kids-church/`**, which is itself a redirect (to the Notion page), so it takes two hops on both. The same goes for `/hamper` → `/shop/` → store and `/ascendcamp22` → `/ascendcamp/` → Brushfire. These work, and could point straight at the final URL.
- Redirects `/test-page-here` (→ google.com) and `/broken-link` (→ google.com) look like leftovers in Prismic.

## What live has that the build lacks

- **Root-level files from Gatsby's `static/`**, each 200 on live, will 404 after cutover unless they are copied to `themes/main/public/`: `/card.jpg`, `/live.jpg`, `/live2.jpg`, `/manifest-logo.png`, `/home/1.jpg` ... `/home/7.jpg` and `/home/1-rect.jpg` ... `/home/4-rect.jpg`, and `/fonts/*.otf` (5 fonts). No built page uses them; the build serves the logo and the two fonts it uses under `/static/`. They might be linked from emails or other sites, so keep them if any of those links exist. (`favicon.ico` and `social_share.jpeg` are in the build.)
- **Live sitemap** (`/sitemap-index.xml` → `/sitemap-0.xml`) has 42 URLs: our 40 plus `/page` and `/preview`. Those two are Gatsby's page template rendered with no data and the Prismic preview page; previews aren't ported (README). The build's sitemap is `/sitemap.xml` (40 URLs, listed in `robots.txt`). Live has no `robots.txt` and no `/sitemap.xml`. Resubmit the sitemap in Search Console after cutover.
- **The live 404 page has an empty `<title>`;** the build's is "Page not found | The C3 Church". Both look the same.
- Nothing visible on any page exists on live but not in the build.

## Pages

Screenshot links are relative to this folder.

| Page | Status | 1440 height live/local, diff | 390 height live/local, diff | Screenshots 1440 | Screenshots 390 | Notes |
|---|---|---|---|---|---|---|
| `/` | **match** | 2224/2224, 0.06% | 3023/3023, 0.03% | [live](home-1440-live.jpg) / [local](home-1440-local.jpg) | [live](home-390-live.jpg) / [local](home-390-local.jpg) |  |
| `/about/` | **minor** | 1588/1588, 0.01% | 2280/2279, 1.10% | [live](about-1440-live.jpg) / [local](about-1440-local.jpg) | [live](about-390-live.jpg) / [local](about-390-local.jpg) ([diff](about-390-diff.jpg)) | Sub-pixel card heights: 390 page 1px shorter; text and links identical. |
| `/acceptable-use/` | **match** | 3454/3454, 0.00% | 4238/4238, 0.00% | [live](acceptable-use-1440-live.jpg) / [local](acceptable-use-1440-local.jpg) | [live](acceptable-use-390-live.jpg) / [local](acceptable-use-390-local.jpg) |  |
| `/belief/` | **match** | 3668/3668, 0.01% | 3217/3217, 0.01% | [live](belief-1440-live.jpg) / [local](belief-1440-local.jpg) | [live](belief-390-live.jpg) / [local](belief-390-local.jpg) |  |
| `/bury/` | **minor** | 4430/4430, 0.18% | 6035/6034, 1.53% | [live](bury-1440-live.jpg) / [local](bury-1440-local.jpg) | [live](bury-390-live.jpg) / [local](bury-390-local.jpg) ([diff](bury-390-diff.jpg)) | Sub-pixel shift (390 1px); photo resampling. |
| `/c3-groups/` | **minor** | 2732/2732, 0.01% | 4249/4249, 0.56% | [live](c3-groups-1440-live.jpg) / [local](c3-groups-1440-local.jpg) | [live](c3-groups-390-live.jpg) / [local](c3-groups-390-local.jpg) ([diff](c3-groups-390-diff.jpg)) | Sub-pixel shift at 390; photo resampling. |
| `/cambridge-west/` | **minor** | 4267/4268, 0.60% | 5998/5998, 0.06% | [live](cambridge-west-1440-live.jpg) / [local](cambridge-west-1440-local.jpg) ([diff](cambridge-west-1440-diff.jpg)) | [live](cambridge-west-390-live.jpg) / [local](cambridge-west-390-local.jpg) | Hero photo resampled/cropped slightly differently; 1440 1px taller locally. |
| `/cambridge/` | **minor** | 4710/4710, 0.15% | 7002/7001, 0.72% | [live](cambridge-1440-live.jpg) / [local](cambridge-1440-local.jpg) | [live](cambridge-390-live.jpg) / [local](cambridge-390-local.jpg) ([diff](cambridge-390-diff.jpg)) | Sub-pixel shift (390 1px); photo resampling. |
| `/colchester/` | **differs** | 4402/4402, 0.02% | 5993/5993, 1.86% | [live](colchester-1440-live.jpg) / [local](colchester-1440-local.jpg) | [live](colchester-390-live.jpg) / [local](colchester-390-local.jpg) ([diff](colchester-390-diff.jpg)) | Prismic link `www.church-online.uk` has no `https://`, so it is relative: live resolves it to `/www.church-online.uk`, the build (trailing-slash URL) to `/colchester/www.church-online.uk`. Both 404. Content fix in Prismic. Visually 1px-level shift at 390 only. |
| `/complaints/` | **match** | 6790/6790, 0.00% | 8978/8978, 0.00% | [live](complaints-1440-live.jpg) / [local](complaints-1440-local.jpg) | [live](complaints-390-live.jpg) / [local](complaints-390-local.jpg) |  |
| `/contact/` | **match** | 1298/1298, 0.00% | 1922/1922, 0.00% | [live](contact-1440-live.jpg) / [local](contact-1440-local.jpg) | [live](contact-390-live.jpg) / [local](contact-390-local.jpg) | Visually identical. The DOM differs: the category is a native `<select>` (options present in the HTML), live a Headless UI listbox (decided, M2). |
| `/cookies/` | **match** | 3490/3490, 0.00% | 4374/4374, 0.00% | [live](cookies-1440-live.jpg) / [local](cookies-1440-local.jpg) | [live](cookies-390-live.jpg) / [local](cookies-390-local.jpg) |  |
| `/copyright/` | **match** | 6182/6182, 0.00% | 7998/7998, 0.00% | [live](copyright-1440-live.jpg) / [local](copyright-1440-local.jpg) | [live](copyright-390-live.jpg) / [local](copyright-390-local.jpg) |  |
| `/feedback/` | **match** | 1694/1694, 0.00% | 2102/2102, 0.00% | [live](feedback-1440-live.jpg) / [local](feedback-1440-local.jpg) | [live](feedback-390-live.jpg) / [local](feedback-390-local.jpg) |  |
| `/giving/` | **minor** | 3565/3564, 0.80% | 5125/5125, 1.58% | [live](giving-1440-live.jpg) / [local](giving-1440-local.jpg) ([diff](giving-1440-diff.jpg)) | [live](giving-390-live.jpg) / [local](giving-390-local.jpg) ([diff](giving-390-diff.jpg)) | Sub-pixel shift (1440 1px); photo resampling. |
| `/impact/` | **match** | 4046/4046, 0.01% | 4046/4046, 0.02% | [live](impact-1440-live.jpg) / [local](impact-1440-local.jpg) | [live](impact-390-live.jpg) / [local](impact-390-local.jpg) |  |
| `/join-us/` | **match** | 4320/4320, 0.05% | 7406/7406, 0.06% | [live](join-us-1440-live.jpg) / [local](join-us-1440-local.jpg) | [live](join-us-390-live.jpg) / [local](join-us-390-local.jpg) |  |
| `/kids/` | **match** | 2795/2795, 0.05% | 4355/4355, 0.19% | [live](kids-1440-live.jpg) / [local](kids-1440-local.jpg) | [live](kids-390-live.jpg) / [local](kids-390-local.jpg) | Visually identical. FAQ answers are in the HTML inside closed `<details>`, so their links (`/contact`, `mailto:kids@thec3.uk`) are in the DOM; live adds answers only when opened (decided, M2). |
| `/leafs/` | **match** | 1138/1138, 0.00% | 974/974, 0.00% | [live](leafs-1440-live.jpg) / [local](leafs-1440-local.jpg) | [live](leafs-390-live.jpg) / [local](leafs-390-local.jpg) |  |
| `/locations/` | **match** | 1454/1454, 0.01% | 1574/1574, 0.00% | [live](locations-1440-live.jpg) / [local](locations-1440-local.jpg) | [live](locations-390-live.jpg) / [local](locations-390-local.jpg) |  |
| `/online/` | **minor** | 3601/3600, 0.97% | 4834/4833, 2.71% | [live](online-1440-live.jpg) / [local](online-1440-local.jpg) ([diff](online-1440-diff.jpg)) | [live](online-390-live.jpg) / [local](online-390-local.jpg) ([diff](online-390-diff.jpg)) | Photo resampling; 1px height at both widths. |
| `/ourleaders/` | **minor** | 3259/3258, 0.43% | 5514/5514, 0.16% | [live](ourleaders-1440-live.jpg) / [local](ourleaders-1440-local.jpg) ([diff](ourleaders-1440-diff.jpg)) | [live](ourleaders-390-live.jpg) / [local](ourleaders-390-local.jpg) | Sub-pixel shift (1440 1px). |
| `/privacy/` | **match** | 10698/10698, 0.00% | 14106/14106, 0.00% | [live](privacy-1440-live.jpg) / [local](privacy-1440-local.jpg) | [live](privacy-390-live.jpg) / [local](privacy-390-local.jpg) |  |
| `/problem-solving/` | **match** | 10602/10602, 0.00% | 12482/12482, 0.00% | [live](problem-solving-1440-live.jpg) / [local](problem-solving-1440-local.jpg) | [live](problem-solving-390-live.jpg) / [local](problem-solving-390-local.jpg) |  |
| `/racial-unity/` | **match** | 3775/3775, 0.00% | 4666/4666, 0.00% | [live](racial-unity-1440-live.jpg) / [local](racial-unity-1440-local.jpg) | [live](racial-unity-390-live.jpg) / [local](racial-unity-390-local.jpg) | Fixed in M5 (hero link printed "None"). Now pixel-identical. Live's empty hero link has `href=""`; ours has no href. |
| `/raise-a-concern/` | **match** | 1454/1454, 0.00% | 1570/1570, 0.00% | [live](raise-a-concern-1440-live.jpg) / [local](raise-a-concern-1440-local.jpg) | [live](raise-a-concern-390-live.jpg) / [local](raise-a-concern-390-local.jpg) |  |
| `/reaching/` | **match** | 1194/1194, 0.00% | 1430/1430, 0.00% | [live](reaching-1440-live.jpg) / [local](reaching-1440-local.jpg) | [live](reaching-390-live.jpg) / [local](reaching-390-local.jpg) |  |
| `/room-hire/` | **match** | 8503/8503, 0.00% | 5151/5151, 0.00% | [live](room-hire-1440-live.jpg) / [local](room-hire-1440-local.jpg) | [live](room-hire-390-live.jpg) / [local](room-hire-390-local.jpg) |  |
| `/safeguarding/` | **match** | 4210/4210, 0.00% | 4878/4878, 0.00% | [live](safeguarding-1440-live.jpg) / [local](safeguarding-1440-local.jpg) | [live](safeguarding-390-live.jpg) / [local](safeguarding-390-local.jpg) |  |
| `/shaping/` | **minor** | 4903/4903, 0.05% | 8806/8806, 1.61% | [live](shaping-1440-live.jpg) / [local](shaping-1440-local.jpg) | [live](shaping-390-live.jpg) / [local](shaping-390-local.jpg) ([diff](shaping-390-diff.jpg)) | Sub-pixel shift at 390 (realigns); 1440 near-identical. |
| `/subscribe/` | **match** | 1128/1128, 0.00% | 1345/1345, 0.00% | [live](subscribe-1440-live.jpg) / [local](subscribe-1440-local.jpg) | [live](subscribe-390-live.jpg) / [local](subscribe-390-local.jpg) |  |
| `/teaching-series/` | **match** | 1454/1454, 0.00% | 1430/1430, 0.00% | [live](teaching-series-1440-live.jpg) / [local](teaching-series-1440-local.jpg) | [live](teaching-series-390-live.jpg) / [local](teaching-series-390-local.jpg) |  |
| `/team/` | **minor** | 3466/3466, 0.39% | 6036/6034, 2.86% | [live](team-1440-live.jpg) / [local](team-1440-local.jpg) ([diff](team-1440-diff.jpg)) | [live](team-390-live.jpg) / [local](team-390-local.jpg) ([diff](team-390-diff.jpg)) | Sub-pixel image-card heights add up to 2px at 390. |
| `/terms/` | **match** | 4774/4774, 0.00% | 5958/5958, 0.00% | [live](terms-1440-live.jpg) / [local](terms-1440-local.jpg) | [live](terms-390-live.jpg) / [local](terms-390-local.jpg) |  |
| `/trustees/` | **match** | 10180/10180, 0.01% | 23166/23166, 0.02% | [live](trustees-1440-live.jpg) / [local](trustees-1440-local.jpg) | [live](trustees-390-live.jpg) / [local](trustees-390-local.jpg) | Fixed in M5 (16px gap in cards without content). Now pixel-identical. Live has an empty, invisible `<a>` in the image cell of the "Vision, Values and Core Beliefs" card (no image); not reproduced. |
| `/values/` | **match** | 2166/2166, 0.04% | 2154/2154, 0.00% | [live](values-1440-live.jpg) / [local](values-1440-local.jpg) | [live](values-390-live.jpg) / [local](values-390-local.jpg) |  |
| `/vision/` | **match** | 3214/3214, 0.05% | 3666/3666, 0.00% | [live](vision-1440-live.jpg) / [local](vision-1440-local.jpg) | [live](vision-390-live.jpg) / [local](vision-390-local.jpg) |  |
| `/visionandvalues/` | **match** | 8372/8372, 0.00% | 9626/9626, 0.00% | [live](visionandvalues-1440-live.jpg) / [local](visionandvalues-1440-local.jpg) | [live](visionandvalues-390-live.jpg) / [local](visionandvalues-390-local.jpg) |  |
| `/whistleblowing/` | **match** | 8478/8478, 0.00% | 10322/10322, 0.00% | [live](whistleblowing-1440-live.jpg) / [local](whistleblowing-1440-local.jpg) | [live](whistleblowing-390-live.jpg) / [local](whistleblowing-390-local.jpg) |  |
| `/youth/` | **match** | 2458/2458, 0.03% | 3262/3262, 0.01% | [live](youth-1440-live.jpg) / [local](youth-1440-local.jpg) | [live](youth-390-live.jpg) / [local](youth-390-local.jpg) |  |
| `/404.html` | **match** | 1214/1214, 0.00% | 1494/1494, 0.00% | [live](404.html-1440-live.jpg) / [local](404.html-1440-local.jpg) | [live](404.html-390-live.jpg) / [local](404.html-390-local.jpg) | Live: `/parity-check-missing-page` (404). Local `/404.html` served by the script's plain file server, hence 200; Netlify serves it with 404. Live 404 has an empty `<title>`; ours "Page not found | The C3 Church". |

## Redirects

Each source was requested once on live without following the redirect. **Build** is the status in `dist/_redirects`; **Target** compares live's `Location` with the build's target.

| Source | Build target | Build | Live | Live Location | Target |
|---|---|---|---|---|---|
| `/debrief` | https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=3W6n-46yPkqAhAf3hHjUYP8vYQJxLIxGiXPE2vNQI79UMTRLVEVHU1YxR0tHMFVRMDUzRkE2SzlOVS4u | 302 | 301 | https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=3W6n-46yPkqAhAf3hHjUYP8vYQJxLIxGiXPE2vNQI79UMTRLVEVHU1YxR0tHMFVRMDUzRkE2SzlOVS4u | same |
| `/bible` | https://bible.com/events/49682212 | 302 | 301 | https://bible.com/events/49682212 | same |
| `/headcount` | https://forms.cloud.microsoft/e/8Hu7xckJ6s | 302 | 301 | https://forms.cloud.microsoft/e/8Hu7xckJ6s | same |
| `/giftaid` | https://thec3.churchsuite.com/-/forms/h8po0xdj | 302 | 301 | https://thec3.churchsuite.com/-/forms/h8po0xdj | same |
| `/prophetic-teaching-day` | https://thec3.churchsuite.com/events/oeigcfbm | 302 | 301 | https://thec3.churchsuite.com/events/oeigcfbm | same |
| `/gls` | https://thec3.churchsuite.com/events/7jkscdle | 302 | 301 | https://thec3.churchsuite.com/events/7jkscdle | same |
| `/4thservice` | https://thec3.churchsuite.com/-/forms/vcmr5v4n | 302 | 301 | https://thec3.churchsuite.com/-/forms/vcmr5v4n | same |
| `/lightnight` | https://thec3.churchsuite.com/-/calendar/ce91e008-808b-4683-a898-cda981e810b6 | 302 | 301 | https://thec3.churchsuite.com/-/calendar/ce91e008-808b-4683-a898-cda981e810b6 | same |
| `/academyopenevening` | https://thec3.churchsuite.com/events/tvxvflie | 302 | 301 | https://thec3.churchsuite.com/events/tvxvflie | same |
| `/propheticmorning` | https://thec3.churchsuite.com/events/eexvqq5p | 302 | 301 | https://thec3.churchsuite.com/events/eexvqq5p | same |
| `/alpha` | https://thec3.churchsuite.com/events/wswkhomf | 302 | 301 | https://thec3.churchsuite.com/events/wswkhomf | same |
| `/messyplay` | https://thec3.churchsuite.com/events/yzrfqwmd | 302 | 301 | https://thec3.churchsuite.com/events/yzrfqwmd | same |
| `/calendar-bury` | https://thec3.churchsuite.com/-/calendar/410a57b3-3344-4660-968e-54a27594701f?preview=1 | 301 | 301 | https://thec3.churchsuite.com/-/calendar/410a57b3-3344-4660-968e-54a27594701f?preview=1 | same |
| `/christmasinabox` | https://thec3.churchsuite.com/-/calendar/e0e42240-7be0-4ed8-bad0-edbbb044fc1c | 302 | 301 | https://thec3.churchsuite.com/-/calendar/e0e42240-7be0-4ed8-bad0-edbbb044fc1c | same |
| `/wtc` | https://www.eventbrite.co.uk/e/kingdom-theology-event-in-cambridge-with-alister-wallace-tickets-1984457635207?aff=oddtdtcreator | 302 | 301 | https://www.eventbrite.co.uk/e/kingdom-theology-event-in-cambridge-with-alister-wallace-tickets-1984457635207?aff=oddtdtcreator | same |
| `/baptismclasses` | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20&body_bgcolor=ffffff&event_border_color=228ae6&heading_color=228ae6&text_color=000000&icon_color=000000 | 302 | 301 | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20&body_bgcolor=ffffff&event_border_color=228ae6&heading_color=228ae6&text_color=000000&icon_color=000000 | same |
| `/gls-c3family` | https://thec3.churchsuite.com/events/7jkscdle?tickets=xV8K | 301 | 301 | https://thec3.churchsuite.com/events/7jkscdle?tickets=xV8K | same |
| `/kintsugi` | https://thec3.churchsuite.com/events/gpcmzx8m | 302 | 301 | https://thec3.churchsuite.com/events/gpcmzx8m | same |
| `/teardrop` | https://www.teardropgrief.co.uk/shop/p/griefandloss-webinar | 302 | 301 | https://www.teardropgrief.co.uk/shop/p/griefandloss-webinar | same |
| `/gameplan` | https://thec3.churchsuite.com/-/calendar/43ce142b-6e7f-4991-9fb7-2a228ff1502a?preview=1 | 302 | 301 | https://thec3.churchsuite.com/-/calendar/43ce142b-6e7f-4991-9fb7-2a228ff1502a?preview=1 | same |
| `/btg` | https://btgfootballbookings.com/bookings/Cambridge?utm_source=ig&utm_medium=social&utm_content=link_in_bio&fbclid=PAZXh0bgNhZW0CMTEAc3J0YwZhcHBfaWQMMjU2MjgxMDQwNTU4AAGnJSA_IFRLeSMrwqbJLxgEceCI_y0SIXZ4BZfnyD6eEHkpx2dtjr07AXLvDwM_aem_f_T8DYWGMPxJlyl4iBudMg | 302 | 301 | https://btgfootballbookings.com/bookings/Cambridge?utm_source=ig&utm_medium=social&utm_content=link_in_bio&fbclid=PAZXh0bgNhZW0CMTEAc3J0YwZhcHBfaWQMMjU2MjgxMDQwNTU4AAGnJSA_IFRLeSMrwqbJLxgEceCI_y0SIXZ4BZfnyD6eEHkpx2dtjr07AXLvDwM_aem_f_T8DYWGMPxJlyl4iBudMg | same |
| `/prayersubscribe` | https://thec3.churchsuite.com/-/forms/ytxl0non | 302 | 301 | https://thec3.churchsuite.com/-/forms/ytxl0non | same |
| `/athome` | https://youtube.com/live/SAkB48Oyrdg?feature=share | 302 | 301 | https://youtube.com/live/SAkB48Oyrdg?feature=share | same |
| `/revelation` | https://thec3.churchsuite.com/events/edpl6ody | 302 | 301 | https://thec3.churchsuite.com/events/edpl6ody | same |
| `/worldchangers` | https://thec3.churchsuite.com/events/ynjs8lm1 | 302 | 301 | https://thec3.churchsuite.com/events/ynjs8lm1 | same |
| `/ascend-reflection` | https://thec3.churchsuite.com/events/9cm6cdri | 302 | 301 | https://thec3.churchsuite.com/events/9cm6cdri | same |
| `/prayerfasting` | https://www.youtube.com/watch?v=jHSrczIYDTA&t=11s | 302 | 301 | https://www.youtube.com/watch?v=jHSrczIYDTA&t=11s | same |
| `/test-page-here` | https://www.google.com | 301 | 301 | https://www.google.com/ | same (live adds `/`) |
| `/coach` | https://thec3.churchsuite.com/events/mbqq46rc | 301 | 301 | https://thec3.churchsuite.com/events/mbqq46rc | same |
| `/visionoffering2026` | https://thec3.churchsuite.com/donate/fund/ukevxdcx | 302 | 301 | https://thec3.churchsuite.com/donate/fund/ukevxdcx | same |
| `/watoto` | https://thec3.churchsuite.com/-/forms/ztashznr | 302 | 301 | https://thec3.churchsuite.com/-/forms/ztashznr | same |
| `/overwhelmtour` | https://thec3.churchsuite.com/events/uy2uahd4 | 302 | 301 | https://thec3.churchsuite.com/events/uy2uahd4 | same |
| `/stw` | https://www.stewardship.org.uk/pages/stw2025 | 302 | 301 | https://www.stewardship.org.uk/pages/stw2025 | same |
| `/yasouls` | https://brushfire.com/thec3uk/yasouls/615662 | 302 | 301 | https://brushfire.com/thec3uk/yasouls/615662 | same |
| `/help` | https://www.samaritans.org/how-we-can-help/contact-samaritan/?utm_source=google&utm_medium=organic&utm_campaign=onebox | 302 | 301 | https://www.samaritans.org/how-we-can-help/contact-samaritan/?utm_source=google&utm_medium=organic&utm_campaign=onebox | same |
| `/watototrip` | https://thec3.churchsuite.com/-/forms/ztashznr | 301 | 301 | https://thec3.churchsuite.com/-/forms/ztashznr | same |
| `/reflection` | https://www.teardropgrief.co.uk/shop/p/teardrop-online-christmas-reflection | 302 | 301 | https://www.teardropgrief.co.uk/shop/p/teardrop-online-christmas-reflection | same |
| `/restoration` | https://thec3.churchsuite.com/events/bjh1cia4 | 302 | 301 | https://thec3.churchsuite.com/events/bjh1cia4 | same |
| `/yachristmasparty` | https://thec3.churchsuite.com/events/d8ezbeuv | 302 | 301 | https://thec3.churchsuite.com/events/d8ezbeuv | same |
| `/team-26` | https://thec3.churchsuite.com/forms/wxu56079 | 302 | 301 | https://thec3.churchsuite.com/forms/wxu56079 | same |
| `/divorcerecovery` | https://thec3.churchsuite.com/events/j46sqy7f | 302 | 301 | https://thec3.churchsuite.com/events/j46sqy7f | same |
| `/prophetic-morning` | https://thec3.churchsuite.com/events/eexvqq5p | 301 | 301 | https://thec3.churchsuite.com/events/eexvqq5p | same |
| `/openevening` | https://thec3.churchsuite.com/events/tvxvflie | 302 | 301 | https://thec3.churchsuite.com/events/tvxvflie | same |
| `/cared` | https://thec3.churchsuite.com/events/mfnk3fij | 302 | 301 | https://thec3.churchsuite.com/events/mfnk3fij | same |
| `/academy-open` | https://thec3.churchsuite.com/events/l1cbespe | 302 | 301 | https://thec3.churchsuite.com/events/l1cbespe | same |
| `/wellbeing-workshop` | https://thec3.churchsuite.com/events/zqvcwdbo | 302 | 301 | https://thec3.churchsuite.com/events/zqvcwdbo | same |
| `/youversion` | https://www.youversion.com/the-bible-app/ | 302 | 301 | https://www.youversion.com/the-bible-app/ | same |
| `/dylan` | https://youtu.be/ilVRZYI5dMk | 302 | 301 | https://youtu.be/ilVRZYI5dMk | same |
| `/prophetic` | https://thec3.churchsuite.com/events/emgrows6 | 302 | 301 | https://thec3.churchsuite.com/events/emgrows6 | same |
| `/greatiam` | https://wingsmusic.lnk.to/GreatIAMYahwehLive | 302 | 301 | https://wingsmusic.lnk.to/GreatIAMYahwehLive | same |
| `/nationalprayer` | https://www.youtube.com/watch?v=tPUpTvvLoRY | 301 | 301 | https://www.youtube.com/watch?v=tPUpTvvLoRY | same |
| `/55` | https://thec3.churchsuite.com/events/lquf4igc | 302 | 301 | https://thec3.churchsuite.com/events/lquf4igc | same |
| `/stayingsafeonline` | https://thec3.churchsuite.com/events/7ncpz09i | 302 | 301 | https://thec3.churchsuite.com/events/7ncpz09i | same |
| `/table` | https://thec3.churchsuite.com/events/61zzb8mw | 302 | 301 | https://thec3.churchsuite.com/events/61zzb8mw | same |
| `/ascendmen` | https://www.facebook.com/groups/527708931330993 | 302 | 301 | https://www.facebook.com/groups/527708931330993 | same |
| `/backtoschool` | https://thec3.churchsuite.com/-/calendar/cb41ebe8-4807-4f8c-ad41-3a550bbe4b0c | 302 | 301 | https://thec3.churchsuite.com/-/calendar/cb41ebe8-4807-4f8c-ad41-3a550bbe4b0c | same |
| `/guestspeaker` | https://thec3church.typeform.com/to/DHC1Uv4G | 302 | 301 | https://thec3church.typeform.com/to/DHC1Uv4G | same |
| `/churchsuite` | https://churchsuite.com/apps/ | 302 | 301 | https://churchsuite.com/apps/ | same |
| `/laura` | https://youtu.be/T0ST70FiR8w | 302 | 301 | https://youtu.be/T0ST70FiR8w | same |
| `/autumn` | https://youtu.be/BqOk7IyolKc | 302 | 301 | https://youtu.be/BqOk7IyolKc | same |
| `/ubuntu` | https://open.substack.com/pub/thec3church/p/ubuntu?r=5dfdqj&utm_campaign=post&utm_medium=web | 302 | 301 | https://open.substack.com/pub/thec3church/p/ubuntu?r=5dfdqj&utm_campaign=post&utm_medium=web | same |
| `/bigchurch` | https://bigchurchtickets.com/events/tim-the-glory-boys-philippa-hanna?fbclid=PAZXh0bgNhZW0CMTEAAafyumyud8jcfvvNy-C1NbjSX1mR_ycG3tnpNE7G67N4JREjOBv1j3M0N9vbfQ_aem_-jnikfOSUB2-1KdZ_9y82Q | 302 | 301 | https://bigchurchtickets.com/events/tim-the-glory-boys-philippa-hanna?fbclid=PAZXh0bgNhZW0CMTEAAafyumyud8jcfvvNy-C1NbjSX1mR_ycG3tnpNE7G67N4JREjOBv1j3M0N9vbfQ_aem_-jnikfOSUB2-1KdZ_9y82Q | same |
| `/teamcol` | https://thec3.churchsuite.com/forms/tzissv55 | 301 | 301 | https://thec3.churchsuite.com/forms/tzissv55 | same |
| `/pilates` | https://thec3.churchsuite.com/events/uujt8mvp | 302 | 301 | https://thec3.churchsuite.com/events/uujt8mvp | same |
| `/kidsmail` | https://mailchi.mp/dabde5024bdb/kids-mailout-sign-up | 301 | 301 | https://mailchi.mp/dabde5024bdb/kids-mailout-sign-up | same |
| `/prophetictraining` | https://thec3.churchsuite.com/events/y8int78b | 302 | 301 | https://thec3.churchsuite.com/events/y8int78b | same |
| `/kidsgroup` | https://thec3.churchsuite.com/events/jrvqmijr | 302 | 301 | https://thec3.churchsuite.com/events/jrvqmijr | same |
| `/yourkingdomcome` | https://wingsmusic.lnk.to/YourKingdomCome | 302 | 301 | https://wingsmusic.lnk.to/YourKingdomCome | same |
| `/baptisms` | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20&body_b[…]0000&icon_color=000000&mc_cid=b9f72f2951&mc_eid=2db005e1de | 302 | 301 | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20&body_b[…]0000&icon_color=000000&mc_cid=b9f72f2951&mc_eid=2db005e1de | same |
| `/wellbeingcol` | https://thec3.churchsuite.com/events/rlpysgrs | 301 | 301 | https://thec3.churchsuite.com/events/rlpysgrs | same |
| `/open` | https://www.eventbrite.co.uk/e/monday-hub-open-eve-for-bris-camb-emid-manc-scot-sotn-wmid-tickets-816680221527 | 301 | 301 | https://www.eventbrite.co.uk/e/monday-hub-open-eve-for-bris-camb-emid-manc-scot-sotn-wmid-tickets-816680221527 | same |
| `/atwork` | https://brushfire.com/thec3uk/c3atwork/577791 | 301 | 301 | https://brushfire.com/thec3uk/c3atwork/577791 | same |
| `/burykidsfest` | https://thec3.churchsuite.com/events/0ahemc4v | 301 | 301 | https://thec3.churchsuite.com/events/0ahemc4v | same |
| `/step1` | https://thec3.churchsuite.com/-/calendar/7071888a-8b5e-4655-8b10-4c511479efb8 | 301 | 301 | https://thec3.churchsuite.com/-/calendar/7071888a-8b5e-4655-8b10-4c511479efb8 | same |
| `/dti` | https://brushfire.com/thec3uk/dreamingtheimpossible/582890 | 302 | 301 | https://brushfire.com/thec3uk/dreamingtheimpossible/582890 | same |
| `/cambkidsfest` | https://thec3.churchsuite.com/events/kt7xjuvw | 302 | 301 | https://thec3.churchsuite.com/events/kt7xjuvw | same |
| `/followthatverse` | https://us02web.zoom.us/j/83856907739?pwd=iObDaXB1J804jtr3gBX6oqD6Wsffwa.1 | 302 | 301 | https://us02web.zoom.us/j/83856907739?pwd=iObDaXB1J804jtr3gBX6oqD6Wsffwa.1 | same |
| `/party` | https://thec3.churchsuite.com/events/h2zlwnhr | 302 | 301 | https://thec3.churchsuite.com/events/h2zlwnhr | same |
| `/sound` | https://youtu.be/HDA0Hk93CsQ | 302 | 301 | https://youtu.be/HDA0Hk93CsQ | same |
| `/pctraining` | https://thec3.churchsuite.com/events/kwmf9w1z | 302 | 301 | https://thec3.churchsuite.com/events/kwmf9w1z | same |
| `/propheticpod` | https://youtu.be/0N_Y7Bs7xiE | 302 | 301 | https://youtu.be/0N_Y7Bs7xiE | same |
| `/wellbeing` | https://thec3.churchsuite.com/-/calendar/843a3727-0e54-4538-9baf-b74006ef1a80 | 302 | 301 | https://thec3.churchsuite.com/-/calendar/843a3727-0e54-4538-9baf-b74006ef1a80 | same |
| `/colkidsfest` | https://thec3.churchsuite.com/events/v4ddyfhi | 302 | 301 | https://thec3.churchsuite.com/events/v4ddyfhi | same |
| `/hello` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 302 | 301 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same |
| `/burybbq` | https://thec3.churchsuite.com/events/93p5ehhj | 302 | 301 | https://thec3.churchsuite.com/events/93p5ehhj | same |
| `/marriage` | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-england-tickets-872798061497 | 302 | 301 | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-england-tickets-872798061497 | same |
| `/colgroups` | https://thec3.churchsuite.com/embed/v2/smallgroups/35b73a5a-f3b2-4584-90bb-6bb437e14466 | 302 | 301 | https://thec3.churchsuite.com/embed/v2/smallgroups/35b73a5a-f3b2-4584-90bb-6bb437e14466 | same |
| `/onlinebible` | https://bible.com/events/49299352 | 302 | 301 | https://bible.com/events/49299352 | same |
| `/lightnightcam` | https://thec3.churchsuite.com/events/tdmifgli | 301 | 301 | https://thec3.churchsuite.com/events/tdmifgli | same |
| `/recording` | https://thec3.churchsuite.com/events/gbyjigo0 | 301 | 301 | https://thec3.churchsuite.com/events/gbyjigo0 | same |
| `/ascendcamp` | https://brushfire.com/thec3uk/ascend/585411 | 302 | 301 | https://brushfire.com/thec3uk/ascend/585411 | same |
| `/lightnightbury` | https://thec3.churchsuite.com/events/6gzhj93y | 301 | 301 | https://thec3.churchsuite.com/events/6gzhj93y | same |
| `/dedications` | https://thec3.churchsuite.com/-/calendar/21cdc4b7-883b-48ce-9332-d803d63fc33a | 302 | 301 | https://thec3.churchsuite.com/-/calendar/21cdc4b7-883b-48ce-9332-d803d63fc33a | same |
| `/baptism` | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20 | 301 | 301 | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20 | same |
| `/training` | https://thec3.churchsuite.com/events/amhhr4f5 | 301 | 301 | https://thec3.churchsuite.com/events/amhhr4f5 | same |
| `/cause` | https://thec3.churchsuite.com/events/zp7oe7d2 | 302 | 301 | https://thec3.churchsuite.com/events/zp7oe7d2 | same |
| `/worshiprecording` | https://thec3.churchsuite.com/events/gbyjigo0 | 301 | 301 | https://thec3.churchsuite.com/events/gbyjigo0 | same |
| `/fordhamfb` | https://www.facebook.com/groups/thec3fordham | 302 | 301 | https://www.facebook.com/groups/thec3fordham | same |
| `/lightnightcol` | https://thec3.churchsuite.com/events/j5cpqhy7 | 301 | 301 | https://thec3.churchsuite.com/events/j5cpqhy7 | same |
| `/step2` | https://thec3.churchsuite.com/-/calendar/88c4f896-0205-4502-b90d-fc3e406757a9?preview=1 | 301 | 301 | https://thec3.churchsuite.com/-/calendar/88c4f896-0205-4502-b90d-fc3e406757a9?preview=1 | same |
| `/homelessness` | https://thec3.churchsuite.com/events/rbkimwmh | 301 | 301 | https://thec3.churchsuite.com/events/rbkimwmh | same |
| `/cookingonabudget` | https://thec3.churchsuite.com/-/calendar/65d35796-f7c5-4c38-88a6-28df26aed03a | 302 | 301 | https://thec3.churchsuite.com/-/calendar/65d35796-f7c5-4c38-88a6-28df26aed03a | same |
| `/marathon` | https://www.stewardship.org.uk/pages/CHM2025?fbclid=IwY2xjawIwUpxleHRuA2FlbQIxMAABHcOHkJ[…]ptu3X2fRIdavYcEEWLTw0-eBLNI3JQ_aem_-URsxqPPK4bBy48HoJ_dgw | 302 | 301 | https://www.stewardship.org.uk/pages/CHM2025?fbclid=IwY2xjawIwUpxleHRuA2FlbQIxMAABHcOHkJ[…]ptu3X2fRIdavYcEEWLTw0-eBLNI3JQ_aem_-URsxqPPK4bBy48HoJ_dgw | same |
| `/teamfordham` | https://thec3.churchsuite.com/-/forms/xnh7hyde | 301 | 301 | https://thec3.churchsuite.com/-/forms/xnh7hyde | same |
| `/teambury` | https://thec3.churchsuite.com/-/forms/jbi3orhk | 301 | 301 | https://thec3.churchsuite.com/-/forms/jbi3orhk | same |
| `/teamwest` | https://thec3.churchsuite.com/-/forms/3x0e0y2t | 301 | 301 | https://thec3.churchsuite.com/-/forms/3x0e0y2t | same |
| `/cooking` | https://thec3.churchsuite.com/events/pzgehiog | 302 | 301 | https://thec3.churchsuite.com/events/pzgehiog | same |
| `/tour` | https://youtu.be/Y4XU08z6JN0 | 302 | 301 | https://youtu.be/Y4XU08z6JN0 | same |
| `/teamcam` | https://thec3.churchsuite.com/-/forms/6bz8hlfi | 302 | 301 | https://thec3.churchsuite.com/-/forms/6bz8hlfi | same |
| `/socialmedia` | https://thec3.churchsuite.com/events/igzucy2p | 302 | 301 | https://thec3.churchsuite.com/events/igzucy2p | same |
| `/activityday` | https://thec3.churchsuite.com/events/zs5uglxp | 302 | 301 | https://thec3.churchsuite.com/events/zs5uglxp | same |
| `/fordhamreview` | https://g.page/r/CdXUoF0ARd-6EB0/review | 302 | 301 | https://g.page/r/CdXUoF0ARd-6EB0/review | same |
| `/photography` | https://us02web.zoom.us/j/9909172921?pwd=U0N4aFF2T3NQSlpHS2hBQXd6M3BUdz09 | 302 | 301 | https://us02web.zoom.us/j/9909172921?pwd=U0N4aFF2T3NQSlpHS2hBQXd6M3BUdz09 | same |
| `/gifts` | https://assessments.lifethrive.com/SpiritualGifts.php | 302 | 301 | https://assessments.lifethrive.com/SpiritualGifts.php | same |
| `/burygroup` | https://thec3.churchsuite.com/embed/v2/smallgroups/bdc24f05-ebda-402f-aabe-26bf0649437c | 302 | 301 | https://thec3.churchsuite.com/embed/v2/smallgroups/bdc24f05-ebda-402f-aabe-26bf0649437c | same |
| `/marketlaunch` | https://thec3.churchsuite.com/events/lk8vkaji | 301 | 301 | https://thec3.churchsuite.com/events/lk8vkaji | same |
| `/vote` | https://thec3church.typeform.com/to/RWsj7vNq?mc_cid=f0d85b4082&mc_eid=6923d6d819&typeform-source=breathe.thec3.uk&mc_cid=173028fd91&mc_eid=6923d6d819 | 302 | 301 | https://thec3church.typeform.com/to/RWsj7vNq?mc_cid=f0d85b4082&mc_eid=6923d6d819&typeform-source=breathe.thec3.uk&mc_cid=173028fd91&mc_eid=6923d6d819 | same |
| `/sundaysetlist` | https://open.spotify.com/playlist/4PHcojwPvGZhnAgz110fv2?si=ecd60aa506cd473a | 302 | 301 | https://open.spotify.com/playlist/4PHcojwPvGZhnAgz110fv2?si=ecd60aa506cd473a | same |
| `/westsignup` | https://thec3.churchsuite.com/-/forms/ugaclyfc | 302 | 301 | https://thec3.churchsuite.com/-/forms/ugaclyfc | same |
| `/funday` | http://tinyurl.com/c3funday | 302 | 301 | http://tinyurl.com/c3funday | same |
| `/eggs` | https://thec3.churchsuite.com/donate/fund/baysvabt | 302 | 301 | https://thec3.churchsuite.com/donate/fund/baysvabt | same |
| `/sciencefaith` | https://thec3.churchsuite.com/events/zqagqdbq | 302 | 301 | https://thec3.churchsuite.com/events/zqagqdbq | same |
| `/adura` | https://youtu.be/y7E_WQq4v1Q | 302 | 301 | https://youtu.be/y7E_WQq4v1Q | same |
| `/bbqteam` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=66&e[…]ries=0&show_search=0&show_sites=1&sites=&text_color=666666 | 302 | 301 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=66&e[…]ries=0&show_search=0&show_sites=1&sites=&text_color=666666 | same |
| `/tastelife` | https://airtable.com/shr79kzXbas0pvHIl?prefill_Course%20Allocated%2FAttended%3A=Onl[…]%20January%202024&prefill_LL+sign+up=true&hide_LL+sign+up=true | 302 | 301 | https://airtable.com/shr79kzXbas0pvHIl?prefill_Course%20Allocated%2FAttended%3A=Onl[…]%20January%202024&prefill_LL+sign+up=true&hide_LL+sign+up=true | same |
| `/colchestergroup` | https://www.facebook.com/groups/thec3colchester | 302 | 301 | https://www.facebook.com/groups/thec3colchester | same |
| `/quiz` | https://brushfire.com/thec3uk/quiznight/554145/details | 302 | 301 | https://brushfire.com/thec3uk/quiznight/554145/details | same |
| `/healthyliving` | https://thec3.churchsuite.com/events/snsgii7d | 301 | 301 | https://thec3.churchsuite.com/events/snsgii7d | same |
| `/communitysupper` | https://thec3.churchsuite.com/events/b26mc16y | 302 | 301 | https://thec3.churchsuite.com/events/b26mc16y | same |
| `/burybuilding` | https://thec3.churchsuite.com/events/7lbh1irh | 301 | 301 | https://thec3.churchsuite.com/events/7lbh1irh | same |
| `/bbq` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=65&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=&months=&show_categories=0&show_search=0&show_sites=1&sites=&text_color=666666 | 301 | 301 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=65&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=&months=&show_categories=0&show_search=0&show_sites=1&sites=&text_color=666666 | same |
| `/c3atwork` | https://thec3.churchsuite.com/events/xirfkth3?fbclid=IwAR2_bWGCRs3INUPjOzF8wCzRTaAkXwNdMsn2_pZ2RNYU2-aasp2Zc6CLRF8 | 302 | 301 | https://thec3.churchsuite.com/events/xirfkth3?fbclid=IwAR2_bWGCRs3INUPjOzF8wCzRTaAkXwNdMsn2_pZ2RNYU2-aasp2Zc6CLRF8 | same |
| `/markritchie` | https://brushfire.com/thec3uk/markritchie/ | 301 | 301 | https://brushfire.com/thec3uk/markritchie/ | same |
| `/kidscraft` | https://thec3.churchsuite.com/events/mnvlk4ox | 302 | 301 | https://thec3.churchsuite.com/events/mnvlk4ox | same |
| `/teamrally` | https://us02web.zoom.us/j/83120323814?pwd=YXI2REcvYzA4VjR1L0k0Szhia1dSQT09 | 301 | 301 | https://us02web.zoom.us/j/83120323814?pwd=YXI2REcvYzA4VjR1L0k0Szhia1dSQT09 | same |
| `/print-progress` | https://www.notion.so/thec3/DESIGN-TO-PRINT-PROGRESS-b6fcccad23c345668e83f130f3716aae | 302 | 301 | https://www.notion.so/thec3/DESIGN-TO-PRINT-PROGRESS-b6fcccad23c345668e83f130f3716aae | same |
| `/teamchristmas` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=68&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=signup_to_sequence&num_results=&months=6&show_categories=0&show_search=1&show_sites=0&sites=1,4,7&text_color=666666 | 302 | 301 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=68&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=signup_to_sequence&num_results=&months=6&show_categories=0&show_search=1&show_sites=0&sites=1,4,7&text_color=666666 | same |
| `/robparsons` | https://www.eventbrite.co.uk/e/an-evening-with-rob-parsons-cambridge-tickets-633251350837 | 302 | 301 | https://www.eventbrite.co.uk/e/an-evening-with-rob-parsons-cambridge-tickets-633251350837 | same |
| `/glspodcast` | https://www.youtube.com/watch?v=q-wWbNV9OnM | 302 | 301 | https://www.youtube.com/watch?v=q-wWbNV9OnM | same |
| `/christmasbox` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=62&event_bgcolor=FFFFFF&event_border=&featured=1&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=3&months=&show_categories=0&show_search=0&show_sites=0&sites=1,4,7&text_color=666666 | 302 | 301 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=62&event_bgcolor=FFFFFF&event_border=&featured=1&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=3&months=&show_categories=0&show_search=0&show_sites=0&sites=1,4,7&text_color=666666 | same |
| `/survey` | https://youtu.be/6eqvtt-kiFg | 302 | 301 | https://youtu.be/6eqvtt-kiFg | same |
| `/yapodcast` | https://feeds.transistor.fm/ya-pod | 302 | 301 | https://feeds.transistor.fm/ya-pod | same |
| `/propheticday` | https://thec3.churchsuite.com/events/jwditxpg | 302 | 301 | https://thec3.churchsuite.com/events/jwditxpg | same |
| `/christmas` | https://christmas.thec3.uk | 301 | 301 | https://christmas.thec3.uk/ | same (live adds `/`) |
| `/breatheontheroad` | https://brushfire.com/thec3uk/breathe?fbclid=iwar1wycp-g-eado-vrh_bay-t4ov6ym7q07f8nfgwxmunxqty-iv3k14q7_c | 302 | 301 | https://brushfire.com/thec3uk/breathe?fbclid=iwar1wycp-g-eado-vrh_bay-t4ov6ym7q07f8nfgwxmunxqty-iv3k14q7_c | same |
| `/kids-church` | https://thec3.notion.site/Kids-Church-This-Sunday-226d5cedcf0f45a483cb8d276abce64b | 302 | 301 | https://thec3.notion.site/Kids-Church-This-Sunday-226d5cedcf0f45a483cb8d276abce64b | same |
| `/divorce-recovery23` | https://thec3.churchsuite.com/events/pvfsctiu | 302 | 301 | https://thec3.churchsuite.com/events/pvfsctiu | same |
| `/kidschurch` | /kids-church/ | 301 | 301 | /kids-church/ | same |
| `/creativebbq` | https://thec3.churchsuite.com/events/sueg3px9 | 302 | 301 | https://thec3.churchsuite.com/events/sueg3px9 | same |
| `/lifeguitar` | https://thec3.churchsuite.com/events/iclkzswa | 302 | 301 | https://thec3.churchsuite.com/events/iclkzswa | same |
| `/honoursbbq` | https://thec3.churchsuite.com/events/u9sbiab6 | 302 | 301 | https://thec3.churchsuite.com/events/u9sbiab6 | same |
| `/music` | https://open.spotify.com/playlist/4S6fEWlrNtbjWu6Bx6qHgh?si=577cc523446f4bb1&pt=e9b902d05b169549e3955fbfb8b454b5 | 302 | 301 | https://open.spotify.com/playlist/4S6fEWlrNtbjWu6Bx6qHgh?si=577cc523446f4bb1&pt=e9b902d05b169549e3955fbfb8b454b5 | same |
| `/downloads` | https://we.tl/t-1Y5hKqECwK | 301 | 301 | https://we.tl/t-1Y5hKqECwK | same |
| `/funnyhowmarriage` | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-uk-tickets-872798061497 | 301 | 301 | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-uk-tickets-872798061497 | same |
| `/marathonworld` | https://portal.trustbridgeglobal.com/public/donate?id=a65bb8fa7c0cffcf68651252dc4fcdc0fe0d59b3 | 302 | 301 | https://portal.trustbridgeglobal.com/public/donate?id=a65bb8fa7c0cffcf68651252dc4fcdc0fe0d59b3 | same |
| `/teameaster` | https://thec3.churchsuite.com/-/calendar/200e53c7-ea91-4631-ade9-4c90db6527ec | 301 | 301 | https://thec3.churchsuite.com/-/calendar/200e53c7-ea91-4631-ade9-4c90db6527ec | same |
| `/workshop` | https://thec3.churchsuite.com/events/vjvfwj9r | 301 | 301 | https://thec3.churchsuite.com/events/vjvfwj9r | same |
| `/groupleaders` | https://thec3.churchsuite.com/forms/gc7qfw97 | 301 | 301 | https://thec3.churchsuite.com/forms/gc7qfw97 | same |
| `/store` | https://store.thec3.uk | 301 | 301 | https://store.thec3.uk/ | same (live adds `/`) |
| `/ascendpod` | https://feeds.transistor.fm/ascend | 301 | 301 | https://feeds.transistor.fm/ascend | same |
| `/kintsugihope` | https://https:/https://thec3.churchsuite.com/events/ihiqkzpx | 302 | 301 | https://https:/https://thec3.churchsuite.com/events/ihiqkzpx | same |
| `/christmasmeal` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=f5f6f7&categories=61&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=ffffff&heading_color=202945&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | 302 | 301 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=f5f6f7&categories=61&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=ffffff&heading_color=202945&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | same |
| `/discord` | https://discord.gg/z6GTSTWsXn | 301 | 301 | https://discord.gg/z6GTSTWsXn | same |
| `/cambridge-connect` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 302 | 301 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same |
| `/online-connect` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 302 | 301 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same |
| `/newyear` | https://brushfire.com/thec3uk/christmas/544521 | 301 | 301 | https://brushfire.com/thec3uk/christmas/544521 | same |
| `/hire` | /room-hire/ | 301 | 301 | /room-hire/ | same |
| `/hamper` | /shop/ | 302 | 301 | /shop/ | same |
| `/griefshare` | https://thec3.churchsuite.com/groups/vibunzhp | 301 | 301 | https://thec3.churchsuite.com/groups/vibunzhp | same |
| `/connect` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 301 | 301 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same |
| `/courses` | https://thec3.churchsuite.com/embed/calendar/featured?category=0 | 301 | 301 | https://thec3.churchsuite.com/embed/calendar/featured?category=0 | same |
| `/howrich` | https://howrichami.givingwhatwecan.org/how-rich-am-i?income=30000&countryCode=GBR&household%5Badults%5D=2&household%5Bchildren%5D=1 | 301 | 301 | https://howrichami.givingwhatwecan.org/how-rich-am-i?income=30000&countryCode=GBR&household%5Badults%5D=2&household%5Bchildren%5D=1 | same |
| `/breathebanquet` | https://thec3uk.brushfire.com/breathe/548748 | 301 | 301 | https://thec3uk.brushfire.com/breathe/548748 | same |
| `/compassion` | https://forms.office.com/e/EetLD3YLJ4 | 301 | 301 | https://forms.office.com/e/EetLD3YLJ4 | same |
| `/c3-marriage-courses` | https://thec3.churchsuite.com/groups/xjkqfivh | 301 | 301 | https://thec3.churchsuite.com/groups/xjkqfivh | same |
| `/wellbeingworkshop` | https://thec3.churchsuite.com/events/vjvfwj9r | 301 | 301 | https://thec3.churchsuite.com/events/vjvfwj9r | same |
| `/teamsignup` | https://thec3.churchsuite.com/forms/wxu56079 | 301 | 301 | https://thec3.churchsuite.com/forms/wxu56079 | same |
| `/easter` | https://love.thec3.uk | 301 | 301 | https://love.thec3.uk/ | same (live adds `/`) |
| `/bury-connect` | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=4 | 301 | 301 | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=4 | same |
| `/lifeatc3` | http://eepurl.com/hpqSKX | 301 | 301 | http://eepurl.com/hpqSKX | same |
| `/myc3` | https://myc3.life | 301 | 301 | https://myc3.life/ | same (live adds `/`) |
| `/colchester-c3-groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=35&text_color=666666 | 302 | 301 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=35&text_color=666666 | same |
| `/shop` | https://store.thec3.uk | 301 | 301 | https://store.thec3.uk/ | same (live adds `/`) |
| `/buryc3groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=33&text_color=666666 | 302 | 301 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=33&text_color=666666 | same |
| `/howtounhurry` | https://static1.squarespace.com/static/58431a7603596e3099e87531/t/5dcd82a34474a007a68a3b47/1573749412344/How+to+Un-Hurry+Workbook.pdf | 301 | 301 | https://static1.squarespace.com/static/58431a7603596e3099e87531/t/5dcd82a34474a007a68a3b47/1573749412344/How+to+Un-Hurry+Workbook.pdf | same |
| `/c3kidslifegoals` | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=12&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&num_results=3&show_categories=0&site=&text_color=666666 | 302 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=12&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&num_results=3&show_categories=0&site=&text_color=666666 | same |
| `/onlinefb` | https://facebook.com/groups/thec3online | 301 | 301 | https://facebook.com/groups/thec3online | same |
| `/ohwhatwonder` | https://thec3uk.brushfire.com/christmas/ | 301 | 301 | https://thec3uk.brushfire.com/christmas/ | same |
| `/fbonline` | https://facebook.com/groups/thec3online | 301 | 301 | https://facebook.com/groups/thec3online | same |
| `/summerparties` | https://thec3uk.brushfire.com/parties/534815 | 302 | 301 | https://thec3uk.brushfire.com/parties/534815 | same |
| `/ascendcamp22` | /ascendcamp/ | 301 | 301 | /ascendcamp/ | same |
| `/teamnight` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=18&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=4&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | 302 | 301 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=18&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=4&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | same |
| `/yth` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=13&event_bgcolor=FFFFFF&event_border=&featured=1&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=sequence_name&num_results=6&show_categories=0&show_search=0&show_sites=1&sites=&text_color=666666 | 301 | 301 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=13&event_bgcolor=FFFFFF&event_border=&featured=1&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=sequence_name&num_results=6&show_categories=0&show_search=0&show_sites=1&sites=&text_color=666666 | same |
| `/allnations` | https://thec3.churchsuite.com/events/jourkgga | 301 | 301 | https://thec3.churchsuite.com/events/jourkgga | same |
| `/alphaonline` | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=15&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&num_results=&show_categories=0&site= | 302 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=15&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&num_results=&show_categories=0&site= | same |
| `/ascendevents` | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=21&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&num_results=&show_categories=0&site= | 302 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=21&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&num_results=&show_categories=0&site= | same |
| `/tithetrial` | https://thec3.churchsuite.co.uk/donate/fund/e2pp8en9 | 301 | 301 | https://thec3.churchsuite.co.uk/donate/fund/e2pp8en9 | same |
| `/kidsevents` | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=12&num_results=20&body_bgcolor=ffffff | 301 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=12&num_results=20&body_bgcolor=ffffff | same |
| `/myrotas` | https://thec3.churchsuite.co.uk/my | 301 | 301 | https://thec3.churchsuite.co.uk/my | same |
| `/give` | https://thec3.churchsuite.co.uk/donate/ | 301 | 301 | https://thec3.churchsuite.co.uk/donate/ | same |
| `/online-c3-groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=32&text_color=666666 | 302 | 301 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=32&text_color=666666 | same |
| `/prayer` | https://prayer.thec3.uk | 301 | 301 | https://prayer.thec3.uk/ | same (live adds `/`) |
| `/christmasmeal-cambridge` | https://thec3.churchsuite.co.uk/events/qgok6byn | 301 | 301 | https://thec3.churchsuite.co.uk/events/qgok6byn | same |
| `/donate` | https://thec3.churchsuite.co.uk/donate/ | 301 | 301 | https://thec3.churchsuite.co.uk/donate/ | same |
| `/yaquestions` | https://docs.google.com/forms/d/e/1FAIpQLSfVNzKcZLStFmdO8OcK6mRr4ZcoBiT5Jfca1xfabx0P1qq3BQ/viewform | 301 | 301 | https://docs.google.com/forms/d/e/1FAIpQLSfVNzKcZLStFmdO8OcK6mRr4ZcoBiT5Jfca1xfabx0P1qq3BQ/viewform | same |
| `/calendar` | https://thec3.churchsuite.co.uk/embed/calendar | 301 | 301 | https://thec3.churchsuite.co.uk/embed/calendar | same |
| `/mychurchsuite` | https://thec3.churchsuite.co.uk/my | 301 | 301 | https://thec3.churchsuite.co.uk/my | same |
| `/cambridge-c3-groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=31&text_color=666666 | 302 | 301 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=31&text_color=666666 | same |
| `/connectform` | https://thec3.churchsuite.co.uk/connect/mydetails/submit | 301 | 301 | https://thec3.churchsuite.co.uk/connect/mydetails/submit | same |
| `/brushfire` | https://thec3uk.brushfire.com/ | 301 | 301 | https://thec3uk.brushfire.com/ | same |
| `/colchester-connect` | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=7 | 301 | 301 | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=7 | same |
| `/chapel` | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=50&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&heading=444444&icon=BBBBBB&num_results=6&show_categories=0&site=&text=666666 | 301 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=50&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&heading=444444&icon=BBBBBB&num_results=6&show_categories=0&site=&text=666666 | same |
| `/slack` | https://join.slack.com/t/thec3uk/shared_invite/zt-8i989kv6-QVF_M7WoZo877ikJNfiPRA | 302 | 301 | https://join.slack.com/t/thec3uk/shared_invite/zt-8i989kv6-QVF_M7WoZo877ikJNfiPRA | same |
| `/ascendsummit` | https://thec3uk.brushfire.com/ascend/ | 302 | 301 | https://thec3uk.brushfire.com/ascend/ | same |
| `/christmasmeal-colchester` | https://thec3.churchsuite.co.uk/events/hzknwb0y | 301 | 301 | https://thec3.churchsuite.co.uk/events/hzknwb0y | same |
| `/buryevents` | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | 301 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | same |
| `/bury-events` | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | 301 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | same |
| `/christmasmeal-bury` | https://thec3uk.brushfire.com/christmas/520273 | 301 | 301 | https://thec3uk.brushfire.com/christmas/520273 | same |
| `/academy` | https://thec3.academy | 301 | 301 | https://thec3.academy/ | same (live adds `/`) |
| `/ccr` | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=49 | 301 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=49 | same |
| `/c3kidsathome` | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=48&num_results=1 | 301 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=48&num_results=1 | same |
| `/donate-nhs` | https://thec3.churchsuite.co.uk/donate/fund/clfqaoft | 301 | 301 | https://thec3.churchsuite.co.uk/donate/fund/clfqaoft | same |
| `/nhs-template-letter` | https://thec3.cdn.prismic.io/thec3/0d1ac88a-b2a6-435d-8830-06334f06d3a3_NHS+Template+Letter.pdf | 301 | 301 | https://thec3.cdn.prismic.io/thec3/0d1ac88a-b2a6-435d-8830-06334f06d3a3_NHS+Template+Letter.pdf | same |
| `/racism-and-injustice-paper` | https://thec3.cdn.prismic.io/thec3/c2d015a1-487a-4d2e-b9c9-9d7c113fc67b_Racism+and+Injustice+Paper.pdf | 301 | 301 | https://thec3.cdn.prismic.io/thec3/c2d015a1-487a-4d2e-b9c9-9d7c113fc67b_Racism+and+Injustice+Paper.pdf | same |
| `/bury-sunday-services` | https://thec3uk.brushfire.com/bury | 302 | 301 | https://thec3uk.brushfire.com/bury | same |
| `/sunday-services-colchester` | https://thec3uk.brushfire.com/colchester/ | 301 | 301 | https://thec3uk.brushfire.com/colchester/ | same |
| `/ythonline` | https://thec3.churchsuite.co.uk/events/ur8lqpbg | 302 | 301 | https://thec3.churchsuite.co.uk/events/ur8lqpbg | same |
| `/cambridge-sunday-services` | https://thec3uk.brushfire.com/cambridge | 302 | 301 | https://thec3uk.brushfire.com/cambridge | same |
| `/give-help` | https://thec3.churchsuite.co.uk/events/g2vedgl5 | 302 | 301 | https://thec3.churchsuite.co.uk/events/g2vedgl5 | same |
| `/yalive` | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=11&body_bgcolor=ffffff | 302 | 301 | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=11&body_bgcolor=ffffff | same |
| `/get-help` | https://thec3.churchsuite.co.uk/events/1nb0ciwz | 302 | 301 | https://thec3.churchsuite.co.uk/events/1nb0ciwz | same |
| `/c3-youth` | https://thec3.uk/c3youth | 301 | 301 | https://thec3.uk/c3youth | same |
| `/yawelcome` | https://zoom.us/j/99248772819?pwd=bWoyeFVvdjNaSEQ4cXc0UnlEd1Fmdz09 | 302 | 301 | https://zoom.us/j/99248772819?pwd=bWoyeFVvdjNaSEQ4cXc0UnlEd1Fmdz09 | same |
| `/cv19support` | https://thec3.churchsuite.co.uk/events/yzj0aaqd | 301 | 301 | https://thec3.churchsuite.co.uk/events/yzj0aaqd | same |
| `/love-your-neighbour` | https://thec3.churchsuite.co.uk/donate/fund/qsmtu2lw | 301 | 301 | https://thec3.churchsuite.co.uk/donate/fund/qsmtu2lw | same |
| `/ya-signup` | https://thec3.churchsuite.co.uk/groups/rbos2oqs | 301 | 301 | https://thec3.churchsuite.co.uk/groups/rbos2oqs | same |
| `/youtube` | https://www.youtube.com/user/cthreemedia | 301 | 301 | https://www.youtube.com/user/cthreemedia | same |
| `/pineapple` | https://forms.gle/pjmtFvLLvH4jpDzZ9 | 301 | 301 | https://forms.gle/pjmtFvLLvH4jpDzZ9 | same |
| `/broken-link` | https://google.com | 301 | 301 | https://google.com/ | same (live adds `/`) |
| `/breathe` | https://breathe.thec3.uk | 301 | 301 | https://breathe.thec3.uk/ | same (live adds `/`) |
| `/openletter` | https://thec3.cdn.prismic.io/thec3/65763cd7-4260-46a2-9875-32dede16905d_Open+letter.pdf | 301 | 301 | https://thec3.cdn.prismic.io/thec3/65763cd7-4260-46a2-9875-32dede16905d_Open+letter.pdf | same |
| `/breatheconference` | https://breathe.thec3.uk | 301 | 301 | https://breathe.thec3.uk/ | same (live adds `/`) |
