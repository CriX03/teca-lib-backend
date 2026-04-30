from flask import Flask
from flask import Blueprint

from app.controllers import (
    create_48h_reminder_controller,
    create_notification_controller,
    get_notification_controller,
    process_queue_controller,
)

from app.middlewares.auth import auth_required
from app.routes.health_routes import health_bp


notifications_bp = Blueprint(
    "notificaciones",
    __name__,
    url_prefix="/api/v1/notificaciones",
)


@notifications_bp.post("")
@auth_required
def create_notification_endpoint():
    return create_notification_controller()


@notifications_bp.post("/recordatorios/48h")
@auth_required
def create_48h_reminder_endpoint():
    return create_48h_reminder_controller()


@notifications_bp.get("/<int:notification_id>")
@auth_required
def get_notification_endpoint(notification_id: int):
    return get_notification_controller(notification_id)


@notifications_bp.post("/process-queue")
@auth_required
def process_queue_endpoint():
    return process_queue_controller()


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(notifications_bp)
