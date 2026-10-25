import re

import pytest
from django.template import Context, Template

from content.models import Page, Slice
from pages.templatetags.slices import MissingSliceTemplate


@pytest.fixture
def dirs(tmp_path, settings):
    theme, shared = tmp_path / "theme", tmp_path / "shared"
    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [theme, shared],
            "APP_DIRS": True,
        }
    ]

    def write(root, name, body):
        path = (theme if root == "theme" else shared) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)

    return write


def render_wrapped(page):
    return Template("{% load slices %}{% render_slices page %}").render(Context({"page": page}))


def render(page):
    """Slice output without the <section> wrapper each slice gets."""
    return re.sub(r"</?section[^>]*>", "", render_wrapped(page))


def page_with(*slices):
    return Page(id="1", type="page", uid="x", url="/x/", slices=tuple(slices))


def test_renders_each_slice_with_its_type_template(dirs):
    dirs("shared", "slices/text.html", "[text:{{ slice.primary.body }}]")
    dirs("shared", "slices/quote.html", "[quote]")

    html = render(page_with(Slice("text", primary={"body": "hi"}), Slice("quote")))

    assert html == "[text:hi][quote]"


def test_slice_template_gets_page_and_index(dirs):
    dirs("shared", "slices/text.html", "{{ page.url }}#{{ index }}")

    assert render(page_with(Slice("text"), Slice("text"))) == "/x/#0/x/#1"


def test_theme_overrides_shared_template(dirs):
    dirs("shared", "slices/text.html", "shared")
    dirs("theme", "slices/text.html", "theme")

    assert render(page_with(Slice("text"))) == "theme"


def test_variation_template_beats_type_template(dirs):
    dirs("theme", "slices/header.html", "type")
    dirs("shared", "slices/header/heroWithImage.html", "variation")

    assert render(page_with(Slice("header", variation="heroWithImage"))) == "variation"


def test_missing_template_fails_the_build(dirs):
    with pytest.raises(MissingSliceTemplate, match="'card'.*'default'.*/x/"):
        render(page_with(Slice("card")))


def test_missing_template_shows_placeholder_in_debug(dirs, settings):
    settings.DEBUG = True

    assert 'data-missing-slice="card/default"' in render(page_with(Slice("card")))


def test_page_without_slices_renders_nothing(dirs):
    assert render(page_with()) == ""


def test_each_slice_is_wrapped_with_its_type_and_variation(dirs):
    dirs("shared", "slices/text.html", "hi")

    html = render_wrapped(page_with(Slice("text", variation="wide")))

    assert html == '<section class="slice" data-slice="text" data-variation="wide">hi</section>'
