"""Route registration helpers for the production API."""

from flask import Flask

from .convert_excel import bp as convert_blueprint
from .save_letter import bp as save_letter_blueprint
from .aliases import bp as aliases_blueprint
from .review_routes import bp as review_blueprint


def register_routes(app: Flask) -> None:
    app.register_blueprint(convert_blueprint)
    app.register_blueprint(save_letter_blueprint)
    app.register_blueprint(aliases_blueprint)
    app.register_blueprint(review_blueprint)
