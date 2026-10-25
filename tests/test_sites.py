import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings.sites import load_site


def test_load_site_returns_academy_config():
    site = load_site("academy")

    assert site.name == "academy"
    assert site.theme == "academy"
    assert site.prismic_types == ("academy_page", "site_config")


def test_load_site_rejects_unknown_name():
    with pytest.raises(ImproperlyConfigured, match="nope"):
        load_site("nope")


def test_settings_expose_current_site(settings):
    assert settings.SITE.name == "academy"


def test_load_site_returns_main_config():
    site = load_site("main")

    assert site.name == "main"
    assert site.domain == "thec3.uk"
    assert site.theme == "main"
    assert site.prismic_tags == ("domain:thec3.uk",)
    assert site.page_types == ("page",)
    assert site.umami_website_id == "ee3c430d-e2d2-4256-973e-7c0be0223d63"
    assert site.umami_src == "https://analytics.thec3.uk/script.js"
