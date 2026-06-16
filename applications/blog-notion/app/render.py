"""Convert Notion blocks into safe HTML.

Handles the block types that show up in practice. Consecutive list items are
grouped into <ul>/<ol>. Images are routed through the local /img proxy so that
Notion's expiring signed URLs never reach the browser.
"""
import hashlib
import html
from typing import Iterable

# Notion annotation colors we pass through as a CSS class.
_COLOR_PREFIX = "notion-color-"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_rich_text(rich: list[dict]) -> str:
    """Render an array of Notion rich_text fragments to inline HTML."""
    out: list[str] = []
    for frag in rich or []:
        text = _esc(frag.get("plain_text", ""))
        if not text:
            continue
        ann = frag.get("annotations", {})
        if ann.get("code"):
            text = f"<code>{text}</code>"
        if ann.get("bold"):
            text = f"<strong>{text}</strong>"
        if ann.get("italic"):
            text = f"<em>{text}</em>"
        if ann.get("strikethrough"):
            text = f"<del>{text}</del>"
        if ann.get("underline"):
            text = f"<u>{text}</u>"
        color = ann.get("color", "default")
        if color and color != "default":
            text = f'<span class="{_COLOR_PREFIX}{_esc(color)}">{text}</span>'
        href = frag.get("href")
        if href:
            text = f'<a href="{_esc(href)}" rel="noopener" target="_blank">{text}</a>'
        out.append(text)
    return "".join(out)


def plain_text(rich: list[dict]) -> str:
    return "".join(frag.get("plain_text", "") for frag in rich or [])


def _image_url(block: dict) -> str:
    """Build the local proxy URL for an image block."""
    return f"/img/{block['id']}"


def render_blocks(blocks: list[dict]) -> str:
    """Render a flat list of Notion blocks to an HTML string."""
    html_parts: list[str] = []
    list_buffer: list[str] = []
    list_kind: str | None = None  # "ul" or "bulleted", "ol" for numbered

    def flush_list():
        nonlocal list_buffer, list_kind
        if not list_buffer:
            return
        tag = "ol" if list_kind == "numbered" else "ul"
        html_parts.append(f"<{tag}>" + "".join(list_buffer) + f"</{tag}>")
        list_buffer = []
        list_kind = None

    for block in blocks:
        btype = block.get("type")
        data = block.get(btype, {})
        rich = data.get("rich_text", [])

        if btype == "bulleted_list_item":
            if list_kind not in (None, "bulleted"):
                flush_list()
            list_kind = "bulleted"
            list_buffer.append(f"<li>{render_rich_text(rich)}</li>")
            continue
        if btype == "numbered_list_item":
            if list_kind not in (None, "numbered"):
                flush_list()
            list_kind = "numbered"
            list_buffer.append(f"<li>{render_rich_text(rich)}</li>")
            continue

        # Any non-list block ends an open list.
        flush_list()

        if btype == "paragraph":
            inner = render_rich_text(rich)
            html_parts.append(f"<p>{inner}</p>" if inner else "<p>&nbsp;</p>")
        elif btype == "heading_1":
            html_parts.append(f"<h2>{render_rich_text(rich)}</h2>")
        elif btype == "heading_2":
            html_parts.append(f"<h3>{render_rich_text(rich)}</h3>")
        elif btype == "heading_3":
            html_parts.append(f"<h4>{render_rich_text(rich)}</h4>")
        elif btype == "quote":
            html_parts.append(f"<blockquote>{render_rich_text(rich)}</blockquote>")
        elif btype == "callout":
            icon = data.get("icon", {}) or {}
            emoji = _esc(icon.get("emoji", "💡"))
            html_parts.append(
                f'<div class="callout"><span class="callout-icon">{emoji}</span>'
                f"<div>{render_rich_text(rich)}</div></div>"
            )
        elif btype == "code":
            lang = _esc(data.get("language", "text"))
            code = _esc(plain_text(rich))
            html_parts.append(
                f'<pre class="code" data-lang="{lang}"><code>{code}</code></pre>'
            )
        elif btype == "to_do":
            checked = "checked" if data.get("checked") else ""
            html_parts.append(
                f'<div class="todo"><input type="checkbox" disabled {checked}>'
                f"<span>{render_rich_text(rich)}</span></div>"
            )
        elif btype == "toggle":
            html_parts.append(
                f"<details><summary>{render_rich_text(rich)}</summary></details>"
            )
        elif btype == "divider":
            html_parts.append("<hr>")
        elif btype == "image":
            caption = render_rich_text(data.get("caption", []))
            fig = f'<img src="{_image_url(block)}" loading="lazy" alt="{_esc(plain_text(data.get("caption", [])))}">'
            if caption:
                fig += f"<figcaption>{caption}</figcaption>"
            html_parts.append(f"<figure>{fig}</figure>")
        elif btype == "bookmark":
            url = _esc(data.get("url", "#"))
            html_parts.append(f'<p><a href="{url}" rel="noopener" target="_blank">{url}</a></p>')
        # Unknown block types are skipped silently.

    flush_list()
    return "".join(html_parts)


def placeholder_svg(seed: str) -> bytes:
    """Deterministic gradient cover for posts without a Notion cover image."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    hue = h % 360
    hue2 = (hue + 45) % 360
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="300">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="hsl({hue},42%,40%)"/>'
        f'<stop offset="1" stop-color="hsl({hue2},42%,24%)"/>'
        "</linearGradient></defs>"
        '<rect width="480" height="300" fill="url(#g)"/></svg>'
    )
    return svg.encode()


def summary_from_blocks(blocks: Iterable[dict], limit: int = 180) -> str:
    """First paragraph text, truncated — used as the card blurb."""
    for block in blocks:
        if block.get("type") == "paragraph":
            text = plain_text(block["paragraph"].get("rich_text", [])).strip()
            if text:
                return text[:limit] + ("…" if len(text) > limit else "")
    return ""
