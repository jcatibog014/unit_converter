"""The two web pages: the converter page and the JSON API used by app.js.

Both read the same query fields: category, value, from, to and all ("1"
shows the convert-to-all table). The form uses GET, so every conversion
has its own URL that can be bookmarked or shared.

The page works without JavaScript: the server converts and renders the
answer. With JavaScript, app.js asks /api/convert while the user types.
"""
from flask import Blueprint, jsonify, render_template, request, url_for

from .conversions import convert, convert_all, format_number
from .units import CATEGORIES, DEFAULT_CATEGORY
from .validation import fill_defaults, validate_conversion

bp = Blueprint("converter", __name__)


def build_result(data, show_all):
    """Convert checked data and describe the answer for the page or the API."""
    category = CATEGORIES[data["category"]]
    from_unit = category.units[data["from_unit"]]
    to_unit = category.units[data["to_unit"]]
    result = convert(data["value"], data["category"], data["from_unit"], data["to_unit"])
    formatted = format_number(result)
    given = f"{format_number(data['value'])} {from_unit.symbol}"

    payload = {
        "result": result,
        "formatted": formatted,
        "symbol": to_unit.symbol,
        "input": given,  # e.g. "1 kg"
        "summary": f"{given} = {formatted} {to_unit.symbol}",  # e.g. "1 kg = 1,000 g"
    }
    if show_all:
        payload["all"] = [
            {
                "unit": key,
                "label": unit.label,
                "symbol": unit.symbol,
                "result": value,
                "formatted": format_number(value),
            }
            for key, unit, value in convert_all(data["value"], data["category"], data["from_unit"])
        ]
    return payload


def units_for_script():
    """The unit menus as plain data, so app.js can rebuild them."""
    return {
        key: {
            "label": category.label,
            "defaultFrom": category.default_from,
            "defaultTo": category.default_to,
            "units": [[unit_key, unit.label, unit.symbol] for unit_key, unit in category.units.items()],
        }
        for key, category in CATEGORIES.items()
    }


@bp.get("/")
def index():
    params = fill_defaults(request.args)
    show_all = request.args.get("all") == "1"
    data, errors = validate_conversion(params)
    result = None if errors else build_result(data, show_all)

    # Draw the menus for a real category, even if the URL named a wrong one.
    category = params["category"] if params["category"] in CATEGORIES else DEFAULT_CATEGORY

    # Links for visitors without JavaScript. app.js handles these clicks itself.
    def page_url(**changes):
        fields = {"category": category, "value": params["value"],
                  "from": params["from"], "to": params["to"], "all": "1" if show_all else None}
        fields.update(changes)
        return url_for("converter.index", **{k: v for k, v in fields.items() if v is not None})

    return render_template(
        "index.html",
        categories=CATEGORIES,
        category=category,
        params=params,
        errors=errors,
        result=result,
        show_all=show_all,
        category_urls={key: page_url(category=key, **{"from": None, "to": None}) for key in CATEGORIES},
        swap_url=page_url(**{"from": params["to"], "to": params["from"]}),
        toggle_all_url=page_url(all=None if show_all else "1"),
        units_data=units_for_script(),
    ), (400 if errors else 200)


@bp.get("/api/convert")
def api_convert():
    data, errors = validate_conversion(request.args)
    if errors:
        return jsonify(errors=errors), 400
    return jsonify(build_result(data, request.args.get("all") == "1"))
