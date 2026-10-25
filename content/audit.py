"""Read-only audit of every Prismic document and redirect (Phase 6 cleanup)."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlsplit

import httpx

from content.prismic_client import resolve_link

DOMAIN_TAG = "domain:"
AGE_UNITS = {"d": 1, "w": 7, "m": 30, "mo": 30, "y": 365}
# Bot protection answers these, so the link may still work for people.
BLOCKED_STATUSES = {401, 403, 429}


@dataclass(frozen=True)
class AuditRow:
    id: str
    type: str
    uid: str | None
    tags: tuple[str, ...]
    domains: tuple[str, ...]
    url: str
    created: datetime | None
    published: datetime | None
    target: str = ""
    target_broken: bool = False
    permanent: bool | None = None


@dataclass(frozen=True)
class Finding:
    row: AuditRow
    problem: str


def _date(value: str | None) -> datetime | None:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z") if value else None


def audit_rows(documents: list[dict]) -> list[AuditRow]:
    rows = []
    for d in documents:
        tags = tuple(d.get("tags") or ())
        destination = d["data"].get("destination") or {}
        is_redirect = d["type"] == "redirect"
        rows.append(
            AuditRow(
                id=d["id"],
                type=d["type"],
                uid=d.get("uid"),
                tags=tags,
                domains=tuple(t.removeprefix(DOMAIN_TAG) for t in tags if t.startswith(DOMAIN_TAG)),
                url=resolve_link(d),
                created=_date(d.get("first_publication_date")),
                published=_date(d.get("last_publication_date")),
                target=resolve_link(destination) if is_redirect else "",
                target_broken=bool(destination.get("isBroken")),
                permanent=d["data"].get("permanent") if is_redirect else None,
            )
        )
    return rows


def parse_age(age: str) -> timedelta:
    """'3d', '2w', '1m' or '2mo' (30-day months), '1y'."""
    match = re.fullmatch(r"(\d+)(d|w|mo|m|y)", age)
    if not match:
        raise ValueError(f"Can't read age '{age}'; use e.g. 3d, 2w, 1m, 2mo, 1y")
    return timedelta(days=int(match[1]) * AGE_UNITS[match[2]])


def filter_rows(
    rows: list[AuditRow],
    *,
    now: datetime,
    type: str | None = None,
    domain: str | None = None,
    untagged: bool = False,
    since: timedelta | None = None,
    before: timedelta | None = None,
) -> list[AuditRow]:
    def keep(row: AuditRow) -> bool:
        if type and row.type != type:
            return False
        if domain and domain not in row.domains:
            return False
        if untagged and row.tags:
            return False
        if since and (not row.published or row.published < now - since):
            return False
        if before and (not row.published or row.published >= now - before):
            return False
        return True

    return [r for r in rows if keep(r)]


def _internal_path(target: str, domains: tuple[str, ...]) -> str | None:
    """The path if the target points back at one of the row's own domains."""
    parts = urlsplit(target)
    if not parts.netloc:
        return parts.path or "/"
    if parts.netloc.removeprefix("www.") in domains:
        return parts.path or "/"
    return None


class _Checker:
    def __init__(self, http: httpx.Client):
        self.http = http
        self.cache: dict[str, str | None] = {}

    def problem(self, url: str) -> str | None:
        """None if the URL loads, else a short description."""
        if url not in self.cache:
            try:
                # GET, not HEAD: some hosts (e.g. Brushfire) answer 404 to HEAD only.
                with self.http.stream("GET", url, follow_redirects=True) as response:
                    status = response.status_code
                if status in BLOCKED_STATUSES:
                    self.cache[url] = f"blocked automated check ({status}); check by hand"
                else:
                    self.cache[url] = f"returns {status}" if status >= 400 else None
            except httpx.HTTPError as exc:
                self.cache[url] = f"unreachable ({type(exc).__name__})"
        return self.cache[url]


def check_redirects(rows: list[AuditRow], http: httpx.Client) -> list[Finding]:
    redirects = [r for r in rows if r.type == "redirect"]
    by_path = {(domain, r.url): r for r in redirects for domain in (r.domains or (None,))}
    checker = _Checker(http)
    findings = []

    for row in redirects:
        if row.target_broken:
            findings.append(Finding(row, "destination document was deleted"))
            continue
        if not row.target:
            findings.append(Finding(row, "no destination"))
            continue

        hops, current, problem = [row.url], row, None
        while True:
            domain = current.domains[0] if current.domains else None
            path = _internal_path(current.target, current.domains)
            next_row = by_path.get((domain, path)) if path else None
            if next_row is None:
                final = current.target
                if path is not None:
                    final = f"https://{domain}{path}" if domain else None
                if final:
                    problem = checker.problem(final)
                hops.append(current.target)
                break
            if next_row.url in hops:
                hops.append(next_row.url)
                problem = "loop"
                break
            hops.append(next_row.url)
            current = next_row

        if problem == "loop":
            findings.append(Finding(row, "loop " + " -> ".join(hops)))
        elif problem and len(hops) > 2:
            findings.append(Finding(row, f"chain {' -> '.join(hops)} {problem}"))
        elif problem:
            findings.append(Finding(row, f"target {problem}"))
    return findings
