# AGENTS.md

This file guides AI coding agents (Claude Code, Codex, Cursor, Copilot and others) working in this repository.

## Overview

**Swap Meter**, a unit converter web app in Python (Flask, no database, no login). The Python package is still called `converter`. It is a learning project for pure functions, input validation and test cases. Keep the code readable for a learner: short comments that explain *why*, and no extra libraries unless the owner asks for them. The README is written in simple (A1-level) English on purpose; keep it that way.

Python 3.13 is at `%LOCALAPPDATA%\Programs\Python\Python313\python.exe`. Use the virtual environment:

- Install: `.venv\Scripts\python -m pip install -r requirements.txt` (create `.venv` with `python -m venv .venv` first if it's missing).
- Run: `.venv\Scripts\flask --app converter run --debug`, then open http://127.0.0.1:5000.
- Test: `.venv\Scripts\python -m pytest`.

## Architecture

- `converter/__init__.py` holds `create_app(test_config)` and the 404 handler (renders `error.html`).
- `converter/units.py` is data only. `CATEGORIES` maps a category key to a `Category` (label, units, default_from, default_to, allow_negative, popular). `popular` holds 3–4 `(from, to)` quick-pick pairs shown as chips; `tests/test_units.py` checks they are real units. Each `Unit` has a label, symbol and `factor` (how many base units make one of it). Temperature units have `factor=None`; `ABSOLUTE_ZERO` gives each one's lowest value.
  - To add a unit, add one line to its category. Use exact factors. The round-trip test in `tests/test_conversions.py` covers new units automatically; add a known-value test too.
  - To add a category, also add its label to the README table. `allow_negative` decides if values below zero are refused.
- `converter/conversions.py` holds pure functions only (no Flask, no I/O): `convert()` (through the base unit, or through Celsius for temperature), `convert_all()`, `format_number()` (10 significant digits, thousands commas, `× 10ⁿ` outside 1e-6..1e15) and `describe_formula()` (the "Multiply by …" / "Divide by …" line; temperature uses `TEMPERATURE_FORMULAS`).
- `converter/validation.py` must not import Flask. `validate_conversion(params)` returns `(data, errors)`; errors map a field (`value`, `category`, `from`, `to`) to a message. `parse_number()` accepts digits, one decimal point, a sign and correctly grouped thousands commas; it refuses `1e5`, `nan`, `inf`, more than 30 characters and values beyond ±1e15. `fill_defaults()` fills fields missing from the page URL.
- `converter/views.py` is the `converter` blueprint. Both routes read the query fields `category`, `value`, `from`, `to` and `all` (`"1"` shows the convert-to-all table).
  - `GET /` renders `index.html` on the server, so the page works without JavaScript. Invalid input re-renders with HTTP 400 and keeps the user's input. Tabs, swap and the all-units toggle are plain links built by `page_url()`.
  - `GET /api/convert` returns the `build_result()` JSON (`result`, `formatted`, `symbol`, `input`, `summary`, `formula`, and `all` when asked), or 400 with `{errors}`.
  - `units_for_script()` is the `units-data` JSON for app.js: units, defaults, `allowNegative` and `popular` (from `popular_pairs()`).
- `converter/templates/_icons.html` has the `category_icon(key)` macro (inline SVG, `currentColor`, `aria-hidden`). A new category needs an icon there.
- `converter/static/app.js` progressively enhances the page: it calls the API 250 ms after typing stops, intercepts the tab/swap/chip/toggle links, keeps the URL in step with `history.replaceState`, and handles the copy button and the theme toggle (saved in `localStorage` inside try/catch). Build DOM with `textContent`, never `innerHTML`.
  - The ± button shows only when the category has `allowNegative` (temperature); the × button only when the box isn't empty. Both start `hidden` in the HTML because they need JS.
  - An empty box (or just `-`, `+`, `.`) shows the calm "Type a number to convert." instead of calling the API.
  - Keys: `/` focuses the value box, `Esc` in it clears it.
- Each field shows its error in `<p class="error" id="{field}-error">`. Only `#result-summary` is `aria-live`; on errors it holds the first error message, so screen readers hear it.

## Conventions

- Styling: `converter/static/style.css`, with colours as CSS variables on `:root`. Dark mode redefines them under `prefers-color-scheme: dark` (unless `data-theme="light"`) and under `[data-theme="dark"]`; change both blocks together. The phone breakpoint is 520px; there the tabs and chips become one swipeable row.
- Brand: the palette comes from the logo, deep teal `#0f3d3e` (`--accent`, `--logo-teal`) and orange `#c76e00` (`--logo-orange`, focus ring). Orange *text* uses the darker `--highlight` (`#9a5200` light, `#f0a04b` dark) to keep 4.5:1. The logo drawing lives twice, in `templates/_logo.html` (inline, themed through `.logo-teal`/`.logo-orange`) and `static/icons/logo.svg` (favicon, own dark-mode style); keep them in sync. The PNG icons in `static/icons/` and `site.webmanifest` are rendered from `logo.svg`; `docs/brand/swap-meter-logo.png` is the owner's original.
- Accessibility rules (see `docs/UI_UX_PLAN.md`): text colours ≥ 4.5:1 and `--control-border` ≥ 3:1 against the card in both themes; touch targets ≥ 44px on phones; every icon-only button has an `aria-label`.
- Keep comments teaching-oriented but brief. Add or update a test with every behaviour change.
- README screenshots live in `docs/screenshots/`. Retake them when the UI changes visibly.
