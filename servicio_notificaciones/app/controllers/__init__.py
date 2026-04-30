from __future__ import annotations

from typing import Any

from flask import Response, current_app, jsonify, request

from app.errors import ApiError
from app.services import (
    create_notification,
    create_reminder_48h_before_due,
    get_notification,
    process_pending_notifications,
)


def _extract_json() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(
            "INVALID_REQUEST_BODY",
            "El cuerpo de la peticion debe ser JSON valido.",
            400,
        )
    return data


def _success_response(data: Any, message: str, status_code: int = 200) -> tuple[Response, int]:
    return jsonify({"success": True, "data": data, "message": message}), status_code


def create_notification_controller() -> tuple[Response, int]:
    data = create_notification(
        _extract_json(),
        default_max_retries=current_app.config["MAX_REINTENTOS_ENVIO"],
    )
    return _success_response(data, "Notificacion creada correctamente.", 201)


def create_48h_reminder_controller() -> tuple[Response, int]:
    data = create_reminder_48h_before_due(
        _extract_json(),
        default_max_retries=current_app.config["MAX_REINTENTOS_ENVIO"],
    )
    return _success_response(data, "Recordatorio 48h programado correctamente.", 201)


def get_notification_controller(notification_id: int) -> tuple[Response, int]:
    data = get_notification(notification_id)
    return _success_response(data, "Notificacion obtenida correctamente.")


def process_queue_controller() -> tuple[Response, int]:
    data = process_pending_notifications(
        batch_size=current_app.config["NOTIFICATIONS_WORKER_BATCH_SIZE"],
        smtp_host=current_app.config["SMTP_HOST"],
        smtp_port=current_app.config["SMTP_PORT"],
        smtp_username=current_app.config["SMTP_USERNAME"],
        smtp_password=current_app.config["SMTP_PASSWORD"],
        smtp_use_tls=current_app.config["SMTP_USE_TLS"],
        smtp_use_ssl=current_app.config["SMTP_USE_SSL"],
        smtp_timeout_seconds=current_app.config["SMTP_TIMEOUT_SECONDS"],
        from_email=current_app.config["SMTP_FROM_EMAIL"],
        from_name=current_app.config["SMTP_FROM_NAME"],
        retry_base_delay_minutes=current_app.config["RETRY_BASE_DELAY_MINUTES"],
    )
    return _success_response(data, "Cola procesada correctamente.")
