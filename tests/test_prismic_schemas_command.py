import io
import json
from pathlib import Path

import httpx
import pytest
from django.core.management import CommandError, call_command

from pages.management.commands import prismic_schemas

TYPE = {"id": "page", "label": "Page", "repeatable": True, "status": True, "json": {"Main": {"uid": {"type": "UID"}}}}
SLICE = {"id": "text", "type": "SharedSlice", "name": "Text", "variations": [{"id": "default"}]}


@pytest.fixture
def schemas(tmp_path, monkeypatch):
    for folder, item in (("customtypes", TYPE), ("slices", SLICE)):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / f"{item['id']}.json").write_text(json.dumps(item, indent=2))
    monkeypatch.setattr(prismic_schemas, "SCHEMAS_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def live(monkeypatch, settings):
    settings.PRISMIC_CUSTOM_TYPES_API_TOKEN = "secret-token"
    settings.PRISMIC_REPOSITORY = "thec3"
    state = {"types": [TYPE], "slices": [SLICE], "requests": []}

    def handler(request):
        state["requests"].append(request)
        body = state["types"] if request.url.path == "/customtypes" else state["slices"]
        return httpx.Response(200, json=body)

    monkeypatch.setattr(
        prismic_schemas, "make_client", lambda token, repo: prismic_schemas.build_client(token, repo, httpx.MockTransport(handler))
    )
    return state


def run(*args):
    out = io.StringIO()
    try:
        call_command("prismic_schemas", *args, stdout=out)
        code = 0
    except SystemExit as exc:
        code = exc.code
    return code, out.getvalue()


def test_all_same_exits_zero(schemas, live):
    code, out = run("diff")

    assert code == 0
    assert "same  customtypes/page" in out and "same  slices/text" in out


def test_key_order_is_ignored(schemas, live):
    live["types"] = [dict(reversed(list(TYPE.items())))]

    assert run("diff")[0] == 0


def test_changed_lists_field_paths(schemas, live):
    live["types"] = [{**TYPE, "label": "Other", "json": {"Main": {"uid": {"type": "Text"}}}}]

    code, out = run("diff")

    assert code == 1
    assert "changed  customtypes/page" in out
    assert "label" in out and "json.Main.uid.type" in out


def test_only_in_either_side(schemas, live):
    live["slices"] = [{**SLICE, "id": "extra"}]

    code, out = run("diff")

    assert code == 1
    assert "only in schemas/  slices/text" in out
    assert "only in Prismic  slices/extra" in out


def test_requests_are_gets_with_auth_and_honest_agent(schemas, live):
    run("diff")

    assert {r.url.path for r in live["requests"]} == {"/customtypes", "/slices"}
    for r in live["requests"]:
        assert r.method == "GET"
        assert r.headers["Authorization"] == "Bearer secret-token"
        assert r.headers["repository"] == "thec3"
        assert r.headers["User-Agent"] == "c3-sites prismic_schemas"


def test_token_never_printed(schemas, live):
    assert "secret-token" not in run("diff")[1]


def test_missing_token_is_a_clear_error(schemas, settings):
    settings.PRISMIC_CUSTOM_TYPES_API_TOKEN = ""

    with pytest.raises(CommandError, match="PRISMIC_CUSTOM_TYPES_API_TOKEN"):
        call_command("prismic_schemas", "diff")


def test_api_error_is_reported_without_token(schemas, live, monkeypatch):
    monkeypatch.setattr(
        prismic_schemas,
        "make_client",
        lambda token, repo: prismic_schemas.build_client(token, repo, httpx.MockTransport(lambda r: httpx.Response(401))),
    )

    with pytest.raises(CommandError, match="401") as exc:
        call_command("prismic_schemas", "diff")
    assert "secret-token" not in str(exc.value)


def test_no_write_methods():
    source = Path(prismic_schemas.__file__).read_text()
    for verb in (".post(", ".put(", ".delete(", ".patch("):
        assert verb not in source


def test_values_flag_shows_both_sides(schemas, live):
    live["types"] = [{**TYPE, "label": "Other"}]

    out = run("diff", "--values")[1]

    assert 'schemas/: "Page"' in out and 'Prismic:  "Other"' in out
