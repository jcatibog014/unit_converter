"""Unit Converter.

Flask builds the app inside create_app() (the "app factory" pattern).
Tests call it with their own settings, so each test gets a fresh app.
"""
from flask import Flask, render_template


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.update(test_config)

    from . import views

    app.register_blueprint(views.bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, message="We couldn't find that page."), 404

    return app
