"""Main-theme slice templates, ported from new_to_church's components."""

import copy
import json
import re
from pathlib import Path

import pytest
from django.template import Context, Template
from django.utils.html import escape

from content.models import Page, RichText
from content.sources.prismic import _slice

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLES = json.loads((FIXTURES / "slice_samples.json").read_text())
LINKED = json.loads((FIXTURES / "linked_documents.json").read_text())
PHOTO = "https://images.prismic.io/thec3/photo.jpg?auto=format,compress"
# Fields live (Gatsby) never shows, kept hidden for parity: see evidence/m2/NOTES.md.
NOT_SHOWN = {("text", "title"), ("faq_section", "title"), ("card", "ctaTitle")}


@pytest.fixture(autouse=True)
def linked(main):
    main += LINKED


def raw(slice_type, variation=None, **primary):
    """A copy of the real sample, with primary fields overridden."""
    sample = next(
        s for s in SAMPLES if s["slice_type"] == slice_type and (variation is None or s.get("variation") == variation)
    )
    sample = copy.deepcopy(sample)
    sample["primary"].update(primary)
    return sample


def render(*raws):
    page = Page(id="p", type="page", uid="x", url="/x/", slices=tuple(_slice(r, "thec3.uk") for r in raws))
    return Template("{% load slices %}{% render_slices page %}").render(Context({"page": page}))


def inner(html):
    return re.sub(r"</?section[^>]*>", "", html).strip()


def photo(alt=None, width=4000, height=3000):
    return {"dimensions": {"width": width, "height": height}, "alt": alt, "url": PHOTO}


def text_of(value):
    return value.text if isinstance(value, RichText) else value


# header/default-slice renders nothing: test_default_header_renders_nothing.
SHOWN = [s for s in SAMPLES if (s["slice_type"], s.get("variation")) != ("header", "default-slice")]


@pytest.mark.parametrize("sample", SHOWN, ids=lambda s: f"{s['slice_type']}/{s.get('variation')}")
def test_every_real_variation_renders_its_content(sample):
    slice = _slice(sample, "thec3.uk")

    html = render(sample)
    text = re.sub(r"<[^>]+>", "", html)

    assert inner(html)
    for name in ("title", "subtitle", "linkTitle", "ctaTitle", "question", "content", "leadParagraph"):
        if (slice.type, name) in NOT_SHOWN:
            continue
        for source in [slice.primary, *slice.items]:
            value = text_of(source.get(name))
            if isinstance(value, str) and value.strip():
                snippet = value.strip().splitlines()[0][:20]
                assert snippet in text or escape(snippet) in text, name


def test_default_header_renders_nothing():
    assert inner(render(raw("header", "default-slice"))) == ""


def test_quick_links_block_lists_its_documents_links_beside_main():
    html = render(raw("quick_links_block"))

    assert '<aside class="my-3 md:col-start-10 md:col-span-2 space-y-3">' in html
    assert ">quick links</h2>" in html
    assert re.findall(r'href="([^"]*)"[^>]*><h1>([^<]*)</h1>', html)[:3] == [
        ("/shaping/", "Connect"),
        ("/giving/", "Give"),
        ("/c3-groups/", "Groups"),
    ]


def test_social_links_block_links_each_network_with_socials_as_default_title():
    html = render(raw("social_links_block"))

    assert ">Socials</h3>" in html
    hrefs = re.findall(r'<a href="([^"]*)"', html)
    assert hrefs == [
        "https://www.facebook.com/thec3uk",
        "https://www.instagram.com/thec3_church/",
        "https://www.youtube.com/channel/UCHXr4-EV0nF5rhlhJmDhIWQ",
    ]
    assert "<title>Facebook</title>" in html


def test_social_links_block_skips_empty_networks():
    ya = {"link_type": "Document", "id": "Y2LewhAAACIAH4el", "type": "social-links"}

    html = render(raw("social_links_block", link=ya))

    assert ">YA</h3>" in html
    assert "Facebook" not in html
    assert "https://www.instagram.com/thec3_ya/" in html


def test_linked_block_without_its_document_renders_nothing():
    missing = {"link_type": "Document", "id": "gone", "type": "quick-links"}

    assert inner(render(raw("quick_links_block", link=missing))) == ""


def test_text_slice_shows_content_in_main_column_as_prose():
    html = render(raw("text"))

    assert 'class="my-6 lg:col-span-8 lg:col-start-2 md:my-4 lg:my-3"' in html
    assert "prose" in html and "advertised roles" in html
    assert "How to apply for roles" not in html


