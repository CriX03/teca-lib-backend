from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture()
def client():
    os.environ["DATABASE_URL"] = "sqlite://"

    from app import create_app

    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def external_state(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    import app.services as prestamos_services

    state: dict[str, Any] = {
        "user_id": 7,
        "libros": {
            10: {"id": 10, "disponibilidad": True},
            11: {"id": 11, "disponibilidad": False},
        },
    }

    class _FakeResponse:
        def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
            self.status_code = status_code
            self._payload = payload
            self.content = b"x"

        def json(self) -> dict[str, Any]:
            return self._payload

    def fake_request(
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float = 5,
    ) -> _FakeResponse:
        del timeout
        token = (headers or {}).get("Authorization")

        if url.endswith("/api/v1/auth/me"):
            if token != "Bearer valid-token":
                return _FakeResponse(
                    401,
                    {
                        "success": False,
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": "Token invalido.",
                        },
                    },
                )
            return _FakeResponse(200, {"success": True, "data": {"id": state["user_id"]}})

        if "/api/v1/catalogo/libros/" in url and not url.endswith("/disponibilidad"):
            libro_id = int(url.rsplit("/", 1)[-1])
            libro = state["libros"].get(libro_id)
            if libro is None:
                return _FakeResponse(
                    404,
                    {
                        "success": False,
                        "error": {
                            "code": "LIBRO_NOT_FOUND",
                            "message": "Libro no encontrado.",
                        },
                    },
                )
            return _FakeResponse(200, {"success": True, "data": libro})

        if url.endswith("/disponibilidad") and json is not None:
            parts = url.split("/")
            libro_id = int(parts[-2])
            libro = state["libros"].get(libro_id)
            if libro is None:
                return _FakeResponse(
                    404,
                    {
                        "success": False,
                        "error": {
                            "code": "LIBRO_NOT_FOUND",
                            "message": "Libro no encontrado.",
                        },
                    },
                )

            libro["disponibilidad"] = bool(json.get("disponibilidad"))
            return _FakeResponse(200, {"success": True, "data": libro})

        return _FakeResponse(
            500,
            {
                "success": False,
                "error": {
                    "code": "UNEXPECTED_ENDPOINT",
                    "message": f"No mock for {method} {url}",
                },
            },
        )

    monkeypatch.setattr(prestamos_services.requests, "request", fake_request)
    return state


def _auth_header(token: str = "valid-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_flujo_crear_y_devolver_prestamo(client, external_state):
    create_response = client.post(
        "/api/v1/prestamos",
        json={"libro_id": 10, "dias_prestamo": 7},
        headers=_auth_header(),
    )
    assert create_response.status_code == 201
    create_payload = create_response.get_json()
    prestamo_id = create_payload["data"]["id"]
    assert create_payload["data"]["estado"] == "activo"
    assert external_state["libros"][10]["disponibilidad"] is False

    get_response = client.get(f"/api/v1/prestamos/{prestamo_id}", headers=_auth_header())
    assert get_response.status_code == 200
    assert get_response.get_json()["data"]["libro_id"] == 10

    list_response = client.get("/api/v1/prestamos/mis-prestamos", headers=_auth_header())
    assert list_response.status_code == 200
    assert len(list_response.get_json()["data"]["items"]) == 1

    devolver_response = client.post(
        f"/api/v1/prestamos/{prestamo_id}/devolucion",
        headers=_auth_header(),
    )
    assert devolver_response.status_code == 200
    assert devolver_response.get_json()["data"]["estado"] == "devuelto"
    assert external_state["libros"][10]["disponibilidad"] is True


def test_no_crea_prestamo_si_libro_no_disponible(client, external_state):
    response = client.post(
        "/api/v1/prestamos",
        json={"libro_id": 11},
        headers=_auth_header(),
    )

    assert response.status_code == 409
    payload = response.get_json()
    assert payload["error"]["code"] == "BOOK_NOT_AVAILABLE"
    assert external_state["libros"][11]["disponibilidad"] is False


def test_requiere_autorizacion(client, external_state):
    del external_state
    response = client.post("/api/v1/prestamos", json={"libro_id": 10})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "MISSING_AUTH_HEADER"
