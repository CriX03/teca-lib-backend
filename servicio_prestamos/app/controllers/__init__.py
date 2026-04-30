from __future__ import annotations

from typing import Any

from flask import Response, current_app, jsonify, request

from app.errors import ApiError
from app.services import (
    create_prestamo,
    devolver_prestamo,
    get_prestamo,
    list_prestamos_by_usuario,
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


def create_prestamo_controller() -> tuple[Response, int]:
    data = create_prestamo(
        _extract_json(),
        authorization_header=request.headers.get("Authorization"),
        usuarios_service_url=current_app.config["USUARIOS_SERVICE_URL"],
        catalogo_service_url=current_app.config["CATALOGO_SERVICE_URL"],
        timeout_seconds=current_app.config["EXTERNAL_SERVICES_TIMEOUT_SECONDS"],
        default_days=current_app.config["PRESTAMO_DIAS_POR_DEFECTO"],
    )
    return _success_response(data, "Prestamo creado correctamente.", 201)


def get_prestamo_controller(prestamo_id: int) -> tuple[Response, int]:
    data = get_prestamo(
        prestamo_id,
        authorization_header=request.headers.get("Authorization"),
        usuarios_service_url=current_app.config["USUARIOS_SERVICE_URL"],
        timeout_seconds=current_app.config["EXTERNAL_SERVICES_TIMEOUT_SECONDS"],
    )
    return _success_response(data, "Prestamo obtenido correctamente.")


def list_mis_prestamos_controller() -> tuple[Response, int]:
    data = list_prestamos_by_usuario(
        authorization_header=request.headers.get("Authorization"),
        usuarios_service_url=current_app.config["USUARIOS_SERVICE_URL"],
        timeout_seconds=current_app.config["EXTERNAL_SERVICES_TIMEOUT_SECONDS"],
    )
    return _success_response(data, "Prestamos obtenidos correctamente.")


def devolver_prestamo_controller(prestamo_id: int) -> tuple[Response, int]:
    data = devolver_prestamo(
        prestamo_id,
        authorization_header=request.headers.get("Authorization"),
        usuarios_service_url=current_app.config["USUARIOS_SERVICE_URL"],
        catalogo_service_url=current_app.config["CATALOGO_SERVICE_URL"],
        timeout_seconds=current_app.config["EXTERNAL_SERVICES_TIMEOUT_SECONDS"],
    )
    return _success_response(data, "Devolucion registrada correctamente.")