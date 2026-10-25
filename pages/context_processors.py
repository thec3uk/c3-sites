from django.conf import settings

from pages.content import site_document


def site(request):
    return {"site": settings.SITE, "site_config": site_document("site_config")}
