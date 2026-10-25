# django_distill patches django.urls.path when the app loads, adding distill_* arguments.
from django.urls import path

from pages.views import page_paths, page_view

urlpatterns = [
    path("", page_view, name="home", distill_path=True, distill_file="index.html"),
    path("<path:path>/", page_view, name="page", distill_path=True, distill_func=page_paths),
]
