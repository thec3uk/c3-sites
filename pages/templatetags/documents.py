from django import template

from content.models import Link, Page
from pages import content

register = template.Library()


@register.simple_tag
def site_document(type: str) -> Page | None:
    return content.site_document(type)


@register.filter
def linked_document(link) -> Page | None:
    """The site document a Link points at, e.g. a quick-links block's content."""
    if not isinstance(link, Link):
        return None
    return next((p for p in content.site_documents() if p.id == link.id), None)
