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
def site_documents() -> tuple[Page, ...]:
    """Every document selected for the site, pages and data alike."""
    return tuple(to_page(d) for d in fetch_documents(settings.SITE))


def site_pages() -> tuple[Page, ...]:
    pages = (p for p in site_documents() if p.type in settings.SITE.page_types and p.url)
    return tuple(sorted(pages, key=lambda p: p.url))


def site_document(type: str) -> Page | None:
    """The site's single document of a data type, such as site_config."""
    return next((p for p in site_documents() if p.type == type), None)


def page_by_url(url: str) -> Page | None:
    return next((p for p in site_pages() if p.url == url), None)
