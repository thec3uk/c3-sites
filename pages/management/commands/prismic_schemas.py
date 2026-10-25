"""Compare schemas/ with Prismic's custom types and slices. Read-only: GET requests only."""

import json
import re
from pathlib import Path

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

SCHEMAS_DIR = Path(settings.BASE_DIR) / "schemas"
API_URL = "https://customtypes.prismic.io"
KINDS = (("customtypes", "/customtypes"), ("slices", "/slices"))


def build_client(token: str, repository: str, transport=None) -> httpx.Client:
    headers = {"Authorization": f"Bearer {token}", "repository": repository, "User-Agent": "c3-sites prismic_schemas"}
    return httpx.Client(base_url=API_URL, headers=headers, timeout=30, transport=transport)


def make_client(token: str, repository: str) -> httpx.Client:
    return build_client(token, repository)


def fetch_live(client: httpx.Client, path: str) -> dict[str, dict]:
    response = client.get(path)
    if response.status_code != 200:
        raise CommandError(f"GET {path} returned {response.status_code}")
    return {item["id"]: item for item in response.json()}


def load_local(folder: str) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted((SCHEMAS_DIR / folder).glob("*.json"))}


def changed_paths(local, live, prefix="") -> list[str]:
    if isinstance(local, dict) and isinstance(live, dict):
        paths = []
        for key in sorted(local.keys() | live.keys()):
            here = f"{prefix}.{key}" if prefix else str(key)
            if key not in local or key not in live:
                paths.append(here)
            else:
                paths += changed_paths(local[key], live[key], here)
        return paths
    if isinstance(local, list) and isinstance(live, list) and len(local) == len(live):
        return [p for i, (a, b) in enumerate(zip(local, live)) for p in changed_paths(a, b, f"{prefix}[{i}]")]
    return [] if local == live else [prefix]


def value_at(doc, path: str):
    for key in re.findall(r"[^.\[\]]+", path):
        if isinstance(doc, list):
            doc = doc[int(key)]
        elif isinstance(doc, dict) and key in doc:
            doc = doc[key]
        else:
            return "<absent>"
    return doc


def diff_lines(kind: str, local: dict[str, dict], live: dict[str, dict], values: bool = False) -> list[tuple[str, str]]:
    """(status, line) per id; status is one of same, changed, local, live."""
    lines = []
    for id in sorted(local.keys() | live.keys()):
        name = f"{kind}/{id}"
        if id not in live:
            lines.append(("local", f"only in schemas/  {name}"))
        elif id not in local:
            lines.append(("live", f"only in Prismic  {name}"))
        elif local[id] == live[id]:
            lines.append(("same", f"same  {name}"))
        else:
            paths = changed_paths(local[id], live[id])
            line = f"changed  {name}  {', '.join(paths)}"
            if values:
                for path in paths:
                    line += f"\n  {path}\n    schemas/: {json.dumps(value_at(local[id], path))}"
                    line += f"\n    Prismic:  {json.dumps(value_at(live[id], path))}"
            lines.append(("changed", line))
    return lines


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("action", choices=("diff",))
        parser.add_argument("--values", action="store_true", help="Show both values for each changed path")

    def handle(self, *args, **options):
        token = settings.PRISMIC_CUSTOM_TYPES_API_TOKEN
        if not token:
            raise CommandError("PRISMIC_CUSTOM_TYPES_API_TOKEN is not set (see .env.example)")

        results = []
        try:
            with make_client(token, settings.PRISMIC_REPOSITORY) as client:
                for folder, path in KINDS:
                    results += diff_lines(folder, load_local(folder), fetch_live(client, path), options["values"])
        except httpx.HTTPError as exc:
            raise CommandError(f"Custom Types API request failed: {type(exc).__name__}") from exc

        for _, line in results:
            self.stdout.write(line)
        if any(status != "same" for status, _ in results):
            raise SystemExit(1)
