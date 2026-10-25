"""myc3 slice templates, ported from the Next site's slices/*/index.js."""

import re

import pytest
from django.template import Context, Template

from django.utils.html import escape

from content.models import Image, Page
from content.sources.prismic import _slice
from pages.templatetags.images import imgix

LOGO = "https://images.prismic.io/thec3/logo.png?auto=format,compress"
PHOTO = "https://images.prismic.io/thec3/photo.jpg?auto=format,compress"
BUTTON = (
    "transition duration-200 text-lg mx-4 lg:mx-20 py-3 px-2 border shadow hover:translate-y-px"
    " hover:shadow-none col-start-1 col-span-1 md:col-span-1 md:col-start-2 text-center"
    " bg-white text-gray-900 hover:text-red-500 active:text-red-400"
)
FOOTER_LINK = "text-gray-900 hover:text-gray-700 active:text-gray-800 hover:underline whitespace-nowrap"


@pytest.fixture(autouse=True)
def site(myc3):
    return myc3


def raw(slice_type, variation="default-slice", primary=None, items=None):
    return {"slice_type": slice_type, "variation": variation, "primary": primary or {}, "items": items or []}


def render(*raws):
    page = Page(id="p", type="page", uid="x", url="/x/", slices=tuple(_slice(r, "myc3.life", "next") for r in raws))
    html = Template("{% load slices %}{% render_slices page %}").render(Context({"page": page}))
    # Drop render_slices' own wrapper; the slice's markup is what Next rendered.
    return re.sub(r'^<section class="slice"[^>]*>|</section>$', "", html).strip()


def image(url, width=600, height=400, alt=None):
    return {"dimensions": {"width": width, "height": height}, "alt": alt, "url": url}


def rich(text, type="paragraph"):
    return [{"type": type, "text": text, "spans": []}]


def doc_link(uid, type="page"):
    return {"link_type": "Document", "id": uid, "type": type, "uid": uid}


@pytest.mark.parametrize("variation", ["default-slice", "heroWithImage", "textOnlyHero"])
def test_header_renders_the_same_markup_for_every_variation(variation):
    primary = {"title": "growth path", "logo": image(LOGO, 2108, 2108, alt="The C3 Church Logo")}

    html = render(raw("header", variation, primary))

    assert html == (
        '<section class="flex justify-center pt-8 pb-8 md:pt-20">'
        '<a href="/" class="flex flex-col justify-center items-center md:space-y-2 max-h-24 md:px-20 md:max-h-48 text-center">'
        f'<img src="{escape(imgix(Image(LOGO), 384))}" alt="The C3 Church Logo" width="2108" height="2108"'
        ' loading="lazy" decoding="async" class="filter object-contain md:max-w-32 max-w-20">'
        '<h1 class="text-4xl md:text-6xl font-title font-bold text-gray-900">growth path</h1>'
        "</a></section>"
    )


def test_header_without_a_logo_still_shows_its_title():
    # thec3.uk's hero variations have no logo; Next crashed on them, so live serves 500.
    html = render(raw("header", "textOnlyHero", {"title": "Trustees", "leadParagraph": rich("ignored")}))

    assert "<img" not in html
    assert ">Trustees</h1>" in html
    assert "ignored" not in html


def test_button_links_its_title_with_the_next_classes():
    primary = {"linkTitle": "Get exploring!", "linkUrl": {"link_type": "Web", "url": "https://thec3.churchsuite.com/x"}}

    html = render(raw("button", primary=primary))

    assert html == (
        '<section class="grid grid-cols-1 md:grid-cols-3 justify-center items-center my-6">'
        f'<a href="https://thec3.churchsuite.com/x" class="{BUTTON}">Get exploring!</a></section>'
    )


def test_button_to_a_document_uses_the_myc3_url():
    html = render(raw("button", primary={"linkTitle": "Steps", "linkUrl": doc_link("next-steps")}))

    assert 'href="/next-steps/"' in html


