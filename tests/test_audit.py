from datetime import UTC, datetime, timedelta

import httpx
import pytest

from content.audit import audit_rows, check_redirects, filter_rows, parse_age

NOW = datetime(2026, 10, 25, tzinfo=UTC)


def doc(id, type="page", uid=None, tags=(), published="2026-10-20T09:00:00+0000", **data):
    return {
        "id": id,
        "type": type,
        "uid": uid,
        "tags": list(tags),
        "first_publication_date": "2020-01-01T09:00:00+0000",
        "last_publication_date": published,
        "data": data,
    }


def redirect(id, uid, url=None, tags=("domain:thec3.uk",), **kwargs):
    destination = {"link_type": "Web", "url": url} if url else {"link_type": "Any"}
    return doc(id, type="redirect", uid=uid, tags=tags, destination=destination, permanent=True, **kwargs)


def test_rows_describe_pages_and_redirects():
    rows = audit_rows([
        doc("p", uid="about", tags=["domain:thec3.uk", "domain:myc3.life"]),
        redirect("r", "give", "https://pay.example/give"),
    ])

    page, red = rows
    assert (page.type, page.url, page.domains) == ("page", "/about/", ("thec3.uk", "myc3.life"))
    assert page.created.year == 2020 and page.published.day == 20
    assert (red.url, red.target, red.permanent) == ("/give/", "https://pay.example/give", True)


def test_document_destination_resolves_and_flags_deleted_targets():
    rows = audit_rows([
        doc("r1", type="redirect", uid="a", destination={"link_type": "Document", "type": "page", "uid": "visit"}),
        doc("r2", type="redirect", uid="b", destination={"link_type": "Document", "isBroken": True}),
    ])

    assert rows[0].target == "/visit/"
    assert rows[1].target_broken


@pytest.mark.parametrize(
    "age, delta",
    [("3d", timedelta(days=3)), ("2w", timedelta(weeks=2)), ("1m", timedelta(days=30)),
     ("2mo", timedelta(days=60)), ("1y", timedelta(days=365))],
)
def test_parse_age(age, delta):
    assert parse_age(age) == delta


def test_parse_age_rejects_nonsense():
    with pytest.raises(ValueError, match="2x"):
        parse_age("2x")


def test_filters():
    rows = audit_rows([
        doc("old", uid="old", tags=["domain:thec3.uk"], published="2025-01-01T00:00:00+0000"),
        doc("new", uid="new", tags=["domain:myc3.life"]),
        redirect("r", "r", "https://x", tags=()),
    ])

    def ids(**kw):
        return [r.id for r in filter_rows(rows, now=NOW, **kw)]

    assert ids(type="redirect") == ["r"]
    assert ids(domain="thec3.uk") == ["old"]
    assert ids(untagged=True) == ["r"]
    assert ids(since=parse_age("1m")) == ["new", "r"]
    assert ids(before=parse_age("1m")) == ["old"]


def http_returning(statuses):
    def handler(request):
        return httpx.Response(statuses.get(str(request.url), 200))

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_check_redirects_reports_problems():
    rows = audit_rows([
        redirect("ok", "ok", "https://fine.example/"),
        redirect("dead", "dead", "https://gone.example/"),
        redirect("empty", "empty"),
        redirect("hop1", "hop1", "https://www.thec3.uk/hop2/"),
        redirect("hop2", "hop2", "https://gone.example/"),
        redirect("loop1", "loop1", "/loop2/"),
        redirect("loop2", "loop2", "/loop1/"),
        doc("del", type="redirect", uid="del", tags=["domain:thec3.uk"],
            destination={"link_type": "Document", "isBroken": True}),
    ])

    findings = check_redirects(rows, http_returning({"https://gone.example/": 404}))

    by_id = {f.row.id: f.problem for f in findings}
    assert "ok" not in by_id
    assert by_id["dead"] == "target returns 404"
    assert by_id["empty"] == "no destination"
    assert by_id["hop1"] == "chain /hop1/ -> /hop2/ -> https://gone.example/ returns 404"
    assert by_id["loop1"].startswith("loop")
    assert by_id["del"] == "destination document was deleted"


def test_check_redirects_reports_unreachable_targets():
    def handler(request):
        raise httpx.ConnectError("no route")

    rows = audit_rows([redirect("x", "x", "https://down.example/")])

    findings = check_redirects(rows, httpx.Client(transport=httpx.MockTransport(handler)))

    assert findings[0].problem == "target unreachable (ConnectError)"


def test_check_uses_get_because_some_sites_404_on_head():
    def handler(request):
        return httpx.Response(404 if request.method == "HEAD" else 200)

    rows = audit_rows([redirect("b", "b", "https://brushfire.example/")])

    assert check_redirects(rows, httpx.Client(transport=httpx.MockTransport(handler))) == []


def test_blocked_targets_are_flagged_for_a_manual_check():
    rows = audit_rows([redirect("cs", "cs", "https://churchsuite.example/")])

    findings = check_redirects(rows, http_returning({"https://churchsuite.example/": 403}))

    assert findings[0].problem == "target blocked automated check (403); check by hand"
