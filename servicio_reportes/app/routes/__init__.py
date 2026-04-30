from flask import Flask
from flask import Blueprint

from app.controllers import (
    libros_mas_prestados_controller,
    prestamos_por_usuario_controller,
    retrasos_controller,
    sync_libros_controller,
    sync_lote_controller,
    sync_prestamos_controller,
    sync_usuarios_controller,
)

from app.middlewares.auth import auth_required
from app.routes.health_routes import health_bp


reportes_bp = Blueprint("reportes", __name__, url_prefix="/api/v1/reportes")


@reportes_bp.get("/libros-mas-prestados")
@auth_required
def libros_mas_prestados_endpoint():
    return libros_mas_prestados_controller()


@reportes_bp.get("/prestamos-por-usuario")
@auth_required
def prestamos_por_usuario_endpoint():
    return prestamos_por_usuario_controller()


@reportes_bp.get("/retrasos")
@auth_required
def retrasos_endpoint():
    return retrasos_controller()


@reportes_bp.post("/sync/usuarios")
@auth_required
def sync_usuarios_endpoint():
    return sync_usuarios_controller()


@reportes_bp.post("/sync/libros")
@auth_required
def sync_libros_endpoint():
    return sync_libros_controller()


@reportes_bp.post("/sync/prestamos")
@auth_required
def sync_prestamos_endpoint():
    return sync_prestamos_controller()


@reportes_bp.post("/sync/lote")
@auth_required
def sync_lote_endpoint():
    return sync_lote_controller()


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(reportes_bp)
