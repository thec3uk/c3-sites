import json
import os
from urllib.parse import parse_qs, urlparse
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




@pytest.fixture
def evidence(tmp_path):
    """Where screenshots go: tmp_path, or $EVIDENCE_DIR to refresh committed evidence."""
    path = Path(os.environ.get("EVIDENCE_DIR") or tmp_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def mocked_posts(desktop):
    """Records POSTs and answers them; nothing reaches Netlify or Mailchimp."""
    posts = []

    def answer(route):
        request = route.request
        if request.method != "POST":
            return route.continue_()
        posts.append(request.post_data)
        route.fulfill(status=200, body="ok")

    desktop.route("**/", answer)
    return posts


def fill_contact_form(page):
    page.get_by_label("Full Name").fill("Jane Smith")
    page.get_by_label("Email").fill("jane@example.com")
    page.get_by_label("Category").select_option("Safeguarding")
    page.get_by_label("Your Subject").fill("A question")
    page.get_by_label("Your Message").fill("Hello there, a longer message")


def test_contact_form_posts_to_netlify_and_shows_thank_you(dist_url, desktop, mocked_posts, evidence):
    desktop.goto(dist_url + "/contact/")
    send = desktop.get_by_role("button", name="Send")
    expect(send).to_be_disabled()

    fill_contact_form(desktop)
    expect(send).to_be_enabled()
    desktop.screenshot(path=str(evidence / "contact-filled.png"))
    send.click()

    expect(desktop.get_by_text("Thanks for your message!")).to_be_visible()
    expect(desktop.get_by_label("Full Name")).to_be_hidden()
    desktop.screenshot(path=str(evidence / "contact-thanks.png"))
    body = parse_qs(mocked_posts[0], keep_blank_values=True)
    assert body["form-name"] == ["Contact Us"]
    assert body["category_name"] == ["Safeguarding"]
    assert body["email_recipient"] == ["safeguarding@thec3.uk"]
    assert body["email"] == ["jane@example.com"] and body["bot-field"] == [""]


def test_send_enables_when_fields_are_restored_without_input_events(dist_url, desktop):
    desktop.goto(dist_url + "/contact/")
    # Mimics autofill or back-navigation: values set, no input/change events.
    desktop.evaluate(
        """() => {
          const f = document.querySelector("form[name='Contact Us']") || document.querySelector("form");
          f.elements.name.value = "Jane Smith";
          f.elements.email.value = "jane@example.com";
          f.elements.subject.value = "A question";
          f.elements.message.value = "Hello there, a longer message";
          f.elements.category_name.value = "Safeguarding";
          const root = f.closest("[x-data]");
          Alpine.destroyTree(root);
          Alpine.initTree(root);
        }"""
    )

    expect(desktop.get_by_role("button", name="Send")).to_be_enabled()
    assert desktop.locator("input[name=email_recipient]").input_value() == "safeguarding@thec3.uk"


def test_contact_form_keeps_the_form_when_the_post_fails(dist_url, desktop):
    desktop.route("**/", lambda route: route.fulfill(status=500) if route.request.method == "POST" else route.continue_())
    desktop.goto(dist_url + "/contact/")
    fill_contact_form(desktop)

    desktop.get_by_role("button", name="Send").click()

    expect(desktop.get_by_role("alert")).to_contain_text("could not be sent")
    expect(desktop.get_by_label("Full Name")).to_be_visible()


MAILCHIMP = "https://thec3.us19.list-manage.com/subscribe/post-json**"


def answer_jsonp(requests, payload):
    def handler(route):
        url = urlparse(route.request.url)
        requests.append(parse_qs(url.query))
        callback = requests[-1]["c"][0]
        route.fulfill(content_type="text/javascript", body=f"{callback}({json.dumps(payload)})")

    return handler


def fill_newsletter(page):
    page.locator("#name").fill("Josh")
    page.locator("#email").fill("josh@example.com")
    page.get_by_text("Cambridge").click()
    page.get_by_text("Online").click()


def test_newsletter_subscribes_through_mailchimp_jsonp(dist_url, desktop, evidence):
    requests = []
    desktop.route(MAILCHIMP, answer_jsonp(requests, {"result": "success", "msg": "Thank you for subscribing!"}))
    desktop.goto(dist_url + "/subscribe/")
    fill_newsletter(desktop)
    desktop.screenshot(path=str(evidence / "newsletter-filled.png"))

    desktop.get_by_role("button", name="Subscribe").click()

    expect(desktop.get_by_text("Thank you for subscribing!")).to_be_visible()
    desktop.screenshot(path=str(evidence / "newsletter-success.png"))
    query = requests[0]
    assert query["u"] == ["baac982817e7fb161022a1253"] and query["id"] == ["d62f87b12a"]
    assert query["EMAIL"] == ["josh@example.com"] and query["FNAME"] == ["Josh"]
    assert query["LOCATION"] == ['"CAMBRIDGE", "ONLINE"']
    assert query["SOURCE"] == ["website signup"] and query["SIGNUPURL"] == ["/subscribe/"]


def test_newsletter_shows_mailchimps_error_and_keeps_the_form(dist_url, desktop, evidence):
    error = "0 - Please enter a value"
    desktop.route(MAILCHIMP, answer_jsonp([], {"result": "error", "msg": error}))
    desktop.goto(dist_url + "/subscribe/")
    fill_newsletter(desktop)

    desktop.get_by_role("button", name="Subscribe").click()

    expect(desktop.get_by_text(error)).to_be_visible()
    expect(desktop.locator("#email")).to_be_visible()
    desktop.screenshot(path=str(evidence / "newsletter-error.png"))
