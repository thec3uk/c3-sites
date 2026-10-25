"""Compare the main site built in dist/ with live https://thec3.uk, page by page.

Run after `just build main`:
    SITE=main uv run python scripts/parity_check.py [--pages /about/ ...] [--skip-pages] [--skip-redirects]

Writes screenshots and results.json to docs/plans/phase-3/evidence/m5/. Read-only and sequential:
plain Playwright and httpx with an honest user agent, redirects checked once each without following.
"""

import argparse
import base64
import difflib
import json
import os
import sys
import threading
import time
from collections import Counter
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUT = ROOT / "docs/plans/phase-3/evidence/m5"
LIVE = "https://thec3.uk"
USER_AGENT = "c3-sites parity-check (+https://thec3.uk)"
WIDTHS = ((1440, 900), (390, 844))


def setup_django():
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("SITE", "main")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
    import django

    django.setup()


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def serve_dist(directory=DIST):
    """Serve dist/ on a free local port; yields the base URL."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(directory)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()


def block_analytics(context):
    # Keep parity runs out of Umami's numbers, live and local.
    context.route("**/analytics.thec3.uk/**", lambda route: route.abort())


def load(page, url):
    """Go to url, scroll through so lazy images load; returns the final response."""
    response = page.goto(url, wait_until="networkidle")
    page.evaluate("""async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 400) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 100));
        }
        window.scrollTo(0, 0);
        // Lazy images near the bottom can still be loading; a capture then shows a hole.
        await Promise.all([...document.images].map(i => i.complete ? null
            : new Promise(r => { i.addEventListener('load', r); i.addEventListener('error', r); })));
    }""")
    page.wait_for_load_state("networkidle")
    return response


def shoot(page, url, path):
    """Full-page JPEG of url (kept for evidence/m2/screenshots.py)."""
    load(page, url)
    page.screenshot(path=path, full_page=True, type="jpeg", quality=70)


FACTS_JS = """() => ({
    title: document.title,
    description: [...document.querySelectorAll('meta[name="description"]')].map(m => m.content),
    canonical: [...document.querySelectorAll('link[rel="canonical"]')].map(l => l.href),
    links: [...document.querySelectorAll('a[href]')].map(a => a.href),
    text: document.body.innerText,
})"""


def normalise_link(href, hosts):
    """Same-site links as a path without trailing slash; others as given."""
    parts = urlsplit(href)
    if parts.netloc in hosts:
        path = parts.path.rstrip("/") or "/"
        return path + (f"?{parts.query}" if parts.query else "") + (f"#{parts.fragment}" if parts.fragment else "")
    return href


def statuses(response):
    chain, request = [], response.request
    while request.redirected_from:
        request = request.redirected_from
        chain.insert(0, request.response().status)
    return chain + [response.status]


# Diff two PNGs in the browser (no image library in the project); returns ratios and JPEGs.
DIFF_JS = """async ([a, b]) => {
    const img = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = src; });
    const [ia, ib] = await Promise.all([img(a), img(b)]);
    const w = Math.min(ia.width, ib.width), h = Math.min(ia.height, ib.height);
    const pixels = i => { const c = new OffscreenCanvas(w, h), x = c.getContext('2d');
        x.drawImage(i, 0, 0); return x.getImageData(0, 0, w, h).data; };
    const pa = pixels(ia), pb = pixels(ib);
    const diff = new OffscreenCanvas(w, h), dx = diff.getContext('2d');
    dx.drawImage(ib, 0, 0); dx.fillStyle = 'rgba(255,255,255,0.7)'; dx.fillRect(0, 0, w, h);
    const out = dx.getImageData(0, 0, w, h);
    let total = 0; const rows = [];
    for (let y = 0; y < h; y++) {
        let n = 0;
        for (let x = 0; x < w; x++) {
            const k = (y * w + x) * 4;
            if (Math.max(Math.abs(pa[k] - pb[k]), Math.abs(pa[k+1] - pb[k+1]), Math.abs(pa[k+2] - pb[k+2])) > 48) {
                n++; out.data[k] = 255; out.data[k+1] = 0; out.data[k+2] = 0; out.data[k+3] = 255;
            }
        }
        total += n; rows.push(n / w);
    }
    dx.putImageData(out, 0, 0);
    // Row bands where more than 1% of the row differs, merged across gaps under 20px.
    const bands = [];
    rows.forEach((r, y) => {
        if (r <= 0.01) return;
        const last = bands[bands.length - 1];
        if (last && y - last[1] < 20) last[1] = y; else bands.push([y, y]);
    });
    const jpeg = async c => { const blob = await c.convertToBlob({type: 'image/jpeg', quality: 0.55});
        const buf = new Uint8Array(await blob.arrayBuffer()); let s = '';
        for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
        return btoa(s); };
    const whole = async i => { const c = new OffscreenCanvas(i.width, i.height);
        c.getContext('2d').drawImage(i, 0, 0); return jpeg(c); };
    return {live_height: ia.height, local_height: ib.height, ratio: total / (w * h),
            bands, live_jpeg: await whole(ia), local_jpeg: await whole(ib), diff_jpeg: await jpeg(diff)};
}"""


def compare_images(tool_page, live_png, local_png, stem):
    uri = lambda png: "data:image/png;base64," + base64.b64encode(png).decode()  # noqa: E731
    result = tool_page.evaluate(DIFF_JS, [uri(live_png), uri(local_png)])
    result["ratio"] = round(result["ratio"], 4)
    # A diff image only where there is something to see; keeps the evidence small.
    keep_diff = result["ratio"] > 0.002 or result["live_height"] != result["local_height"]
    for kind in ("live", "local", "diff"):
        data = base64.b64decode(result.pop(f"{kind}_jpeg"))
        if kind != "diff" or keep_diff:
            (OUT / f"{stem}-{kind}.jpg").write_bytes(data)
    return result


def check_pages(paths, local):
    from playwright.sync_api import sync_playwright

    hosts = {"thec3.uk", "www.thec3.uk", urlsplit(local).netloc}
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tool = browser.new_page()
        tool.set_content("<!doctype html><title>diff</title>")
        for width, height in WIDTHS:
            context = browser.new_context(viewport={"width": width, "height": height}, user_agent=USER_AGENT)
            block_analytics(context)
            page = context.new_page()
            for path, live_path in paths:
                name = path.strip("/") or "home"
                row = results.setdefault(name, {"path": path})
                shots = {}
                for side, url in (("live", LIVE + live_path), ("local", local + path)):
                    response = load(page, url)
                    if width == 1440:
                        facts = page.evaluate(FACTS_JS)
                        facts["links"] = [normalise_link(h, hosts) for h in facts["links"]]
                        facts["status"] = statuses(response)
                        facts["final_url"] = page.url.replace(local, "")
                        row[side] = facts
                    shots[side] = page.screenshot(full_page=True)
                row[f"shots_{width}"] = compare_images(tool, shots["live"], shots["local"], f"{name}-{width}")
                print(name, width, row[f"shots_{width}"]["ratio"], flush=True)
            context.close()
        browser.close()
    for row in results.values():
        live, local_facts = row.pop("live"), row.pop("local")
        row["status"] = {"live": live["status"], "local": local_facts["status"]}
        for key in ("title", "description", "canonical", "final_url"):
            row[key] = {"live": live[key], "local": local_facts[key]}
        lc, kc = Counter(live["links"]), Counter(local_facts["links"])
        row["links"] = {"count": {"live": len(live["links"]), "local": len(local_facts["links"])},
                        "only_live": sorted((lc - kc).elements()), "only_local": sorted((kc - lc).elements())}
        split = lambda t: [line.strip() for line in t.splitlines() if line.strip()]  # noqa: E731
        row["text_diff"] = [d for d in difflib.ndiff(split(live["text"]), split(local_facts["text"]))
                            if d[:1] in "+-"]
    return results


def check_redirects():
    """Each generated rule's source on live, once, without following."""
    import httpx

    from pages.redirects import redirect_rules

    rows = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20) as client:
        for rule in redirect_rules():
            try:
                response = client.get(LIVE + rule.source, follow_redirects=False)
                live_status, location = response.status_code, response.headers.get("location", "")
            except httpx.HTTPError as error:
                live_status, location = None, f"error: {error}"
            rows.append({
                "source": rule.source, "target": rule.target, "status": rule.status,
                "live_status": live_status, "live_location": location,
                "same_class": live_status is not None and live_status // 100 == rule.status // 100,
                "same_target": location == rule.target,
            })
            time.sleep(0.2)
    return rows


