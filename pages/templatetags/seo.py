from django import template

from content.models import Page

register = template.Library()


@register.simple_tag
def seo_meta(page: Page | None, site_config: Page | None) -> dict:
    """Title, description and image as in Gatsby's SEO.tsx, falling back to site_config."""
    fields = page.fields if page else {}
    config = site_config.fields if site_config else {}
    site_title = config.get("title") or ""
    return {
        "title": f"{fields['seo_title']} | {site_title}" if fields.get("seo_title") else site_title,
        "description": fields.get("seo_description") or config.get("description") or "",
        "image": fields.get("seo_image") or config.get("banner"),
    }
