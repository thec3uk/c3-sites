"""Source-neutral content objects. Templates only ever see these."""

from dataclasses import dataclass, field
from html import escape
from typing import Any

from django.utils.safestring import SafeString, mark_safe

BLOCK_TAGS = {
    "paragraph": "p",
    "preformatted": "pre",
    **{f"heading{n}": f"h{n}" for n in range(1, 7)},
}
LIST_TAGS = {"list-item": "ul", "o-list-item": "ol"}


@dataclass(frozen=True)
class Image:
    url: str
    alt: str = ""
    width: int | None = None
    height: int | None = None


class Link(str):
    """A link to a document: prints as its URL ('' if it has none) and names its target."""

    def __new__(cls, url: str, id: str, type: str, broken: bool = False):
        link = super().__new__(cls, url)
        link.id, link.type, link.broken = id, type, broken
        return link


@dataclass(frozen=True)
class Slice:
    type: str
    variation: str = "default"
    primary: dict[str, Any] = field(default_factory=dict)
    items: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class Page:
    id: str
    type: str
    uid: str | None
    url: str
    title: str = ""
    tags: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)
    slices: tuple[Slice, ...] = ()


@dataclass(frozen=True)
class RichText:
    """Structured text blocks; hyperlink spans carry a resolved {"url": ...}."""

    blocks: tuple[dict, ...]

    @property
    def text(self) -> str:
        return "\n".join(b.get("text", "") for b in self.blocks)

    @property
    def html(self) -> str:
        out, open_list = [], None
        for block in self.blocks:
            list_tag = LIST_TAGS.get(block["type"])
            if open_list and list_tag != open_list:
                out.append(f"</{open_list}>")
                open_list = None
            if list_tag:
                if not open_list:
                    out.append(f"<{list_tag}>")
                    open_list = list_tag
                out.append(f"<li>{render_spans(block['text'], block['spans'])}</li>")
            elif block["type"] == "image":
                out.append(
                    f'<p class="block-img"><img src="{escape(block["url"])}"'
                    f' alt="{escape(block.get("alt") or "")}"></p>'
                )
            elif tag := BLOCK_TAGS.get(block["type"]):
                out.append(f"<{tag}>{render_spans(block['text'], block['spans'])}</{tag}>")
        if open_list:
            out.append(f"</{open_list}>")
        return "".join(out)

    def __html__(self) -> str:
        return self.html

    def __str__(self) -> SafeString:
        return mark_safe(self.html)

    def __bool__(self) -> bool:
        return bool(self.text.strip())


def _open_tag(span: dict) -> str:
    match span["type"]:
        case "strong":
            return "<strong>"
        case "em":
            return "<em>"
        case "hyperlink":
            data = span.get("data", {})
            target = ' target="_blank" rel="noopener"' if data.get("target") == "_blank" else ""
            return f'<a href="{escape(data.get("url", ""))}"{target}>'
        case "label":
            return f'<span class="{escape(span.get("data", {}).get("label", ""))}">'
    return ""


def _close_tag(span: dict) -> str:
    return {"strong": "</strong>", "em": "</em>", "hyperlink": "</a>", "label": "</span>"}.get(
        span["type"], ""
    )


def render_spans(text: str, spans: list[dict]) -> str:
    """Text with inline spans as HTML. Span offsets count UTF-16 units, as Prismic does."""
    spans = sorted(spans, key=lambda s: (s["start"], -s["end"]))
    out, stack, next_span, offset = [], [], 0, 0

    def boundary(pos: int) -> None:
        nonlocal next_span
        # Close spans ending here; reopen any inner ones that overlap past this point.
        reopen = []
        while any(s["end"] == pos for s in stack):
            span = stack.pop()
            out.append(_close_tag(span))
            if span["end"] != pos:
                reopen.append(span)
        for span in reversed(reopen):
            out.append(_open_tag(span))
            stack.append(span)
        while next_span < len(spans) and spans[next_span]["start"] <= pos:
            span = spans[next_span]
            next_span += 1
            if span["end"] > pos:
                out.append(_open_tag(span))
                stack.append(span)

    for char in text:
        boundary(offset)
        out.append("<br>" if char == "\n" else escape(char))
        offset += len(char.encode("utf-16-le")) // 2
    boundary(offset)
    while stack:
        out.append(_close_tag(stack.pop()))
    return "".join(out)
