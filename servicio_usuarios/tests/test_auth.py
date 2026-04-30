from __future__ import annotations

import os

import pytest


@pytest.fixture()
def client():
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"] = "60"

    from app import create_app

    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client


def test_register_and_login_ok(client):
    register_response = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Admin Uno",
            "email": "admin@example.com",
            "contrasena": "Secure123!",
            "rol": "admin",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "contrasena": "Secure123!"},
    )
    assert login_response.status_code == 200

    payload = login_response.get_json()
    token = payload["data"]["access_token"]

    me_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    me_payload = me_response.get_json()
    assert me_payload["data"]["email"] == "admin@example.com"


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Usuario",
            "email": "user@example.com",
            "contrasena": "weak",
            "rol": "estudiante",
        },
    )

    assert response.status_code == 422
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_admin_check_requires_admin_role(client):
    register_response = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Estudiante Uno",
            "email": "estudiante@example.com",
            "contrasena": "Secure123!",
            "rol": "estudiante",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "estudiante@example.com", "contrasena": "Secure123!"},
    )
    assert login_response.status_code == 200

    token = login_response.get_json()["data"]["access_token"]
    forbidden_response = client.get(
        "/api/v1/auth/admin/check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert forbidden_response.status_code == 403
