import json
import re
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings as django_settings

from tests.documents import BANNER_IMAGE, SEO_IMAGE, banner_doc, image, page_doc

ROOT = Path(django_settings.BASE_DIR)
NAV = [
    ("New to Church", "/reaching/"),
    ("Next Steps", "/shaping/"),
    ("Our Locations", "/locations/"),
    ("About Us", "/about/"),
    ("Get Prayer", "https://prayer.thec3.uk"),
    ("Give", "/giving/"),
]
def get(client, path="/about/"):
    response = client.get(path)
    return response.content.decode()


VOID = {"img", "br", "meta", "link", "input", "hr"}


class Links(HTMLParser):
    """(text, href) for every link inside elements matching an id."""

    def __init__(self, container_id):
        super().__init__()
        self.container_id, self.depth, self.links, self.href = container_id, 0, [], None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in VOID:
            return
        if self.depth or attrs.get("id") == self.container_id:
            self.depth += 1
        if self.depth and tag == "a":
            self.href, self.text = attrs.get("href"), ""

    def handle_endtag(self, tag):
        if self.depth and tag == "a" and self.href is not None:
            self.links.append((self.text.strip(), self.href))
            self.href = None
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.href is not None:
            self.text += data


def links_in(html, container_id):
    parser = Links(container_id)
    parser.feed(html)
    return parser.links


def meta(html, attr, name):
    match = re.search(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)"', html)
    return match and match.group(1)


def test_page_is_wrapped_in_the_main_layout(main, client):
    html = get(client)

    assert html.count("<header") == 1
    assert "<main" in html
    assert "<footer" in html
    assert "/static/css/site.css" in html
    assert 'data-website-id="ee3c430d-e2d2-4256-973e-7c0be0223d63"' in html
    assert 'src="https://analytics.thec3.uk/script.js"' in html


def test_desktop_nav_has_logo_and_six_links(main, client):
    links = links_in(get(client), "desktop-menu")

    assert links[0] == ("", "/")
    assert links[1:] == NAV


def test_mobile_menu_has_button_and_panel_with_logo_and_six_links(main, client):
    html = get(client)

    assert re.search(r'<button[^>]*aria-controls="mobile-menu"', html)
    assert links_in(html, "mobile-bar")[0] == ("", "/")
    assert links_in(html, "mobile-menu") == NAV
    assert re.search(r'src="https://cdn\.jsdelivr\.net/npm/alpinejs@\d+\.\d+\.\d+/dist/cdn\.min\.js"', html)


def test_active_banner_links_to_its_url_and_remembers_dismissal(main, client):
    main.append(banner_doc("yes"))

    html = get(client)

    assert "Global Leadership Summit 2026" in html
    assert 'href="http://www.thec3.uk/gls"' in html
    assert 'x-data="notificationBanner"' in html
    assert 'data-message="Global Leadership Summit 2026"' in html


def test_inactive_banner_is_not_rendered(main, client):
    main.append(banner_doc("no"))

    assert "Global Leadership Summit" not in get(client)


def test_footer_lists_link_lists_and_charity_number(main, client):
    html = get(client)

    assert links_in(html, "footer-links") == [
        ("about", "/about/"),
        ("leaders", "/ourleaders/"),
        ("Breathe", "https://breathe.thec3.uk"),
    ]
    assert re.search(r"<h4[^>]*>Our Church</h4>", html)
    assert re.search(r"<h4[^>]*>Our Network</h4>", html)
    assert "Charity number: 1132699" in html


def test_seo_uses_the_page_fields(main, client):
    html = get(client, "/")

    assert "<title>Welcome Home | The C3 Church</title>" in html
    assert meta(html, "name", "description") == "A church with locations in Cambridge"
    assert meta(html, "property", "og:title") == "Welcome Home | The C3 Church"
    assert meta(html, "property", "og:url") == "https://thec3.uk/"
    assert meta(html, "property", "og:image").startswith("https://images.prismic.io/thec3/seo.jpg")
    assert meta(html, "name", "twitter:title") == "Welcome Home | The C3 Church"
    assert meta(html, "name", "twitter:card") == "summary_large_image"
    assert meta(html, "name", "twitter:creator") == "@thec3_church"
    assert '<link rel="canonical" href="https://thec3.uk/">' in html


def test_seo_falls_back_to_site_config(main, client):
    html = get(client, "/about/")

    assert "<title>The C3 Church</title>" in html
    assert meta(html, "name", "description") == "The C3 Church is a church."
    assert meta(html, "property", "og:title") == "The C3 Church"
    assert meta(html, "property", "og:description") == "The C3 Church is a church."
    # Gatsby SEO.tsx falls back to the site's social_share.jpeg, not site_config's banner.
    assert meta(html, "name", "image") == "https://thec3.uk/social_share.jpeg"
    assert meta(html, "property", "og:image") == "https://thec3.uk/social_share.jpeg"
    assert meta(html, "name", "twitter:image") == "https://thec3.uk/social_share.jpeg"
    assert (ROOT / "themes/main/public/social_share.jpeg").is_file()
    assert '<link rel="canonical" href="https://thec3.uk/about/">' in html


def rich(text):
    return [{"type": "paragraph", "text": text, "spans": []}]


def test_rich_text_in_attributes_renders_as_escaped_plain_text(main, client):
    banner = banner_doc("yes")
    banner["data"]["content"] = rich('Say "hi"')
    main.append(banner)
    main[0]["data"].update(seo_title=rich('Welcome "Home"'), seo_description=rich('A "quoted" church'))

    html = get(client, "/")

    assert 'data-message="Say &quot;hi&quot;"' in html
    assert "<title>Welcome &quot;Home&quot; | The C3 Church</title>" in html
    assert meta(html, "name", "description") == "A &quot;quoted&quot; church"
    assert meta(html, "property", "og:title") == "Welcome &quot;Home&quot; | The C3 Church"
    assert meta(html, "name", "twitter:description") == "A &quot;quoted&quot; church"


def test_404_uses_the_main_layout(main, client):
    response = client.get("/404.html")
    html = response.content.decode()

    assert response.status_code == 404
    assert "the page is not here!" in html
    assert "Charity number: 1132699" in html
    assert links_in(html, "desktop-menu")[1:] == NAV
    assert '<meta name="robots" content="noindex">' in html


def test_manifest_is_linked_and_matches_gatsby_config(main, client):
    html = get(client)
    manifest = json.loads((ROOT / "themes/main/public/manifest.webmanifest").read_text())

    assert '<link rel="manifest" href="/manifest.webmanifest">' in html
    assert meta(html, "name", "theme-color") == "#202945"
    assert manifest["name"] == "The C3 Church"
    assert manifest["short_name"] == "The C3"
    assert manifest["start_url"] == "/"
    assert manifest["background_color"] == "#f05356"
    assert manifest["theme_color"] == "#202945"
    assert manifest["display"] == "standalone"
    assert manifest["icons"][0]["src"] == "/static/images/manifest-logo.png"
