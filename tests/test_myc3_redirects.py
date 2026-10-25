"""myc3's _redirects and sitemap.xml: the shared generators, driven by the site's tag and link rule."""

import logging
from xml.etree import ElementTree

from pages.redirects import redirect_rules, redirects_text, shadowed_sources

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
TAG = "domain:myc3.life"


def doc(type, uid, tags=(TAG,), **data):
    return {"id": f"{type}-{uid}", "type": type, "uid": uid, "tags": list(tags), "data": data}


def redirect(uid, destination, permanent=True, tags=(TAG,)):
    return doc("redirect", uid, tags, destination=destination, permanent=permanent)


def web(url):
    return {"link_type": "Web", "url": url}


def page(uid, tags=(TAG,)):
    return doc("page", uid, tags, seo_title=None, background_image={}, body=[])


def test_redirects_get_uppercase_twins(myc3):
    myc3.append(redirect("give", web("https://pay.example/give")))

    assert redirects_text() == "/give https://pay.example/give 301\n/GIVE https://pay.example/give 301\n"


def test_permanent_decides_301_or_302(myc3):
    myc3.append(redirect("yes", web("https://a.example"), permanent=True))
    myc3.append(redirect("no", web("https://b.example"), permanent=False))

    assert [str(r) for r in redirect_rules()] == ["/yes https://a.example 301", "/no https://b.example 302"]


def test_document_destinations_follow_the_next_resolver(myc3):
    myc3.append(redirect("old", {"link_type": "Document", "id": "x", "type": "page", "uid": "thec3.uk_about"}))
    myc3.append(redirect("chain", {"link_type": "Document", "id": "y", "type": "redirect", "uid": "give"}))
    myc3.append(redirect("data", {"link_type": "Document", "id": "z", "type": "site_config", "uid": None}))

    assert [str(r) for r in redirect_rules()] == [
        "/old /thec3.uk_about/ 301",
        "/chain /give/ 301",
        "/data / 301",
    ]


def test_unsafe_redirects_are_skipped_and_logged_with_a_reason(myc3, caplog):
    myc3.append(redirect("empty", {}))
    myc3.append(redirect("space", web("https://a.example/a b")))
    myc3.append(redirect("proto", web("//evil.example")))
    myc3.append(redirect("mail", web("mailto:a@b.example")))
    myc3.append(redirect("myc3", web("https://x.example")))
    myc3.append(redirect("ok", web("/ok/")))

    with caplog.at_level(logging.WARNING):
        rules = redirect_rules()

    assert [str(r) for r in rules] == ["/ok /ok/ 301"]
    for uid, reason in (("empty", "no destination"), ("space", "unsafe"), ("proto", "unsafe"), ("mail", "unsafe"),
                        ("myc3", "redirect from the home page")):
        assert f"Redirect {uid} (redirect-{uid}) skipped: {reason}" in caplog.text


def test_a_redirect_sharing_a_page_path_is_reported_so_the_page_wins(myc3, client, caplog):
    myc3.append(page("alpha"))
    myc3.append(redirect("alpha", web("https://elsewhere.example")))
    myc3.append(redirect("give", web("https://pay.example")))

    assert shadowed_sources() == ["/alpha"]
    with caplog.at_level(logging.WARNING):
        client.get("/_redirects")
    assert "Redirect /alpha is also a built page" in caplog.text


def test_sitemap_lists_every_page_but_no_redirects_or_404(myc3, client):
    myc3.append(page("myc3"))
    myc3.append(page("growth-path"))
    myc3.append(page("thec3.uk_about", tags=(TAG, "domain:thec3.uk")))
    myc3.append(redirect("give", web("https://pay.example")))

    response = client.get("/sitemap.xml")

    urls = [e.text for e in ElementTree.fromstring(response.content).findall("s:url/s:loc", NS)]
    assert urls == [
        "https://myc3.life/",
        "https://myc3.life/growth-path/",
        "https://myc3.life/thec3.uk_about/",
    ]
