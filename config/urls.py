# django_distill patches django.urls.path when the app loads, adding distill_* arguments.
from django.urls import path

from pages.views import not_found_view, page_paths, page_view, redirects_view

urlpatterns = [
    path("", page_view, name="home", distill_path=True, distill_file="index.html"),
    # Netlify serves 404.html for missing paths.
    path(
        "404.html",
        not_found_view,
        name="not-found",
        distill_path=True,
        distill_file="404.html",
        distill_status_codes=(404,),
    ),
    # Netlify reads this from the site root, after build.sh prepends the theme's rules.
    path("_redirects", redirects_view, name="redirects", distill_path=True, distill_file="_redirects"),
    path("<path:path>/", page_view, name="page", distill_path=True, distill_func=page_paths),
]
