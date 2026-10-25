import json
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from django.conf import settings
from playwright.sync_api import expect, sync_playwright

from tests.documents import banner_doc, page_doc

pytestmark = pytest.mark.browser
DIST = Path(settings.BASE_DIR) / "dist"
FIXTURES = Path(__file__).parent / "fixtures"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(directory)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(scope="module")
def dist_url():
    if not (DIST / "manifest.webmanifest").exists():
        pytest.fail("dist/ is not a main build: run `just build main` first")
    server = serve(DIST)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def phone(browser):
    context = browser.new_context(viewport={"width": 390, "height": 844})
    yield context.new_page()
    context.close()


def open_menu(page):
    page.get_by_role("button", name="Menu").click()
    expect(page.locator("#mobile-menu")).to_be_visible()


def expect_closed(page):
    button = page.get_by_role("button", name="Menu")
    expect(page.locator("#mobile-menu")).to_be_hidden()
    expect(button).to_be_focused()
    expect(button).to_have_attribute("aria-expanded", "false")
    assert page.evaluate("document.body.style.overflow") == ""


def test_menu_opens_with_focus_inside_and_scroll_locked(dist_url, phone):
    phone.goto(dist_url + "/")
    expect(phone.locator("#desktop-menu")).to_be_hidden()
    expect(phone.locator("#mobile-menu")).to_be_hidden()

    open_menu(phone)

    expect(phone.get_by_role("button", name="Menu")).to_have_attribute("aria-expanded", "true")
    expect(phone.locator("#mobile-menu a")).to_have_count(6)
    expect(phone.locator("#mobile-menu a").first).to_be_focused()
    assert phone.evaluate("document.body.style.overflow") == "hidden"


def test_menu_closes_on_the_button(dist_url, phone):
    phone.goto(dist_url + "/")
    open_menu(phone)

    phone.get_by_role("button", name="Menu").click()

    expect_closed(phone)


def test_menu_closes_on_escape(dist_url, phone):
    phone.goto(dist_url + "/")
    open_menu(phone)

    phone.keyboard.press("Escape")

    expect_closed(phone)


def test_menu_closes_on_a_link(dist_url, phone):
    phone.goto(dist_url + "/")
    open_menu(phone)
    link = phone.locator("#mobile-menu a", has_text="About Us")
    # Stay on the page so the closed state can be checked.
    link.evaluate("a => a.addEventListener('click', e => e.preventDefault())")

    link.click()

    expect_closed(phone)


@pytest.fixture
def banner_site(main, client, tmp_path, dist_url):  # noqa: F811
    main.append(banner_doc("yes"))
    (tmp_path / "index.html").write_bytes(client.get("/").content)
    shutil.copytree(DIST / "static", tmp_path / "static")
    server = serve(tmp_path)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_dismissed_banner_stays_dismissed(banner_site, phone):
    phone.goto(banner_site + "/")
    banner = phone.get_by_text("Global Leadership Summit 2026")
    expect(banner).to_be_visible()

    phone.get_by_role("button", name="Dismiss").click()

    expect(banner).to_be_hidden()
    stored = json.loads(phone.evaluate("localStorage.getItem('NOTIFICATIONBAR')"))
    assert stored == [{"message": "Global Leadership Summit 2026", "closed": True}]
    phone.reload()
    expect(phone.get_by_role("button", name="Dismiss")).to_be_hidden()


def sample(slice_type, variation=None):
    samples = json.loads((FIXTURES / "slice_samples.json").read_text())
    return next(s for s in samples if s["slice_type"] == slice_type and s.get("variation", variation) == variation)


@pytest.fixture
def slices_site(main, client, tmp_path, dist_url):  # noqa: F811
    """/slices/ built from real slice samples, served with the built CSS."""
    main += json.loads((FIXTURES / "linked_documents.json").read_text())
    body = [sample("header", "textOnlyHero"), sample("text"), sample("quick_links_block")]
    body += [sample("card", "imageCard"), sample("faq_section")]
    main.append(page_doc("thec3.uk_slices", body=body))
    (tmp_path / "index.html").write_bytes(client.get("/slices/").content)
    shutil.copytree(DIST / "static", tmp_path / "static")
    server = serve(tmp_path)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def desktop(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    yield context.new_page()
    context.close()


def test_slices_sit_in_mains_grid_with_asides_beside_text(slices_site, desktop):
    desktop.goto(slices_site + "/")
    text = desktop.locator("[data-slice=text] > div").bounding_box()
    aside = desktop.locator("[data-slice=quick_links_block] aside").bounding_box()

    # Gatsby: text in columns 2-9, the aside in 10-11 on the same row.
    assert 100 < text["x"] and text["width"] > 700
    assert aside["x"] > text["x"] + text["width"]
    assert abs(aside["y"] - text["y"]) < 1


def test_image_card_is_at_least_25rem_tall_on_desktop(slices_site, desktop):
    desktop.goto(slices_site + "/")

    assert desktop.locator("[data-slice=card] a > div").bounding_box()["height"] >= 400


def test_faq_answer_opens_on_its_question(slices_site, phone):
    phone.goto(slices_site + "/")
    answer = phone.get_by_text("we run mid-week life groups", exact=False)
    expect(answer).to_be_hidden()

    phone.get_by_text("What is a Kids Life Group?").click()

    expect(answer).to_be_visible()
