import json
from collections import deque
from typing import Any

from app.core.errors import AppError


class DuplicateKeyError(ValueError):
    pass


class NonStandardConstantError(ValueError):
    pass


def _reject_constant(value: str) -> None:
    raise NonStandardConstantError(value)


def _unique_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise DuplicateKeyError(key)
        seen.add(key)
        result[key] = value
    return result


def _max_lexical_depth(text: str) -> int:
    depth = 0
    max_depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif char in "]}":
            depth -= 1
            if depth < 0:
                return max_depth
    return max_depth


def _count_nodes(value: Any, *, max_nodes: int) -> int:
    count = 0
    queue: deque[Any] = deque([value])
    while queue:
        current = queue.popleft()
        count += 1
        if count > max_nodes:
            raise AppError(
                code="JSON_NODE_LIMIT_EXCEEDED",
                message="The JSON file contains too many values.",
                status_code=413,
            )
        if isinstance(current, dict):
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)
    return count


def decode_strict_json_body(body: bytes, *, max_depth: int, max_nodes: int) -> Any:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AppError(code="INVALID_UTF8", message="Request body must be valid UTF-8 JSON.", status_code=422) from exc
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.strip():
        raise AppError(code="INVALID_JSON", message="Request body must contain JSON.", status_code=422)
    if _max_lexical_depth(text) > max_depth:
        raise AppError(code="JSON_DEPTH_EXCEEDED", message="The JSON structure is nested too deeply.", status_code=413)
    try:
        value = json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_unique_object_pairs)
    except DuplicateKeyError as exc:
        raise AppError(code="DUPLICATE_JSON_KEY", message="The JSON contains a duplicate object key.", status_code=422) from exc
    except NonStandardConstantError as exc:
        raise AppError(code="NON_STANDARD_JSON_CONSTANT", message="JSON cannot contain NaN or Infinity.", status_code=422) from exc
    except json.JSONDecodeError as exc:
        raise AppError(code="INVALID_JSON", message="Request body is not valid JSON.", status_code=422) from exc
    except RecursionError as exc:
        raise AppError(code="JSON_DEPTH_EXCEEDED", message="The JSON structure is nested too deeply.", status_code=413) from exc
    _count_nodes(value, max_nodes=max_nodes)
    return value
