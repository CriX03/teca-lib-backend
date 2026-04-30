from flask import Flask
from flask import Blueprint
from app.controllers import (
    create_prestamo_controller,
    devolver_prestamo_controller,
    get_prestamo_controller,
    list_mis_prestamos_controller,
)
from app.routes.health_routes import health_bp
prestamos_bp = Blueprint("prestamos", __name__, url_prefix="/api/v1/prestamos")

@prestamos_bp.route("", methods=["POST"])
def create_prestamo_endpoint():
    return create_prestamo_controller()

@prestamos_bp.route("/mis-prestamos", methods=["GET"])
def list_mis_prestamos_endpoint():
    return list_mis_prestamos_controller()

@prestamos_bp.route("/<int:prestamo_id>", methods=["GET"])
def get_prestamo_endpoint(prestamo_id: int):
    return get_prestamo_controller(prestamo_id)

@prestamos_bp.route("/<int:prestamo_id>/devolucion", methods=["POST"])
def devolver_prestamo_endpoint(prestamo_id: int):
    return devolver_prestamo_controller(prestamo_id)

def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(prestamos_bp)