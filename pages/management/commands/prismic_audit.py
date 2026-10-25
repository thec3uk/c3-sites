"""List every Prismic document and redirect. Read-only: never writes to Prismic."""

import csv
import json
from datetime import UTC, datetime

import httpx
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from config.settings.sites import load_site
from content.audit import AuditRow, check_redirects, filter_rows, parse_age, audit_rows
from content.prismic_client import PrismicClient

COLUMNS = ("id", "type", "uid", "domains", "url", "target", "permanent", "tags", "created", "published")


def fetch_all_documents() -> list[dict]:
    return PrismicClient(settings.PRISMIC_REPOSITORY, settings.PRISMIC_ACCESS_TOKEN).search()


def _domain(site: str) -> str:
    try:
        return load_site(site).domain
    except ImproperlyConfigured:
        return site


def _record(row: AuditRow) -> dict:
    def cell(value):
        if isinstance(value, tuple):
            return " ".join(value)
        if isinstance(value, datetime):
            return value.date().isoformat()
        return "" if value is None else value

    return {c: cell(getattr(row, c)) for c in COLUMNS}


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--type", help="Document type, e.g. page or redirect")
        parser.add_argument("--site", help="Site name (e.g. academy) or domain (e.g. thec3.uk)")
        parser.add_argument("--untagged", action="store_true", help="Only documents with no tags")
        parser.add_argument("--since", help="Published within this age, e.g. 2w, 1m, 2mo")
        parser.add_argument("--before", help="Last published longer ago than this age")
        parser.add_argument("--check-urls", action="store_true", help="HTTP-check redirect targets")
        parser.add_argument("--format", choices=("table", "csv", "json"), default="table")

    def handle(self, *args, **options):
        try:
            since = parse_age(options["since"]) if options["since"] else None
            before = parse_age(options["before"]) if options["before"] else None
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        rows = filter_rows(
            audit_rows(fetch_all_documents()),
            now=datetime.now(UTC),
            type=options["type"],
            domain=_domain(options["site"]) if options["site"] else None,
            untagged=options["untagged"],
            since=since,
            before=before,
        )
        records = [_record(r) for r in rows]

        if options["format"] == "json":
            self.stdout.write(json.dumps(records, indent=2))
        elif options["format"] == "csv":
            writer = csv.DictWriter(self.stdout, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(records)
        else:
            self._table(records)
            self.stdout.write(f"\n{len(records)} documents")

        if options["check_urls"]:
            with httpx.Client(timeout=15, headers={"User-Agent": "c3-sites prismic_audit"}) as http:
                findings = check_redirects(rows, http)
            for finding in findings:
                self.stdout.write(f"{finding.row.url}: {finding.problem}")
            plural = "" if len(findings) == 1 else "s"
            self.stdout.write(f"{len(findings)} redirect problem{plural}")

    def _table(self, records: list[dict]) -> None:
        shown = ("type", "domains", "url", "target", "published")
        widths = {c: min(60, max([len(c)] + [len(str(r[c])) for r in records])) for c in shown}
        self.stdout.write("  ".join(c.ljust(widths[c]) for c in shown))
        for r in records:
            self.stdout.write("  ".join(str(r[c])[: widths[c]].ljust(widths[c]) for c in shown))
