from django.http import Http404
from django.shortcuts import render

from pages.content import page_by_url, site_pages


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
