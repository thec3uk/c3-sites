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


def test_load_site_returns_myc3_config():
    site = load_site("myc3")

    assert site.name == "myc3"
    assert site.domain == "myc3.life"
    assert site.theme == "myc3"
    assert site.prismic_tags == ("domain:myc3.life",)
    assert site.page_types == ("page",)
    assert site.umami_website_id == "231a1dee-01c4-422e-adbc-d253914fe38c"
    assert site.umami_src == "https://analytics.myc3.life/script.js"
    assert site.link_rule == "next"


@pytest.mark.parametrize("name", ["main", "academy"])
def test_main_and_academy_keep_the_domain_uid_link_rule(name):
    assert load_site(name).link_rule == "domain_uid"