def check_extras(local_paths):
    """Live sitemap URLs and Gatsby static files the build may lack."""
    import re

    import httpx

    static = sorted(str(p.relative_to(Path.home() / "c3/creative/websites/new_to_church/static"))
                    for p in (Path.home() / "c3/creative/websites/new_to_church/static").rglob("*") if p.is_file())
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20) as client:
        index = client.get(LIVE + "/sitemap-index.xml").text
        live_urls = []
        for loc in re.findall(r"<loc>(.*?)</loc>", index):
            live_urls += re.findall(r"<loc>(.*?)</loc>", client.get(loc).text)
        live_paths = sorted(urlsplit(u).path.rstrip("/") or "/" for u in live_urls)
        files = {}
        for name in static:
            files[name] = {"live": client.head(f"{LIVE}/{name}").status_code, "dist": (DIST / name).exists()}
            time.sleep(0.2)
    built = {p.rstrip("/") or "/" for p in local_paths}
    return {"live_sitemap_not_built": [p for p in live_paths if p not in built],
            "built_not_in_live_sitemap": sorted(built - set(live_paths)), "static_files": files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", nargs="*", help="only these paths, e.g. /about/")
    parser.add_argument("--skip-pages", action="store_true")
    parser.add_argument("--skip-redirects", action="store_true")
    args = parser.parse_args()
    setup_django()
    from pages.content import site_pages

    built = [p.url for p in site_pages()]
    # Live serves pages without the trailing slash; ask for that to skip its 301.
    paths = [(u, u.rstrip("/") or "/") for u in (args.pages or built)]
    if not args.pages:
        paths.append(("/404.html", "/parity-check-missing-page"))
    OUT.mkdir(parents=True, exist_ok=True)
    results_file = OUT / "results.json"
    results = json.loads(results_file.read_text()) if results_file.exists() else {}
    if not args.skip_pages:
        with serve_dist() as local:
            results.setdefault("pages", {}).update(check_pages(paths, local))
        results["extras"] = check_extras(built)
    if not args.skip_redirects:
        results["redirects"] = check_redirects()
    results_file.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
