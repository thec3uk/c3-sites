"""The My C3 contact form in a real browser; every request except Alpine's CDN script is mocked."""

import os
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import pytest
from django.conf import settings
from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.browser
THEME = Path(settings.BASE_DIR) / "themes/myc3"
ALPINE = "https://cdn.jsdelivr.net/npm/alpinejs@"
SLICE = {
    "slice_type": "contact_form",
    "variation": "default-slice",
    "primary": {
        "form_name": "story",
        "name_label": "Your name",
        "email_label": "Your email",
        "category_label": "Topic",
        "subject_label": "About",
        "message_label": "Tell us more",
        "submit_button_label": "SEND",
        "consent_label": [{"type": "paragraph", "text": "I agree to the privacy policy", "spans": []}],
        "thank_you_message": [{"type": "paragraph", "text": "Thanks, friend", "spans": []}],
    },
    "items": [{"category_name": "Story"}, {"category_name": "Prayer"}],
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def site_url(myc3, client, tmp_path):
    myc3.append(
        {
            "id": "p",
            "type": "page",
            "uid": "share-your-story",
            "tags": ["domain:myc3.life"],
            "data": {"seo_title": None, "background_image": {}, "body": [SLICE]},
        }
    )
    page = tmp_path / "share-your-story"
    page.mkdir()
    (page / "index.html").write_bytes(client.get("/share-your-story/").content)
    shutil.copytree(THEME / "static", tmp_path / "static")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(tmp_path)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/share-your-story/"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def evidence(tmp_path):
    path = Path(os.environ.get("EVIDENCE_DIR") or tmp_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def posts():
    return []


@pytest.fixture
def desktop(browser, site_url, posts):
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    def answer(route):
        request = route.request
        if request.url.startswith(ALPINE) or request.url.startswith("http://127.0.0.1"):
            if request.method == "POST":
                posts.append(request.post_data)
                return route.fulfill(status=getattr(page, "post_status", 200), body="ok")
            return route.continue_()
        route.abort()

    page.route("**/*", answer)
    yield page
    context.close()


def fill(page, **overrides):
    values = {
        "Your name": "Jane Smith",
        "Your email": "jane@example.com",
        "About": "A question",
        "Tell us more": "Hello there",
        **overrides,
    }
    for label, value in values.items():
        page.get_by_label(label).fill(value)
    page.get_by_label("Topic").select_option("Prayer")
    page.get_by_label("I agree to the privacy policy").check()


def test_valid_submission_posts_to_netlify_and_shows_thank_you(site_url, desktop, posts, evidence):
    desktop.goto(site_url)
    fill(desktop)
    desktop.screenshot(path=str(evidence / "share-your-story-filled.png"))

    desktop.get_by_role("button", name="SEND").click()

    expect(desktop.get_by_text("Thanks, friend")).to_be_visible()
    expect(desktop.get_by_label("Your name")).to_be_hidden()
    desktop.screenshot(path=str(evidence / "share-your-story-thanks.png"))
    body = parse_qs(posts[0], keep_blank_values=True)
    assert body == {
        "form-name": ["story"],
        "bot-field": [""],
        "name": ["Jane Smith"],
        "email": ["jane@example.com"],
        "category": ["Prayer"],
        "subject": ["A question"],
        "message": ["Hello there"],
        "consent": ["yes"],
    }


def test_empty_submission_shows_next_messages_and_sends_nothing(site_url, desktop, posts, evidence):
    desktop.goto(site_url)
    expect(desktop.get_by_role("button", name="SEND")).to_be_enabled()

    desktop.get_by_role("button", name="SEND").click()

    for message in (
        "Name is required",
        "Email is required",
        "Please select a category",
        "Subject is required",
        "Message is required",
        "You must agree to continue",
    ):
        expect(desktop.get_by_text(message)).to_be_visible()
    desktop.screenshot(path=str(evidence / "share-your-story-errors.png"))
    assert posts == []


def test_bad_email_is_reported_and_typing_clears_the_error(site_url, desktop, posts):
    desktop.goto(site_url)
    fill(desktop, **{"Your email": "jane@nowhere"})

    desktop.get_by_role("button", name="SEND").click()

    expect(desktop.get_by_text("Please enter a valid email")).to_be_visible()
    assert posts == []
    desktop.get_by_label("Your email").fill("jane@example.com")
    expect(desktop.get_by_text("Please enter a valid email")).to_be_hidden()


def test_unchecked_consent_blocks_the_post(site_url, desktop, posts):
    desktop.goto(site_url)
    fill(desktop)
    desktop.get_by_label("I agree to the privacy policy").uncheck()

    desktop.get_by_role("button", name="SEND").click()

    expect(desktop.get_by_text("You must agree to continue")).to_be_visible()
    assert posts == []


def test_failed_post_keeps_the_form_and_shows_an_error(site_url, desktop, posts):
    desktop.post_status = 500
    desktop.goto(site_url)
    fill(desktop)

    desktop.get_by_role("button", name="SEND").click()

    expect(desktop.get_by_role("alert")).to_contain_text("Something went wrong")
    expect(desktop.get_by_label("Your name")).to_be_visible()


def test_without_js_the_form_is_plain_and_the_honeypot_is_hidden(browser, site_url):
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    page.route("**/*", lambda route: route.continue_() if route.request.url.startswith("http://127.0.0.1") else route.abort())

    page.goto(site_url)

    expect(page.get_by_label("Your name")).to_be_visible()
    expect(page.get_by_role("button", name="SEND")).to_be_enabled()
    expect(page.locator("input[name=bot-field]")).to_be_hidden()
    expect(page.locator("form[name=story][data-netlify=true]")).to_have_count(1)
    context.close()
