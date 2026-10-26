"""Tests for the pure conversion functions.

Pure functions are the easiest code to test: no app, no browser, just
"this input should give that answer". pytest.approx allows the tiny float
errors computers make (1e-12 relative by default here).
"""
import pytest

from converter.conversions import convert, convert_all, describe_formula, format_number
from converter.units import CATEGORIES


def approx(x):
    return pytest.approx(x, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize(
    "value, category, from_unit, to_unit, expected",
    [
        # Length
        (1, "length", "kilometre", "metre", 1000),
        (1, "length", "metre", "centimetre", 100),
        (1, "length", "mile", "kilometre", 1.609344),
        (12, "length", "inch", "foot", 1),
        (1, "length", "yard", "inch", 36),
        (1, "length", "nautical_mile", "metre", 1852),
        # Weight
        (1, "weight", "kilogram", "gram", 1000),
        (1, "weight", "gram", "milligram", 1000),
        (2500, "weight", "gram", "kilogram", 2.5),
        (1, "weight", "tonne", "kilogram", 1000),
        (1, "weight", "pound", "ounce", 16),
        (1, "weight", "stone", "pound", 14),
        (1, "weight", "kilogram", "pound", 2.2046226218487757),
        # Temperature
        (0, "temperature", "celsius", "fahrenheit", 32),
        (100, "temperature", "celsius", "fahrenheit", 212),
        (-40, "temperature", "celsius", "fahrenheit", -40),
        (98.6, "temperature", "fahrenheit", "celsius", 37),
        (0, "temperature", "kelvin", "celsius", -273.15),
        (32, "temperature", "fahrenheit", "kelvin", 273.15),
        # Area
        (1, "area", "hectare", "square_metre", 10000),
        (1, "area", "square_foot", "square_inch", 144),
        (1, "area", "square_mile", "acre", 640),
        # Volume
        (1, "volume", "litre", "millilitre", 1000),
        (1, "volume", "cubic_metre", "litre", 1000),
        (1, "volume", "gallon", "quart", 4),
        (1, "volume", "cup", "tablespoon", 16),
        (1, "volume", "tablespoon", "teaspoon", 3),
        # Speed
        (36, "speed", "kilometre_per_hour", "metre_per_second", 10),
        (60, "speed", "mile_per_hour", "kilometre_per_hour", 96.56064),
        (1, "speed", "knot", "kilometre_per_hour", 1.852),
        # Time
        (1, "time", "hour", "minute", 60),
        (1, "time", "day", "hour", 24),
        (1, "time", "week", "day", 7),
        (1, "time", "second", "millisecond", 1000),
        # Digital storage
        (1, "data", "byte", "bit", 8),
        (1, "data", "gigabyte", "megabyte", 1000),
        (1, "data", "gibibyte", "mebibyte", 1024),
        (1, "data", "kibibyte", "byte", 1024),
    ],
)
def test_known_values(value, category, from_unit, to_unit, expected):
    assert convert(value, category, from_unit, to_unit) == approx(expected)


# Every (category, unit) pair, so the next two tests check all units.
ALL_UNITS = [(category, unit) for category, c in CATEGORIES.items() for unit in c.units]


@pytest.mark.parametrize("category, unit", ALL_UNITS)
def test_same_unit_gives_same_value(category, unit):
    assert convert(42.5, category, unit, unit) == approx(42.5)


@pytest.mark.parametrize("category, unit", ALL_UNITS)
def test_there_and_back_again(category, unit):
    # Convert into every other unit and back: we should get the start value.
    for other in CATEGORIES[category].units:
        there = convert(123.456, category, unit, other)
        assert convert(there, category, other, unit) == approx(123.456)


def test_convert_is_pure():
    # Same input, same answer, every time.
    answers = [convert(5, "length", "foot", "metre") for _ in range(3)]
    assert answers[0] == approx(1.524)
    assert answers == [answers[0]] * 3


def test_convert_all_lists_every_unit_in_order():
    rows = convert_all(1, "weight", "kilogram")
    assert [key for key, unit, result in rows] == list(CATEGORIES["weight"].units)
    results = {key: result for key, unit, result in rows}
    assert results["gram"] == approx(1000)
    assert results["kilogram"] == approx(1)


def test_unknown_unit_raises():
    with pytest.raises(KeyError):
        convert(1, "length", "metre", "parsec")
    with pytest.raises(KeyError):
        convert(1, "temperature", "celsius", "rankine")


@pytest.mark.parametrize(
    "number, text",
    [
        (0, "0"),
        (-0.0, "0"),
        (1000.0, "1,000"),
        (1234567.891, "1,234,567.891"),
        (2.50, "2.5"),
        (0.1 + 0.2, "0.3"),
        (26.850000000000023, "26.85"),
        (-40.0, "-40"),
        (-1234.5, "-1,234.5"),
        (0.00001, "0.00001"),
        (2.2046226218487757, "2.204622622"),
        (1.5e21, "1.5 × 10²¹"),
        (1e15, "1 × 10¹⁵"),
        (123456789012345, "123,456,789,000,000"),  # kept to 10 digits
        (999999999999999, "1 × 10¹⁵"),  # rounds up to 10 digits
        (1.23e-9, "1.23 × 10⁻⁹"),
    ],
)
def test_format_number(number, text):
    assert format_number(number) == text


@pytest.mark.parametrize(
    "category, from_unit, to_unit, text",
    [
        # Multiply when the factor is 1 or more.
        ("weight", "kilogram", "gram", "Multiply by 1,000"),
        ("length", "mile", "kilometre", "Multiply by 1.609344"),
        ("time", "hour", "minute", "Multiply by 60"),
        ("weight", "kilogram", "pound", "Multiply by 2.204622622"),
        # Divide when that reads better...
        ("weight", "gram", "kilogram", "Divide by 1,000"),
        ("length", "millimetre", "kilometre", "Divide by 1,000,000"),
        ("length", "kilometre", "mile", "Divide by 1.609344"),
        ("length", "centimetre", "inch", "Divide by 2.54"),
        ("data", "bit", "byte", "Divide by 8"),
        # ...but not when the multiply number is shorter.
        ("length", "foot", "metre", "Multiply by 0.3048"),
        ("weight", "pound", "kilogram", "Multiply by 0.45359237"),
        # Temperature has real formulas.
        ("temperature", "celsius", "fahrenheit", "°F = °C × 9/5 + 32"),
        ("temperature", "fahrenheit", "celsius", "°C = (°F − 32) × 5/9"),
        ("temperature", "kelvin", "celsius", "°C = K − 273.15"),
        # Same unit.
        ("length", "metre", "metre", "Same unit: the number doesn't change"),
        ("temperature", "kelvin", "kelvin", "Same unit: the number doesn't change"),
    ],
)
def test_describe_formula(category, from_unit, to_unit, text):
    assert describe_formula(category, from_unit, to_unit) == text


@pytest.mark.parametrize("category, unit", ALL_UNITS)
def test_every_pair_has_a_formula(category, unit):
    for other in CATEGORIES[category].units:
        assert describe_formula(category, unit, other)
