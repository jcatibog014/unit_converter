# AGENTS.md

This file guides AI coding agents (Claude Code, Codex, Cursor, Copilot and others) working in this repository.

## Overview

A unit converter web app in Python (Flask, no database, no login). It is a learning project for pure functions, input validation and test cases. Keep the code readable for a learner: short comments that explain *why*, and no extra libraries unless the owner asks for them. The README is written in simple (A1-level) English on purpose; keep it that way.

Python 3.13 is at `%LOCALAPPDATA%\Programs\Python\Python313\python.exe`. Use the virtual environment:

- Install: `.venv\Scripts\python -m pip install -r requirements.txt` (create `.venv` with `python -m venv .venv` first if it's missing).
- Run: `.venv\Scripts\flask --app converter run --debug`, then open http://127.0.0.1:5000.
- Test: `.venv\Scripts\python -m pytest`.

## Architecture

- `converter/__init__.py` holds `create_app(test_config)` and the 404 handler (renders `error.html`).
- `converter/units.py` is data only. `CATEGORIES` maps a category key to a `Category` (label, units, default_from, default_to, allow_negative). Each `Unit` has a label, symbol and `factor` (how many base units make one of it). Temperature units have `factor=None`; `ABSOLUTE_ZERO` gives each one's lowest value.
  - To add a unit, add one line to its category. Use exact factors. The round-trip test in `tests/test_conversions.py` covers new units automatically; add a known-value test too.
  - To add a category, also add its label to the README table. `allow_negative` decides if values below zero are refused.
- `converter/conversions.py` holds pure functions only (no Flask, no I/O): `convert()` (through the base unit, or through Celsius for temperature), `convert_all()` and `format_number()` (10 significant digits, thousands commas, `× 10ⁿ` outside 1e-6..1e15).
- `converter/validation.py` must not import Flask. `validate_conversion(params)` returns `(data, errors)`; errors map a field (`value`, `category`, `from`, `to`) to a message. `parse_number()` accepts digits, one decimal point, a sign and correctly grouped thousands commas; it refuses `1e5`, `nan`, `inf`, more than 30 characters and values beyond ±1e15. `fill_defaults()` fills fields missing from the page URL.
- `converter/views.py` is the `converter` blueprint. Both routes read the query fields `category`, `value`, `from`, `to` and `all` (`"1"` shows the convert-to-all table).
  - `GET /` renders `index.html` on the server, so the page works without JavaScript. Invalid input re-renders with HTTP 400 and keeps the user's input. Tabs, swap and the all-units toggle are plain links built by `page_url()`.
  - `GET /api/convert` returns the `build_result()` JSON (`result`, `formatted`, `symbol`, `input`, `summary`, and `all` when asked), or 400 with `{errors}`.
- `converter/static/app.js` progressively enhances the page: it calls the API 250 ms after typing stops, intercepts the tab/swap/toggle links, keeps the URL in step with `history.replaceState`, and handles the copy button and the theme toggle (saved in `localStorage` inside try/catch). The unit menus come from the `units-data` JSON in `index.html`. Build DOM with `textContent`, never `innerHTML`.
- Each field shows its error in `<p class="error" id="{field}-error">`.

## Conventions

- Styling: `converter/static/style.css`, with colours as CSS variables on `:root`. Dark mode redefines them under `prefers-color-scheme: dark` (unless `data-theme="light"`) and under `[data-theme="dark"]`; change both blocks together. The phone breakpoint is 520px.
- Keep comments teaching-oriented but brief. Add or update a test with every behaviour change.
- README screenshots live in `docs/screenshots/`. Retake them when the UI changes visibly.
