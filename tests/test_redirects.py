import logging

from config.urls import urlpatterns
from pages import content
from pages.redirects import redirect_rules, redirects_text, shadowed_sources


def redirect_doc(uid, destination, permanent=True, tags=("domain:thec3.uk",)):
    return {
        "id": f"r-{uid}",
        "type": "redirect",
        "uid": uid,
        "tags": list(tags),
        "data": {"destination": destination, "permanent": permanent},
    }


def web(url):
    return {"link_type": "Web", "url": url}


def test_web_destination_becomes_a_301_with_an_uppercase_twin(main):
    main.append(redirect_doc("give", web("https://pay.example/give")))

    assert redirects_text().splitlines()[-2:] == [
        "/give https://pay.example/give 301",
        "/GIVE https://pay.example/give 301",
    ]


def test_not_permanent_is_a_302(main):
    main.append(redirect_doc("gls", web("https://gls.example"), permanent=False))

    assert "/gls https://gls.example 302" in redirects_text()


def test_document_destination_uses_the_sites_uid_convention(main):
    main.append(
        redirect_doc("about-us", {"link_type": "Document", "id": "x", "type": "page", "uid": "thec3.uk_about"})
    )

    assert "/about-us /about/ 301" in redirects_text()


def test_skips_missing_and_deleted_destinations_and_logs_them(main, caplog):
    main.append(redirect_doc("empty", {}))
    main.append(redirect_doc("gone", {"link_type": "Document", "id": "x", "type": "page", "isBroken": True}))
    main.append(redirect_doc("unsafe", web("javascript:alert(1)")))

    with caplog.at_level(logging.WARNING):
        rules = redirect_rules()

    assert rules == []
    for uid in ("empty", "gone", "unsafe"):
        assert f"Redirect {uid} " in caplog.text


def test_uppercase_twin_is_not_repeated_when_case_is_irrelevant(main):
    main.append(redirect_doc("4", web("https://x.example")))

    assert redirects_text().count("/4 ") == 1


def test_sources_matching_a_built_page_are_reported(main):
    main.append(redirect_doc("about", web("https://x.example")))
    main.append(redirect_doc("give", web("https://x.example")))

    assert shadowed_sources() == ["/about"]


def test_no_redirects_gives_an_empty_file(main):
    assert redirects_text() == ""


def test_route_writes_underscore_redirects_as_plain_text():
    pattern = next(p for p in urlpatterns if p.name == "redirects")

    assert pattern.distill_file == "_redirects"


def test_view_serves_text_plain(main, client):
    main.append(redirect_doc("give", web("https://pay.example/give")))

    response = client.get("/_redirects")

    assert response["Content-Type"].startswith("text/plain")
    assert "/give https://pay.example/give 301" in response.content.decode()
