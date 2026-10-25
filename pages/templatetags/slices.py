from django import template
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from content.models import Page, Slice

register = template.Library()


class MissingSliceTemplate(Exception):
    pass


def slice_template_names(slice: Slice) -> list[str]:
    """Most specific first; the theme dir comes before shared templates in DIRS."""
    return [f"slices/{slice.type}/{slice.variation}.html", f"slices/{slice.type}.html"]


@register.simple_tag
def render_slices(page: Page) -> str:
    out = []
    for index, slice in enumerate(page.slices):
        try:
            tpl = select_template(slice_template_names(slice))
        except TemplateDoesNotExist:
            message = (
                f"No template for slice '{slice.type}' (variation '{slice.variation}')"
                f" on page {page.url}"
            )
            if not settings.DEBUG:
                raise MissingSliceTemplate(message) from None
            out.append(
                format_html(
                    '<div data-missing-slice="{}/{}" style="border:2px dashed red;padding:1rem">{}</div>',
                    slice.type,
                    slice.variation,
                    message,
                )
            )
            continue
        out.append(tpl.render({"slice": slice, "page": page, "index": index}))
    return mark_safe("".join(out))
