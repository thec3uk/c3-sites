from dataclasses import dataclass
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class SiteConfig:
    name: str
    domain: str
    theme: str
    # A site selects Prismic documents by tag, by custom type, or both.
    prismic_tags: tuple[str, ...] = ()
    prismic_types: tuple[str, ...] = ()
    # Document types that get their own URL; the rest are data (config, banners).
    page_types: tuple[str, ...] = ("page",)
    umami_website_id: str = ""
    umami_src: str = ""


def load_site(name: str) -> SiteConfig:
    try:
        module = import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as exc:
        raise ImproperlyConfigured(f"Unknown SITE '{name}'") from exc
    return module.SITE
