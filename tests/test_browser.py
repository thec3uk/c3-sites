import json
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from django.conf import settings
from playwright.sync_api import expect, sync_playwright

from tests.documents import banner_doc

pytestmark = pytest.mark.browser
DIST = Path(settings.BASE_DIR) / "dist"


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
