from __future__ import annotations

from typing import Any

from flask import Response, current_app, jsonify, request

from app.errors import ApiError
from app.services import (
    create_prestamo,
    devolver_prestamo,
    devolver_prestamo_admin,
    get_prestamo,
    list_all_prestamos,
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


def _success_response(
    data: Any, message: str, status_code: int = 200
) -> tuple[Response, int]:
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


def list_all_prestamos_controller() -> tuple[Response, int]:
    args = request.args
    data = list_all_prestamos(
        authorization_header=request.headers.get("Authorization"),
        usuarios_service_url=current_app.config["USUARIOS_SERVICE_URL"],
        catalogo_service_url=current_app.config["CATALOGO_SERVICE_URL"],
        timeout_seconds=current_app.config["EXTERNAL_SERVICES_TIMEOUT_SECONDS"],
        page=args.get("page", 1, type=int),
        limit=min(args.get("limit", 20, type=int), 100),
        estado=args.get("estado", None) if args.get("estado") else None,
        fecha_prestamo_desde=args.get("fecha_prestamo_desde", None),
        fecha_prestamo_hasta=args.get("fecha_prestamo_hasta", None),
        fecha_limite_desde=args.get("fecha_limite_desde", None),
        fecha_limite_hasta=args.get("fecha_limite_hasta", None),
        libro_id=args.get("libro_id", None, type=int) if args.get("libro_id") else None,
        libro_titulo=args.get("libro_titulo", None),
    )
    return _success_response(data, "Prestamos obtenidos correctamente.")


def devolver_prestamo_admin_controller() -> tuple[Response, int]:
    payload = _extract_json()
    prestamo_id = payload.get("prestamo_id")
    if not isinstance(prestamo_id, int) or prestamo_id <= 0:
        raise ApiError(
            "VALIDATION_ERROR",
            "El campo 'prestamo_id' debe ser un entero positivo.",
            422,
        )
    forzar = payload.get("forzar", False)
    if not isinstance(forzar, bool):
        forzar = False

    data = devolver_prestamo_admin(
        prestamo_id,
        authorization_header=request.headers.get("Authorization"),
        usuarios_service_url=current_app.config["USUARIOS_SERVICE_URL"],
        catalogo_service_url=current_app.config["CATALOGO_SERVICE_URL"],
        timeout_seconds=current_app.config["EXTERNAL_SERVICES_TIMEOUT_SECONDS"],
        forzar=forzar,
    )
    return _success_response(data, "Prestamo devuelto por administrador.")
