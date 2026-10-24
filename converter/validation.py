"""Checking what the user typed before we convert it.

validate_conversion() is a plain function: the submitted fields go in, and
clean data plus error messages come out. It doesn't use Flask, which makes
it easy to test (see tests/test_validation.py).

The rule: never trust input. A URL can hold anything, so even the menus
(category and units) are checked, not only the number box.
"""
import re

from .units import ABSOLUTE_ZERO, CATEGORIES, DEFAULT_CATEGORY

VALUE_MAX_LENGTH = 30
VALUE_LIMIT = 1e15  # no bigger than a million billion, either way

# A sign, then digits (commas allowed every 3 digits, like 1,250,000),
# then maybe a decimal part. "1e5", "nan" and "inf" don't match, on purpose.
NUMBER_FORMAT = re.compile(
    r"""
    [+-]?
    (?: [0-9]{1,3} (?: ,[0-9]{3} )+ | [0-9]+ )?   # whole part
    (?: \.[0-9]* )?                               # decimal part
    """,
    re.VERBOSE,
)


def fill_defaults(params):
    """Fill in the fields a visitor left out, so the page always has a value.

    Opening "/" with nothing shows "1 metre in feet". Choosing a category
    without units picks that category's usual pair. A field that was sent
    empty stays empty, so validation can say what's wrong.
    """
    category = params.get("category") or DEFAULT_CATEGORY
    filled = {
        "category": category,
        "value": params.get("value", "1"),
        "from": params.get("from"),
        "to": params.get("to"),
    }
    if category in CATEGORIES:
        filled["from"] = filled["from"] or CATEGORIES[category].default_from
        filled["to"] = filled["to"] or CATEGORIES[category].default_to
    return filled


def parse_number(text):
    """Return (number, error). Exactly one of the two is None."""
    text = text.strip()
    if not text:
        return None, "Please enter a number."
    if len(text) > VALUE_MAX_LENGTH:
        return None, f"That number is too long (at most {VALUE_MAX_LENGTH} characters)."
    if not NUMBER_FORMAT.fullmatch(text) or not any(c.isdigit() for c in text):
        return None, "Please enter a number, like 12 or 3.5."
    number = float(text.replace(",", ""))
    if abs(number) > VALUE_LIMIT:
        return None, "That number is too big. Please use at most 1,000,000,000,000,000."
    return number, None


def validate_conversion(params):
    """Return (data, errors).

    params -- the submitted fields: category, value, from and to
              (request.args or a plain dict)

    `data` holds the cleaned values: category, value (a float), from_unit
    and to_unit. `errors` maps a field name to a message, and the input is
    valid when it's empty. When there are errors, don't use `data`.
    """
    errors = {}
    category_key = (params.get("category") or "").strip()
    from_unit = (params.get("from") or "").strip()
    to_unit = (params.get("to") or "").strip()

    value, value_error = parse_number(params.get("value") or "")
    if value_error:
        errors["value"] = value_error

    category = CATEGORIES.get(category_key)
    if category is None:
        errors["category"] = "Please choose a category from the list."
    else:
        if from_unit not in category.units:
            errors["from"] = "Please choose a unit from the list."
        if to_unit not in category.units:
            errors["to"] = "Please choose a unit from the list."

        # Only check the size of a number we understood, in a unit we know.
        if "value" not in errors and "from" not in errors:
            if category_key == "temperature" and value < ABSOLUTE_ZERO[from_unit]:
                symbol = category.units[from_unit].symbol
                lowest = f"{ABSOLUTE_ZERO[from_unit]:g} {symbol}"
                errors["value"] = (
                    f"That is colder than absolute zero ({lowest}), "
                    "the lowest temperature possible."
                )
            elif not category.allow_negative and value < 0:
                errors["value"] = f"{category.label} can't be negative."

    data = {
        "category": category_key,
        "value": value,
        "from_unit": from_unit,
        "to_unit": to_unit,
    }
    return data, errors
