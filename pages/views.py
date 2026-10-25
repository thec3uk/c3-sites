import logging
from xml.sax.saxutils import escape

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render

from pages.content import page_by_url, site_pages
from pages.redirects import redirects_text, shadowed_sources

log = logging.getLogger(__name__)


def page_view(request, path=""):
    page = page_by_url(f"/{path}/" if path else "/")
    if page is None:
        raise Http404
    return render(request, [f"pages/{page.type}.html", "pages/page.html"], {"page": page})


def page_paths():
    """distill_func: every page URL except the home page, which has its own route."""
    for page in site_pages():
        if page.url != "/":
            yield {"path": page.url.strip("/")}


def not_found_view(request):
    return render(request, "404.html", status=404)


def redirects_view(request):
    for source in shadowed_sources():
        log.warning("Redirect %s is also a built page; not forced, so the page wins", source)
    return HttpResponse(redirects_text(), content_type="text/plain")


def sitemap_view(request):
    locs = "".join(f"<url><loc>{escape(f'https://{settings.SITE.domain}{p.url}')}</loc></url>" for p in site_pages())
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>'
    return HttpResponse(xml, content_type="application/xml")
