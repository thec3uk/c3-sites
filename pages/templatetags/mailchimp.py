from django import template
from django.conf import settings

register = template.Library()

ENDPOINT = "https://thec3.us19.list-manage.com/subscribe/post?u=baac982817e7fb161022a1253&id="
# Dev builds subscribe to a test list, as Gatsby did outside production.
PRODUCTION_LIST = "d62f87b12a"
DEV_LIST = "7443c2e349"


@register.simple_tag
def mailchimp_endpoint() -> str:
    return ENDPOINT + (DEV_LIST if settings.DEBUG else PRODUCTION_LIST)
