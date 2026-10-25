import pytest

from content.models import Image
from pages.templatetags.images import imgix


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://images.prismic.io/thec3/a.png?auto=format,compress",
            "https://images.prismic.io/thec3/a.png?auto=format%2Ccompress&w=1920",
        ),
        ("https://images.prismic.io/thec3/a.png?w=5760&h=10", "https://images.prismic.io/thec3/a.png?w=800"),
        ("https://images.prismic.io/thec3/a.png", "https://images.prismic.io/thec3/a.png?w=800"),
    ],
)
def test_imgix_sets_width_and_drops_height(url, expected):
    width = 1920 if "auto" in url else 800
    assert imgix(Image(url=url), width) == expected


def test_imgix_of_missing_image_is_blank():
    assert imgix(None, 800) == ""
