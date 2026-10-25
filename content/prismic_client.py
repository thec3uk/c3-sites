"""A thin client for the Prismic v2 Content API.

It returns raw document JSON; mapping to Page/Slice lives in content/sources/.
"""

import json
import re
from urllib.parse import urlsplit

import httpx

from config.settings.sites import SiteConfig

PAGE_SIZE = 100
# Types whose single document is the site's home page.
HOMEPAGE_TYPES = {"academy_page", "homepage"}
SAFE_SCHEMES = {"", "http", "https", "mailto", "tel"}


class PrismicClient:
    def __init__(self, repository: str, access_token: str = "", http: httpx.Client | None = None):
        self.api_url = f"https://{repository}.cdn.prismic.io/api/v2"
        self.access_token = access_token
        self.http = http or httpx.Client(timeout=30)
        self._ref: str | None = None

    def _get(self, url: str, params: list[tuple[str, str]] | None = None) -> dict:
        params = list(params or [])
        if self.access_token:
            params.append(("access_token", self.access_token))
        response = self.http.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def master_ref(self) -> str:
        if self._ref is None:
            refs = self._get(self.api_url)["refs"]
            self._ref = next(r["ref"] for r in refs if r.get("isMasterRef"))
        return self._ref

    def search(self, *predicates: str) -> list[dict]:
        """Every document matching all predicates, across all pages."""
        results, page = [], 1
        while True:
            params = [("ref", self.master_ref()), ("pageSize", str(PAGE_SIZE)), ("page", str(page))]
            params += [("q", p) for p in predicates]
            body = self._get(f"{self.api_url}/documents/search", params)
            results += body["results"]
            if page >= body["total_pages"]:
                return results
            page += 1


def any_predicate(field: str, values: tuple[str, ...]) -> str:
    return f"[[any({field}, {json.dumps(list(values))})]]"


def fetch_site_documents(client: PrismicClient, site: SiteConfig) -> list[dict]:
    """Documents tagged for the site, plus documents of the site's own types."""
    if not site.prismic_tags and not site.prismic_types:
        raise ValueError(f"Site '{site.name}' has no Prismic tags or types")
    queries = []
    if site.prismic_tags:
        queries.append(any_predicate("document.tags", site.prismic_tags))
    if site.prismic_types:
        queries.append(any_predicate("document.type", site.prismic_types))

    documents: dict[str, dict] = {}
    for query in queries:
        for document in client.search(query):
            documents.setdefault(document["id"], document)
    return list(documents.values())


def resolve_link(link: dict, domain: str = "") -> str:
    """URL for a Prismic link field or a whole document; '' if it goes nowhere.

    Pages shared in one repository use the uid '<domain>' for a site's home page
    and '<domain>_<slug>' for a page served at /<slug>/ on that site.
    """
    if link.get("link_type") in ("Web", "Media"):
        return safe_url(link.get("url", ""))
    if link.get("type") in HOMEPAGE_TYPES:
        return "/"
    uid = link.get("uid")
    if not uid:
        return ""
    if domain and uid == domain:
        return "/"
    if domain and uid.startswith(f"{domain}_"):
        uid = uid.removeprefix(f"{domain}_")
    return f"/{uid}/"


def safe_url(url: str) -> str:
    """The URL if its scheme is allowed in an href, else ''."""
    url = url.strip()
    # Browsers ignore tabs and newlines inside a scheme, e.g. "java\tscript:".
    scheme = urlsplit(re.sub(r"[\x00-\x20]", "", url)).scheme.lower()
    return url if scheme in SAFE_SCHEMES else ""
