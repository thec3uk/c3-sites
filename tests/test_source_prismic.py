import json
from pathlib import Path

import pytest

from content.models import Image, Page, RichText, Slice
from content.sources.prismic import convert, to_page

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def academy():
    return to_page(load("academy_page.json"))


def test_page_identity(academy):
    assert isinstance(academy, Page)
    assert (academy.id, academy.type, academy.uid) == ("XqfyaBAAACMA9P5V", "academy_page", "academy")
    assert academy.url == "/"
    assert academy.tags == ("domain:thec3.academy",)


def test_page_title_comes_from_page_title_field(academy):
    assert academy.title == "The C3 Academy"


def test_image_field_becomes_image(academy):
    hero = academy.fields["hero_image"]

    assert hero == Image(
        url="https://images.prismic.io/thec3/XQgK4uOpKcS4eFH9_001a.png?auto=format,compress",
        alt="",
        width=5760,
        height=3840,
    )


def test_rich_text_field_becomes_rich_text(academy):
    lead = academy.fields["lead_paragraph"]

    assert isinstance(lead, RichText)
    assert lead.text.startswith("Equipping and developing you")


def test_group_links_become_urls(academy):
    ctas = academy.fields["ctas"]

    assert [c["text"] for c in ctas] == ["Apply", "Prospectus", "Open Day"]
    assert ctas[2]["link"] == "https://thec3.churchsuite.com/events/tvxvflie"


def test_empty_slice_zone(academy):
    assert academy.slices == ()
    assert "body" not in academy.fields


def test_slices_map_type_primary_and_items():
    page = to_page(load("page_with_slices.json"))

    assert page.url == "/room-hire/"
    assert [s.type for s in page.slices][:3] == ["header", "text", "quick_links_block"]
    header = page.slices[0]
    assert isinstance(header, Slice)
    assert header.variation == "heroWithImage"
    assert isinstance(header.primary["title"], (RichText, str))


def test_empty_image_and_empty_link_become_none_and_blank():
    assert convert({}) is None
    assert convert({"link_type": "Any"}) == ""


@pytest.mark.parametrize(
    "blocks, html",
    [
        ([{"type": "paragraph", "text": "Hi", "spans": []}], "<p>Hi</p>"),
        ([{"type": "heading2", "text": "Title", "spans": []}], "<h2>Title</h2>"),
        (
            [{"type": "paragraph", "text": "a <b> & c", "spans": []}],
            "<p>a &lt;b&gt; &amp; c</p>",
        ),
        (
            [
                {"type": "list-item", "text": "one", "spans": []},
                {"type": "list-item", "text": "two", "spans": []},
                {"type": "paragraph", "text": "after", "spans": []},
            ],
            "<ul><li>one</li><li>two</li></ul><p>after</p>",
        ),
        (
            [{"type": "o-list-item", "text": "first", "spans": []}],
            "<ol><li>first</li></ol>",
        ),
        (
            [{"type": "paragraph", "text": "bold and em", "spans": [
                {"start": 0, "end": 4, "type": "strong"},
                {"start": 9, "end": 11, "type": "em"},
            ]}],
            "<p><strong>bold</strong> and <em>em</em></p>",
        ),
        (
            [{"type": "paragraph", "text": "see here", "spans": [
                {"start": 4, "end": 8, "type": "hyperlink", "data": {"url": "/visit/"}},
            ]}],
            '<p>see <a href="/visit/">here</a></p>',
        ),
        (
            [{"type": "paragraph", "text": "nested", "spans": [
                {"start": 0, "end": 6, "type": "strong"},
                {"start": 0, "end": 3, "type": "em"},
            ]}],
            "<p><strong><em>nes</em>ted</strong></p>",
        ),
        (
            [{"type": "paragraph", "text": "😀 bold", "spans": [
                {"start": 3, "end": 7, "type": "strong"},
            ]}],
            "<p>😀 <strong>bold</strong></p>",
        ),
        (
            [{"type": "image", "url": "https://i/x.png", "alt": "A cat", "spans": [], "text": ""}],
            '<p class="block-img"><img src="https://i/x.png" alt="A cat"></p>',
        ),
        (
            [{"type": "paragraph", "text": "line\nbreak", "spans": []}],
            "<p>line<br>break</p>",
        ),
    ],
)
def test_rich_text_html(blocks, html):
    assert RichText(tuple(blocks)).html == html


def test_rich_text_hyperlinks_are_resolved_by_the_source():
    blocks = [{"type": "paragraph", "text": "go", "spans": [
        {"start": 0, "end": 2, "type": "hyperlink",
         "data": {"link_type": "Document", "type": "page", "uid": "visit"}},
    ]}]

    assert convert(blocks).html == '<p><a href="/visit/">go</a></p>'


def test_rich_text_renders_unescaped_in_templates():
    from django.template import Context, Template

    rich = RichText(({"type": "paragraph", "text": "Hi", "spans": []},))

    assert Template("{{ r }}").render(Context({"r": rich})) == "<p>Hi</p>"


def test_embed_blocks_are_not_rendered():
    blocks = ({"type": "embed", "oembed": {"html": "<script>x</script>"}, "text": "", "spans": []},)

    assert RichText(blocks).html == ""


def test_to_page_resolves_urls_and_links_for_the_site_domain():
    document = {
        "id": "h", "type": "page", "uid": "thec3.uk", "tags": [],
        "data": {
            "cta": {"link_type": "Document", "type": "page", "uid": "thec3.uk_about"},
            "body": [{"slice_type": "text", "primary": {"text": [
                {"type": "paragraph", "text": "about", "spans": [
                    {"start": 0, "end": 5, "type": "hyperlink",
                     "data": {"link_type": "Document", "type": "page", "uid": "thec3.uk_about"}},
                ]},
            ]}, "items": []}],
        },
    }

    page = to_page(document, domain="thec3.uk")

    assert page.url == "/"
    assert page.fields["cta"] == "/about/"
    assert 'href="/about/"' in page.slices[0].primary["text"].html


def test_site_documents_use_the_site_domain(settings, monkeypatch):
    from config.settings.sites import SiteConfig
    from pages import content

    settings.SITE = SiteConfig(name="main", domain="thec3.uk", theme="main", prismic_tags=("domain:thec3.uk",))
    monkeypatch.setattr(content, "fetch_documents", lambda site: [
        {"id": "a", "type": "page", "uid": "thec3.uk_about", "tags": [], "data": {}},
    ])
    content.site_documents.cache_clear()

    assert [p.url for p in content.site_pages()] == ["/about/"]
    content.site_documents.cache_clear()
