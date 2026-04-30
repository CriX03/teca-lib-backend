from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from app.errors import ApiError
from app.services import (
    create_autor,
    create_categoria,
    create_editorial,
    create_libro,
    delete_autor,
    delete_categoria,
    delete_editorial,
    delete_libro,
    get_autor,
    get_categoria,
    get_editorial,
    get_libro,
    list_autores,
    list_categorias,
    list_editoriales,
    list_libros,
    parse_catalog_query_params,
    parse_simple_list_query_params,
    update_autor,
    update_categoria,
    update_disponibilidad,
    update_editorial,
    update_libro,
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


def list_autores_controller() -> tuple[Response, int]:
    params = parse_simple_list_query_params(request.args.to_dict())
    data = list_autores(**params)
    return _success_response(data, "Autores obtenidos correctamente.")


def create_autor_controller() -> tuple[Response, int]:
    data = create_autor(_extract_json())
    return _success_response(data, "Autor creado correctamente.", 201)


def get_autor_controller(autor_id: int) -> tuple[Response, int]:
    data = get_autor(autor_id)
    return _success_response(data, "Autor obtenido correctamente.")


def update_autor_controller(autor_id: int) -> tuple[Response, int]:
    data = update_autor(autor_id, _extract_json())
    return _success_response(data, "Autor actualizado correctamente.")


def delete_autor_controller(autor_id: int) -> tuple[Response, int]:
    delete_autor(autor_id)
    return _success_response(None, "Autor eliminado correctamente.")


def list_editoriales_controller() -> tuple[Response, int]:
    params = parse_simple_list_query_params(request.args.to_dict())
    data = list_editoriales(**params)
    return _success_response(data, "Editoriales obtenidas correctamente.")


def create_editorial_controller() -> tuple[Response, int]:
    data = create_editorial(_extract_json())
    return _success_response(data, "Editorial creada correctamente.", 201)


def get_editorial_controller(editorial_id: int) -> tuple[Response, int]:
    data = get_editorial(editorial_id)
    return _success_response(data, "Editorial obtenida correctamente.")


def update_editorial_controller(editorial_id: int) -> tuple[Response, int]:
    data = update_editorial(editorial_id, _extract_json())
    return _success_response(data, "Editorial actualizada correctamente.")


def delete_editorial_controller(editorial_id: int) -> tuple[Response, int]:
    delete_editorial(editorial_id)
    return _success_response(None, "Editorial eliminada correctamente.")


def list_categorias_controller() -> tuple[Response, int]:
    params = parse_simple_list_query_params(request.args.to_dict())
    data = list_categorias(**params)
    return _success_response(data, "Categorias obtenidas correctamente.")


def create_categoria_controller() -> tuple[Response, int]:
    data = create_categoria(_extract_json())
    return _success_response(data, "Categoria creada correctamente.", 201)


def get_categoria_controller(categoria_id: int) -> tuple[Response, int]:
    data = get_categoria(categoria_id)
    return _success_response(data, "Categoria obtenida correctamente.")


def update_categoria_controller(categoria_id: int) -> tuple[Response, int]:
    data = update_categoria(categoria_id, _extract_json())
    return _success_response(data, "Categoria actualizada correctamente.")


def delete_categoria_controller(categoria_id: int) -> tuple[Response, int]:
    delete_categoria(categoria_id)
    return _success_response(None, "Categoria eliminada correctamente.")


def list_libros_controller() -> tuple[Response, int]:
    params = parse_catalog_query_params(request.args.to_dict())
    data = list_libros(**params)
    return _success_response(data, "Libros obtenidos correctamente.")


def create_libro_controller() -> tuple[Response, int]:
    data = create_libro(_extract_json())
    return _success_response(data, "Libro creado correctamente.", 201)


def get_libro_controller(libro_id: int) -> tuple[Response, int]:
    data = get_libro(libro_id)
    return _success_response(data, "Libro obtenido correctamente.")


def update_libro_controller(libro_id: int) -> tuple[Response, int]:
    data = update_libro(libro_id, _extract_json())
    return _success_response(data, "Libro actualizado correctamente.")


def update_disponibilidad_controller(libro_id: int) -> tuple[Response, int]:
    payload = _extract_json()
    data = update_disponibilidad(libro_id, payload.get("disponibilidad"))
    return _success_response(data, "Disponibilidad actualizada correctamente.")


def delete_libro_controller(libro_id: int) -> tuple[Response, int]:
    delete_libro(libro_id)
    return _success_response(None, "Libro eliminado correctamente.")
