from __future__ import annotations

import smtplib
import threading
import time
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from typing import Any

from flask import Flask
from sqlalchemy import or_

from app.errors import ApiError
from app.extensions import db
from app.models import (
    ESTADO_ENVIADA,
    ESTADO_FALLIDA,
    ESTADO_PENDIENTE,
    ESTADO_REINTENTO,
    Notificacion,
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def _parse_iso_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser una fecha ISO8601 valida.",
            422,
        )

    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser una fecha ISO8601 valida.",
            422,
        ) from error

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    else:
        parsed = parsed.astimezone(UTC)

    return parsed


def _clean_positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser un entero positivo.",
            422,
        )
    return value


def _clean_email(value: Any) -> str:
    if not isinstance(value, str):
        raise ApiError(
            "VALIDATION_ERROR",
            "El campo 'destinatario_email' debe ser un email valido.",
            422,
        )

    email = value.strip().lower()
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ApiError(
            "VALIDATION_ERROR",
            "El campo 'destinatario_email' debe ser un email valido.",
            422,
        )

    return email


def _clean_text(value: Any, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' es obligatorio y debe ser texto.",
            422,
        )

    clean_value = value.strip()
    if not clean_value:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' es obligatorio y debe ser texto.",
            422,
        )

    if len(clean_value) > max_length:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' no puede superar {max_length} caracteres.",
            422,
        )

    return clean_value


def _clean_max_reintentos(value: Any, default_value: int) -> int:
    if value is None:
        return default_value
    retries = _clean_positive_int(value, "max_reintentos")
    if retries > 20:
        raise ApiError(
            "VALIDATION_ERROR",
            "El campo 'max_reintentos' no puede superar 20.",
            422,
        )
    return retries


def _send_email_via_smtp(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    smtp_use_tls: bool,
    smtp_use_ssl: bool,
    smtp_timeout_seconds: float,
    from_email: str,
    from_name: str,
    destinatario_email: str,
    asunto: str,
    mensaje: str,
) -> None:
    email_message = EmailMessage()
    email_message["From"] = f"{from_name} <{from_email}>"
    email_message["To"] = destinatario_email
    email_message["Subject"] = asunto
    email_message.set_content(mensaje)

    smtp_class = smtplib.SMTP_SSL if smtp_use_ssl else smtplib.SMTP
    with smtp_class(host=smtp_host, port=smtp_port, timeout=smtp_timeout_seconds) as smtp_client:
        smtp_client.ehlo()
        if smtp_use_tls and not smtp_use_ssl:
            smtp_client.starttls()
            smtp_client.ehlo()
        if smtp_username:
            smtp_client.login(smtp_username, smtp_password)
        smtp_client.send_message(email_message)


def create_notification(
    payload: dict[str, Any],
    *,
    default_max_retries: int,
) -> dict[str, int | str | None]:
    usuario_id = _clean_positive_int(payload.get("usuario_id"), "usuario_id")
    prestamo_id_raw = payload.get("prestamo_id")
    prestamo_id = None
    if prestamo_id_raw is not None:
        prestamo_id = _clean_positive_int(prestamo_id_raw, "prestamo_id")

    tipo_raw = payload.get("tipo", "general")
    tipo = _clean_text(tipo_raw, "tipo", 50)
    destinatario_email = _clean_email(payload.get("destinatario_email"))
    asunto = _clean_text(payload.get("asunto"), "asunto", 255)
    mensaje = _clean_text(payload.get("mensaje"), "mensaje", 10000)
    fecha_programada_raw = payload.get("fecha_programada")
    fecha_programada = (
        _parse_iso_datetime(fecha_programada_raw, "fecha_programada")
        if fecha_programada_raw is not None
        else now_utc()
    )
    max_reintentos = _clean_max_reintentos(payload.get("max_reintentos"), default_max_retries)

    notificacion = Notificacion()
    notificacion.usuario_id = usuario_id
    notificacion.prestamo_id = prestamo_id
    notificacion.tipo = tipo
    notificacion.destinatario_email = destinatario_email
    notificacion.asunto = asunto
    notificacion.mensaje = mensaje
    notificacion.fecha_programada = fecha_programada
    notificacion.estado = ESTADO_PENDIENTE
    notificacion.reintentos = 0
    notificacion.max_reintentos = max_reintentos

    db.session.add(notificacion)
    db.session.commit()

    return notificacion.to_dict()


def create_reminder_48h_before_due(
    payload: dict[str, Any],
    *,
    default_max_retries: int,
) -> dict[str, int | str | None]:
    usuario_id = _clean_positive_int(payload.get("usuario_id"), "usuario_id")
    prestamo_id = _clean_positive_int(payload.get("prestamo_id"), "prestamo_id")
    destinatario_email = _clean_email(payload.get("destinatario_email"))
    fecha_limite = _parse_iso_datetime(payload.get("fecha_limite"), "fecha_limite")

    libro_titulo_raw = payload.get("libro_titulo", "el libro prestado")
    libro_titulo = _clean_text(libro_titulo_raw, "libro_titulo", 255)

    fecha_programada = fecha_limite - timedelta(hours=48)
    if fecha_programada < now_utc():
        fecha_programada = now_utc()

    notificacion = Notificacion()
    notificacion.usuario_id = usuario_id
    notificacion.prestamo_id = prestamo_id
    notificacion.tipo = "recordatorio_48h"
    notificacion.destinatario_email = destinatario_email
    notificacion.asunto = "Recordatorio de devolucion (48h)"
    notificacion.mensaje = (
        "Tu prestamo vence en menos de 48 horas. "
        f"Por favor devuelve '{libro_titulo}' antes de la fecha limite."
    )
    notificacion.fecha_programada = fecha_programada
    notificacion.estado = ESTADO_PENDIENTE
    notificacion.reintentos = 0
    notificacion.max_reintentos = default_max_retries

    db.session.add(notificacion)
    db.session.commit()

    return notificacion.to_dict()


