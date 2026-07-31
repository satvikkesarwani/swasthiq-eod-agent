import re

from app.agent.facts import ApprovedFact

TOKEN_RE = re.compile(r"\{\{([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)\}\}")
MAX_PLACEHOLDERS = 40


class PlaceholderError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def extract_placeholders(template: str) -> list[str]:
    if not template or not template.strip():
        raise PlaceholderError("EMPTY_TEMPLATE")
    keys: list[str] = []
    spans: list[tuple[int, int]] = []
    for match in TOKEN_RE.finditer(template):
        start, end = match.span()
        if start > 0 and template[start - 1].isalnum():
            raise PlaceholderError("MALFORMED_PLACEHOLDER")
        if end < len(template) and template[end:end + 1].isalnum():
            raise PlaceholderError("MALFORMED_PLACEHOLDER")
        keys.append(match.group(1))
        spans.append((start, end))
    scrubbed = list(template)
    for start, end in spans:
        scrubbed[start:end] = " " * (end - start)
    if "{{" in "".join(scrubbed) or "}}" in "".join(scrubbed):
        raise PlaceholderError("MALFORMED_PLACEHOLDER")
    if len(keys) > MAX_PLACEHOLDERS:
        raise PlaceholderError("TEMPLATE_TOO_LONG")
    if len(keys) != len(set(keys)):
        raise PlaceholderError("DUPLICATE_FACT_USAGE")
    return keys


def validate_placeholders(template: str, catalogue: dict[str, ApprovedFact]) -> list[str]:
    keys = extract_placeholders(template)
    if not keys:
        raise PlaceholderError("TRACE_NOT_USED")
    if any(key not in catalogue for key in keys):
        raise PlaceholderError("UNKNOWN_PLACEHOLDER")
    return keys


def render_template(template: str, catalogue: dict[str, ApprovedFact]) -> str:
    keys = validate_placeholders(template, catalogue)
    rendered = template
    for key in keys:
        rendered = rendered.replace(f"{{{{{key}}}}}", catalogue[key].display_value)
    if "{{" in rendered or "}}" in rendered:
        raise PlaceholderError("MALFORMED_PLACEHOLDER")
    return " ".join(rendered.strip().split())
