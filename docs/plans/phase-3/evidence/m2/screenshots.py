"""Full-page screenshots of each page, local dist/ vs live thec3.uk, at 1440 and 390 wide.

Run after `just build main`: uv run python docs/plans/phase-3/evidence/m2/screenshots.py /contact/ ...
Serving and shooting come from scripts/parity_check.py (M5), which covers every page.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "scripts"))

from parity_check import LIVE, WIDTHS, serve_dist, shoot  # noqa: E402

with serve_dist() as local, sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in WIDTHS:
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        for path in sys.argv[1:]:
            name = path.strip("/") or "home"
            shoot(page, f"{LIVE}{path}", HERE / f"{name}-{width}-live.jpg")
            shoot(page, f"{local}{path}", HERE / f"{name}-{width}-local.jpg")
            print(name, width)
        context.close()
    browser.close()
