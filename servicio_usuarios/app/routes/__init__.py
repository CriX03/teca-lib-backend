"""
Registro de rutas del servicio de usuarios.

Este modulo registra todos los blueprints de la aplicacion en la instancia Flask.
Los blueprints definen grupos de rutas relacionadas que se montan en la aplicacion.

Blueprints registrados:
    - health_bp: Endpoints de verificacion de salud (/health).
    - users_bp: Endpoints de autenticacion (/api/v1/auth/*).
"""

from flask import Flask

from app.routes.auth_routes import users_bp
from app.routes.health_routes import health_bp


def register_routes(app: Flask) -> None:
    """Registra todos los blueprints en la aplicacion Flask."""

    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)