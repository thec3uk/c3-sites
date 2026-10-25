import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings.sites import load_site


def test_load_site_returns_academy_config():
    site = load_site("academy")

    assert site.name == "academy"
    assert site.theme == "academy"
    assert site.prismic_types == ("academy_page",)


def test_load_site_rejects_unknown_name():
    with pytest.raises(ImproperlyConfigured, match="nope"):
        load_site("nope")


def test_settings_expose_current_site(settings):
    assert settings.SITE.name == "academy"
