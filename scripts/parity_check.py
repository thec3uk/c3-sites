"""Compare a site built in dist/ with its live site, page by page, plus every redirect.

Run after `just build <site>`:
    SITE=myc3 uv run python scripts/parity_check.py --out docs/plans/phase-4/evidence/m4 \
        [--live https://myc3.life] [--static ~/c3/creative/websites/myc3/public] [--live-sitemap /sitemap.xml] \
        [--pages /team/ ...] [--skip-pages] [--skip-redirects]
    Main: --live-sitemap /sitemap-index.xml --static ~/c3/creative/websites/new_to_church/static
    uv run python scripts/parity_check.py --classify-only docs/plans/phase-3/evidence/m5/results.json

Writes screenshots and results.json to --out. Read-only and sequential: plain Playwright and httpx
with an honest user agent, redirects checked once each without following.
"""

import argparse
import base64
import difflib
import json
import os
import re
import sys
import threading
import time
from collections import Counter
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
# Phase 3's evidence/m2/screenshots.py imports this; other runs take the site's live base.
LIVE = "https://thec3.uk"
USER_AGENT = "c3-sites parity-check"
WIDTHS = ((1440, 900), (390, 844))
GAP = 0.2  # seconds between live requests
NOT_FOUND_PATH = "/404.html"

# Classifier thresholds, chosen to reproduce Phase 3's hand labels (see tests).
MATCH_MAX_RATIO = 0.003  # share of differing pixels, at each width
MINOR_MAX_RATIO = 0.05
MINOR_MAX_HEIGHT_PX = 2  # page height difference, at each width
# Hidden form text (a listbox label) can differ by a line with nothing visible.
MAX_LIVE_ONLY_TEXT_LINES = 1


def live_base(site):
    return f"https://{site.domain}"


def site_hosts(site, local):
    return {site.domain, f"www.{site.domain}", urlsplit(local).netloc}


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


def block_analytics(context, site):
    # Keep parity runs out of Umami's numbers, live and local.
    host = urlsplit(site.umami_src).netloc
    if host:
        context.route(f"**/{host}/**", lambda route: route.abort())


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
        // Hidden lazy images never load, so wait only for visible ones, at most 10s.
        const pending = [...document.images].filter(i => !i.complete && i.offsetParent !== null)
            .map(i => new Promise(r => { i.addEventListener('load', r); i.addEventListener('error', r); }));
        await Promise.race([Promise.all(pending), new Promise(r => setTimeout(r, 10000))]);
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
    const jpeg = async c => { const blob = await c.convertToBlob({type: 'image/jpeg', quality: 0.5});
        const buf = new Uint8Array(await blob.arrayBuffer()); let s = '';
        for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
        return btoa(s); };
    // Desktop shots saved at half size to keep the evidence small; the diff is done at full size.
    const whole = async i => { const s = i.width > 1000 ? 0.5 : 1;
        const c = new OffscreenCanvas(Math.round(i.width * s), Math.round(i.height * s));
        c.getContext('2d').drawImage(i, 0, 0, c.width, c.height); return jpeg(c); };
    return {live_height: ia.height, local_height: ib.height, ratio: total / (w * h),
            bands, live_jpeg: await whole(ia), local_jpeg: await whole(ib), diff_jpeg: await jpeg(diff)};
}"""


def compare_images(tool_page, live_png, local_png, stem, out):
    uri = lambda png: "data:image/png;base64," + base64.b64encode(png).decode()  # noqa: E731
    result = tool_page.evaluate(DIFF_JS, [uri(live_png), uri(local_png)])
    result["ratio"] = round(result["ratio"], 4)
    # A diff image only where there is something to see; keeps the evidence small.
    keep_diff = result["ratio"] > 0.002 or result["live_height"] != result["local_height"]
    for kind in ("live", "local", "diff"):
        data = base64.b64decode(result.pop(f"{kind}_jpeg"))
        if kind != "diff" or keep_diff:
            (out / f"{stem}-{kind}.jpg").write_bytes(data)
    return result


def unreachable_facts(url, error, client=None):
    """Facts for a live page the browser couldn't load, e.g. a redirect to a site that refuses bots."""
    with client or http_client() as client:
        response = client.get(url, follow_redirects=False)
    return {"title": "", "description": [], "canonical": [], "links": [], "text": "",
            "status": [response.status_code], "final_url": response.headers.get("location", url),
            "error": str(error).splitlines()[0]}


