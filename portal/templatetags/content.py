from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt

register = template.Library()
markdown = MarkdownIt("commonmark", {"html": False, "breaks": True})


@register.filter
def render_markdown(value):
    # Raw HTML is disabled, and markdown-it-py rejects unsafe link protocols.
    return mark_safe(markdown.render(value or ""))


@register.filter
def file_size(value):
    size = float(value or 0)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024 or unit == "ГБ":
            return f"{size:.0f} {unit}" if unit == "Б" else f"{size:.1f} {unit}"
        size /= 1024