def get_notification(notification_id: int) -> dict[str, int | str | None]:
    notification = Notificacion.query.filter_by(id=notification_id).first()
    if notification is None:
        raise ApiError("NOTIFICATION_NOT_FOUND", "Notificacion no encontrada.", 404)
    return notification.to_dict()


def _compute_next_retry(
    *,
    base_delay_minutes: int,
    current_retries: int,
) -> datetime:
    multiplier = 2 ** max(current_retries - 1, 0)
    return now_utc() + timedelta(minutes=base_delay_minutes * multiplier)


def process_pending_notifications(
    *,
    batch_size: int,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    smtp_use_tls: bool,
    smtp_use_ssl: bool,
    smtp_timeout_seconds: float,
    from_email: str,
    from_name: str,
    retry_base_delay_minutes: int,
) -> dict[str, int]:
    current_time = now_utc()
    pending_states = [ESTADO_PENDIENTE, ESTADO_REINTENTO]

    due_notifications = (
        Notificacion.query.filter(Notificacion.estado.in_(pending_states))
        .filter(Notificacion.fecha_programada <= current_time)
        .filter(
            or_(
                Notificacion.proximo_reintento.is_(None),
                Notificacion.proximo_reintento <= current_time,
            )
        )
        .order_by(Notificacion.fecha_programada.asc(), Notificacion.id.asc())
        .limit(batch_size)
        .all()
    )

    processed = 0
    sent = 0
    failed = 0

    for notification in due_notifications:
        processed += 1
        try:
            _send_email_via_smtp(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                smtp_use_tls=smtp_use_tls,
                smtp_use_ssl=smtp_use_ssl,
                smtp_timeout_seconds=smtp_timeout_seconds,
                from_email=from_email,
                from_name=from_name,
                destinatario_email=notification.destinatario_email,
                asunto=notification.asunto,
                mensaje=notification.mensaje,
            )
            notification.estado = ESTADO_ENVIADA
            notification.fecha_envio = now_utc()
            notification.proximo_reintento = None
            notification.ultimo_error = None
            sent += 1
        except Exception as error:
            notification.reintentos += 1
            notification.ultimo_error = str(error)
            if notification.reintentos >= notification.max_reintentos:
                notification.estado = ESTADO_FALLIDA
                notification.proximo_reintento = None
            else:
                notification.estado = ESTADO_REINTENTO
                notification.proximo_reintento = _compute_next_retry(
                    base_delay_minutes=retry_base_delay_minutes,
                    current_retries=notification.reintentos,
                )
            failed += 1

    db.session.commit()
    return {"processed": processed, "sent": sent, "failed": failed}


def _run_worker_loop(app: Flask) -> None:
    interval_seconds = app.config["NOTIFICATIONS_WORKER_INTERVAL_SECONDS"]
    with app.app_context():
        while True:
            try:
                result = process_pending_notifications(
                    batch_size=app.config["NOTIFICATIONS_WORKER_BATCH_SIZE"],
                    smtp_host=app.config["SMTP_HOST"],
                    smtp_port=app.config["SMTP_PORT"],
                    smtp_username=app.config["SMTP_USERNAME"],
                    smtp_password=app.config["SMTP_PASSWORD"],
                    smtp_use_tls=app.config["SMTP_USE_TLS"],
                    smtp_use_ssl=app.config["SMTP_USE_SSL"],
                    smtp_timeout_seconds=app.config["SMTP_TIMEOUT_SECONDS"],
                    from_email=app.config["SMTP_FROM_EMAIL"],
                    from_name=app.config["SMTP_FROM_NAME"],
                    retry_base_delay_minutes=app.config["RETRY_BASE_DELAY_MINUTES"],
                )
                if result["processed"] > 0:
                    app.logger.info(
                        "Notifications processed=%s sent=%s failed=%s",
                        result["processed"],
                        result["sent"],
                        result["failed"],
                    )
            except Exception as error:
                app.logger.exception("Notification worker iteration failed: %s", error)
            time.sleep(interval_seconds)


def start_worker_thread(app: Flask) -> None:
    if not app.config["NOTIFICATIONS_WORKER_ENABLED"]:
        app.logger.info("Notification worker disabled by configuration.")
        return

    thread = threading.Thread(
        target=_run_worker_loop,
        args=(app,),
        daemon=True,
        name="notifications-worker",
    )
    thread.start()
    app.logger.info("Notification worker started.")


__all__ = [
    "create_notification",
    "create_reminder_48h_before_due",
    "get_notification",
    "process_pending_notifications",
    "start_worker_thread",
]
