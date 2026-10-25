import json
from pathlib import Path

import pytest

from config.settings.sites import SiteConfig
from pages import content
from pages.views import page_paths

FIXTURES = Path(__file__).parent / "fixtures"
SITE = SiteConfig(
    name="test",
    domain="testserver",
    theme="test",
    prismic_types=("academy_page", "page", "site_config"),
    page_types=("academy_page", "page"),
)


@pytest.fixture
def site(settings, monkeypatch, tmp_path):
    docs = [
        json.loads((FIXTURES / "academy_page.json").read_text()),
        json.loads((FIXTURES / "page_with_slices.json").read_text()),
        {"id": "cfg", "type": "site_config", "uid": None, "tags": [], "data": {"title": "The C3 Church"}},
    ]
    for d in docs[1]["data"]["body"]:
        d["slice_type"] = "text"  # one shared template keeps the test small
    monkeypatch.setattr(content, "fetch_documents", lambda site: docs)
    content.site_documents.cache_clear()

    templates = tmp_path / "templates"
    (templates / "pages").mkdir(parents=True)
    (templates / "slices").mkdir()
    (templates / "pages" / "academy_page.html").write_text(
        "home:{{ page.title }}|{{ site_config.fields.title }}"
    )
    (templates / "pages" / "page.html").write_text(
        "{% load slices %}page:{{ page.uid }}|{% render_slices page %}"
    )
    (templates / "slices" / "text.html").write_text("[s]")
    settings.SITE = SITE
    settings.ALLOWED_HOSTS = ["testserver"]
    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [templates],
            "APP_DIRS": True,
            "OPTIONS": {"context_processors": ["pages.context_processors.site"]},
        }
    ]
    yield
    content.site_documents.cache_clear()


def test_only_page_types_become_pages(site):
    assert [p.url for p in content.site_pages()] == ["/", "/room-hire/"]


def test_page_paths_list_every_page_except_home(site):
    assert list(page_paths()) == [{"path": "room-hire"}]


def test_home_renders_its_type_template(site, client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.content.decode() == "home:The C3 Academy|The C3 Church"


def test_page_renders_with_slices(site, client):
    response = client.get("/room-hire/")

    assert response.content.decode().startswith("page:room-hire|[s][s]")


def test_unknown_path_is_404(site, client):
    assert client.get("/nope/").status_code == 404


def test_documents_are_fetched_once_per_build(site, monkeypatch):
    calls = []
    monkeypatch.setattr(content, "fetch_documents", lambda site: calls.append(1) or [])
    content.site_documents.cache_clear()

    content.site_pages()
    content.site_pages()

    assert len(calls) == 1
