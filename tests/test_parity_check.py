import json
from pathlib import Path

import httpx
import pytest

from config.settings.sites import load_site
from pages.redirects import Rule
from scripts.parity_check import (
    check_extras,
    check_redirects,
    classify,
    live_base,
    normalise_link,
    same_target,
    site_hosts,
)

HOSTS = {"thec3.uk", "127.0.0.1:8000"}
PHASE_3 = Path(__file__).resolve().parents[1] / "docs/plans/phase-3/evidence/m5/results.json"


def test_same_site_links_compare_without_trailing_slash():
    assert normalise_link("https://thec3.uk/about", HOSTS) == "/about"
    assert normalise_link("http://127.0.0.1:8000/about/", HOSTS) == "/about"
    assert normalise_link("http://127.0.0.1:8000/", HOSTS) == "/"


def test_query_and_fragment_kept():
    assert normalise_link("https://thec3.uk/contact/?a=1#form", HOSTS) == "/contact?a=1#form"


def test_other_sites_unchanged():
    assert normalise_link("https://prayer.thec3.uk/", HOSTS) == "https://prayer.thec3.uk/"


def test_live_base_and_hosts_come_from_the_site_config():
    site = load_site("myc3")
    assert live_base(site) == "https://myc3.life"
    assert site_hosts(site, "http://127.0.0.1:9000") == {"myc3.life", "www.myc3.life", "127.0.0.1:9000"}


# classify


def row(ratio_1440=0.0, ratio_390=0.0, heights=((1000, 1000), (2000, 2000)), path="/about/", **extra):
    (l1, k1), (l2, k2) = heights
    base = {
        "path": path,
        "shots_1440": {"live_height": l1, "local_height": k1, "ratio": ratio_1440},
        "shots_390": {"live_height": l2, "local_height": k2, "ratio": ratio_390},
        "status": {"live": [200], "local": [200]},
        "links": {"count": {"live": 1, "local": 1}, "only_live": [], "only_local": [], "missing": []},
        "text_diff": [],
    }
    return base | extra


def test_identical_page_matches():
    assert classify(row(0.002, 0.0019)) == ("match", [])


def test_resampled_photos_are_minor():
    status, reasons = classify(row(0.0043, 0.0))
    assert status == "minor"
    assert reasons


def test_a_pixel_of_height_is_minor_and_more_than_two_differs():
    assert classify(row(heights=((1000, 1001), (2000, 2000))))[0] == "minor"
    assert classify(row(heights=((1000, 1000), (2000, 2002))))[0] == "minor"
    assert classify(row(heights=((1000, 1003), (2000, 2000))))[0] == "differs"


def test_large_pixel_difference_differs():
    assert classify(row(0.0, 0.06))[0] == "differs"


def test_status_class_difference_differs():
    status, reasons = classify(row(status={"live": [500], "local": [200]}))
    assert status == "differs"
    assert any("500" in r for r in reasons)


def test_live_redirect_where_the_build_serves_a_page_differs():
    assert classify(row(status={"live": [307, 200], "local": [200]}))[0] == "differs"


def test_404_page_is_expected_to_be_404_live_and_200_from_the_file_server():
    assert classify(row(path="/404.html", status={"live": [404], "local": [200]}))[0] == "match"
    assert classify(row(path="/404.html", status={"live": [500], "local": [200]}))[0] == "differs"


def test_live_link_target_missing_from_the_build_differs():
    links = {"only_live": ["/www.church-online.uk"], "only_local": [], "missing": ["/www.church-online.uk"]}
    assert classify(row(links=links))[0] == "differs"


def test_fewer_links_to_the_same_target_or_a_self_link_dont_count():
    links = {"only_live": ["/visionandvalues", "/about"], "only_local": [], "missing": ["/about"]}
    assert classify(row(links=links)) == ("match", [])


def test_text_only_on_live_differs_beyond_one_line():
    assert classify(row(text_diff=["- Category", "+ General Enquiry"]))[0] == "match"
    assert classify(row(text_diff=["- Category", "- Welcome"]))[0] == "differs"


def test_reclassifies_phase_3_with_one_known_mismatch():
    pages = json.loads(PHASE_3.read_text())["pages"]
    labels = {r["path"]: classify(r)[0] for r in pages.values()}
    minor = {"/about/", "/bury/", "/c3-groups/", "/cambridge-west/", "/cambridge/", "/giving/",
             "/online/", "/ourleaders/", "/shaping/", "/team/"}
    expected = {p: "minor" if p in minor else "match" for p in labels} | {"/colchester/": "differs"}
    # Phase 3 rows lack links.missing, so trustees' duplicate link looks missing.
    assert {p for p in labels if labels[p] != expected[p]} == {"/trustees/"}


