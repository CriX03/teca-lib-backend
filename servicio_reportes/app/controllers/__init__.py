from __future__ import annotations

from typing import Any

from flask import Response, current_app, jsonify, request

from app.errors import ApiError
from app.services import (
    get_libros_mas_prestados,
    get_prestamos_por_usuario,
    get_retrasos,
    sync_libros,
    sync_lote,
    sync_prestamos,
    sync_usuarios,
)


def _extract_limit_arg() -> int | None:
    raw_value = request.args.get("limit")
    if raw_value is None:
        return None

    clean_value = raw_value.strip()
    if not clean_value:
        raise ApiError(
            "VALIDATION_ERROR",
            "El parametro 'limit' debe ser un entero positivo.",
            422,
        )

    try:
        return int(clean_value)
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR",
            "El parametro 'limit' debe ser un entero positivo.",
            422,
        ) from error


def _success_response(data: Any, message: str) -> tuple[Response, int]:
    return jsonify({"success": True, "data": data, "message": message}), 200


def _extract_json() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(
            "INVALID_REQUEST_BODY",
            "El cuerpo de la peticion debe ser JSON valido.",
            400,
        )
    return data


def libros_mas_prestados_controller() -> tuple[Response, int]:
    data = get_libros_mas_prestados(
        limit=_extract_limit_arg(),
        default_limit=current_app.config["REPORTES_DEFAULT_LIMIT"],
        max_limit=current_app.config["REPORTES_MAX_LIMIT"],
    )
    return _success_response(
        data, "Reporte de libros mas prestados generado correctamente."
    )


def prestamos_por_usuario_controller() -> tuple[Response, int]:
    data = get_prestamos_por_usuario(
        limit=_extract_limit_arg(),
        default_limit=current_app.config["REPORTES_DEFAULT_LIMIT"],
        max_limit=current_app.config["REPORTES_MAX_LIMIT"],
    )
    return _success_response(
        data, "Reporte de prestamos por usuario generado correctamente."
    )


def retrasos_controller() -> tuple[Response, int]:
    data = get_retrasos(
        limit=_extract_limit_arg(),
        default_limit=current_app.config["REPORTES_DEFAULT_LIMIT"],
        max_limit=current_app.config["REPORTES_MAX_LIMIT"],
    )
    return _success_response(data, "Reporte de retrasos generado correctamente.")


def sync_usuarios_controller() -> tuple[Response, int]:
    payload = _extract_json()
    items = payload.get("items")
    if not isinstance(items, list):
        raise ApiError("VALIDATION_ERROR", "El campo 'items' debe ser una lista.", 422)
    data = sync_usuarios(items)
    return _success_response(data, "Usuarios analiticos sincronizados correctamente.")


def sync_libros_controller() -> tuple[Response, int]:
    payload = _extract_json()
    items = payload.get("items")
    if not isinstance(items, list):
        raise ApiError("VALIDATION_ERROR", "El campo 'items' debe ser una lista.", 422)
    data = sync_libros(items)
    return _success_response(data, "Libros analiticos sincronizados correctamente.")


def sync_prestamos_controller() -> tuple[Response, int]:
    payload = _extract_json()
    items = payload.get("items")
    if not isinstance(items, list):
        raise ApiError("VALIDATION_ERROR", "El campo 'items' debe ser una lista.", 422)
    data = sync_prestamos(items)
    return _success_response(data, "Prestamos analiticos sincronizados correctamente.")


def sync_lote_controller() -> tuple[Response, int]:
    data = sync_lote(_extract_json())
    return _success_response(data, "Sincronizacion analitica por lote completada.")
