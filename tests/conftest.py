from pathlib import Path

import pytest
from django.conf import settings as django_settings

from config.settings.sites import load_site
from pages import content
from tests.documents import main_documents

ROOT = Path(django_settings.BASE_DIR)


@pytest.fixture
def documents(monkeypatch):
    """Replaces the Prismic fetch; append raw documents to the returned list."""
    docs = []
    monkeypatch.setattr(content, "fetch_documents", lambda site: docs)
    content.site_documents.cache_clear()
    yield docs
    content.site_documents.cache_clear()


@pytest.fixture
def main(settings, documents):
    """The main site and theme, with its home, about, site_config and footer documents."""
    settings.SITE = load_site("main")
    settings.ALLOWED_HOSTS = ["testserver"]
    settings.TEMPLATES = [
        {**django_settings.TEMPLATES[0], "DIRS": [ROOT / "themes/main/templates", ROOT / "templates"]}
    ]
    documents += main_documents()
    return documents
