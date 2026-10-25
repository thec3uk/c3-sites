"""The site's Prismic redirect documents as a Netlify _redirects file."""

import logging
from dataclasses import dataclass

from pages.content import site_documents, site_pages

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rule:
    source: str
    target: str
    status: int

    def __str__(self) -> str:
        return f"{self.source} {self.target} {self.status}"


def redirect_rules() -> list[Rule]:
    """One rule per usable redirect document; skipped ones are logged."""
    rules = []
    for doc in site_documents():
        if doc.type != "redirect":
            continue
        target = str(doc.fields.get("destination") or "")
        if not doc.url or doc.url == "/" or not target:
            log.warning("Redirect %s (%s) skipped: no destination or deleted target", doc.uid, doc.id)
            continue
        status = 301 if doc.fields.get("permanent") else 302
        rules.append(Rule("/" + doc.url.strip("/"), target, status))
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
