"""The site's Prismic redirect documents as a Netlify _redirects file."""

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from pages.content import site_documents, site_pages

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rule:
    source: str
    target: str
    status: int

    def __str__(self) -> str:
        return f"{self.source} {self.target} {self.status}"


# Whitespace or control characters would start a new rule or shift Netlify's columns.
UNSAFE = re.compile(r"[\s\x00-\x1f\x7f]")


def _skip_reason(source: str, target: str, destination) -> str:
    """Why the redirect can't be written, or '' if it can."""
    if getattr(destination, "broken", False):
        return "destination document was deleted"
    if not target:
        return "no destination"
    if source == "/":
        return "redirect from the home page"
    if UNSAFE.search(source) or UNSAFE.search(target):
        return "unsafe source or target (whitespace or control characters)"
    # Browsers read "/\host" as "//host", another site.
    site_path = target.startswith("/") and not target.startswith(("//", "/\\"))
    if not (site_path or urlsplit(target).scheme in ("http", "https")):
        return "unsafe target (not an http(s) URL or site path)"
    return ""


def redirect_rules() -> list[Rule]:
    """One rule per usable redirect document; skipped ones are logged."""
    rules = []
    for doc in site_documents():
        if doc.type != "redirect":
            continue
        destination = doc.fields.get("destination")
        target = str(destination or "")
        source = "/" + doc.url.strip("/")
        reason = _skip_reason(source, target, destination)
        if reason:
            log.warning("Redirect %s (%s) skipped: %s", doc.uid, doc.id, reason)
            continue
        status = 301 if doc.fields.get("permanent") else 302
        rules.append(Rule(source, target, status))
    return rules


def _with_uppercase(rules: list[Rule]) -> list[Rule]:
    # Gatsby also redirected /<UID>. Netlify's redirect docs don't say whether paths
    # match case-insensitively (unclear, https://docs.netlify.com/manage/routing/redirects/redirect-options/),
    # so keep the twins; duplicates are harmless.
    twins = [Rule(r.source.upper(), r.target, r.status) for r in rules if r.source.upper() != r.source]
    return rules + twins


def redirects_text() -> str:
    lines = [str(r) for r in _with_uppercase(redirect_rules())]
    return "\n".join(lines) + "\n" if lines else ""


def shadowed_sources() -> list[str]:
    """Redirect sources that are also built pages; the page wins unless the rule is forced."""
    built = {p.url.rstrip("/") for p in site_pages()}
    return [r.source for r in redirect_rules() if r.source in built]
