# django_distill patches django.urls.path when the app loads, adding distill_* arguments.
from django.urls import path

from pages.views import not_found_view, page_paths, page_view

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
    path("<path:path>/", page_view, name="page", distill_path=True, distill_func=page_paths),
]
