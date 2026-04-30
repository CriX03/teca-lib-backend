from flask import Flask

from app.routes.auth_routes import users_bp
from app.routes.health_routes import health_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)
