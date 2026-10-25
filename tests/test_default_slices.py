"""Every slice variation in real use renders with the shared default templates."""

import json
from pathlib import Path

import pytest
from django.template import Context, Template
from django.utils.html import escape

from content.models import Page, RichText
from content.sources.prismic import _slice

SAMPLES = json.loads((Path(__file__).parent / "fixtures" / "slice_samples.json").read_text())


def render(slice):
    page = Page(id="p", type="page", uid="x", url="/x/", slices=(slice,))
    return Template("{% load slices %}{% render_slices page %}").render(Context({"page": page}))


def text_of(value):
    return value.text if isinstance(value, RichText) else value


@pytest.fixture(autouse=True)
def shared_templates_only(settings):
    # No theme: these are the defaults every site falls back to.
    settings.TEMPLATES = [{**settings.TEMPLATES[0], "DIRS": [settings.BASE_DIR / "templates"]}]


@pytest.mark.parametrize("raw", SAMPLES, ids=lambda s: f"{s['slice_type']}/{s.get('variation')}")
def test_every_real_variation_renders(raw):
    slice = _slice(raw, "thec3.uk")

    html = render(slice)

    assert html.strip()
    for name in ("title", "linkTitle", "ctaTitle", "question"):
        for source in [slice.primary, *slice.items]:
            value = text_of(source.get(name))
            if isinstance(value, str) and value.strip():
                snippet = value.strip().splitlines()[0][:20]
                assert snippet in html or escape(snippet) in html, name


def test_slice_wrapper_names_type_and_variation():
    raw = next(s for s in SAMPLES if s["slice_type"] == "header" and s["variation"] == "heroWithImage")

    html = render(_slice(raw, "thec3.uk"))

    assert 'data-slice="header"' in html and 'data-variation="heroWithImage"' in html
