"""The current site's content, fetched once per build process."""

from functools import lru_cache

from django.conf import settings

from config.settings.sites import SiteConfig
from content.models import Page
from content.prismic_client import PrismicClient, fetch_site_documents
from content.sources.prismic import to_page


def fetch_documents(site: SiteConfig) -> list[dict]:
    client = PrismicClient(settings.PRISMIC_REPOSITORY, settings.PRISMIC_ACCESS_TOKEN)
    return fetch_site_documents(client, site)


@lru_cache
def site_pages() -> tuple[Page, ...]:
    site = settings.SITE
    pages = (to_page(d) for d in fetch_documents(site) if d["type"] in site.page_types)
    return tuple(sorted((p for p in pages if p.url), key=lambda p: p.url))


def page_by_url(url: str) -> Page | None:
    return next((p for p in site_pages() if p.url == url), None)
