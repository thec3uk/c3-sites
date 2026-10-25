from django import template

from content.models import RichText

register = template.Library()


@register.filter
def plain(value) -> str:
    """Text without markup, for attributes: RichText is SafeString, so it would skip autoescape."""
    if isinstance(value, RichText):
        return value.text
    return "" if value is None else str(value)
