"""Maps raw Prismic document JSON to Page and Slice objects."""

from typing import Any

from content.models import Image, Page, RichText, Slice
from content.prismic_client import resolve_link

SLICE_ZONES = ("body", "slices")
TITLE_FIELDS = ("page_title", "title", "seo_title")


def _is_rich_text(value: list) -> bool:
    return bool(value) and all(
        isinstance(b, dict) and "type" in b and "spans" in b for b in value
    )


def _rich_text(blocks: list[dict]) -> RichText:
    converted = []
    for block in blocks:
        spans = [
            {**span, "data": {"url": resolve_link(span["data"]), "target": span["data"].get("target")}}
            if span["type"] == "hyperlink"
            else span
            for span in block.get("spans", [])
        ]
        converted.append({**block, "spans": spans})
    return RichText(tuple(converted))


def convert(value: Any) -> Any:
    """Converts any Prismic field by its shape: rich text, link, image or group."""
    if isinstance(value, list):
        if _is_rich_text(value):
            return _rich_text(value)
        return [convert(v) for v in value]
    if isinstance(value, dict):
        if "link_type" in value:
            return resolve_link(value)
        if "dimensions" in value and "url" in value:
            return Image(
                url=value["url"],
                alt=value.get("alt") or "",
                width=value["dimensions"].get("width"),
                height=value["dimensions"].get("height"),
            )
        if not value:
            return None
        return {k: convert(v) for k, v in value.items()}
    return value


def _slice(raw: dict) -> Slice:
    return Slice(
        type=raw["slice_type"],
        variation=raw.get("variation") or "default",
        primary=convert(raw.get("primary") or {}) or {},
        items=convert(raw.get("items") or []),
    )


def _title(fields: dict) -> str:
    for name in TITLE_FIELDS:
        value = fields.get(name)
        if value:
            return value.text if isinstance(value, RichText) else str(value)
    return ""


def to_page(document: dict) -> Page:
    data = dict(document.get("data") or {})
    raw_slices = next((data.pop(zone) for zone in SLICE_ZONES if zone in data), [])
    fields = {name: convert(value) for name, value in data.items()}
    return Page(
        id=document["id"],
        type=document["type"],
        uid=document.get("uid"),
        url=resolve_link(document),
        title=_title(fields),
        tags=tuple(document.get("tags") or ()),
        fields=fields,
        slices=tuple(_slice(s) for s in raw_slices),
    )