def check_pages(paths, local, live, site, out):
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    hosts = site_hosts(site, local)
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tool = browser.new_page()
        tool.set_content("<!doctype html><title>diff</title>")
        for width, height in WIDTHS:
            context = browser.new_context(viewport={"width": width, "height": height}, user_agent=USER_AGENT)
            block_analytics(context, site)
            page = context.new_page()
            for path, live_path in paths:
                name = path.strip("/") or "home"
                row = results.setdefault(name, {"path": path})
                shots = {}
                for side, url in (("live", live + live_path), ("local", local + path)):
                    try:
                        response, facts = load(page, url), None
                    except PlaywrightError as error:
                        if side == "local":
                            raise
                        # Compared with a blank page; the redirect check covers where it goes.
                        facts = unreachable_facts(url, error)
                        page.set_content("<!doctype html><title></title>")
                    if width == 1440:
                        if facts is None:
                            facts = page.evaluate(FACTS_JS)
                            facts["links"] = [normalise_link(h, hosts) for h in facts["links"]]
                            facts["status"] = statuses(response) if response else [None]
                            facts["final_url"] = page.url.replace(local, "")
                        row[side] = facts
                    shots[side] = page.screenshot(full_page=True)
                row[f"shots_{width}"] = compare_images(tool, shots["live"], shots["local"], f"{name}-{width}", out)
                print(name, width, row[f"shots_{width}"]["ratio"], flush=True)
            context.close()
        browser.close()
    for row in results.values():
        live_facts, local_facts = row.pop("live"), row.pop("local")
        row["status"] = {"live": live_facts["status"], "local": local_facts["status"]}
        for key in ("title", "description", "canonical", "final_url"):
            row[key] = {"live": live_facts[key], "local": local_facts[key]}
        if "error" in live_facts:
            row["live_error"] = live_facts["error"]
        lc, kc = Counter(live_facts["links"]), Counter(local_facts["links"])
        row["links"] = {"count": {"live": len(live_facts["links"]), "local": len(local_facts["links"])},
                        "only_live": sorted((lc - kc).elements()), "only_local": sorted((kc - lc).elements()),
                        "missing": sorted(set(lc) - set(kc))}
        split = lambda t: [line.strip() for line in t.splitlines() if line.strip()]  # noqa: E731
        row["text_diff"] = [d for d in difflib.ndiff(split(live_facts["text"]), split(local_facts["text"]))
                            if d[:1] in "+-"]
    return results


def classify(row):
    """(status, reasons) for a page row: match, minor or differs."""
    differs, minor = [], []
    live_status, local_status = row["status"]["live"], row["status"]["local"]
    if row["path"] == NOT_FOUND_PATH:
        # The script's file server sends 404.html as 200; Netlify sends it as 404.
        if live_status[-1:] != [404] or local_status != [200]:
            differs.append(f"status live {live_status}, local {local_status}")
    elif [s and s // 100 for s in live_status] != [s and s // 100 for s in local_status]:
        differs.append(f"status live {live_status}, local {local_status}")
    for width in (1440, 390):
        shot = row[f"shots_{width}"]
        height = abs(shot["live_height"] - shot["local_height"])
        if height > MINOR_MAX_HEIGHT_PX:
            differs.append(f"{width}: height differs by {height}px")
        elif height:
            minor.append(f"{width}: height differs by {height}px")
        if shot["ratio"] > MINOR_MAX_RATIO:
            differs.append(f"{width}: {shot['ratio']:.2%} of pixels differ")
        elif shot["ratio"] > MATCH_MAX_RATIO:
            minor.append(f"{width}: {shot['ratio']:.2%} of pixels differ")
    links = row["links"]
    own = row["path"].rstrip("/") or "/"
    # Phase 3 rows lack "missing"; their only_live also counts fewer links to the same target.
    missing = [link for link in links.get("missing", links["only_live"]) if link != own]
    if missing:
        differs.append(f"live links the build lacks: {missing}")
    live_only_text = [line[2:] for line in row["text_diff"] if line.startswith("- ")]
    if len(live_only_text) > MAX_LIVE_ONLY_TEXT_LINES:
        differs.append(f"{len(live_only_text)} lines of text only on live")
    if differs:
        return "differs", differs + minor
    return ("minor", minor) if minor else ("match", [])


def same_target(target, location, live):
    """Same URL, treating a bare domain with and without its trailing / as one."""
    def norm(url):
        parts = urlsplit(urljoin(live + "/", url))
        return parts._replace(path=parts.path or "/").geturl()

    return norm(target) == norm(location)


PERMANENT, TEMPORARY = {301, 308}, {302, 303, 307}


def redirect_class(status):
    """'permanent', 'temporary', or the status itself for anything else."""
    return "permanent" if status in PERMANENT else "temporary" if status in TEMPORARY else status


def http_client():
    import httpx

    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20)


