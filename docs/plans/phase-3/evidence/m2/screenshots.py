"""Full-page screenshots of each page, local dist/ vs live thec3.uk, at 1440 and 390 wide.

Run after `just build main`: uv run python docs/plans/phase-3/evidence/m2/screenshots.py /contact/ ...
Plain Playwright with its default user agent.
"""

import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
DIST = HERE.parents[4] / "dist"


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def shoot(page, url, path):
    page.goto(url, wait_until="networkidle")
    # Scroll through so lazy images load before the full-page capture.
    page.evaluate("""async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 400) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 100));
        }
        window.scrollTo(0, 0);
    }""")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=path, full_page=True, type="jpeg", quality=70)


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(DIST)))
threading.Thread(target=server.serve_forever, daemon=True).start()
local = f"http://127.0.0.1:{server.server_port}"
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in ((1440, 900), (390, 844)):
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        for path in sys.argv[1:]:
            name = path.strip("/") or "home"
            shoot(page, f"https://thec3.uk{path}", HERE / f"{name}-{width}-live.jpg")
            shoot(page, f"{local}{path}", HERE / f"{name}-{width}-local.jpg")
            print(name, width)
        context.close()
    browser.close()
server.shutdown()
