"""The conversion math, written as pure functions.

A pure function only uses its arguments, and gives the same answer every
time for the same input. It doesn't read files, use Flask or change
anything outside itself. That makes it simple to test: call it, check the
answer (see tests/test_conversions.py).

These functions expect checked input. Run validation.validate_conversion()
first; an unknown unit here raises KeyError.
"""
from decimal import Decimal

from .units import CATEGORIES


def to_celsius(value, unit):
    """Turn a temperature in `unit` into degrees Celsius."""
    if unit == "celsius":
        return value
    if unit == "fahrenheit":
        return (value - 32) * 5 / 9
    if unit == "kelvin":
        return value - 273.15
    raise KeyError(unit)


def from_celsius(celsius, unit):
    """Turn degrees Celsius into a temperature in `unit`."""
    if unit == "celsius":
        return celsius
    if unit == "fahrenheit":
        return celsius * 9 / 5 + 32
    if unit == "kelvin":
        return celsius + 273.15
    raise KeyError(unit)


def convert(value, category, from_unit, to_unit):
    """Convert `value` from one unit to another in the same category.

    >>> convert(1, "weight", "kilogram", "gram")
    1000.0
    """
    if category == "temperature":
        return from_celsius(to_celsius(value, from_unit), to_unit)
    units = CATEGORIES[category].units
    # Go through the base unit: first into metres (or kg...), then out again.
    return value * units[from_unit].factor / units[to_unit].factor


def convert_all(value, category, from_unit):
    """Convert `value` into every unit of the category.

    Returns a list of (unit_key, unit, result), in the same order as units.py.
    """
    return [
        (key, unit, convert(value, category, from_unit, key))
        for key, unit in CATEGORIES[category].units.items()
    ]


TEMPERATURE_FORMULAS = {
    ("celsius", "fahrenheit"): "°F = °C × 9/5 + 32",
    ("fahrenheit", "celsius"): "°C = (°F − 32) × 5/9",
    ("celsius", "kelvin"): "K = °C + 273.15",
    ("kelvin", "celsius"): "°C = K − 273.15",
    ("fahrenheit", "kelvin"): "K = (°F − 32) × 5/9 + 273.15",
    ("kelvin", "fahrenheit"): "°F = (K − 273.15) × 9/5 + 32",
}


def describe_formula(category, from_unit, to_unit):
    """Explain how the answer is made, in a few words.

    >>> describe_formula("weight", "kilogram", "gram")
    'Multiply by 1,000'
    >>> describe_formula("weight", "gram", "kilogram")
    'Divide by 1,000'
    """
    if from_unit == to_unit:
        return "Same unit: the number doesn't change"
    if category == "temperature":
        return TEMPERATURE_FORMULAS[(from_unit, to_unit)]

    units = CATEGORIES[category].units
    ratio = units[from_unit].factor / units[to_unit].factor
    multiply = format_number(ratio)
    divide = format_number(1 / ratio)
    # "Divide by 1,000" reads better than "Multiply by 0.001", and
    # "Divide by 1.609344" better than "Multiply by 0.6213711922".
    # But "Multiply by 0.3048" beats "Divide by 3.280839895".
    if ratio < 1 and ("." not in divide or len(divide) < len(multiply)):
        return f"Divide by {divide}"
    return f"Multiply by {multiply}"


SUPERSCRIPTS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def format_number(x, sig_digits=10):
    """Show a number in a friendly way, as text.

    - Computers store decimals with tiny errors (0.1 + 0.2 gives
      0.30000000000000004). Keeping 10 significant digits hides them: "0.3".
    - Trailing zeros go away: 2.50 -> "2.5", 1000.0 -> "1,000".
    - Big whole parts get commas: 1234567 -> "1,234,567".
    - Very big or very small numbers use powers of ten: "1.5 × 10²¹".
    """
    if x == 0:
        return "0"  # also turns -0.0 into "0"
    rounded = float(f"{x:.{sig_digits}g}")

    if abs(rounded) >= 1e15 or abs(rounded) < 1e-6:
        mantissa, exponent = f"{rounded:.{sig_digits - 1}e}".split("e")
        mantissa = mantissa.rstrip("0").rstrip(".")
        power = str(int(exponent)).translate(SUPERSCRIPTS)
        return f"{mantissa} × 10{power}"

    # Decimal writes the number out in full (str(0.00001) would be "1e-05").
    text = format(Decimal(repr(rounded)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    sign = "-" if text.startswith("-") else ""
    whole, _, fraction = text.lstrip("-").partition(".")
    whole = f"{int(whole):,}"
    return sign + whole + ("." + fraction if fraction else "")
