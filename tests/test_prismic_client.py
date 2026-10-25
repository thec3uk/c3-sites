import httpx
import pytest

from config.settings.sites import SiteConfig
from content.prismic_client import PrismicClient, fetch_site_documents, resolve_link


def doc(id, type="page", uid=None, tags=()):
    return {"id": id, "type": type, "uid": uid, "tags": list(tags), "data": {}}


class FakePrismic:
    """Serves the Prismic v2 API from an in-memory list of documents."""

    def __init__(self, documents, page_size=2):
        self.documents = documents
        self.page_size = page_size
        self.searches = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2":
            return httpx.Response(
                200, json={"refs": [{"id": "master", "ref": "REF1", "isMasterRef": True}]}
            )
        params = request.url.params
        assert params["ref"] == "REF1"
        self.searches.append(params.get_list("q"))
        matched = [d for d in self.documents if self._matches(d, params.get_list("q"))]
        page = int(params.get("page", 1))
        start = (page - 1) * self.page_size
        total_pages = max(1, -(-len(matched) // self.page_size))
        return httpx.Response(
            200,
            json={
                "page": page,
                "total_pages": total_pages,
                "results": matched[start : start + self.page_size],
            },
        )

    @staticmethod
    def _matches(document, predicates):
        for predicate in predicates:
            values = predicate.split("[", 3)[-1].rstrip("])").replace('"', "").split(",")
            if "document.type" in predicate and document["type"] not in values:
                return False
            if "document.tags" in predicate and not set(document["tags"]) & set(values):
                return False
        return True


def make_client(fake):
    http = httpx.Client(transport=httpx.MockTransport(fake))
    return PrismicClient("thec3", access_token="tok", http=http)


def test_client_uses_repository_cdn_and_token():
    seen = []

    def handler(request):
        seen.append(request.url)
        return FakePrismic([])(request)

    make_client(handler).search()

    assert seen[0].host == "thec3.cdn.prismic.io"
    assert all(url.params["access_token"] == "tok" for url in seen)


def test_search_follows_every_page():
    fake = FakePrismic([doc(str(i)) for i in range(5)], page_size=2)

    results = make_client(fake).search()

    assert [d["id"] for d in results] == ["0", "1", "2", "3", "4"]


def test_fetch_site_documents_by_type():
    fake = FakePrismic([doc("a", type="academy_page"), doc("b", type="page")])
    site = SiteConfig(name="academy", domain="x", theme="academy", prismic_types=("academy_page",))

    results = fetch_site_documents(make_client(fake), site)

    assert [d["id"] for d in results] == ["a"]


def test_fetch_site_documents_unions_tags_and_types_without_duplicates():
    fake = FakePrismic(
        [
            doc("a", type="academy_page"),
            doc("b", tags=["main"]),
            doc("c", type="academy_page", tags=["main"]),
            doc("d", tags=["myc3"]),
        ]
    )
    site = SiteConfig(
        name="s", domain="x", theme="t", prismic_tags=("main",), prismic_types=("academy_page",)
    )

    results = fetch_site_documents(make_client(fake), site)

    assert sorted(d["id"] for d in results) == ["a", "b", "c"]


def test_fetch_site_documents_requires_a_selector():
    site = SiteConfig(name="s", domain="x", theme="t")

    with pytest.raises(ValueError, match="no Prismic tags or types"):
        fetch_site_documents(make_client(FakePrismic([])), site)


@pytest.mark.parametrize(
    "link, url",
    [
        ({"link_type": "Web", "url": "https://example.com"}, "https://example.com"),
        ({"link_type": "Media", "url": "https://images.prismic.io/a.pdf"}, "https://images.prismic.io/a.pdf"),
        ({"link_type": "Document", "type": "academy_page", "uid": None}, "/"),
        ({"link_type": "Document", "type": "page", "uid": "about"}, "/about/"),
        (doc("x", type="page", uid="visit-us"), "/visit-us/"),
        ({"link_type": "Any"}, ""),
    ],
)
def test_resolve_link(link, url):
    assert resolve_link(link) == url
