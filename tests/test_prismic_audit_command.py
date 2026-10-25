import csv
import io
import json

import pytest
from django.core.management import CommandError, call_command

from pages.management.commands import prismic_audit
from tests.test_audit import doc, redirect


@pytest.fixture(autouse=True)
def documents(monkeypatch):
    docs = [
        doc("p", uid="about", tags=["domain:thec3.uk"]),
        doc("a", type="academy_page", uid="academy", tags=["domain:thec3.academy"]),
        redirect("r", "give", "https://pay.example/give"),
    ]
    monkeypatch.setattr(prismic_audit, "fetch_all_documents", lambda: docs)


def run(*args):
    out = io.StringIO()
    call_command("prismic_audit", *args, stdout=out)
    return out.getvalue()


def test_table_lists_every_document():
    output = run()

    assert "/about/" in output and "/give/" in output and "https://pay.example/give" in output
    assert "3 documents" in output


def test_csv_has_header_and_rows():
    rows = list(csv.DictReader(io.StringIO(run("--format", "csv"))))

    assert [r["url"] for r in rows] == ["/about/", "/", "/give/"]
    assert rows[0]["domains"] == "thec3.uk"


def test_json_filters_by_type():
    rows = json.loads(run("--type", "redirect", "--format", "json"))

    assert [r["id"] for r in rows] == ["r"]
    assert rows[0]["target"] == "https://pay.example/give"


def test_site_accepts_a_site_name_or_domain():
    by_name = json.loads(run("--site", "academy", "--format", "json"))
    by_domain = json.loads(run("--site", "thec3.uk", "--format", "json"))

    assert [r["id"] for r in by_name] == ["a"]
    assert [r["id"] for r in by_domain] == ["p", "r"]


def test_bad_age_is_a_command_error():
    with pytest.raises(CommandError, match="2x"):
        run("--since", "2x")


def test_check_urls_prints_findings(monkeypatch):
    from content.audit import Finding

    monkeypatch.setattr(
        prismic_audit, "check_redirects",
        lambda rows, http: [Finding(rows[-1], "target returns 404")],
    )

    output = run("--check-urls")

    assert "/give/: target returns 404" in output
    assert "1 redirect problem" in output
