from decimal import Decimal, ROUND_HALF_UP


def format_paise(value: int) -> str:
    """Format integer paise as Indian rupees without using float arithmetic."""
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


def format_hour_range(start_hour_utc: int, end_hour_utc: int) -> str:
    def hour_label(hour: int) -> str:
        normalized = hour % 24
        suffix = "am" if normalized < 12 else "pm"
        display = normalized % 12 or 12
        return f"{display}{suffix}"

    return f"{hour_label(start_hour_utc)}–{hour_label(end_hour_utc)} UTC"
