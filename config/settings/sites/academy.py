from . import SiteConfig

SITE = SiteConfig(
    name="academy",
    domain="thec3.academy",
    theme="academy",
    prismic_types=("academy_page", "site_config"),
    page_types=("academy_page",),
    umami_website_id="c9ca3f93-1107-49cc-b2e4-ddb0dbae79d1",
    umami_src="https://analytics.thec3.academy/script.js",
)
