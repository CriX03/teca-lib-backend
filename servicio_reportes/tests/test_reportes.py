from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture()
def app():
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["REPORTES_DEFAULT_LIMIT"] = "5"
    os.environ["REPORTES_MAX_LIMIT"] = "50"

    from app import create_app
    from app.extensions import db
    from app.models import LibroAnalitico, PrestamoAnalitico, UsuarioAnalitico

    flask_app = create_app()
    flask_app.config.update(TESTING=True)

    now = datetime.now(UTC)
    with flask_app.app_context():
        usuario_1 = UsuarioAnalitico()
        usuario_1.id = 1
        usuario_1.nombre = "Ada"
        usuario_1.email = "ada@example.com"

        usuario_2 = UsuarioAnalitico()
        usuario_2.id = 2
        usuario_2.nombre = "Linus"
        usuario_2.email = "linus@example.com"

        db.session.add_all(
            [
                usuario_1,
                usuario_2,
            ]
        )

        libro_1 = LibroAnalitico()
        libro_1.id = 10
        libro_1.titulo = "Domain-Driven Design"

        libro_2 = LibroAnalitico()
        libro_2.id = 11
        libro_2.titulo = "Refactoring"

        db.session.add_all(
            [
                libro_1,
                libro_2,
            ]
        )

        prestamo_1 = PrestamoAnalitico()
        prestamo_1.usuario_id = 1
        prestamo_1.libro_id = 10
        prestamo_1.fecha_prestamo = now - timedelta(days=12)
        prestamo_1.fecha_limite = now - timedelta(days=5)
        prestamo_1.fecha_devolucion = now - timedelta(days=3)
        prestamo_1.estado = "devuelto"

        prestamo_2 = PrestamoAnalitico()
        prestamo_2.usuario_id = 1
        prestamo_2.libro_id = 10
        prestamo_2.fecha_prestamo = now - timedelta(days=9)
        prestamo_2.fecha_limite = now - timedelta(days=2)
        prestamo_2.estado = "activo"

        prestamo_3 = PrestamoAnalitico()
        prestamo_3.usuario_id = 2
        prestamo_3.libro_id = 11
        prestamo_3.fecha_prestamo = now - timedelta(days=4)
        prestamo_3.fecha_limite = now + timedelta(days=3)
        prestamo_3.estado = "activo"

        db.session.add_all(
            [
                prestamo_1,
                prestamo_2,
                prestamo_3,
            ]
        )
        db.session.commit()

    return flask_app


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


def test_libros_mas_prestados(client) -> None:
    response = client.get("/api/v1/reportes/libros-mas-prestados?limit=10")
    assert response.status_code == 200
    items = response.get_json()["data"]["items"]
    assert items[0]["libro_id"] == 10
    assert items[0]["total_prestamos"] == 2


def test_prestamos_por_usuario(client) -> None:
    response = client.get("/api/v1/reportes/prestamos-por-usuario")
    assert response.status_code == 200
    items = response.get_json()["data"]["items"]
    assert items[0]["usuario_id"] == 1
    assert items[0]["total_prestamos"] == 2


def test_retrasos(client) -> None:
    response = client.get("/api/v1/reportes/retrasos")
    assert response.status_code == 200
    items = response.get_json()["data"]["items"]
    assert len(items) >= 1
    assert items[0]["dias_retraso"] >= 1


def test_limit_invalido(client) -> None:
    response = client.get("/api/v1/reportes/retrasos?limit=abc")
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_sync_lote_y_reportes(client) -> None:
    lote = {
        "usuarios": [
            {"id": 100, "nombre": "Grace", "email": "grace@example.com"},
            {"id": 101, "nombre": "Alan", "email": "alan@example.com"},
        ],
        "libros": [
            {"id": 200, "titulo": "Patterns of Enterprise Application Architecture"},
            {"id": 201, "titulo": "Clean Code"},
        ],
        "prestamos": [
            {
                "id": 900,
                "usuario_id": 100,
                "libro_id": 200,
                "fecha_prestamo": "2030-01-01T10:00:00+00:00",
                "fecha_limite": "2030-01-10T10:00:00+00:00",
                "fecha_devolucion": "2030-01-12T10:00:00+00:00",
                "estado": "devuelto",
            },
            {
                "id": 901,
                "usuario_id": 100,
                "libro_id": 200,
                "fecha_prestamo": "2030-02-01T10:00:00+00:00",
                "fecha_limite": "2030-02-10T10:00:00+00:00",
                "estado": "activo",
            },
            {
                "id": 902,
                "usuario_id": 101,
                "libro_id": 201,
                "fecha_prestamo": "2030-03-01T10:00:00+00:00",
                "fecha_limite": "2030-03-10T10:00:00+00:00",
                "estado": "activo",
            },
        ],
    }

    sync_response = client.post("/api/v1/reportes/sync/lote", json=lote)
    assert sync_response.status_code == 200
    sync_data = sync_response.get_json()["data"]
    assert sync_data["usuarios"]["created"] == 2
    assert sync_data["libros"]["created"] == 2
    assert sync_data["prestamos"]["created"] == 3

    top_books = client.get("/api/v1/reportes/libros-mas-prestados?limit=1")
    assert top_books.status_code == 200
    top_book_item = top_books.get_json()["data"]["items"][0]
    assert top_book_item["libro_id"] == 200
    assert top_book_item["total_prestamos"] == 2

    loans_by_user = client.get("/api/v1/reportes/prestamos-por-usuario?limit=1")
    assert loans_by_user.status_code == 200
    top_user_item = loans_by_user.get_json()["data"]["items"][0]
    assert top_user_item["usuario_id"] == 100
    assert top_user_item["total_prestamos"] == 2

    delays = client.get("/api/v1/reportes/retrasos")
    assert delays.status_code == 200
    delay_items = delays.get_json()["data"]["items"]
    assert any(item["prestamo_id"] == 900 and item["dias_retraso"] >= 2 for item in delay_items)
