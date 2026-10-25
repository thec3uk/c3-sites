# Phase 4 M4: myc3.life parity check

Every myc3 page built locally (`just build myc3`, `dist/`) compared with live https://myc3.life on 25 Oct 2026, plus every generated redirect. Use it to decide on the preview and cutover.

## Summary

- **Live returns HTTP 500 on the five pages shared with thec3.uk**: `/trustees/`, `/online/`, `/cambridge/`, `/team/` and `/visionandvalues/`. The build renders them, but their cards show Slice Machine placeholder text ("Template slice, update me!" / "start by editing this slice from inside Slice Machine!"). That is faithful to the Next Card, which reads the myc3 card fields that these thec3.uk documents leave empty. **Suggested fix (Andy's call): untag `domain:myc3.life` from those five pages in Prismic**, so neither site serves them on myc3.life.
- **Pages: 16** (15 from `site_pages()` plus the 404 page). **9 match, 0 minor, 7 differs.** The seven are the five 500 pages above, `/alpha/` (live redirects, the build serves the page, by decision) and the 404 page (shared template, by decision). Every page that renders on live is pixel-identical or within 0.1%, with the same text and links.
- **Redirects: 185** (one per Prismic redirect document; the 184 uppercase twins weren't requested). **182 have the same class** (302 vs 307, 301 vs 308) and **180 the same target**. 175 Location headers are byte-identical, and 5 differ only by live's `/` after a bare domain. Of the other five:
  - three 500 on live because their Prismic URL holds a pasted `[…]`;
  - two point at another document, which live writes without the trailing slash and the build with it.
  - Details are under "Redirects that differ" below.
- **No port bugs found.** M1-M3 files are unchanged in M4.
- **Nothing blocked the check.** It used plain Playwright and httpx with the user agent `c3-sites parity-check`. Requests were sequential with a 0.2s gap, read-only, and sent no form submissions. Umami requests (`analytics.myc3.life`) were blocked on both sides. Two runs hit transient errors, both re-run:
  - Chromium's `net::ERR_NETWORK_CHANGED` while following `/alpha` to ChurchSuite. The script now records such a page instead of crashing; the re-run loaded it normally.
  - One home 390px live shot that loaded without its CSS. Re-run with `--pages /`; it matches.

## How it was checked

`scripts/parity_check.py`, generalised in M4, was run like this after `just build myc3`:

```
SITE=myc3 uv run python scripts/parity_check.py --out docs/plans/phase-4/evidence/m4 \
    --static ~/c3/creative/websites/myc3/public
```

The live base (`https://myc3.life`), link hosts and analytics host come from the site config (`config/settings/sites/myc3.py`); `--live` overrides the base. For each page, as in Phase 3, the script:

- takes full-page screenshots at 1440x900 and 390x844;
- records status, `<title>`, meta description, canonical, every `a[href]` and the visible text;
- diffs the two screenshots pixel by pixel.

Live is requested without the trailing slash (Next's own URLs). Raw data is in [results.json](results.json); screenshots stay local (git-ignored).

**Statuses are now set in code** (`classify()`), with these constants in the script:

- **differs**:
  - a status class differs (the 404 page must be 404 live and 200 from the local file server);
  - a page height differs by more than `MINOR_MAX_HEIGHT_PX` = 2 at either width;
  - more than `MINOR_MAX_RATIO` = 5% of pixels differ;
  - a live link target is missing from the build entirely (self-links and duplicates aside);
  - or more than `MAX_LIVE_ONLY_TEXT_LINES` = 1 line of text is only on live.
- **minor**: otherwise, a height difference of 1-2px or more than `MATCH_MAX_RATIO` = 0.3% of pixels differ.
- **match**: none of the above.

**Phase 3 re-run.** The classifier was re-run on Phase 3's `results.json` (`--classify-only`). It gives 29 match, 10 minor, 2 differs, against Phase 3's hand labels of 30/10/1. 40 of 41 pages agree. One main-site page now classifies differently:

| Page | Phase 3 | Classifier | Why |
|---|---|---|---|
| `/trustees/` | match | differs | Phase 3's rows recorded only link-count differences, not which targets the build lacks. Live has two links to `/visionandvalues` and the build one (the empty image-cell link Phase 3 noted), so from that data it looks missing. The main build does link to it (`https://thec3.uk/visionandvalues`). New runs record `links.missing`, and on fresh data this page would be **match**. |

On Phase 3's data, any match threshold from 0.19% (the largest match, `/kids/` at 390) up to just under 0.56% (`/c3-groups/`, the smallest minor without a height change) gives the same labels. So does any minor threshold above 2.86% (`/team/` at 390); no Phase 3 page differed visually. The text allowance of one line keeps `/contact/` a **match**: its only live-only line is the hidden listbox label "Category".

**Redirect class** is now permanent (301/308) vs temporary (302/303/307), as the brief asks. Phase 3 counted any 3xx as the same class. Under the new rule, Phase 3's 242 redirects are 100 same and 142 different: the decided 302s where Gatsby sent 301. **Redirect targets** now treat a bare domain with and without `/` as the same (Phase 3's 11 flagged rows become same). Site paths are resolved against the live base before comparing.

## For Andy: differences that are decided or are content

1. **Five shared pages 500 on live, render placeholders in the build** (see Summary). Untagging `domain:myc3.life` in Prismic is the suggested fix; after that the build drops them on the next build and live 404s them.
2. **`/alpha/` is both a page and a redirect.** It is the only path where live serves a redirect but the build serves a page. Live 307s `/alpha` to https://thec3.churchsuite.com/events/wswkhomf. The build serves the myc3 "Alpha at C3" page, because the page wins (README decision, as on the main site). Untag or delete one of the two in Prismic if live's behaviour is wanted.
3. **The 404 page.** Live shows Next's default page ("404: This page could not be found", title "404: This page could not be found"). The build uses the shared 404 template in the myc3 layout ("Page not found", a link home, `noindex`).
4. **SEO tags the build adds over live.** Live's `<head>` has only `charset`, `viewport` (`width=device-width`), Next's CSS links and the Umami script; it has **no `<title>`**, description, canonical or Open Graph tags. The build's shared `base.html` adds the following (accepted, README):
   - `<title>` on every page. It is empty on 14 pages, because myc3 has no `site_config` and those pages have no seo_title. On `/share-your-story/` it is "SHARE YOUR STORY" (its seo_title); on the 404 page, "Page not found".
   - `<link rel="canonical" href="https://myc3.life/<uid>/">` on every page except the 404.
   - `<link rel="icon" href="/favicon.ico">`, `initial-scale=1` in the viewport, and `data-do-not-track="true"` on the Umami script.
   - **No** meta description, Open Graph or Twitter tags, because they come from `site_config`, which myc3 lacks. Add a myc3 `site_config` in Prismic if you want them.
5. **Trailing slashes.** Live pages have no trailing slash (Next 308s `/team/` to `/team`). The build uses `/<uid>/` (README decision). As a result, two redirects to other documents differ only by the slash (below), and canonical URLs use the slash. Check on the Netlify preview that `/team` reaches `/team/`.
6. **Redirect status codes**: live 307/308, build 302/301 by `permanent` (same classes, decided).
7. **Sitemap.** Live has no sitemap (`/sitemap.xml` is 404). The build adds `/sitemap.xml` with the 15 pages, but no `robots.txt` points to it (see below).

Content issues for Andy (Prismic, both live and build):

- **Three redirects have truncated destination URLs** containing a literal `[…]`, copied from a shortened display: `/baptisms`, `/marathon` and `/impactnight`. Live returns 500 for each (Next can't send a non-ASCII Location). The build writes the rule, but Netlify will redirect to the broken URL. Paste the full URLs in Prismic. `/baptisms` and `/marathon` are the same documents as on thec3.uk, where Phase 3 saw the same truncation.
- **`/kidschurch` → `/kids-church/` and `/hamper` → `/shop/`** point at other redirects, so both take two hops on live and in the build. They work, and could point straight at the final URL.
- `/test-page-here` (→ google.com) looks like a leftover, as on thec3.uk.

## Redirects that differ

| Source | Build | Live | Why |
|---|---|---|---|
| `/baptisms` | 302 → truncated `…body_b[…]0000…` URL | 500 | Prismic destination contains `[…]`; content fix. |
| `/marathon` | 302 → truncated `…HkJ[…]ptu3…` URL | 500 | Same. |
| `/impactnight` | 301 → truncated `…&e[…]ries=0…` URL | 500 | Same. |
| `/kidschurch` | 301 → `/kids-church/` | 308 → `/kids-church` | Trailing-slash URL style (decided). `/kids-church` is itself a redirect. Netlify should match the slashed path to the `/kids-church` rule, but this is not verified here; check on the preview. |
| `/hamper` | 302 → `/shop/` | 307 → `/shop` | Same; `/shop` is a redirect to the store. |

`/alpha` is the same on both (307 vs 302, same target), but the build serves the `/alpha/` page in front of it, as above.

## What live has that the build lacks

- **`/__forms.html`** (200 on live) is the Next repo's static stub so that Netlify detects the contact form. The build doesn't need it: the form is in the built page's HTML (M2), and Netlify detects forms in static HTML at deploy. Check on the preview that the form appears under Netlify Forms (README step). `favicon.ico` is in the build.
- **`/robots.txt`** (200 on live) is Cloudflare's managed robots.txt (`server: cloudflare`, a Content-Signal line and `Disallow: /` for about 30 AI and SEO crawlers), not a file from the Next repo. The build has none for myc3 (the main theme ships one). If myc3.life stays proxied through Cloudflare with that setting on, it should keep being served after cutover; not verified here.
- **Next's runtime paths** (`/_next/...`, `/api/preview`) aren't ported, by decision.
- Nothing visible on any page that renders on live is missing from the build.

## Pages

Screenshot links are relative to this folder (local only).

| Page | Status | 1440 height live/local, diff | 390 height live/local, diff | Screenshots 1440 | Screenshots 390 | Notes |
|---|---|---|---|---|---|---|
| `/` | **match** | 1282/1282, 0.05% | 1103/1103, 0.00% | [live](home-1440-live.jpg) / [local](home-1440-local.jpg) | [live](home-390-live.jpg) / [local](home-390-local.jpg) |  |
| `/alpha/` | **differs** | 2306/900, 5.99% | 844/844, 3.52% | [live](alpha-1440-live.jpg) / [local](alpha-1440-local.jpg) ([diff](alpha-1440-diff.jpg)) | [live](alpha-390-live.jpg) / [local](alpha-390-local.jpg) ([diff](alpha-390-diff.jpg)) | Live 307s to the ChurchSuite Alpha event (shot is ChurchSuite); the build serves the page (decided, page wins). |
| `/cambridge/` | **differs** | 900/2214, 2.63% | 844/1787, 6.33% | [live](cambridge-1440-live.jpg) / [local](cambridge-1440-local.jpg) ([diff](cambridge-1440-diff.jpg)) | [live](cambridge-390-live.jpg) / [local](cambridge-390-local.jpg) ([diff](cambridge-390-diff.jpg)) | Live 500. Build renders it; cards show Slice Machine placeholder text ("Template slice, update me!"), as Next's Card would. |
| `/groups/` | **match** | 900/900, 0.00% | 844/844, 0.00% | [live](groups-1440-live.jpg) / [local](groups-1440-local.jpg) | [live](groups-390-live.jpg) / [local](groups-390-local.jpg) |  |
| `/growth-path/` | **match** | 2177/2177, 0.00% | 2229/2229, 0.01% | [live](growth-path-1440-live.jpg) / [local](growth-path-1440-local.jpg) | [live](growth-path-390-live.jpg) / [local](growth-path-390-local.jpg) |  |
| `/next-steps/` | **match** | 2612/2612, 0.01% | 2804/2804, 0.03% | [live](next-steps-1440-live.jpg) / [local](next-steps-1440-local.jpg) | [live](next-steps-390-live.jpg) / [local](next-steps-390-local.jpg) |  |
| `/online/` | **differs** | 900/1878, 2.25% | 844/1339, 6.07% | [live](online-1440-live.jpg) / [local](online-1440-local.jpg) ([diff](online-1440-diff.jpg)) | [live](online-390-live.jpg) / [local](online-390-local.jpg) ([diff](online-390-diff.jpg)) | Live 500. Build renders it; cards show Slice Machine placeholder text ("Template slice, update me!"), as Next's Card would. |
| `/share-your-story/` | **match** | 1012/1012, 0.00% | 844/844, 0.02% | [live](share-your-story-1440-live.jpg) / [local](share-your-story-1440-local.jpg) | [live](share-your-story-390-live.jpg) / [local](share-your-story-390-local.jpg) | Build `<title>` is "SHARE YOUR STORY" (the page's seo_title); live has no title tag. |
| `/step-2-complete/` | **match** | 2711/2711, 0.00% | 2715/2715, 0.01% | [live](step-2-complete-1440-live.jpg) / [local](step-2-complete-1440-local.jpg) | [live](step-2-complete-390-live.jpg) / [local](step-2-complete-390-local.jpg) |  |
| `/team-next-steps/` | **match** | 900/900, 0.00% | 844/844, 0.00% | [live](team-next-steps-1440-live.jpg) / [local](team-next-steps-1440-local.jpg) | [live](team-next-steps-390-live.jpg) / [local](team-next-steps-390-local.jpg) |  |
| `/team/` | **differs** | 900/1260, 1.73% | 844/1408, 5.00% | [live](team-1440-live.jpg) / [local](team-1440-local.jpg) ([diff](team-1440-diff.jpg)) | [live](team-390-live.jpg) / [local](team-390-local.jpg) ([diff](team-390-diff.jpg)) | Live 500. Build renders it; cards show Slice Machine placeholder text ("Template slice, update me!"), as Next's Card would. |
| `/teamc3/` | **match** | 2700/2700, 0.00% | 2820/2820, 0.00% | [live](teamc3-1440-live.jpg) / [local](teamc3-1440-local.jpg) | [live](teamc3-390-live.jpg) / [local](teamc3-390-local.jpg) |  |
| `/trustees/` | **differs** | 900/2168, 4.69% | 844/2480, 9.05% | [live](trustees-1440-live.jpg) / [local](trustees-1440-local.jpg) ([diff](trustees-1440-diff.jpg)) | [live](trustees-390-live.jpg) / [local](trustees-390-local.jpg) ([diff](trustees-390-diff.jpg)) | Live 500. Build renders it; cards show Slice Machine placeholder text ("Template slice, update me!"), as Next's Card would. |
| `/visionandvalues/` | **differs** | 900/7628, 3.17% | 844/8808, 7.59% | [live](visionandvalues-1440-live.jpg) / [local](visionandvalues-1440-local.jpg) ([diff](visionandvalues-1440-diff.jpg)) | [live](visionandvalues-390-live.jpg) / [local](visionandvalues-390-local.jpg) ([diff](visionandvalues-390-diff.jpg)) | Live 500. Build renders it; cards show Slice Machine placeholder text ("Template slice, update me!"), as Next's Card would. |
| `/yth/` | **match** | 1024/1024, 0.07% | 873/873, 0.00% | [live](yth-1440-live.jpg) / [local](yth-1440-local.jpg) | [live](yth-390-live.jpg) / [local](yth-390-local.jpg) |  |
| `/404.html` | **differs** | 900/900, 0.20% | 844/844, 0.79% | [live](404.html-1440-live.jpg) / [local](404.html-1440-local.jpg) | [live](404.html-390-live.jpg) / [local](404.html-390-local.jpg) ([diff](404.html-390-diff.jpg)) | Live: `/parity-check-missing-page` (404), Next's default "404: This page could not be found". Local `/404.html` via the script's file server, hence 200; Netlify sends 404. Build uses the shared 404 template in the myc3 layout ("Page not found", link home). |


## Redirects

Each source was requested once on live without following the redirect. **Build** is the status in `dist/_redirects`; **Class** compares permanent (301/308) vs temporary (302/307); **Target** compares live's `Location` with the build's target.

| Source | Build target | Build | Live | Live Location | Class | Target |
|---|---|---|---|---|---|---|
| `/debrief` | https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=3W6n-46yPkqAhAf3hHjUYP8vYQJxLIxGiXPE2vNQI79UMTRLVEVHU1YxR0tHMFVRMDUzRkE2SzlOVS4u | 302 | 307 | https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=3W6n-46yPkqAhAf3hHjUYP8vYQJxLIxGiXPE2vNQI79UMTRLVEVHU1YxR0tHMFVRMDUzRkE2SzlOVS4u | same | same |
| `/bible` | https://bible.com/events/49682212 | 302 | 307 | https://bible.com/events/49682212 | same | same |
| `/headcount` | https://forms.cloud.microsoft/e/8Hu7xckJ6s | 302 | 307 | https://forms.cloud.microsoft/e/8Hu7xckJ6s | same | same |
| `/group-leaders` | https://thec3.notion.site/Group-Leader-s-Page-cd34acdbf5a148ba93b0c289feb24e72?pvs=74 | 301 | 308 | https://thec3.notion.site/Group-Leader-s-Page-cd34acdbf5a148ba93b0c289feb24e72?pvs=74 | same | same |
| `/giftaid` | https://thec3.churchsuite.com/-/forms/h8po0xdj | 302 | 307 | https://thec3.churchsuite.com/-/forms/h8po0xdj | same | same |
| `/prophetic-teaching-day` | https://thec3.churchsuite.com/events/oeigcfbm | 302 | 307 | https://thec3.churchsuite.com/events/oeigcfbm | same | same |
| `/gls` | https://thec3.churchsuite.com/events/7jkscdle | 302 | 307 | https://thec3.churchsuite.com/events/7jkscdle | same | same |
| `/4thservice` | https://thec3.churchsuite.com/-/forms/vcmr5v4n | 302 | 307 | https://thec3.churchsuite.com/-/forms/vcmr5v4n | same | same |
| `/lightnight` | https://thec3.churchsuite.com/-/calendar/ce91e008-808b-4683-a898-cda981e810b6 | 302 | 307 | https://thec3.churchsuite.com/-/calendar/ce91e008-808b-4683-a898-cda981e810b6 | same | same |
| `/academyopenevening` | https://thec3.churchsuite.com/events/tvxvflie | 302 | 307 | https://thec3.churchsuite.com/events/tvxvflie | same | same |
| `/propheticmorning` | https://thec3.churchsuite.com/events/eexvqq5p | 302 | 307 | https://thec3.churchsuite.com/events/eexvqq5p | same | same |
| `/alpha` (build serves a page) | https://thec3.churchsuite.com/events/wswkhomf | 302 | 307 | https://thec3.churchsuite.com/events/wswkhomf | same | same |
| `/messyplay` | https://thec3.churchsuite.com/events/yzrfqwmd | 302 | 307 | https://thec3.churchsuite.com/events/yzrfqwmd | same | same |
| `/calendar-bury` | https://thec3.churchsuite.com/-/calendar/410a57b3-3344-4660-968e-54a27594701f?preview=1 | 301 | 308 | https://thec3.churchsuite.com/-/calendar/410a57b3-3344-4660-968e-54a27594701f?preview=1 | same | same |
| `/christmasinabox` | https://thec3.churchsuite.com/-/calendar/e0e42240-7be0-4ed8-bad0-edbbb044fc1c | 302 | 307 | https://thec3.churchsuite.com/-/calendar/e0e42240-7be0-4ed8-bad0-edbbb044fc1c | same | same |
| `/wtc` | https://www.eventbrite.co.uk/e/kingdom-theology-event-in-cambridge-with-alister-wallace-tickets-1984457635207?aff=oddtdtcreator | 302 | 307 | https://www.eventbrite.co.uk/e/kingdom-theology-event-in-cambridge-with-alister-wallace-tickets-1984457635207?aff=oddtdtcreator | same | same |
| `/baptismclasses` | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20&body_bgcolor=ffffff&event_border_color=228ae6&heading_color=228ae6&text_color=000000&icon_color=000000 | 302 | 307 | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20&body_bgcolor=ffffff&event_border_color=228ae6&heading_color=228ae6&text_color=000000&icon_color=000000 | same | same |
| `/gls-c3family` | https://thec3.churchsuite.com/events/7jkscdle?tickets=xV8K | 301 | 308 | https://thec3.churchsuite.com/events/7jkscdle?tickets=xV8K | same | same |
| `/kintsugi` | https://thec3.churchsuite.com/events/gpcmzx8m | 302 | 307 | https://thec3.churchsuite.com/events/gpcmzx8m | same | same |
| `/teardrop` | https://www.teardropgrief.co.uk/shop/p/griefandloss-webinar | 302 | 307 | https://www.teardropgrief.co.uk/shop/p/griefandloss-webinar | same | same |
| `/gameplan` | https://thec3.churchsuite.com/-/calendar/43ce142b-6e7f-4991-9fb7-2a228ff1502a?preview=1 | 302 | 307 | https://thec3.churchsuite.com/-/calendar/43ce142b-6e7f-4991-9fb7-2a228ff1502a?preview=1 | same | same |
| `/btg` | https://btgfootballbookings.com/bookings/Cambridge?utm_source=ig&utm_medium=social&utm_content=link_in_bio&fbclid=PAZXh0bgNhZW0CMTEAc3J0YwZhcHBfaWQMMjU2MjgxMDQwNTU4AAGnJSA_IFRLeSMrwqbJLxgEceCI_y0SIXZ4BZfnyD6eEHkpx2dtjr07AXLvDwM_aem_f_T8DYWGMPxJlyl4iBudMg | 302 | 307 | https://btgfootballbookings.com/bookings/Cambridge?utm_source=ig&utm_medium=social&utm_content=link_in_bio&fbclid=PAZXh0bgNhZW0CMTEAc3J0YwZhcHBfaWQMMjU2MjgxMDQwNTU4AAGnJSA_IFRLeSMrwqbJLxgEceCI_y0SIXZ4BZfnyD6eEHkpx2dtjr07AXLvDwM_aem_f_T8DYWGMPxJlyl4iBudMg | same | same |
| `/prayersubscribe` | https://thec3.churchsuite.com/-/forms/ytxl0non | 302 | 307 | https://thec3.churchsuite.com/-/forms/ytxl0non | same | same |
| `/athome` | https://youtube.com/live/SAkB48Oyrdg?feature=share | 302 | 307 | https://youtube.com/live/SAkB48Oyrdg?feature=share | same | same |
| `/revelation` | https://thec3.churchsuite.com/events/edpl6ody | 302 | 307 | https://thec3.churchsuite.com/events/edpl6ody | same | same |
| `/worldchangers` | https://thec3.churchsuite.com/events/ynjs8lm1 | 302 | 307 | https://thec3.churchsuite.com/events/ynjs8lm1 | same | same |
| `/ascend-reflection` | https://thec3.churchsuite.com/events/9cm6cdri | 302 | 307 | https://thec3.churchsuite.com/events/9cm6cdri | same | same |
| `/prayerfasting` | https://www.youtube.com/watch?v=jHSrczIYDTA&t=11s | 302 | 307 | https://www.youtube.com/watch?v=jHSrczIYDTA&t=11s | same | same |
| `/test-page-here` | https://www.google.com | 301 | 308 | https://www.google.com/ | same | same (live adds `/`) |
| `/coach` | https://thec3.churchsuite.com/events/mbqq46rc | 301 | 308 | https://thec3.churchsuite.com/events/mbqq46rc | same | same |
| `/visionoffering2026` | https://thec3.churchsuite.com/donate/fund/ukevxdcx | 302 | 307 | https://thec3.churchsuite.com/donate/fund/ukevxdcx | same | same |
| `/watoto` | https://thec3.churchsuite.com/-/forms/ztashznr | 302 | 307 | https://thec3.churchsuite.com/-/forms/ztashznr | same | same |
| `/overwhelmtour` | https://thec3.churchsuite.com/events/uy2uahd4 | 302 | 307 | https://thec3.churchsuite.com/events/uy2uahd4 | same | same |
| `/stw` | https://www.stewardship.org.uk/pages/stw2025 | 302 | 307 | https://www.stewardship.org.uk/pages/stw2025 | same | same |
| `/yasouls` | https://brushfire.com/thec3uk/yasouls/615662 | 302 | 307 | https://brushfire.com/thec3uk/yasouls/615662 | same | same |
| `/help` | https://www.samaritans.org/how-we-can-help/contact-samaritan/?utm_source=google&utm_medium=organic&utm_campaign=onebox | 302 | 307 | https://www.samaritans.org/how-we-can-help/contact-samaritan/?utm_source=google&utm_medium=organic&utm_campaign=onebox | same | same |
| `/reflection` | https://www.teardropgrief.co.uk/shop/p/teardrop-online-christmas-reflection | 302 | 307 | https://www.teardropgrief.co.uk/shop/p/teardrop-online-christmas-reflection | same | same |
| `/restoration` | https://thec3.churchsuite.com/events/bjh1cia4 | 302 | 307 | https://thec3.churchsuite.com/events/bjh1cia4 | same | same |
| `/yachristmasparty` | https://thec3.churchsuite.com/events/d8ezbeuv | 302 | 307 | https://thec3.churchsuite.com/events/d8ezbeuv | same | same |
| `/divorcerecovery` | https://thec3.churchsuite.com/events/j46sqy7f | 302 | 307 | https://thec3.churchsuite.com/events/j46sqy7f | same | same |
| `/openevening` | https://thec3.churchsuite.com/events/tvxvflie | 302 | 307 | https://thec3.churchsuite.com/events/tvxvflie | same | same |
| `/cared` | https://thec3.churchsuite.com/events/mfnk3fij | 302 | 307 | https://thec3.churchsuite.com/events/mfnk3fij | same | same |
| `/academy-open` | https://thec3.churchsuite.com/events/l1cbespe | 302 | 307 | https://thec3.churchsuite.com/events/l1cbespe | same | same |
| `/wellbeing-workshop` | https://thec3.churchsuite.com/events/zqvcwdbo | 302 | 307 | https://thec3.churchsuite.com/events/zqvcwdbo | same | same |
| `/youversion` | https://www.youversion.com/the-bible-app/ | 302 | 307 | https://www.youversion.com/the-bible-app/ | same | same |
| `/prophetic` | https://thec3.churchsuite.com/events/emgrows6 | 302 | 307 | https://thec3.churchsuite.com/events/emgrows6 | same | same |
| `/greatiam` | https://wingsmusic.lnk.to/GreatIAMYahwehLive | 302 | 307 | https://wingsmusic.lnk.to/GreatIAMYahwehLive | same | same |
| `/nationalprayer` | https://www.youtube.com/watch?v=tPUpTvvLoRY | 301 | 308 | https://www.youtube.com/watch?v=tPUpTvvLoRY | same | same |
| `/55` | https://thec3.churchsuite.com/events/lquf4igc | 302 | 307 | https://thec3.churchsuite.com/events/lquf4igc | same | same |
| `/stayingsafeonline` | https://thec3.churchsuite.com/events/7ncpz09i | 302 | 307 | https://thec3.churchsuite.com/events/7ncpz09i | same | same |
| `/table` | https://thec3.churchsuite.com/events/61zzb8mw | 302 | 307 | https://thec3.churchsuite.com/events/61zzb8mw | same | same |
| `/ascendmen` | https://www.facebook.com/groups/527708931330993 | 302 | 307 | https://www.facebook.com/groups/527708931330993 | same | same |
| `/backtoschool` | https://thec3.churchsuite.com/-/calendar/cb41ebe8-4807-4f8c-ad41-3a550bbe4b0c | 302 | 307 | https://thec3.churchsuite.com/-/calendar/cb41ebe8-4807-4f8c-ad41-3a550bbe4b0c | same | same |
| `/guestspeaker` | https://thec3church.typeform.com/to/DHC1Uv4G | 302 | 307 | https://thec3church.typeform.com/to/DHC1Uv4G | same | same |
| `/churchsuite` | https://churchsuite.com/apps/ | 302 | 307 | https://churchsuite.com/apps/ | same | same |
| `/laura` | https://youtu.be/T0ST70FiR8w | 302 | 307 | https://youtu.be/T0ST70FiR8w | same | same |
| `/autumn` | https://youtu.be/BqOk7IyolKc | 302 | 307 | https://youtu.be/BqOk7IyolKc | same | same |
| `/ubuntu` | https://open.substack.com/pub/thec3church/p/ubuntu?r=5dfdqj&utm_campaign=post&utm_medium=web | 302 | 307 | https://open.substack.com/pub/thec3church/p/ubuntu?r=5dfdqj&utm_campaign=post&utm_medium=web | same | same |
| `/all-kids-team` | https://thec3.notion.site/ALL-KIDS-TEAM-1cba6815f917802081eff157cdefb670 | 301 | 308 | https://thec3.notion.site/ALL-KIDS-TEAM-1cba6815f917802081eff157cdefb670 | same | same |
| `/bigchurch` | https://bigchurchtickets.com/events/tim-the-glory-boys-philippa-hanna?fbclid=PAZXh0bgNhZW0CMTEAAafyumyud8jcfvvNy-C1NbjSX1mR_ycG3tnpNE7G67N4JREjOBv1j3M0N9vbfQ_aem_-jnikfOSUB2-1KdZ_9y82Q | 302 | 307 | https://bigchurchtickets.com/events/tim-the-glory-boys-philippa-hanna?fbclid=PAZXh0bgNhZW0CMTEAAafyumyud8jcfvvNy-C1NbjSX1mR_ycG3tnpNE7G67N4JREjOBv1j3M0N9vbfQ_aem_-jnikfOSUB2-1KdZ_9y82Q | same | same |
| `/teamcol` | https://thec3.churchsuite.com/forms/tzissv55 | 301 | 308 | https://thec3.churchsuite.com/forms/tzissv55 | same | same |
| `/pilates` | https://thec3.churchsuite.com/events/uujt8mvp | 302 | 307 | https://thec3.churchsuite.com/events/uujt8mvp | same | same |
| `/kidsmail` | https://mailchi.mp/dabde5024bdb/kids-mailout-sign-up | 301 | 308 | https://mailchi.mp/dabde5024bdb/kids-mailout-sign-up | same | same |
| `/prophetictraining` | https://thec3.churchsuite.com/events/y8int78b | 302 | 307 | https://thec3.churchsuite.com/events/y8int78b | same | same |
| `/kidsgroup` | https://thec3.churchsuite.com/events/jrvqmijr | 302 | 307 | https://thec3.churchsuite.com/events/jrvqmijr | same | same |
| `/yourkingdomcome` | https://wingsmusic.lnk.to/YourKingdomCome | 302 | 307 | https://wingsmusic.lnk.to/YourKingdomCome | same | same |
| `/baptisms` | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20&body_b[…]0000&icon_color=000000&mc_cid=b9f72f2951&mc_eid=2db005e1de | 302 | 500 |  | **differs** | **differs** |
| `/wellbeingcol` | https://thec3.churchsuite.com/events/rlpysgrs | 301 | 308 | https://thec3.churchsuite.com/events/rlpysgrs | same | same |
| `/open` | https://www.eventbrite.co.uk/e/monday-hub-open-eve-for-bris-camb-emid-manc-scot-sotn-wmid-tickets-816680221527 | 301 | 308 | https://www.eventbrite.co.uk/e/monday-hub-open-eve-for-bris-camb-emid-manc-scot-sotn-wmid-tickets-816680221527 | same | same |
| `/atwork` | https://brushfire.com/thec3uk/c3atwork/577791 | 301 | 308 | https://brushfire.com/thec3uk/c3atwork/577791 | same | same |
| `/burykidsfest` | https://thec3.churchsuite.com/events/0ahemc4v | 301 | 308 | https://thec3.churchsuite.com/events/0ahemc4v | same | same |
| `/step1` | https://thec3.churchsuite.com/-/calendar/7071888a-8b5e-4655-8b10-4c511479efb8 | 301 | 308 | https://thec3.churchsuite.com/-/calendar/7071888a-8b5e-4655-8b10-4c511479efb8 | same | same |
| `/dti` | https://brushfire.com/thec3uk/dreamingtheimpossible/582890 | 302 | 307 | https://brushfire.com/thec3uk/dreamingtheimpossible/582890 | same | same |
| `/cambkidsfest` | https://thec3.churchsuite.com/events/kt7xjuvw | 302 | 307 | https://thec3.churchsuite.com/events/kt7xjuvw | same | same |
| `/followthatverse` | https://us02web.zoom.us/j/83856907739?pwd=iObDaXB1J804jtr3gBX6oqD6Wsffwa.1 | 302 | 307 | https://us02web.zoom.us/j/83856907739?pwd=iObDaXB1J804jtr3gBX6oqD6Wsffwa.1 | same | same |
| `/party` | https://thec3.churchsuite.com/events/h2zlwnhr | 302 | 307 | https://thec3.churchsuite.com/events/h2zlwnhr | same | same |
| `/sound` | https://youtu.be/HDA0Hk93CsQ | 302 | 307 | https://youtu.be/HDA0Hk93CsQ | same | same |
| `/pctraining` | https://thec3.churchsuite.com/events/kwmf9w1z | 302 | 307 | https://thec3.churchsuite.com/events/kwmf9w1z | same | same |
| `/propheticpod` | https://youtu.be/0N_Y7Bs7xiE | 302 | 307 | https://youtu.be/0N_Y7Bs7xiE | same | same |
| `/wellbeing` | https://thec3.churchsuite.com/-/calendar/843a3727-0e54-4538-9baf-b74006ef1a80 | 302 | 307 | https://thec3.churchsuite.com/-/calendar/843a3727-0e54-4538-9baf-b74006ef1a80 | same | same |
| `/teamb2sbbq` | https://thec3.churchsuite.com/-/calendar/cb41ebe8-4807-4f8c-ad41-3a550bbe4b0c | 302 | 307 | https://thec3.churchsuite.com/-/calendar/cb41ebe8-4807-4f8c-ad41-3a550bbe4b0c | same | same |
| `/colkidsfest` | https://thec3.churchsuite.com/events/v4ddyfhi | 302 | 307 | https://thec3.churchsuite.com/events/v4ddyfhi | same | same |
| `/hello` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 302 | 307 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same | same |
| `/burybbq` | https://thec3.churchsuite.com/events/93p5ehhj | 302 | 307 | https://thec3.churchsuite.com/events/93p5ehhj | same | same |
| `/marriage` | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-england-tickets-872798061497 | 302 | 307 | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-england-tickets-872798061497 | same | same |
| `/colgroups` | https://thec3.churchsuite.com/embed/v2/smallgroups/35b73a5a-f3b2-4584-90bb-6bb437e14466 | 302 | 307 | https://thec3.churchsuite.com/embed/v2/smallgroups/35b73a5a-f3b2-4584-90bb-6bb437e14466 | same | same |
| `/teambbq` | https://thec3.churchsuite.com/events/pixsgomx | 302 | 307 | https://thec3.churchsuite.com/events/pixsgomx | same | same |
| `/kidsfest` | https://thec3.churchsuite.com/-/calendar/11c78875-d64c-4c01-a5c4-5a7c700819b4 | 301 | 308 | https://thec3.churchsuite.com/-/calendar/11c78875-d64c-4c01-a5c4-5a7c700819b4 | same | same |
| `/onlinebible` | https://bible.com/events/49299352 | 302 | 307 | https://bible.com/events/49299352 | same | same |
| `/lightnightcam` | https://thec3.churchsuite.com/events/tdmifgli | 301 | 308 | https://thec3.churchsuite.com/events/tdmifgli | same | same |
| `/recording` | https://thec3.churchsuite.com/events/gbyjigo0 | 301 | 308 | https://thec3.churchsuite.com/events/gbyjigo0 | same | same |
| `/ascendcamp` | https://brushfire.com/thec3uk/ascend/585411 | 302 | 307 | https://brushfire.com/thec3uk/ascend/585411 | same | same |
| `/lightnightbury` | https://thec3.churchsuite.com/events/6gzhj93y | 301 | 308 | https://thec3.churchsuite.com/events/6gzhj93y | same | same |
| `/baptism` | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20 | 301 | 308 | https://thec3.churchsuite.com/embed/calendar/featured?category=28&num_results=20 | same | same |
| `/training` | https://thec3.churchsuite.com/events/amhhr4f5 | 301 | 308 | https://thec3.churchsuite.com/events/amhhr4f5 | same | same |
| `/cause` | https://thec3.churchsuite.com/events/zp7oe7d2 | 302 | 307 | https://thec3.churchsuite.com/events/zp7oe7d2 | same | same |
| `/christmascast` | https://thec3.churchsuite.com/-/calendar/a6ad8ad4-54b4-4a45-bb1f-7e3d29a53132 | 301 | 308 | https://thec3.churchsuite.com/-/calendar/a6ad8ad4-54b4-4a45-bb1f-7e3d29a53132 | same | same |
| `/coab` | https://thec3.churchsuite.com/-/calendar/65d35796-f7c5-4c38-88a6-28df26aed03a | 302 | 307 | https://thec3.churchsuite.com/-/calendar/65d35796-f7c5-4c38-88a6-28df26aed03a | same | same |
| `/worshiprecording` | https://thec3.churchsuite.com/events/gbyjigo0 | 301 | 308 | https://thec3.churchsuite.com/events/gbyjigo0 | same | same |
| `/fordhamfb` | https://www.facebook.com/groups/thec3fordham | 302 | 307 | https://www.facebook.com/groups/thec3fordham | same | same |
| `/lightnightcol` | https://thec3.churchsuite.com/events/j5cpqhy7 | 301 | 308 | https://thec3.churchsuite.com/events/j5cpqhy7 | same | same |
| `/step2` | https://thec3.churchsuite.com/-/calendar/88c4f896-0205-4502-b90d-fc3e406757a9?preview=1 | 301 | 308 | https://thec3.churchsuite.com/-/calendar/88c4f896-0205-4502-b90d-fc3e406757a9?preview=1 | same | same |
| `/homelessness` | https://thec3.churchsuite.com/events/rbkimwmh | 301 | 308 | https://thec3.churchsuite.com/events/rbkimwmh | same | same |
| `/cookingonabudget` | https://thec3.churchsuite.com/-/calendar/65d35796-f7c5-4c38-88a6-28df26aed03a | 302 | 307 | https://thec3.churchsuite.com/-/calendar/65d35796-f7c5-4c38-88a6-28df26aed03a | same | same |
| `/marathon` | https://www.stewardship.org.uk/pages/CHM2025?fbclid=IwY2xjawIwUpxleHRuA2FlbQIxMAABHcOHkJ[…]ptu3X2fRIdavYcEEWLTw0-eBLNI3JQ_aem_-URsxqPPK4bBy48HoJ_dgw | 302 | 500 |  | **differs** | **differs** |
| `/teamfordham` | https://thec3.churchsuite.com/-/forms/xnh7hyde | 301 | 308 | https://thec3.churchsuite.com/-/forms/xnh7hyde | same | same |
| `/teambury` | https://thec3.churchsuite.com/-/forms/jbi3orhk | 301 | 308 | https://thec3.churchsuite.com/-/forms/jbi3orhk | same | same |
| `/teamwest` | https://thec3.churchsuite.com/-/forms/3x0e0y2t | 301 | 308 | https://thec3.churchsuite.com/-/forms/3x0e0y2t | same | same |
| `/cooking` | https://thec3.churchsuite.com/events/pzgehiog | 302 | 307 | https://thec3.churchsuite.com/events/pzgehiog | same | same |
| `/tour` | https://youtu.be/Y4XU08z6JN0 | 302 | 307 | https://youtu.be/Y4XU08z6JN0 | same | same |
| `/teamcam` | https://thec3.churchsuite.com/-/forms/6bz8hlfi | 302 | 307 | https://thec3.churchsuite.com/-/forms/6bz8hlfi | same | same |
| `/socialmedia` | https://thec3.churchsuite.com/events/igzucy2p | 302 | 307 | https://thec3.churchsuite.com/events/igzucy2p | same | same |
| `/activityday` | https://thec3.churchsuite.com/events/zs5uglxp | 302 | 307 | https://thec3.churchsuite.com/events/zs5uglxp | same | same |
| `/fordhamreview` | https://g.page/r/CdXUoF0ARd-6EB0/review | 302 | 307 | https://g.page/r/CdXUoF0ARd-6EB0/review | same | same |
| `/photography` | https://us02web.zoom.us/j/9909172921?pwd=U0N4aFF2T3NQSlpHS2hBQXd6M3BUdz09 | 302 | 307 | https://us02web.zoom.us/j/9909172921?pwd=U0N4aFF2T3NQSlpHS2hBQXd6M3BUdz09 | same | same |
| `/gifts` | https://assessments.lifethrive.com/SpiritualGifts.php | 302 | 307 | https://assessments.lifethrive.com/SpiritualGifts.php | same | same |
| `/burygroup` | https://thec3.churchsuite.com/embed/v2/smallgroups/bdc24f05-ebda-402f-aabe-26bf0649437c | 302 | 307 | https://thec3.churchsuite.com/embed/v2/smallgroups/bdc24f05-ebda-402f-aabe-26bf0649437c | same | same |
| `/marketlaunch` | https://thec3.churchsuite.com/events/lk8vkaji | 301 | 308 | https://thec3.churchsuite.com/events/lk8vkaji | same | same |
| `/vote` | https://thec3church.typeform.com/to/RWsj7vNq?mc_cid=f0d85b4082&mc_eid=6923d6d819&typeform-source=breathe.thec3.uk&mc_cid=173028fd91&mc_eid=6923d6d819 | 302 | 307 | https://thec3church.typeform.com/to/RWsj7vNq?mc_cid=f0d85b4082&mc_eid=6923d6d819&typeform-source=breathe.thec3.uk&mc_cid=173028fd91&mc_eid=6923d6d819 | same | same |
| `/sundaysetlist` | https://open.spotify.com/playlist/4PHcojwPvGZhnAgz110fv2?si=ecd60aa506cd473a | 302 | 307 | https://open.spotify.com/playlist/4PHcojwPvGZhnAgz110fv2?si=ecd60aa506cd473a | same | same |
| `/westsignup` | https://thec3.churchsuite.com/-/forms/ugaclyfc | 302 | 307 | https://thec3.churchsuite.com/-/forms/ugaclyfc | same | same |
| `/funday` | http://tinyurl.com/c3funday | 302 | 307 | http://tinyurl.com/c3funday | same | same |
| `/eggs` | https://thec3.churchsuite.com/donate/fund/baysvabt | 302 | 307 | https://thec3.churchsuite.com/donate/fund/baysvabt | same | same |
| `/sciencefaith` | https://thec3.churchsuite.com/events/zqagqdbq | 302 | 307 | https://thec3.churchsuite.com/events/zqagqdbq | same | same |
| `/adura` | https://youtu.be/y7E_WQq4v1Q | 302 | 307 | https://youtu.be/y7E_WQq4v1Q | same | same |
| `/auditions` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=68&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=&months=&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | 301 | 308 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=68&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=&months=&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | same | same |
| `/burybuilding` | https://thec3.churchsuite.com/events/7lbh1irh | 301 | 308 | https://thec3.churchsuite.com/events/7lbh1irh | same | same |
| `/impactnight` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=63&e[…]ries=0&show_search=0&show_sites=1&sites=&text_color=666666 | 301 | 500 |  | **differs** | **differs** |
| `/c3atwork` | https://thec3.churchsuite.com/events/xirfkth3?fbclid=IwAR2_bWGCRs3INUPjOzF8wCzRTaAkXwNdMsn2_pZ2RNYU2-aasp2Zc6CLRF8 | 302 | 307 | https://thec3.churchsuite.com/events/xirfkth3?fbclid=IwAR2_bWGCRs3INUPjOzF8wCzRTaAkXwNdMsn2_pZ2RNYU2-aasp2Zc6CLRF8 | same | same |
| `/creativeteamnight` | https://thec3.churchsuite.com/events/iohxixlh | 301 | 308 | https://thec3.churchsuite.com/events/iohxixlh | same | same |
| `/teamchristmas` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=68&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=signup_to_sequence&num_results=&months=6&show_categories=0&show_search=1&show_sites=0&sites=1,4,7&text_color=666666 | 302 | 307 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=68&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=signup_to_sequence&num_results=&months=6&show_categories=0&show_search=1&show_sites=0&sites=1,4,7&text_color=666666 | same | same |
| `/survey` | https://youtu.be/6eqvtt-kiFg | 302 | 307 | https://youtu.be/6eqvtt-kiFg | same | same |
| `/christmas` | https://christmas.thec3.uk | 301 | 308 | https://christmas.thec3.uk/ | same | same (live adds `/`) |
| `/kids-church` | https://thec3.notion.site/Kids-Church-This-Sunday-226d5cedcf0f45a483cb8d276abce64b | 302 | 307 | https://thec3.notion.site/Kids-Church-This-Sunday-226d5cedcf0f45a483cb8d276abce64b | same | same |
| `/kidschurch` | /kids-church/ | 301 | 308 | /kids-church | same | **differs** |
| `/creativebbq` | https://thec3.churchsuite.com/events/sueg3px9 | 302 | 307 | https://thec3.churchsuite.com/events/sueg3px9 | same | same |
| `/lifeguitar` | https://thec3.churchsuite.com/events/iclkzswa | 302 | 307 | https://thec3.churchsuite.com/events/iclkzswa | same | same |
| `/next-steps-calendar` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid-2019&merge=signup_to_sequence&num_results=&months=&show_categories=1&show_search=1&show_sites=1&sites=&text_color=666666 | 301 | 308 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=F5F6F7&categories=&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid-2019&merge=signup_to_sequence&num_results=&months=&show_categories=1&show_search=1&show_sites=1&sites=&text_color=666666 | same | same |
| `/honoursbbq` | https://thec3.churchsuite.com/events/u9sbiab6 | 302 | 307 | https://thec3.churchsuite.com/events/u9sbiab6 | same | same |
| `/music` | https://open.spotify.com/playlist/4S6fEWlrNtbjWu6Bx6qHgh?si=577cc523446f4bb1&pt=e9b902d05b169549e3955fbfb8b454b5 | 302 | 307 | https://open.spotify.com/playlist/4S6fEWlrNtbjWu6Bx6qHgh?si=577cc523446f4bb1&pt=e9b902d05b169549e3955fbfb8b454b5 | same | same |
| `/downloads` | https://we.tl/t-1Y5hKqECwK | 301 | 308 | https://we.tl/t-1Y5hKqECwK | same | same |
| `/funnyhowmarriage` | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-uk-tickets-872798061497 | 301 | 308 | https://www.eventbrite.com/e/michael-jrs-funny-how-marriage-works-tour-cambridge-uk-tickets-872798061497 | same | same |
| `/teameaster` | https://thec3.churchsuite.com/-/calendar/200e53c7-ea91-4631-ade9-4c90db6527ec | 301 | 308 | https://thec3.churchsuite.com/-/calendar/200e53c7-ea91-4631-ade9-4c90db6527ec | same | same |
| `/groupleaders` | https://thec3.churchsuite.com/forms/gc7qfw97 | 301 | 308 | https://thec3.churchsuite.com/forms/gc7qfw97 | same | same |
| `/store` | https://store.thec3.uk | 301 | 308 | https://store.thec3.uk/ | same | same (live adds `/`) |
| `/ascendpod` | https://feeds.transistor.fm/ascend | 301 | 308 | https://feeds.transistor.fm/ascend | same | same |
| `/kintsugihope` | https://https:/https://thec3.churchsuite.com/events/ihiqkzpx | 302 | 307 | https://https:/https://thec3.churchsuite.com/events/ihiqkzpx | same | same |
| `/discord` | https://discord.gg/z6GTSTWsXn | 301 | 308 | https://discord.gg/z6GTSTWsXn | same | same |
| `/cambridge-connect` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 302 | 307 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same | same |
| `/online-connect` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 302 | 307 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same | same |
| `/hamper` | /shop/ | 302 | 307 | /shop | same | **differs** |
| `/griefshare` | https://thec3.churchsuite.com/groups/vibunzhp | 301 | 308 | https://thec3.churchsuite.com/groups/vibunzhp | same | same |
| `/teambreathe` | https://thec3.notion.site/EVERYTHING-YOU-NEED-TO-KNOW-3540955f33b643f6bbbf10cf11bd68c5 | 301 | 308 | https://thec3.notion.site/EVERYTHING-YOU-NEED-TO-KNOW-3540955f33b643f6bbbf10cf11bd68c5 | same | same |
| `/connect` | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | 301 | 308 | https://thec3.churchsuite.com/embed/addressbook/form?site=1 | same | same |
| `/sunday-briefing` | https://thec3.notion.site/Sunday-Update-f52fd5b76b1d41beb18a4f756950a2c0 | 302 | 307 | https://thec3.notion.site/Sunday-Update-f52fd5b76b1d41beb18a4f756950a2c0 | same | same |
| `/c3-marriage-courses` | https://thec3.churchsuite.com/groups/xjkqfivh | 301 | 308 | https://thec3.churchsuite.com/groups/xjkqfivh | same | same |
| `/bury-connect` | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=4 | 301 | 308 | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=4 | same | same |
| `/team-c3-signup` | https://thec3.churchsuite.com/forms/wxu56079 | 301 | 308 | https://thec3.churchsuite.com/forms/wxu56079 | same | same |
| `/colchester-c3-groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=35&text_color=666666 | 302 | 307 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=35&text_color=666666 | same | same |
| `/shop` | https://store.thec3.uk | 301 | 308 | https://store.thec3.uk/ | same | same (live adds `/`) |
| `/buryc3groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=33&text_color=666666 | 302 | 307 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=33&text_color=666666 | same | same |
| `/onlinefb` | https://facebook.com/groups/thec3online | 301 | 308 | https://facebook.com/groups/thec3online | same | same |
| `/ohwhatwonder` | https://thec3uk.brushfire.com/christmas/ | 301 | 308 | https://thec3uk.brushfire.com/christmas/ | same | same |
| `/fbonline` | https://facebook.com/groups/thec3online | 301 | 308 | https://facebook.com/groups/thec3online | same | same |
| `/teamnight` | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=18&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=4&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | 302 | 307 | https://thec3.churchsuite.com/embed/calendar/events?body_bgcolor=ffffff&categories=18&event_bgcolor=FFFFFF&event_border=&featured=NULL&filters_bgcolor=FFFFFF&heading_color=444444&icon_color=BBBBBB&layout=grid&merge=show_all&num_results=4&show_categories=0&show_search=0&show_sites=0&sites=&text_color=666666 | same | same |
| `/allnations` | https://thec3.churchsuite.com/events/jourkgga | 301 | 308 | https://thec3.churchsuite.com/events/jourkgga | same | same |
| `/tithetrial` | https://thec3.churchsuite.co.uk/donate/fund/e2pp8en9 | 301 | 308 | https://thec3.churchsuite.co.uk/donate/fund/e2pp8en9 | same | same |
| `/kidsevents` | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=12&num_results=20&body_bgcolor=ffffff | 301 | 308 | https://thec3.churchsuite.co.uk/embed/calendar/featured?category=12&num_results=20&body_bgcolor=ffffff | same | same |
| `/myrotas` | https://thec3.churchsuite.co.uk/my | 301 | 308 | https://thec3.churchsuite.co.uk/my | same | same |
| `/give` | https://thec3.churchsuite.co.uk/donate/ | 301 | 308 | https://thec3.churchsuite.co.uk/donate/ | same | same |
| `/online-c3-groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=32&text_color=666666 | 302 | 307 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=32&text_color=666666 | same | same |
| `/prayer` | https://prayer.thec3.uk | 301 | 308 | https://prayer.thec3.uk/ | same | same (live adds `/`) |
| `/donate` | https://thec3.churchsuite.co.uk/donate/ | 301 | 308 | https://thec3.churchsuite.co.uk/donate/ | same | same |
| `/yaquestions` | https://docs.google.com/forms/d/e/1FAIpQLSfVNzKcZLStFmdO8OcK6mRr4ZcoBiT5Jfca1xfabx0P1qq3BQ/viewform | 301 | 308 | https://docs.google.com/forms/d/e/1FAIpQLSfVNzKcZLStFmdO8OcK6mRr4ZcoBiT5Jfca1xfabx0P1qq3BQ/viewform | same | same |
| `/calendar` | https://thec3.churchsuite.co.uk/embed/calendar | 301 | 308 | https://thec3.churchsuite.co.uk/embed/calendar | same | same |
| `/mychurchsuite` | https://thec3.churchsuite.co.uk/my | 301 | 308 | https://thec3.churchsuite.co.uk/my | same | same |
| `/cambridge-c3-groups` | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=31&text_color=666666 | 302 | 307 | https://thec3.churchsuite.co.uk/embed/smallgroups/list?preview=true&body_bgcolor=ffffff&filters_bgcolor=FFFFFF&group_bgcolor=FFFFFF&group_border=CCCCCC&heading_color=444444&icon_color=BBBBBB&show_dow=1&show_tags=0&site=&tag=31&text_color=666666 | same | same |
| `/connectform` | https://thec3.churchsuite.co.uk/connect/mydetails/submit | 301 | 308 | https://thec3.churchsuite.co.uk/connect/mydetails/submit | same | same |
| `/brushfire` | https://thec3uk.brushfire.com/ | 301 | 308 | https://thec3uk.brushfire.com/ | same | same |
| `/colchester-connect` | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=7 | 301 | 308 | https://thec3.churchsuite.co.uk/embed/addressbook/form?site=7 | same | same |
| `/chapel` | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=50&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&heading=444444&icon=BBBBBB&num_results=6&show_categories=0&site=&text=666666 | 301 | 308 | https://thec3.churchsuite.co.uk/embed/calendar/featured?preview=true&body_bgcolor=ffffff&categories=50&event_bgcolor=FFFFFF&event_border=CCCCCC&filters_bgcolor=FFFFFF&heading=444444&icon=BBBBBB&num_results=6&show_categories=0&site=&text=666666 | same | same |
| `/slack` | https://join.slack.com/t/thec3uk/shared_invite/zt-8i989kv6-QVF_M7WoZo877ikJNfiPRA | 302 | 307 | https://join.slack.com/t/thec3uk/shared_invite/zt-8i989kv6-QVF_M7WoZo877ikJNfiPRA | same | same |
| `/ascendsummit` | https://thec3uk.brushfire.com/ascend/ | 302 | 307 | https://thec3uk.brushfire.com/ascend/ | same | same |
| `/buryevents` | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | 301 | 308 | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | same | same |
| `/bury-events` | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | 301 | 308 | https://thec3.churchsuite.co.uk/embed/calendar/featured?site=4 | same | same |
