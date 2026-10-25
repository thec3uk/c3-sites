# Phase 3 M3: contact form and newsletter

## Goal
The contact form submits to Netlify Forms and the newsletter cards subscribe to Mailchimp, both with the inline thank-you behaviour of the live site.

## Read first
- Gatsby: `src/slices/header/components/contactForm.tsx`, `contact/categorySelect.tsx`, `src/components/card/newsletter.tsx`, `newsletterWithLocations.tsx`, the mailchimp options in `gatsby-config.js`
- c3-sites: `themes/main/templates/slices/` from M2

## Facts
- Contact form config is the `contact_form` document (tag `domain:thec3.uk`): labels, `form_name` "Contact Us", `category` list of `{category_name, email_recipient}`, `thank_you_message` (rich text). Gatsby posts url-encoded to `/` with `form-name`, the fields, `category_name` and `email_recipient`, and a honeypot `bot-field`.
- Netlify only accepts a form it found in the deployed static HTML: the `<form name="..." data-netlify="true" data-netlify-honeypot="bot-field">` and a hidden `form-name` input must be in the built page.
- Newsletter production list: `https://thec3.us19.list-manage.com/subscribe/post?u=baac982817e7fb161022a1253&id=d62f87b12a`. The location card sends `FNAME`, `LOCATION` (quoted, comma-joined list), `SIGNUPURL`, `SOURCE: "website signup"`. Read the locations list from `newsletterWithLocations.tsx`.

## Tasks
1. Contact form template: plain HTML that works without JS (posts and Netlify shows its default success page), enhanced with Alpine to post via `fetch` and swap in `thank_you_message`. Category select fills `category_name` and `email_recipient`. Tests on the rendered HTML: Netlify attributes, hidden `form-name`, honeypot, categories.
2. Newsletter card (`card/newsletterLocationSlice`, the only newsletter variation in use; Gatsby's `newsletterSlice` variation is unused and not ported): Alpine JSONP to the Mailchimp `post-json` endpoint (as gatsby-plugin-mailchimp does), with success and error messages; without JS, a plain POST to the `post` endpoint. Use the dev list id `7443c2e349` when `DJANGO_DEBUG=1`.
3. No secrets are involved; nothing goes in `.env`.

## Exit checks
- `uv run pytest` green; `just build main` succeeds.
- The built contact page's form passes Netlify's detection rules (check against Netlify's Forms docs and note the URL in the commit).
- Don't submit real forms. Show the Alpine flows work with the network mocked in Playwright; screenshots in `docs/plans/phase-3/evidence/m3/`.

## Out of scope
Configuring Netlify form notifications or routing by `email_recipient` (Andy, in the Netlify UI, at cutover).
