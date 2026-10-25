import pytest

from pages import content


@pytest.fixture
def documents(monkeypatch):
    """Replaces the Prismic fetch; append raw documents to the returned list."""
    docs = []
    monkeypatch.setattr(content, "fetch_documents", lambda site: docs)
    content.site_documents.cache_clear()
    yield docs
    content.site_documents.cache_clear()
