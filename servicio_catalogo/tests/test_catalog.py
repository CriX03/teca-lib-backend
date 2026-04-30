from __future__ import annotations

import os
import sys
from pathlib import Path

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


def _create_dependencies(client):
    autor = client.post("/api/v1/catalogo/autores", json={"nombre": "Gabriel Garcia Marquez"})
    editorial = client.post("/api/v1/catalogo/editoriales", json={"nombre": "Sudamericana"})
    categoria = client.post("/api/v1/catalogo/categorias", json={"nombre": "Novela"})

    assert autor.status_code == 201
    assert editorial.status_code == 201
    assert categoria.status_code == 201

    return (
        autor.get_json()["data"]["id"],
        editorial.get_json()["data"]["id"],
        categoria.get_json()["data"]["id"],
    )


def test_crud_libro_and_disponibilidad(client):
    autor_id, editorial_id, categoria_id = _create_dependencies(client)

    create_response = client.post(
        "/api/v1/catalogo/libros",
        json={
            "titulo": "Cien anos de soledad",
            "isbn": "978-0307474728",
            "autor_id": autor_id,
            "editorial_id": editorial_id,
            "categoria_id": categoria_id,
            "disponibilidad": True,
        },
    )
    assert create_response.status_code == 201
    libro_id = create_response.get_json()["data"]["id"]

    patch_response = client.patch(
        f"/api/v1/catalogo/libros/{libro_id}/disponibilidad",
        json={"disponibilidad": False},
    )
    assert patch_response.status_code == 200
    assert patch_response.get_json()["data"]["disponibilidad"] is False

    get_response = client.get(f"/api/v1/catalogo/libros/{libro_id}")
    assert get_response.status_code == 200
    assert get_response.get_json()["data"]["isbn"] == "978-0307474728"

    update_response = client.put(
        f"/api/v1/catalogo/libros/{libro_id}",
        json={
            "titulo": "Cien anos de soledad (edicion revisada)",
            "isbn": "978-0307474728",
            "autor_id": autor_id,
            "editorial_id": editorial_id,
            "categoria_id": categoria_id,
            "disponibilidad": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["data"]["disponibilidad"] is True

    delete_response = client.delete(f"/api/v1/catalogo/libros/{libro_id}")
    assert delete_response.status_code == 200

    missing_response = client.get(f"/api/v1/catalogo/libros/{libro_id}")
    assert missing_response.status_code == 404


def test_isbn_unique_validation(client):
    autor_id, editorial_id, categoria_id = _create_dependencies(client)

    payload = {
        "titulo": "Libro Uno",
        "isbn": "9788478884456",
        "autor_id": autor_id,
        "editorial_id": editorial_id,
        "categoria_id": categoria_id,
    }
    first = client.post("/api/v1/catalogo/libros", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/catalogo/libros", json={**payload, "titulo": "Libro Dos"})
    assert second.status_code == 409
    assert second.get_json()["error"]["code"] == "ISBN_ALREADY_EXISTS"


def test_libros_filters(client):
    autor_id, editorial_id, categoria_id = _create_dependencies(client)

    client.post(
        "/api/v1/catalogo/libros",
        json={
            "titulo": "Disponible",
            "isbn": "9780307476463",
            "autor_id": autor_id,
            "editorial_id": editorial_id,
            "categoria_id": categoria_id,
            "disponibilidad": True,
        },
    )
    client.post(
        "/api/v1/catalogo/libros",
        json={
            "titulo": "No disponible",
            "isbn": "9780307476464",
            "autor_id": autor_id,
            "editorial_id": editorial_id,
            "categoria_id": categoria_id,
            "disponibilidad": False,
        },
    )

    available_response = client.get("/api/v1/catalogo/libros?disponible=true")
    assert available_response.status_code == 200
    items = available_response.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["titulo"] == "Disponible"


def test_cannot_delete_autor_with_books(client):
    autor_id, editorial_id, categoria_id = _create_dependencies(client)
    client.post(
        "/api/v1/catalogo/libros",
        json={
            "titulo": "Libro Base",
            "isbn": "9780307476465",
            "autor_id": autor_id,
            "editorial_id": editorial_id,
            "categoria_id": categoria_id,
        },
    )

    response = client.delete(f"/api/v1/catalogo/autores/{autor_id}")
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "AUTOR_IN_USE"


def test_cannot_delete_editorial_or_categoria_with_books(client):
    autor_id, editorial_id, categoria_id = _create_dependencies(client)
    create_book = client.post(
        "/api/v1/catalogo/libros",
        json={
            "titulo": "Libro Base 2",
            "isbn": "9780307476466",
            "autor_id": autor_id,
            "editorial_id": editorial_id,
            "categoria_id": categoria_id,
        },
    )
    assert create_book.status_code == 201

    editorial_response = client.delete(f"/api/v1/catalogo/editoriales/{editorial_id}")
    assert editorial_response.status_code == 409
    assert editorial_response.get_json()["error"]["code"] == "EDITORIAL_IN_USE"

    categoria_response = client.delete(f"/api/v1/catalogo/categorias/{categoria_id}")
    assert categoria_response.status_code == 409
    assert categoria_response.get_json()["error"]["code"] == "CATEGORIA_IN_USE"
