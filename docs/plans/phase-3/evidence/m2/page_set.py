"""Smallest set of main-site pages that together use every slice variation.

Run: SITE=main PYTHONPATH=. uv run python docs/plans/phase-3/evidence/m2/page_set.py
"""

import os
from itertools import combinations

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from pages.content import site_pages  # noqa: E402

pages = {p.url: p for p in site_pages()}
uses = {url: frozenset(f"{s.type}/{s.variation}" for s in p.slices) for url, p in pages.items()}
wanted = frozenset().union(*uses.values())
# One page per distinct set of variations (the one with fewest slices), dropping sets inside another.
by_set = {}
for url in sorted(uses, key=lambda u: (len(pages[u].slices), u)):
    by_set.setdefault(uses[url], url)
candidates = [url for v, url in by_set.items() if not any(v < other for other in by_set)]
# Exact search: every combination of size 1, 2, ... until one covers everything.
for size in range(1, len(candidates) + 1):
    covers = [c for c in combinations(candidates, size) if frozenset().union(*(uses[u] for u in c)) == wanted]
    if covers:
        break
best = min(covers, key=lambda c: sum(len(pages[u].slices) for u in c))
print(f"{len(wanted)} variations on {len(pages)} pages; smallest cover is {size} pages ({len(covers)} such)")
for url in sorted(best):
    print(url, " ".join(sorted(uses[url])))
