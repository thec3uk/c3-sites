from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django import template

from content.models import Image

register = template.Library()


@register.filter
def imgix(image: Image | None, width: int) -> str:
    """Image URL resized by Prismic's imgix CDN; height is dropped to keep the ratio."""
    if not image:
        return ""
    parts = urlsplit(image.url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in ("w", "h")]
    query.append(("w", str(width)))
    return urlunsplit(parts._replace(query=urlencode(query)))