# redirects


def test_bare_domain_with_and_without_slash_is_the_same_target():
    live = "https://thec3.uk"
    assert same_target("https://store.thec3.uk", "https://store.thec3.uk/", live)
    assert same_target("https://store.thec3.uk/", "https://store.thec3.uk", live)
    assert not same_target("https://a.example/x", "https://a.example/x/", live)
    assert not same_target("https://a.example/", "https://b.example/", live)


def test_site_path_target_matches_live_absolute_or_relative_location():
    live = "https://myc3.life"
    assert same_target("/about/", "/about/", live)
    assert same_target("/about/", "https://myc3.life/about/", live)
    assert not same_target("/about/", "/about", live)


def mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_check_redirects_compares_class_and_target_without_following():
    seen = []

    def handler(request):
        seen.append(request)
        locations = {"/a": (308, "https://x.example"), "/b": (307, "https://wrong.example/")}
        status, location = locations[request.url.path]
        return httpx.Response(status, headers={"location": location})

    rules = [Rule("/a", "https://x.example/", 301), Rule("/b", "https://y.example/", 301)]
    rows = check_redirects(rules, "https://myc3.life", client=mock_client(handler), gap=0)
    assert [r["same_class"] for r in rows] == [True, False]
    assert [r["same_target"] for r in rows] == [True, False]
    assert rows[0]["live_status"] == 308
    assert [str(r.url) for r in seen] == ["https://myc3.life/a", "https://myc3.life/b"]


def test_check_redirects_marks_sources_the_build_serves_as_pages():
    rows = check_redirects([Rule("/alpha", "https://x.example/", 302)], "https://myc3.life",
                           client=mock_client(lambda r: httpx.Response(307, headers={"location": "https://x.example/"})),
                           gap=0, page_paths={"/alpha/"})
    assert rows[0]["build_serves_page"] is True


def test_check_redirects_records_network_errors():
    def handler(request):
        raise httpx.ConnectError("down")

    rows = check_redirects([Rule("/a", "/b/", 302)], "https://myc3.life", client=mock_client(handler), gap=0)
    assert rows[0]["live_status"] is None
    assert rows[0]["same_class"] is False


# extras


def test_check_extras_reads_the_static_folder_argument(tmp_path):
    static, dist = tmp_path / "public", tmp_path / "dist"
    (static / "img").mkdir(parents=True)
    (static / "favicon.ico").write_text("x")
    (static / "img" / "a.png").write_text("x")
    dist.mkdir()
    (dist / "favicon.ico").write_text("x")

    def handler(request):
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text="<urlset><url><loc>https://myc3.life/team</loc></url></urlset>")
        return httpx.Response(200 if request.url.path == "/favicon.ico" else 404)

    extras = check_extras(["/", "/team/"], "https://myc3.life", client=mock_client(handler), gap=0,
                          static_dir=static, dist=dist)
    assert extras["static_files"] == {"favicon.ico": {"live": 200, "dist": True},
                                      "img/a.png": {"live": 404, "dist": False}}
    assert extras["live_sitemap_not_built"] == []
    assert extras["built_not_in_live_sitemap"] == ["/"]


def test_check_extras_follows_a_sitemap_index_and_tolerates_none(tmp_path):
    def handler(request):
        pages = {"/sitemap-index.xml": "<sitemapindex><sitemap><loc>https://x/sitemap-0.xml</loc></sitemap></sitemapindex>",
                 "/sitemap-0.xml": "<urlset><url><loc>https://x/page</loc></url></urlset>"}
        text = pages.get(request.url.path)
        return httpx.Response(200, text=text) if text else httpx.Response(404, text="Not found")

    found = check_extras(["/"], "https://x", client=mock_client(handler), gap=0,
                         sitemap="/sitemap-index.xml", dist=tmp_path)
    assert found["live_sitemap_not_built"] == ["/page"]
    missing = check_extras(["/"], "https://x", client=mock_client(handler), gap=0, dist=tmp_path)
    assert missing["live_sitemap_status"] == 404
    assert missing["live_sitemap_not_built"] == []
    assert "static_files" not in missing


@pytest.mark.parametrize("text", ["", "<html>no sitemap</html>"])
def test_check_extras_with_a_non_xml_sitemap_finds_no_urls(tmp_path, text):
    client = mock_client(lambda r: httpx.Response(200, text=text))
    assert check_extras(["/"], "https://x", client=client, gap=0, dist=tmp_path)["live_sitemap_not_built"] == []
