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


# gatsby-plugin-image's default breakpoints.
BREAKPOINTS = (750, 1080, 1366, 1920)


@register.filter
def srcset(image: Image | None) -> str:
    """imgix URLs at each breakpoint narrower than the image, then the image's own width."""
    if not image:
        return ""
    full = image.width or BREAKPOINTS[-1]
    widths = [w for w in BREAKPOINTS if w < full] + [min(full, BREAKPOINTS[-1])]
    return ", ".join(f"{imgix(image, w)} {w}w" for w in widths)
