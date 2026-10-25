"""The myc3 theme's layout, 404, assets and Tailwind tokens, ported from the Next site."""

import re
import subprocess
from pathlib import Path

import pytest
from django.conf import settings as django_settings

ROOT = Path(django_settings.BASE_DIR)
THEME = ROOT / "themes/myc3"
TAILWIND = ROOT / ".bin/tailwindcss-v4.3.3"
BACKGROUND = "https://images.prismic.io/thec3/Zkd4aSol0Zci9P4G_GP_006.png?auto=format,compress"
WRAPPER = '<div class="absolute w-screen min-h-screen pb-4 bg-gray-50"'


def page_doc(uid, **data):
    data = {"seo_title": None, "background_image": {}, "body": [], **data}
    return {"id": uid, "type": "page", "uid": uid, "tags": ["domain:myc3.life"], "data": data}


def get(client, path):
    response = client.get(path)
    return response.status_code, response.content.decode()


def test_home_is_uid_myc3_inside_the_next_page_wrapper(myc3, client):
    myc3.append(page_doc("myc3", seo_title="life @ the c3 church"))

    status, html = get(client, "/")

    assert status == 200
    assert WRAPPER + ">" in html
    assert "<title>life @ the c3 church</title>" in html


def test_background_image_is_the_wrappers_css_background(myc3, client):
    image = {"dimensions": {"width": 2000, "height": 2000}, "alt": None, "url": BACKGROUND}
    myc3.append(page_doc("growth-path", background_image=image))

    _, html = get(client, "/growth-path/")

    assert f"{WRAPPER} style=\"background-image: url('{BACKGROUND.replace('&', '&amp;')}')\">" in html


def test_umami_script_uses_the_myc3_website(myc3, client):
    myc3.append(page_doc("myc3"))

    _, html = get(client, "/")

    assert 'src="https://analytics.myc3.life/script.js"' in html
    assert 'data-website-id="231a1dee-01c4-422e-adbc-d253914fe38c"' in html


def test_pages_load_the_form_script_before_a_pinned_alpine(myc3, client):
    myc3.append(page_doc("myc3"))

    _, html = get(client, "/")

    site_js = html.index("/static/js/site.js")
    alpine = re.search(r'src="https://cdn\.jsdelivr\.net/npm/alpinejs@\d+\.\d+\.\d+/dist/cdn\.min\.js"', html)
    assert site_js < alpine.start()
    assert (THEME / "static/js/site.js").exists()


def test_css_hides_x_cloak_elements(css):
    assert "[x-cloak]" in css


def test_404_is_the_shared_page_inside_the_myc3_layout(myc3, client):
    status, html = get(client, "/404.html")

    assert status == 404
    assert f"{WRAPPER}><main><h1>Page not found</h1>" in html
    assert '<meta name="robots" content="noindex">' in html


def test_theme_has_no_base_template_to_shadow_the_shared_one():
    assert not (THEME / "templates/base.html").exists()


def test_favicon_and_fonts_are_self_hosted():
    assert (THEME / "public/favicon.ico").is_file()
    fonts = {p.name for p in (THEME / "static/fonts").iterdir()}
    assert "Novecentosanswide-Bold.otf" in fonts
    assert "dm-serif-display-latin-400-normal.woff2" in fonts
    assert "montserrat-latin-400-normal.woff2" in fonts


@pytest.fixture(scope="module")
def css(tmp_path_factory):
    if not TAILWIND.exists():
        pytest.skip("Tailwind binary is downloaded by scripts/build.sh")
    out = tmp_path_factory.mktemp("css") / "site.css"
    subprocess.run([TAILWIND, "-i", THEME / "css/site.css", "-o", out], check=True, capture_output=True)
    return out.read_text()


@pytest.mark.parametrize(
    "token",
    [
        "--color-gray-50: #f6f7f7",
        "--color-gray-900: #272b2b",
        "--color-red-500: #f05356",
        "--color-purple-900: #202945",
        "--color-grayscale-50: #f7f7f7",
        "--color-teal-500: #00919F",
        "--color-yellow-300: #f8c23a",
        '--font-title: "Novecento Sans Wide"',
        '--font-serif: "DM Serif Display"',
        "--font-sans: Montserrat,",
    ],
)
def test_theme_declares_the_next_tailwind_tokens(token):
    # v4 only emits the variables that templates use, so read the source.
    assert token in (THEME / "css/site.css").read_text()


def test_css_drops_tailwinds_default_palette(css):
    # Next's tailwind.config.js replaced the colours, so there is no black or blue.
    assert "--color-blue-500" not in css
    assert ".bg-gray-50" in css


def test_css_declares_the_self_hosted_fonts(css):
    assert 'font-family: "DM Serif Display"' in css
    assert "montserrat-latin-400-normal.woff2" in css
    assert "Novecentosanswide-Bold.otf" in css


def test_css_sizes_font_awesome_icons_below_tailwind_utilities(css):
    # react-fontawesome injects these at runtime, before Next's stylesheet, so h-5 and h-8 win.
    components = css[css.index("@layer components") :]
    assert ".svg-inline--fa {" in components
    assert ".fa-fw {" in components