def test_text_shows_title_then_content_in_prose():
    primary = {"title": rich("Step 1: Explore", "heading2"), "title_alignment": "left", "content": rich("Explore.")}

    html = render(raw("text", None, primary))

    # Next read slice.title_alignment, not primary's, so no alignment class ever applied.
    assert html == (
        '<section class="grid items-center justify-center grid-cols-1 my-6 md:grid-cols-3">'
        '<div class="mx-auto md:col-span-1 md:col-start-2 prose px-4">'
        '<div class=" text-lg"><h2>Step 1: Explore</h2></div><p>Explore.</p></div></section>'
    )


def test_text_without_a_title_keeps_the_empty_title_div():
    html = render(raw("text", None, {"content": rich("Just this.")}))

    assert '<div class=" text-lg"></div><p>Just this.</p>' in html


def test_card_is_the_slice_machine_template_with_its_scoped_styles():
    html = render(raw("card", "default", {"title": "Trustees", "content": rich("ignored"), "subtitle": "x"}))

    assert html == (
        '<section class="max-w-[600px] my-[4em] mx-auto text-center">'
        '<span class="title text-[#8592e0]">Trustees</span>'
        "<p>start by editing this slice from inside Slice Machine!</p></section>"
    )


def test_card_without_title_or_description_shows_the_template_placeholders():
    html = render(raw("card", "default", {"title": None, "subtitle": "C3 Trustee Recruitment"}))

    assert '<span class="title text-[#8592e0]"><h2>Template slice, update me!</h2></span>' in html


def test_link_renders_like_card():
    html = render(raw("link", "default", {"title": rich("Go", "heading2"), "description": rich("There.")}))

    assert html == (
        '<section class="max-w-[600px] my-[4em] mx-auto text-center">'
        '<span class="title text-[#8592e0]"><h2>Go</h2></span><p>There.</p></section>'
    )


@pytest.mark.parametrize(
    "fullheight, padding, classes",
    [
        (True, "py-32", "object-cover object-center w-screen h-full aspect-video lg:h-screen-90"),
        (False, "py-16", "object-cover object-center w-screen h-auto aspect-auto"),
    ],
)
def test_media_default_is_full_bleed(fullheight, padding, classes):
    html = render(raw("media", "default", {"image": image(PHOTO, 2400, 1600), "fullheight": fullheight}))

    assert html.startswith(f'<div class="flex justify-center w-screen mx-auto grow max-w-screen {padding}"><img ')
    assert f'class="{classes}"' in html
    assert 'width="2400" height="1600"' in html
    assert 'sizes="100vw"' in html


def test_media_block_image_is_a_small_centred_image():
    html = render(raw("media", "blockImage", {"image": image(PHOTO, 512, 314)}))

    assert html == (
        '<section class="grid items-center justify-center grid-cols-2 my-6 md:grid-cols-3 px-4">'
        f'<img src="{escape(imgix(Image(PHOTO), 256))}" alt="" width="512" height="314"'
        ' loading="lazy" decoding="async" class="md:col-start-2 max-h-32 max-w-32 -mb-12 mt-16"></section>'
    )


@pytest.mark.parametrize("variation", ["default", "blockImage"])
def test_media_without_an_image_renders_nothing(variation):
    assert render(raw("media", variation, {"image": {}})) == ""


def test_media_video_renders_nothing():
    assert render(raw("media", "video", {"image": image(PHOTO)})) == ""


def test_footer_has_social_icons_and_unspaced_links():
    items = [
        {"linkTitle": "Privacy", "linkUrl": {"link_type": "Web", "url": "https://thec3.uk/privacy"}},
        {"linkTitle": "Groups", "linkUrl": doc_link("groups")},
    ]

    html = render(raw("footer", items=items))

    assert html.startswith(
        '<section class="cursor-pointer w-full flex justify-between md:justify-around items-center'
        ' px-4 md:px-8 text-sm pt-8 md:pt-20 space-x-16 md:space-x-48">'
    )
    assert 'href="https://www.facebook.com/thec3uk"' in html
    assert 'data-icon="facebook-f" class="svg-inline--fa fa-facebook-f fa-fw h-5"' in html
    assert 'd="M80 299.3V512H196V299.3h86.5l18-97.8H196V166.9c0-51.7 20.3-71.5 72.7-71.5c16.3 0 29.4 .4 37 1.2V7.9C291.4 4' in html
    assert 'href="https://www.instagram.com/thec3_church"' in html
    assert 'data-icon="instagram" class="svg-inline--fa fa-instagram fa-fw h-8"' in html
    # No whitespace between the inline links, as JSX rendered them.
    assert (
        f'<div class="space-x-2"><a class="{FOOTER_LINK}" href="https://thec3.uk/privacy">Privacy</a>'
        f'<a class="{FOOTER_LINK}" href="/groups/">Groups</a></div></section>'
    ) in html


