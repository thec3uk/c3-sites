import json
from pathlib import Path

import pytest
from django.template.loader import render_to_string

from config.settings.sites import load_site
from content.sources.prismic import to_page

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def html(settings):
    settings.SITE = load_site("academy")
    page = to_page(json.loads((FIXTURES / "academy_page.json").read_text()))
    return render_to_string("pages/academy_page.html", {"page": page, "site": settings.SITE})


def test_hero_shows_title_lead_and_ctas(html):
    assert "Academy</h1>" in html
    assert "Equipping and developing you" in html
    assert html.count('class="cta ') == 3
    assert 'href="https://thec3.churchsuite.com/events/tvxvflie"' in html


def test_ctas_alternate_yellow_and_purple(html):
    import re

    colours = re.findall(r'class="cta [^"]*?(bg-yellow|bg-purple) ', html)
    assert colours == ["bg-yellow", "bg-purple", "bg-yellow"]


def test_hero_image_is_sized_through_imgix(html):
    assert "XQgK4uOpKcS4eFH9_001a.png?auto=format%2Ccompress&amp;w=2400" in html


def test_page_loads_theme_css_and_umami(html):
    assert "/static/css/site.css" in html
    assert 'data-website-id="c9ca3f93-1107-49cc-b2e4-ddb0dbae79d1"' in html
