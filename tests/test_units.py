"""Tests for the unit data: a typo in units.py should fail here, not on the page."""
import pytest

from converter.units import ABSOLUTE_ZERO, CATEGORIES, DEFAULT_CATEGORY


@pytest.mark.parametrize("key", CATEGORIES)
def test_popular_pairs_use_real_units(key):
    category = CATEGORIES[key]
    assert 3 <= len(category.popular) <= 4
    for from_unit, to_unit in category.popular:
        assert from_unit in category.units
        assert to_unit in category.units
        assert from_unit != to_unit


@pytest.mark.parametrize("key", CATEGORIES)
def test_default_units_are_real(key):
    category = CATEGORIES[key]
    assert category.default_from in category.units
    assert category.default_to in category.units


def test_default_category_is_real():
    assert DEFAULT_CATEGORY in CATEGORIES


def test_only_temperature_allows_negatives():
    assert [key for key, c in CATEGORIES.items() if c.allow_negative] == ["temperature"]
    assert set(ABSOLUTE_ZERO) == set(CATEGORIES["temperature"].units)
