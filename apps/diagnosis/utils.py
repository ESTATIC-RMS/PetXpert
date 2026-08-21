import markdown
import bleach


ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "blockquote",
]


ALLOWED_ATTRIBUTES = {}


def markdown_to_html(text):
    if not text:
        return ""

    html = markdown.markdown(
        text,
        extensions=[
            "extra",
            "nl2br",
            "sane_lists",
        ],
    )

    # Sanitize LLM-generated HTML
    html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )

    return html
