"""Tests for the web pages, through Flask's test client (no real browser)."""
import re

import pytest


def test_home_page_shows_a_default_conversion(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "<title>Swap Meter" in html
    assert 'class="brand-name">Swap <span>Meter</span>' in html
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
        "formula": "Multiply by 1,000",
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


def test_page_shows_the_formula(client):
    html = client.get("/?category=temperature&value=100&from=celsius&to=fahrenheit").get_data(as_text=True)
    assert "°F = °C × 9/5 + 32" in html


def test_popular_chips_link_to_their_pair(client):
    html = client.get("/?category=weight&value=2&from=kilogram&to=gram").get_data(as_text=True)
    assert "kg → lb" in html
    assert "category=weight&amp;value=2&amp;from=kilogram&amp;to=pound" in html
    # The chip for the pair on screen (kg → g) is marked as the current one.
    assert re.search(r'data-from="kilogram" data-to="gram"\s+aria-current="true"', html)
    assert not re.search(r'data-to="pound"\s+aria-current', html)


def test_every_tab_has_an_icon(client):
    html = client.get("/").get_data(as_text=True)
    assert html.count('<svg class="icon"') == 8


def test_error_is_in_the_spoken_summary(client):
    html = client.get("/?category=length&value=abc&from=metre&to=foot").get_data(as_text=True)
    assert 'aria-live="polite">Please enter a number, like 12 or 3.5.</p>' in html


def test_script_data_allows_minus_only_for_temperature():
    from converter.views import units_for_script

    data = units_for_script()
    assert [key for key, c in data.items() if c["allowNegative"]] == ["temperature"]
    assert data["weight"]["popular"][0] == {"from": "kilogram", "to": "pound", "label": "kg → lb"}


def test_page_without_javascript(client):
    # This is the HTML before any script runs: buttons that need JS start
    # hidden, and the plain Convert button and links are there.
    html = client.get("/?category=temperature&value=5&from=celsius&to=kelvin").get_data(as_text=True)
    assert re.search(r'id="sign" hidden', html)
    assert re.search(r'id="clear" hidden', html)
    assert re.search(r'id="copy" hidden', html)
    assert 'type="submit" class="btn btn-primary convert-btn">Convert</button>' in html
    assert 'href="/?category=temperature&amp;value=5&amp;from=fahrenheit&amp;to=celsius"' in html  # a chip


def test_logo_and_app_icons_are_linked(client):
    html = client.get("/").get_data(as_text=True)
    assert '<svg class="brand-logo"' in html  # the logo in the header
    assert 'href="/static/icons/logo.svg" type="image/svg+xml"' in html
    assert 'rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png"' in html
    assert 'rel="manifest" href="/static/site.webmanifest"' in html


def test_manifest_names_the_app_and_its_icons_exist(client):
    response = client.get("/static/site.webmanifest")
    assert response.status_code == 200
    assert response.mimetype == "application/manifest+json"
    manifest = response.get_json(force=True)
    assert manifest["name"] == "Swap Meter"
    for icon in manifest["icons"]:
        assert client.get("/static/" + icon["src"]).status_code == 200


@pytest.mark.parametrize("path", ["icons/icon-32.png", "icons/apple-touch-icon.png", "icons/logo.svg"])
def test_icon_files_are_served(client, path):
    assert client.get("/static/" + path).status_code == 200