FORM_PRIMARY = {
    "form_name": "story",
    "name_label": "Your name",
    "email_label": "Your email",
    "category_label": "Topic",
    "subject_label": "About",
    "message_label": "Tell us more",
    "submit_button_label": "SEND",
    "consent_label": rich("I agree to the <privacy> policy"),
    "thank_you_message": rich("Thanks, friend"),
}
CATEGORIES = [{"category_name": "Story"}, {"category_name": "Prayer"}]


def contact_form(primary=None, items=CATEGORIES):
    return render(raw("contact_form", primary=FORM_PRIMARY if primary is None else primary, items=items))


def test_contact_form_passes_netlify_detection_rules():
    html = contact_form()

    form = re.search(r"<form[^>]*>", html).group(0)
    assert 'name="story"' in form and 'method="post"' in form
    assert 'data-netlify="true"' in form and 'data-netlify-honeypot="bot-field"' in form
    assert '<input type="hidden" name="form-name" value="story">' in html
    assert 'name="bot-field"' in html
    # Netlify only collects fields present in the static HTML.
    for field in ("name", "email", "category", "subject", "message", "consent"):
        assert f'name="{field}"' in html


def test_contact_form_name_defaults_to_contact():
    html = contact_form({"submit_button_label": "SEND"}, items=[])

    assert 'name="contact"' in re.search(r"<form[^>]*>", html).group(0)
    assert '<input type="hidden" name="form-name" value="contact">' in html


def test_contact_form_labels_come_from_the_slice_and_default_to_next_text():
    html = contact_form()

    for label in ("Your name", "Your email", "Topic", "About", "Tell us more", "SEND"):
        assert label in html
    bare = contact_form({}, items=CATEGORIES)
    for label in (">Name<", ">Email<", ">Category<", ">Subject<", ">Message<", ">Send<"):
        assert label in bare


def test_contact_form_category_select_lists_the_items_and_is_required():
    html = contact_form()

    assert '<option value="">-- Select --</option>' in html
    assert '<option value="Story">Story</option>' in html
    assert '<option value="Prayer">Prayer</option>' in html
    assert re.search(r"<select[^>]*required", html)


def test_contact_form_without_items_has_no_category():
    html = contact_form(items=[])

    assert "<select" not in html and 'name="category"' not in html


def test_contact_form_fields_are_required_without_js():
    html = contact_form()

    for tag in re.findall(r"<(?:input|textarea)[^>]*name=\"(?:name|email|subject|message|consent)\"[^>]*>", html):
        assert " required" in tag
    assert 'type="email"' in html and 'type="checkbox"' in html
    button = re.search(r"<button[^>]*type=\"submit\"[^>]*>", html).group(0)
    assert not re.search(r"\sdisabled[\s>=]", button)


def test_contact_form_consent_label_is_rich_text_with_a_default():
    assert "I agree to the &lt;privacy&gt; policy" in contact_form()
    assert "I consent to my data being processed." in contact_form({}, items=[])


def test_contact_form_thank_you_is_swapped_in_with_a_default():
    html = contact_form()

    assert 'x-if="submitted"' in html and "Thanks, friend" in html
    assert "Thank you for your message. We will be in touch soon." in contact_form({}, items=[])


def test_contact_form_ids_are_unique_per_form_name():
    assert 'id="name-story"' in contact_form() and 'for="name-story"' in contact_form()
