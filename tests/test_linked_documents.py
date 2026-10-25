"""Document links carry the target's id and type, so templates can reach its content."""

import json
from pathlib import Path

import pytest
from django.template import Context, Template

from content.models import Link
from content.sources.prismic import convert, to_page

FIXTURES = Path(__file__).parent / "fixtures"
LINKED = json.loads((FIXTURES / "linked_documents.json").read_text())
SAMPLES = json.loads((FIXTURES / "slice_samples.json").read_text())
QUICK_LINKS_ID = "Yk2CThAAACMAWbs2"
SOCIAL_LINKS_ID = "Yk2BixAAACMAWbey"


def sample_link(slice_type):
    return next(s for s in SAMPLES if s["slice_type"] == slice_type)["primary"]["link"]


def render(template, **context):
    return Template("{% load documents %}" + template).render(Context(context))


def test_document_link_without_uid_carries_id_and_type():
    link = convert(sample_link("quick_links_block"), "thec3.uk")

    assert isinstance(link, Link)
    assert link == ""
    assert (link.id, link.type) == (QUICK_LINKS_ID, "quick-links")


def test_document_link_with_uid_still_prints_its_url():
    raw = {"link_type": "Document", "id": "YpdCQREAACAAd7-O", "type": "page", "uid": "reaching"}

    link = convert(raw, "thec3.uk")

    assert (link, link.id, link.type) == ("/reaching/", "YpdCQREAACAAd7-O", "page")
    assert render("{{ link }}", link=link) == "/reaching/"


def test_web_and_empty_links_stay_plain_strings():
    assert type(convert({"link_type": "Web", "url": "https://thec3.uk/"})) is str
    assert type(convert({"link_type": "Any"})) is str


@pytest.fixture
def linked(documents):
    documents += LINKED
    return documents


def test_linked_document_is_the_converted_page(linked):
    link = convert(sample_link("quick_links_block"), "thec3.uk")

    html = render(
        "{% with doc=link|linked_document %}{{ doc.title }}: "
        "{% for s in doc.slices %}{{ s.primary.title.text }}={{ s.primary.url }} {% endfor %}{% endwith %}",
        link=link,
    )

    assert html.startswith("quick links: Connect=/shaping/ Give=/giving/ Groups=/c3-groups/")


def test_linked_social_links_document_has_its_urls(linked):
    link = convert(sample_link("social_links_block"), "thec3.uk")

    html = render(
        "{% with doc=link|linked_document %}{{ doc.fields.instagramUrl }} {{ doc.fields.title }}{% endwith %}",
        link=link,
    )

    assert html == "https://www.instagram.com/thec3_church/ None"


@pytest.mark.parametrize(
    "value",
    ["/somewhere/", None, Link("", id="missing", type="quick-links")],
    ids=["plain url", "none", "unknown id"],
)
def test_linked_document_is_none_without_a_known_document(linked, value):
    assert render("{{ value|linked_document }}", value=value) == "None"


def test_page_url_of_a_document_is_not_a_link():
    page = to_page({"id": "p", "type": "page", "uid": "thec3.uk_about", "data": {}}, "thec3.uk")

    assert type(page.url) is str
