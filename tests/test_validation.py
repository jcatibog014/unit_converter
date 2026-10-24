"""Tests for input validation: bad input must give a clear message, not a crash."""
import pytest

from converter.validation import fill_defaults, parse_number, validate_conversion


def params(**changes):
    """A valid request (1 kg in g), with some fields changed."""
    fields = {"category": "weight", "value": "1", "from": "kilogram", "to": "gram"}
    fields.update(changes)
    return fields


def test_valid_input():
    data, errors = validate_conversion(params(value=" 2.5 "))
    assert errors == {}
    assert data == {"category": "weight", "value": 2.5, "from_unit": "kilogram", "to_unit": "gram"}


@pytest.mark.parametrize(
    "text, number",
    [
        ("12", 12),
        ("3.5", 3.5),
        (".5", 0.5),
        ("5.", 5),
        ("-7", -7),
        ("+7", 7),
        ("1,000", 1000),
        ("1,250,000.75", 1250000.75),
        ("0", 0),
    ],
)
def test_numbers_we_accept(text, number):
    assert parse_number(text) == (number, None)


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "Please enter a number."),
        ("   ", "Please enter a number."),
        ("abc", "Please enter a number, like 12 or 3.5."),
        ("12abc", "Please enter a number, like 12 or 3.5."),
        ("1.2.3", "Please enter a number, like 12 or 3.5."),
        ("-", "Please enter a number, like 12 or 3.5."),
        (".", "Please enter a number, like 12 or 3.5."),
        ("1,00", "Please enter a number, like 12 or 3.5."),  # commas go every 3 digits
        ("1e5", "Please enter a number, like 12 or 3.5."),
        ("1e999", "Please enter a number, like 12 or 3.5."),
        ("nan", "Please enter a number, like 12 or 3.5."),
        ("inf", "Please enter a number, like 12 or 3.5."),
        ("١٢", "Please enter a number, like 12 or 3.5."),  # only 0-9 digits
        ("1" * 31, "That number is too long (at most 30 characters)."),
        ("1000000000000001", "That number is too big. Please use at most 1,000,000,000,000,000."),
    ],
)
def test_numbers_we_refuse(text, message):
    assert parse_number(text) == (None, message)


def test_biggest_allowed_number():
    assert parse_number("1,000,000,000,000,000") == (1e15, None)
    assert parse_number("-1000000000000000") == (-1e15, None)


def test_missing_value():
    data, errors = validate_conversion({"category": "weight", "from": "kilogram", "to": "gram"})
    assert errors == {"value": "Please enter a number."}


@pytest.mark.parametrize("category", ["length", "weight", "area", "volume", "speed", "time", "data"])
def test_negative_values_refused_where_they_make_no_sense(category):
    from converter.units import CATEGORIES

    c = CATEGORIES[category]
    data, errors = validate_conversion(
        {"category": category, "value": "-1", "from": c.default_from, "to": c.default_to}
    )
    assert errors == {"value": f"{c.label} can't be negative."}


def test_zero_and_negative_zero_are_fine():
    assert validate_conversion(params(value="0"))[1] == {}
    assert validate_conversion(params(value="-0"))[1] == {}


@pytest.mark.parametrize(
    "value, unit",
    [("-273.15", "celsius"), ("-459.67", "fahrenheit"), ("0", "kelvin"), ("-40", "celsius"), ("-100", "fahrenheit")],
)
def test_temperatures_down_to_absolute_zero_are_fine(value, unit):
    data, errors = validate_conversion({"category": "temperature", "value": value, "from": unit, "to": "kelvin"})
    assert errors == {}


@pytest.mark.parametrize(
    "value, unit, lowest",
    [("-273.16", "celsius", "-273.15 °C"), ("-500", "fahrenheit", "-459.67 °F"), ("-1", "kelvin", "0 K")],
)
def test_colder_than_absolute_zero_is_refused(value, unit, lowest):
    data, errors = validate_conversion({"category": "temperature", "value": value, "from": unit, "to": "celsius"})
    assert errors == {
        "value": f"That is colder than absolute zero ({lowest}), the lowest temperature possible."
    }


def test_unknown_category():
    data, errors = validate_conversion(params(category="happiness"))
    assert errors == {"category": "Please choose a category from the list."}


def test_unknown_units():
    data, errors = validate_conversion(params(**{"from": "parsec", "to": ""}))
    assert errors == {
        "from": "Please choose a unit from the list.",
        "to": "Please choose a unit from the list.",
    }


def test_unit_from_another_category():
    # "metre" is real, but not a weight.
    data, errors = validate_conversion(params(to="metre"))
    assert errors == {"to": "Please choose a unit from the list."}


def test_all_errors_at_once():
    data, errors = validate_conversion({"category": "weight", "value": "abc", "from": "x", "to": "y"})
    assert set(errors) == {"value", "from", "to"}


def test_fill_defaults_with_nothing():
    assert fill_defaults({}) == {"category": "length", "value": "1", "from": "metre", "to": "foot"}


def test_fill_defaults_for_a_category():
    filled = fill_defaults({"category": "weight", "value": "5"})
    assert filled == {"category": "weight", "value": "5", "from": "kilogram", "to": "pound"}


def test_fill_defaults_keeps_what_was_sent():
    sent = {"category": "weight", "value": "", "from": "gram", "to": "ounce"}
    assert fill_defaults(sent) == sent  # an empty value stays empty


def test_fill_defaults_with_unknown_category():
    filled = fill_defaults({"category": "happiness"})
    assert filled == {"category": "happiness", "value": "1", "from": None, "to": None}
