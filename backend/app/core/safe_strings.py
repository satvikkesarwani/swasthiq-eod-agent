from app.core.errors import AppError
from app.core.limits import MAX_ERROR_CODE_LENGTH, MAX_ERROR_MESSAGE_LENGTH, MAX_FIELD_PATH_LENGTH


def has_control_character(value: str) -> bool:
    return any((ord(char) < 32 and char not in {"\t"}) or 127 <= ord(char) <= 159 for char in value)


def clean_user_string(value: object, *, field: str, max_length: int, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise AppError(
            code="INVALID_FIELD_TYPE",
            message=f"{field} must be a string.",
            status_code=422,
            details=[{"field": field, "code": "INVALID_FIELD_TYPE", "message": f"{field} must be a string."}],
        )
    cleaned = value.strip()
    if not cleaned:
        if required:
            raise AppError(
                code="INVALID_IDENTIFIER",
                message=f"{field} must not be blank.",
                status_code=422,
                details=[{"field": field, "code": "INVALID_IDENTIFIER", "message": f"{field} must not be blank."}],
            )
        return None
    if len(cleaned) > max_length:
        raise AppError(
            code="INVALID_IDENTIFIER",
            message=f"{field} is longer than the supported limit.",
            status_code=422,
            details=[{"field": field, "code": "INVALID_IDENTIFIER", "message": f"{field} is too long."}],
        )
    if has_control_character(cleaned):
        raise AppError(
            code="CONTROL_CHARACTER_NOT_ALLOWED",
            message=f"{field} contains unsupported control characters.",
            status_code=422,
            details=[{"field": field, "code": "CONTROL_CHARACTER_NOT_ALLOWED", "message": f"{field} contains unsupported control characters."}],
        )
    return cleaned


def is_safe_display_identifier(value: object, *, max_length: int) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= max_length and not has_control_character(value)


def bounded_text(value: object, *, max_length: int) -> str:
    text = str(value) if isinstance(value, (str, int, float, bool)) else "Invalid value."
    text = " ".join(text.split())
    if len(text) > max_length:
        return f"{text[: max_length - 3]}..."
    return text


def safe_field_path(value: str) -> str:
    return bounded_text(value, max_length=MAX_FIELD_PATH_LENGTH)


def safe_error_code(value: str) -> str:
    return bounded_text(value, max_length=MAX_ERROR_CODE_LENGTH).upper()


def safe_error_message(value: str) -> str:
    return bounded_text(value, max_length=MAX_ERROR_MESSAGE_LENGTH)
