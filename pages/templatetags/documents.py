from django import template

from content.models import Page
from pages import content

register = template.Library()


@register.simple_tag
def site_document(type: str) -> Page | None:
    return content.site_document(type)
