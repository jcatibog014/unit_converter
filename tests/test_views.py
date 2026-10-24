"""Tests for the web pages, through Flask's test client (no real browser)."""
import pytest


def test_home_page_shows_a_default_conversion(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Unit Converter" in html
    assert "1 m = 3.280839895 ft" in html


def test_page_converts_without_javascript(client):
    response = client.get("/?category=weight&value=1&from=kilogram&to=gram")
    assert response.status_code == 200
    assert "1 kg = 1,000 g" in response.get_data(as_text=True)


def test_category_link_uses_its_default_units(client):
    response = client.get("/?category=temperature&value=100")
    assert "100 °C = 212 °F" in response.get_data(as_text=True)


def test_page_shows_errors_and_keeps_the_input(client):
    response = client.get("/?category=length&value=-5&from=metre&to=foot")
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "Length can&#39;t be negative." in html
    assert 'value="-5"' in html
    assert 'aria-invalid="true"' in html


def test_page_with_unknown_category_still_draws(client):
    response = client.get("/?category=happiness")
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "Please choose a category from the list." in html
    assert '<option value="metre"' in html  # falls back to the length menus


def test_all_units_table_is_off_by_default(client):
    html = client.get("/?category=weight&value=1&from=kilogram&to=gram").get_data(as_text=True)
    assert 'id="all-units" hidden' in html
    assert "Show all units" in html


def test_all_units_table_when_turned_on(client):
    html = client.get("/?category=weight&value=1&from=kilogram&to=gram&all=1").get_data(as_text=True)
    assert 'id="all-units" hidden' not in html
    assert "Hide all units" in html
    assert "1 kg in every unit" in html
    assert "Milligram" in html and "1,000,000" in html


def test_swap_link_swaps_units(client):
    html = client.get("/?category=weight&value=1&from=kilogram&to=gram").get_data(as_text=True)
    assert "from=gram&amp;to=kilogram" in html


def test_api_converts(client):
    response = client.get("/api/convert?category=weight&value=1&from=kilogram&to=gram")
    assert response.status_code == 200
    assert response.get_json() == {
        "result": 1000.0,
        "formatted": "1,000",
        "symbol": "g",
        "input": "1 kg",
        "summary": "1 kg = 1,000 g",
    }


def test_api_all_units(client):
    body = client.get("/api/convert?category=time&value=1&from=hour&to=minute&all=1").get_json()
    rows = {row["unit"]: row["formatted"] for row in body["all"]}
    assert rows["minute"] == "60"
    assert rows["second"] == "3,600"
    assert len(rows) == 7


@pytest.mark.parametrize(
    "query, field",
    [
        ("category=weight&value=abc&from=kilogram&to=gram", "value"),
        ("category=weight&from=kilogram&to=gram", "value"),
        ("category=weight&value=1&from=metre&to=gram", "from"),
        ("category=nope&value=1&from=kilogram&to=gram", "category"),
        ("", "category"),
    ],
)
def test_api_bad_input_gives_400(client, query, field):
    response = client.get("/api/convert?" + query)
    assert response.status_code == 400
    assert field in response.get_json()["errors"]


def test_unknown_page_gives_404(client):
    response = client.get("/nothing-here")
    assert response.status_code == 404
    assert "We couldn&#39;t find that page." in response.get_data(as_text=True)