def check_redirects(rules, live, client=None, gap=GAP, page_paths=()):
    """Each generated rule's source on live, once, without following."""
    import httpx

    built = {p.rstrip("/") or "/" for p in page_paths}
    rows = []
    with client or http_client() as client:
        for rule in rules:
            try:
                response = client.get(live + rule.source, follow_redirects=False)
                live_status, location = response.status_code, response.headers.get("location", "")
            except httpx.HTTPError as error:
                live_status, location = None, f"error: {error}"
            rows.append({
                "source": rule.source, "target": rule.target, "status": rule.status,
                "live_status": live_status, "live_location": location,
                "same_class": live_status is not None and redirect_class(live_status) == redirect_class(rule.status),
                "same_target": live_status is not None and same_target(rule.target, location, live),
                "build_serves_page": rule.source in built,
            })
            time.sleep(gap)
    return rows


def sitemap_urls(client, url, gap):
    """Page URLs in a sitemap, following a sitemap index; (status, urls)."""
    response = client.get(url)
    if response.status_code != 200:
        return response.status_code, []
    urls = []
    for loc in re.findall(r"<loc>(.*?)</loc>", response.text):
        if "<sitemapindex" in response.text:
            time.sleep(gap)
            urls += sitemap_urls(client, loc, gap)[1]
        else:
            urls.append(loc)
    return response.status_code, urls


def check_extras(local_paths, live, client=None, gap=GAP, static_dir=None, sitemap="/sitemap.xml", dist=DIST):
    """Live sitemap URLs, and the old site's static files, that the build may lack."""
    extras = {}
    with client or http_client() as client:
        status, live_urls = sitemap_urls(client, live + sitemap, gap)
        live_paths = sorted(urlsplit(u).path.rstrip("/") or "/" for u in live_urls)
        built = {p.rstrip("/") or "/" for p in local_paths}
        extras = {"live_sitemap": sitemap, "live_sitemap_status": status,
                  "live_sitemap_not_built": [p for p in live_paths if p not in built],
                  "built_not_in_live_sitemap": sorted(built - set(live_paths)) if live_paths else []}
        if static_dir:
            files = {}
            for path in sorted(p for p in Path(static_dir).rglob("*") if p.is_file()):
                name = path.relative_to(static_dir).as_posix()
                files[name] = {"live": client.head(f"{live}/{name}").status_code, "dist": (Path(dist) / name).exists()}
                time.sleep(gap)
            extras["static_files"] = files
    return extras


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, help="evidence folder for screenshots and results.json")
    parser.add_argument("--live", help="live base URL; default https://<site domain>")
    parser.add_argument("--static", type=Path, help="the old site's static folder, checked file by file on live")
    parser.add_argument("--live-sitemap", default="/sitemap.xml", help="path of live's sitemap or sitemap index")
    parser.add_argument("--pages", nargs="*", help="only these paths, e.g. /about/")
    parser.add_argument("--skip-pages", action="store_true")
    parser.add_argument("--skip-redirects", action="store_true")
    parser.add_argument("--classify-only", type=Path, metavar="RESULTS", help="print labels for a results.json")
    args = parser.parse_args()
    if args.classify_only:
        for name, row in json.loads(args.classify_only.read_text())["pages"].items():
            print(row["path"], *classify(row))
        return
    if not args.out:
        parser.error("--out is required")
    setup_django()
    from django.conf import settings

    from pages.content import site_pages
    from pages.redirects import redirect_rules

    site = settings.SITE
    live = (args.live or live_base(site)).rstrip("/")
    built = [p.url for p in site_pages()]
    # Live serves pages without the trailing slash; ask for that to skip its redirect.
    paths = [(u, u.rstrip("/") or "/") for u in (args.pages or built)]
    if not args.pages:
        paths.append((NOT_FOUND_PATH, "/parity-check-missing-page"))
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    results_file = out / "results.json"
    results = json.loads(results_file.read_text()) if results_file.exists() else {}
    results["site"], results["live"] = site.name, live
    if not args.skip_pages:
        with serve_dist() as local:
            results.setdefault("pages", {}).update(check_pages(paths, local, live, site, out))
        results["extras"] = check_extras(built, live, static_dir=args.static, sitemap=args.live_sitemap)
    for row in results.get("pages", {}).values():
        row["classification"], row["reasons"] = classify(row)
    if not args.skip_redirects:
        results["redirects"] = check_redirects(redirect_rules(), live, page_paths=built)
    results_file.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
