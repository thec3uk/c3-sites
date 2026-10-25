import pytest

from content.models import Image
from pages.templatetags.images import imgix, srcset


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


def test_srcset_lists_gatsby_breakpoints_up_to_the_image_width():
    image = Image(url="https://images.prismic.io/thec3/a.png", width=1500)

    assert srcset(image) == (
        "https://images.prismic.io/thec3/a.png?w=750 750w, "
        "https://images.prismic.io/thec3/a.png?w=1080 1080w, "
        "https://images.prismic.io/thec3/a.png?w=1366 1366w, "
        "https://images.prismic.io/thec3/a.png?w=1500 1500w"
    )


def test_srcset_of_a_small_image_is_its_own_width():
    assert srcset(Image(url="https://x/a.png", width=512)) == "https://x/a.png?w=512 512w"


def test_srcset_of_missing_image_is_blank():
    assert srcset(None) == ""
