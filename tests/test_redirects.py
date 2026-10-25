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


def test_skips_each_bad_destination_with_its_own_message(main, caplog):
    main.append(redirect_doc("empty", {}))
    main.append(redirect_doc("gone", {"link_type": "Document", "id": "x", "type": "page", "uid": "ghost", "isBroken": True}))
    main.append(redirect_doc("unsafe", web("javascript:alert(1)")))
    main.append(redirect_doc("thec3.uk", web("https://x.example")))
    main.append(redirect_doc("ok", web("https://ok.example")))

    with caplog.at_level(logging.WARNING):
        rules = redirect_rules()

    assert [str(r) for r in rules] == ["/ok https://ok.example 301"]
    messages = {r.getMessage().split()[1]: r.getMessage() for r in caplog.records}
    assert "no destination" in messages["empty"]
    assert "destination document was deleted" in messages["gone"]
    assert "no destination" in messages["unsafe"]
    assert "redirect from the home page" in messages["thec3.uk"]


def test_unusable_rules_are_skipped_and_logged_without_affecting_others(main, caplog):
    main.append(redirect_doc("newline", web("https://a.example/x\n/admin https://evil.example 301")))
    main.append(redirect_doc("space", web("https://a.example/a b")))
    main.append(redirect_doc("bad uid", web("https://a.example")))
    main.append(redirect_doc("mail", web("mailto:a@b.example")))
    main.append(redirect_doc("good", web("https://good.example")))

    with caplog.at_level(logging.WARNING):
        rules = redirect_rules()

    assert [str(r) for r in rules] == ["/good https://good.example 301"]
    for uid in ("newline", "space", "bad uid", "mail"):
        assert f"Redirect {uid} (r-{uid}) skipped: unsafe" in caplog.text
    assert "/admin" not in redirects_text()


def test_site_relative_targets_are_allowed(main):
    main.append(redirect_doc("rel", web("/about/")))

    assert "/rel /about/ 301" in redirects_text()


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
