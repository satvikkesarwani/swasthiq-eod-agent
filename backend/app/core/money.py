from decimal import Decimal, ROUND_HALF_UP

from app.core.errors import AppError
from app.core.limits import MAX_SAFE_JSON_INTEGER


class MoneyDomainError(AppError):
    pass


def require_int(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise MoneyDomainError(
            code="INVALID_FIELD_TYPE",
            message=f"{field} must be an integer paise value.",
            status_code=422,
            details=[{"field": field, "code": "INVALID_FIELD_TYPE", "message": f"{field} must be an integer."}],
        )
    return value


def require_safe_paise(value: int, *, field: str, max_abs: int = MAX_SAFE_JSON_INTEGER) -> int:
    require_int(value, field=field)
    if abs(value) > max_abs:
        raise MoneyDomainError(
            code="NUMERIC_RANGE_EXCEEDED",
            message="A numeric value exceeds the supported exact billing range.",
            status_code=422,
            details=[{"field": field, "code": "NUMERIC_RANGE_EXCEEDED", "message": "Value exceeds the exact safe-integer range."}],
        )
    return value


def checked_add_paise(left: int, right: int, *, field: str, max_abs: int = MAX_SAFE_JSON_INTEGER) -> int:
    result = require_int(left, field=field) + require_int(right, field=field)
    return require_safe_paise(result, field=field, max_abs=max_abs)


def checked_sub_paise(left: int, right: int, *, field: str, max_abs: int = MAX_SAFE_JSON_INTEGER) -> int:
    result = require_int(left, field=field) - require_int(right, field=field)
    return require_safe_paise(result, field=field, max_abs=max_abs)


def checked_mul_paise(left: int, right: int, *, field: str, max_abs: int = MAX_SAFE_JSON_INTEGER) -> int:
    result = require_int(left, field=field) * require_int(right, field=field)
    return require_safe_paise(result, field=field, max_abs=max_abs)


def checked_sum_paise(values: list[int], *, field: str, max_abs: int = MAX_SAFE_JSON_INTEGER) -> int:
    total = 0
    for value in values:
        total = checked_add_paise(total, value, field=field, max_abs=max_abs)
    return total


def collection_rate_basis_points(*, collected_paise: int, billed_paise: int) -> int | None:
    require_safe_paise(collected_paise, field="total_collected_paise")
    require_safe_paise(billed_paise, field="total_billed_paise")
    if billed_paise == 0:
        return None
    if collected_paise < 0 or billed_paise < 0:
        raise MoneyDomainError(code="REPORT_INVARIANT_FAILED", message="Collection rate inputs must be non-negative.", status_code=500)
    return int((Decimal(collected_paise) * Decimal(10_000) / Decimal(billed_paise)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def format_paise(value: int) -> str:
    """Format integer paise as Indian rupees without using float arithmetic."""
    require_int(value, field="display_paise")
    rupees = Decimal(value) / Decimal(100)
    if rupees == rupees.to_integral_value():
        return f"₹{int(rupees):,}"
    return f"₹{rupees.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"


def format_rate(value: float | None) -> str:
    if value is None:
        return "Not available"
    percentage = (Decimal(str(value)) * Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if percentage == percentage.to_integral_value():
        return f"{int(percentage)}%"
    return f"{percentage}%"


def format_basis_points(value: int | None) -> str:
    if value is None:
        return "Not available"
    require_int(value, field="collection_rate_basis_points")
    percentage = (Decimal(value) / Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if percentage == percentage.to_integral_value():
        return f"{int(percentage)}%"
    return f"{percentage}%"


def format_hour_range(start_hour_utc: int, end_hour_utc: int) -> str:
    def hour_label(hour: int) -> str:
        normalized = hour % 24
        suffix = "am" if normalized < 12 else "pm"
        display = normalized % 12 or 12
        return f"{display}{suffix}"

    return f"{hour_label(start_hour_utc)}–{hour_label(end_hour_utc)} UTC"
