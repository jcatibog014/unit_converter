"""Every unit the converter knows, grouped by category.

This file is data only, with no logic. Each linear category picks one
"base" unit, and every unit stores how many base units make one of it.
For example, the length base is the metre and a kilometre has factor 1000.
Converting is then: value * from_factor / to_factor (see conversions.py).

Temperature is different: 0 °C is not 0 °F, so a factor is not enough.
Its units have factor None and conversions.py converts them through Celsius.

The factors are exact, from the international definitions
(for example, 1 inch is exactly 0.0254 metres).
"""
from typing import NamedTuple


class Unit(NamedTuple):
    label: str       # shown in menus, e.g. "Kilogram"
    symbol: str      # shown next to numbers, e.g. "kg"
    factor: float | None  # base units in one of this unit (None for temperature)


class Category(NamedTuple):
    label: str
    units: dict[str, Unit]
    default_from: str
    default_to: str
    allow_negative: bool  # can a value below zero make sense?


CATEGORIES = {
    "length": Category(
        label="Length",
        units={
            "millimetre": Unit("Millimetre", "mm", 0.001),
            "centimetre": Unit("Centimetre", "cm", 0.01),
            "metre": Unit("Metre", "m", 1),
            "kilometre": Unit("Kilometre", "km", 1000),
            "inch": Unit("Inch", "in", 0.0254),
            "foot": Unit("Foot", "ft", 0.3048),
            "yard": Unit("Yard", "yd", 0.9144),
            "mile": Unit("Mile", "mi", 1609.344),
            "nautical_mile": Unit("Nautical mile", "nmi", 1852),
        },
        default_from="metre",
        default_to="foot",
        allow_negative=False,
    ),
    "weight": Category(
        label="Weight",
        units={
            "milligram": Unit("Milligram", "mg", 0.000001),
            "gram": Unit("Gram", "g", 0.001),
            "kilogram": Unit("Kilogram", "kg", 1),
            "tonne": Unit("Tonne", "t", 1000),
            "ounce": Unit("Ounce", "oz", 0.028349523125),
            "pound": Unit("Pound", "lb", 0.45359237),
            "stone": Unit("Stone", "st", 6.35029318),
        },
        default_from="kilogram",
        default_to="pound",
        allow_negative=False,
    ),
    "temperature": Category(
        label="Temperature",
        units={
            "celsius": Unit("Celsius", "°C", None),
            "fahrenheit": Unit("Fahrenheit", "°F", None),
            "kelvin": Unit("Kelvin", "K", None),
        },
        default_from="celsius",
        default_to="fahrenheit",
        allow_negative=True,  # but not below absolute zero, see ABSOLUTE_ZERO
    ),
    "area": Category(
        label="Area",
        units={
            "square_millimetre": Unit("Square millimetre", "mm²", 0.000001),
            "square_centimetre": Unit("Square centimetre", "cm²", 0.0001),
            "square_metre": Unit("Square metre", "m²", 1),
            "hectare": Unit("Hectare", "ha", 10000),
            "square_kilometre": Unit("Square kilometre", "km²", 1000000),
            "square_inch": Unit("Square inch", "in²", 0.00064516),
            "square_foot": Unit("Square foot", "ft²", 0.09290304),
            "square_yard": Unit("Square yard", "yd²", 0.83612736),
            "acre": Unit("Acre", "ac", 4046.8564224),
            "square_mile": Unit("Square mile", "mi²", 2589988.110336),
        },
        default_from="square_metre",
        default_to="square_foot",
        allow_negative=False,
    ),
    "volume": Category(
        label="Volume",
        units={
            "millilitre": Unit("Millilitre", "mL", 0.001),
            "litre": Unit("Litre", "L", 1),
            "cubic_metre": Unit("Cubic metre", "m³", 1000),
            "teaspoon": Unit("Teaspoon (US)", "tsp", 0.00492892159375),
            "tablespoon": Unit("Tablespoon (US)", "tbsp", 0.01478676478125),
            "fluid_ounce": Unit("Fluid ounce (US)", "fl oz", 0.0295735295625),
            "cup": Unit("Cup (US)", "cup", 0.2365882365),
            "pint": Unit("Pint (US)", "pt", 0.473176473),
            "quart": Unit("Quart (US)", "qt", 0.946352946),
            "gallon": Unit("Gallon (US)", "gal", 3.785411784),
            "imperial_gallon": Unit("Gallon (UK)", "gal (UK)", 4.54609),
        },
        default_from="litre",
        default_to="gallon",
        allow_negative=False,
    ),
    "speed": Category(
        label="Speed",
        units={
            "metre_per_second": Unit("Metre per second", "m/s", 1),
            "kilometre_per_hour": Unit("Kilometre per hour", "km/h", 1000 / 3600),
            "mile_per_hour": Unit("Mile per hour", "mph", 0.44704),
            "foot_per_second": Unit("Foot per second", "ft/s", 0.3048),
            "knot": Unit("Knot", "kn", 1852 / 3600),
        },
        default_from="kilometre_per_hour",
        default_to="mile_per_hour",
        allow_negative=False,
    ),
    "time": Category(
        label="Time",
        units={
            "millisecond": Unit("Millisecond", "ms", 0.001),
            "second": Unit("Second", "s", 1),
            "minute": Unit("Minute", "min", 60),
            "hour": Unit("Hour", "h", 3600),
            "day": Unit("Day", "d", 86400),
            "week": Unit("Week", "wk", 604800),
            "year": Unit("Year (365 days)", "yr", 31536000),
        },
        default_from="hour",
        default_to="minute",
        allow_negative=False,
    ),
    "data": Category(
        label="Digital storage",
        units={
            "bit": Unit("Bit", "bit", 0.125),
            "byte": Unit("Byte", "B", 1),
            # KB, MB... count in thousands; KiB, MiB... count in 1024s.
            "kilobyte": Unit("Kilobyte", "KB", 1000),
            "megabyte": Unit("Megabyte", "MB", 1000**2),
            "gigabyte": Unit("Gigabyte", "GB", 1000**3),
            "terabyte": Unit("Terabyte", "TB", 1000**4),
            "kibibyte": Unit("Kibibyte", "KiB", 1024),
            "mebibyte": Unit("Mebibyte", "MiB", 1024**2),
            "gibibyte": Unit("Gibibyte", "GiB", 1024**3),
        },
        default_from="gigabyte",
        default_to="megabyte",
        allow_negative=False,
    ),
}

DEFAULT_CATEGORY = "length"

# The coldest possible temperature in each unit. Nothing can be colder.
ABSOLUTE_ZERO = {"celsius": -273.15, "fahrenheit": -459.67, "kelvin": 0}
