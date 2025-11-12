"""Route registration helpers for the production API."""

from flask import Flask

from .convert_excel import bp as convert_blueprint
from .save_letter import bp as save_letter_blueprint


def register_routes(app: Flask) -> None:
    app.register_blueprint(convert_blueprint)
    app.register_blueprint(save_letter_blueprint)
