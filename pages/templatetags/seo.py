from django import template

from content.models import Page
from pages.templatetags.images import imgix
from pages.templatetags.text import plain

register = template.Library()


@register.simple_tag(takes_context=True)
def seo_meta(context, page: Page | None, site_config: Page | None) -> dict:
    """As Gatsby's SEO.tsx: title and description fall back to site_config, image to social_share.jpeg."""
    fields = page.fields if page else {}
    config = site_config.fields if site_config else {}
    site_title = plain(config.get("title"))
    seo_title = plain(fields.get("seo_title"))
    image = fields.get("seo_image")
    return {
        "title": f"{seo_title} | {site_title}" if seo_title else site_title,
        "description": plain(fields.get("seo_description") or config.get("description")),
        "image": imgix(image, 1200) if image else f"https://{context['site'].domain}/social_share.jpeg",
    }