def test_faq_items_are_disclosures():
    html = render(raw("faq_section"))

    assert html.count("<details") == 5
    assert "<summary" in html and "What is a Kids Life Group?" in html
    assert "kids@thec3.uk" in html


def test_contained_hero_with_image_and_links():
    html = render(raw("header", "heroWithImage", isFullBleed=False, backgroundImage=photo("Worship night")))

    assert "md:col-span-6 lg:col-span-4" in html
    assert re.search(rf'<img src="{re.escape(PHOTO.replace(",", "%2C"))}&amp;w=1920" srcset="[^"]* 1366w', html)
    assert 'alt="Worship night"' in html
    assert ">The C3 Church, Cambridge West</h1>" in html
    assert ">We can&#x27;t wait to meet you soon!</h2>" in html


def test_full_bleed_hero_spans_the_page():
    html = render(raw("header", "heroWithImage", isFullBleed=True))

    assert 'class="lg:relative grid grid-cols-12 col-span-full' in html
    assert "md:col-span-6 lg:col-span-4" not in html


def test_text_only_hero_aligns_centre_and_shows_its_background_cell():
    html = render(raw("header", "textOnlyHero", alignment="center"))

    assert "text-center lg:col-start-5" in html
    assert "hidden lg:flex" not in html


def test_contact_hero_renders_the_contact_form_document():
    html = render(raw("header", "heroWithCustomComponent"))

    assert ">get in touch</h1>" in html
    assert '<form name="Contact Us"' in html
    for label in ("Full Name", "Email", "Category", "Your Subject", "Your Message"):
        assert f">{label}</label>" in html
    assert "<option>Safeguarding</option>" in html
    assert ">Send</button>" in html


def test_newsletter_card_renders_its_sign_up_form():
    html = render(raw("card", "newsletterLocationSlice"))

    assert "Subscribe" in html and "Find out more about what" in html
    assert 'type="email"' in html
    assert html.count('type="checkbox"') == 4 and "Bury St Edmunds" in html


def test_card_links_its_image_and_button():
    link = {"link_type": "Web", "url": "https://thec3.uk/kids/"}

    html = render(raw("card", "default", colour="white", image=photo("Kids"), ctaTitle="Find out", ctaLink=link))

    assert "bg-white text-black" in html
    assert '<a href="https://thec3.uk/kids/" class="w-full px-6' in html
    assert re.search(r'<a href="https://thec3.uk/kids/"><img [^>]*alt="Kids"', html)


def test_card_without_colour_is_unfilled_but_shadowed():
    html = render(raw("card", "default"))

    assert "shadow-md" in html and "bg-white" not in html


def test_image_card_links_with_a_gradient_for_its_colour():
    html = render(raw("card", "imageCard"))

    assert '<a href="https://c3impact.uk/#projects" class="group">' in html
    assert "from-[#343434aa]" in html and "text-white" in html


def test_full_height_media_fills_the_screen():
    html = render(raw("media", "default", fullheight=True))

    assert "col-span-full" in html and "lg:h-screen-90" in html and 'sizes="100vw"' in html


def test_full_width_button():
    html = render(raw("button", alignment="full"))

    assert "max-w-3xl mx-auto flex flex-col" in html and "justify-center" in html
    assert "px-2.5 py-1.5 text-xs rounded-sm" in html
    assert ">Light Night!</a>" in html


def test_card_text_is_not_marked_safe_twice():
    html = render(raw("card", "default", subtitle="<b>bold</b>"))

    assert "&lt;b&gt;bold&lt;/b&gt;" in html


def test_faq_dividers_sit_above_each_question_as_in_tailwind_3():
    # v4's divide-y borders the bottom of each item; Gatsby's v3 bordered the top.
    html = render(raw("faq_section"))

    assert "divide-y" not in html
    assert '<div class="mt-6 space-y-6 border-t-2 border-gray-200">' in html
    assert html.count('<details class="pt-6 group border-t border-gray-900 first:border-t-0">') == 5


def test_image_card_without_image_is_an_empty_cell_as_live():
    html = inner(render(raw("card", "imageCard", image={})))

    assert html == '<div class="my-6 lg:col-span-8 lg:col-start-2 md:my-4 lg:my-3"></div>'


def test_newsletter_inputs_keep_their_gap_below_inline_labels():
    # v4's space-y-1 puts margin-bottom on the inline label, which does nothing; v3 put margin-top on the input.
    html = render(raw("card", "newsletterLocationSlice"))

    assert "space-y-1" not in html
    assert html.count('class="w-full p-3 mt-1 text-2xl') == 2
