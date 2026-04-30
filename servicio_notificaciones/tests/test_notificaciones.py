from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class _OkSMTP:
    def __init__(self, *args, **kwargs):
        del args, kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del exc_type, exc_val, exc_tb
        return False

    def ehlo(self) -> None:
        return None

    def starttls(self) -> None:
        return None

    def login(self, username: str, password: str) -> None:
        del username, password

    def send_message(self, message) -> None:
        del message


class _FailSMTP(_OkSMTP):
    def send_message(self, message) -> None:
        del message
        raise RuntimeError("SMTP down")


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch):
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["NOTIFICATIONS_WORKER_ENABLED"] = "false"
    os.environ["MAX_REINTENTOS_ENVIO"] = "2"
    os.environ["SMTP_FROM_EMAIL"] = "no-reply@test.local"
    os.environ["SMTP_FROM_NAME"] = "Teca Test"

    from app import create_app
    import app.services as notification_services

    flask_app = create_app()
    flask_app.config.update(TESTING=True)

    monkeypatch.setattr(notification_services.smtplib, "SMTP", _OkSMTP)
    monkeypatch.setattr(notification_services.smtplib, "SMTP_SSL", _OkSMTP)
    return flask_app


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


def test_create_and_process_notification(client) -> None:
    create_response = client.post(
        "/api/v1/notificaciones",
        json={
            "usuario_id": 11,
            "prestamo_id": 101,
            "tipo": "general",
            "destinatario_email": "persona@example.com",
            "asunto": "Aviso",
            "mensaje": "Mensaje de prueba",
        },
    )
    assert create_response.status_code == 201
    notification_id = create_response.get_json()["data"]["id"]

    process_response = client.post("/api/v1/notificaciones/process-queue")
    assert process_response.status_code == 200
    process_payload = process_response.get_json()["data"]
    assert process_payload["processed"] == 1
    assert process_payload["sent"] == 1
    assert process_payload["failed"] == 0

    get_response = client.get(f"/api/v1/notificaciones/{notification_id}")
    assert get_response.status_code == 200
    assert get_response.get_json()["data"]["estado"] == "enviada"


def test_schedule_48h_reminder(client) -> None:
    reminder_response = client.post(
        "/api/v1/notificaciones/recordatorios/48h",
        json={
            "usuario_id": 22,
            "prestamo_id": 303,
            "destinatario_email": "lector@example.com",
            "fecha_limite": "2030-01-10T12:00:00+00:00",
            "libro_titulo": "Clean Architecture",
        },
    )
    assert reminder_response.status_code == 201
    payload = reminder_response.get_json()["data"]
    assert payload["tipo"] == "recordatorio_48h"
    assert payload["estado"] == "pendiente"


def test_retries_and_mark_failed(app, client, monkeypatch: pytest.MonkeyPatch) -> None:
    import app.services as notification_services
    from app.extensions import db
    from app.models import Notificacion

    monkeypatch.setattr(notification_services.smtplib, "SMTP", _FailSMTP)
    monkeypatch.setattr(notification_services.smtplib, "SMTP_SSL", _FailSMTP)

    create_response = client.post(
        "/api/v1/notificaciones",
        json={
            "usuario_id": 33,
            "destinatario_email": "fail@example.com",
            "asunto": "Falla",
            "mensaje": "Debe reintentar",
            "max_reintentos": 2,
        },
    )
    assert create_response.status_code == 201
    notification_id = create_response.get_json()["data"]["id"]

    first_try = client.post("/api/v1/notificaciones/process-queue")
    assert first_try.status_code == 200
    first_state = client.get(f"/api/v1/notificaciones/{notification_id}").get_json()["data"]
    assert first_state["estado"] == "reintento"
    assert first_state["reintentos"] == 1

    with app.app_context():
        noti = Notificacion.query.filter_by(id=notification_id).first()
        assert noti is not None
        noti.proximo_reintento = notification_services.now_utc() - timedelta(seconds=1)
        db.session.commit()

    second_try = client.post("/api/v1/notificaciones/process-queue")
    assert second_try.status_code == 200
    second_state = client.get(f"/api/v1/notificaciones/{notification_id}").get_json()["data"]
    assert second_state["estado"] == "fallida"
    assert second_state["reintentos"] == 2
