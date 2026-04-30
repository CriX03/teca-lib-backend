# mypy: disable-error-code=import-untyped

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import requests
from requests import Response

from app.errors import ApiError
from app.extensions import db
from app.models import Prestamo

ESTADO_ACTIVO = "activo"
ESTADO_DEVUELTO = "devuelto"


def _clean_positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser un entero positivo.",
            422,
        )
    return value


def _clean_dias_prestamo(value: Any, default_days: int) -> int:
    if value is None:
        return default_days

    dias = _clean_positive_int(value, "dias_prestamo")
    if dias > 60:
        raise ApiError(
            "VALIDATION_ERROR",
            "El campo 'dias_prestamo' no puede superar 60 dias.",
            422,
        )

    return dias


def _extract_token_from_header(authorization_header: str | None) -> str:
    if authorization_header is None:
        raise ApiError("MISSING_AUTH_HEADER", "Falta el header Authorization.", 401)

    authorization = authorization_header.strip()
    if not authorization:
        raise ApiError("MISSING_AUTH_HEADER", "Falta el header Authorization.", 401)

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ApiError(
            "INVALID_AUTH_HEADER",
            "El header Authorization debe usar el formato Bearer <token>.",
            401,
        )

    return parts[1]


def _request_json(
    method: str,
    url: str,
    *,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
    json_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        response: Response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_payload,
            timeout=timeout_seconds,
        )
    except requests.RequestException as error:
        raise ApiError(
            "DEPENDENCY_UNAVAILABLE",
            "No fue posible comunicarse con un servicio externo.",
            503,
        ) from error

    try:
        data = response.json() if response.content else {}
    except ValueError as error:
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "Servicio externo respondio con JSON invalido.",
            503,
        ) from error
    if response.status_code >= 400:
        message = "Servicio externo respondio con error."
        code = "DEPENDENCY_ERROR"
        status_code = 503
        if isinstance(data, dict):
            error_info = data.get("error")
            if isinstance(error_info, dict) and isinstance(
                error_info.get("message"), str
            ):
                message = error_info["message"]
                external_code = error_info.get("code")
                if isinstance(external_code, str):
                    code = external_code

        if response.status_code in {401, 403, 404, 409, 422}:
            status_code = response.status_code

        raise ApiError(code, message, status_code)

    if not isinstance(data, dict):
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "Servicio externo respondio con un formato no valido.",
            503,
        )

    return data


def _get_authenticated_user_id(
    authorization_header: str | None,
    *,
    usuarios_service_url: str,
    timeout_seconds: float,
) -> int:
    token = _extract_token_from_header(authorization_header)
    response_data = _request_json(
        "GET",
        f"{usuarios_service_url}/api/v1/auth/me",
        timeout_seconds=timeout_seconds,
        headers={"Authorization": f"Bearer {token}"},
    )
    payload = response_data.get("data")
    if not isinstance(payload, dict):
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "La respuesta de usuarios no incluye data valida.",
            503,
        )

    user_id = payload.get("id")
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "La respuesta de usuarios no incluye un id valido.",
            503,
        )

    return user_id


def _get_libro(
    libro_id: int,
    *,
    catalogo_service_url: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    response_data = _request_json(
        "GET",
        f"{catalogo_service_url}/api/v1/catalogo/libros/{libro_id}",
        timeout_seconds=timeout_seconds,
    )
    payload = response_data.get("data")
    if not isinstance(payload, dict):
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "La respuesta de catalogo no incluye data valida.",
            503,
        )

    return payload


def _set_libro_disponibilidad(
    libro_id: int,
    *,
    disponible: bool,
    catalogo_service_url: str,
    timeout_seconds: float,
) -> None:
    _request_json(
        "PATCH",
        f"{catalogo_service_url}/api/v1/catalogo/libros/{libro_id}/disponibilidad",
        timeout_seconds=timeout_seconds,
        json_payload={"disponibilidad": disponible},
    )


def _ensure_book_available(libro: dict[str, Any]) -> None:
    disponible = libro.get("disponibilidad")
    if not isinstance(disponible, bool):
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "La respuesta de catalogo no incluye disponibilidad valida.",
            503,
        )

    if not disponible:
        raise ApiError(
            "BOOK_NOT_AVAILABLE", "El libro no esta disponible para prestamo.", 409
        )


def create_prestamo(
    payload: dict[str, Any],
    *,
    authorization_header: str | None,
    usuarios_service_url: str,
    catalogo_service_url: str,
    timeout_seconds: float,
    default_days: int,
) -> dict[str, int | str | None]:
    usuario_id = _get_authenticated_user_id(
        authorization_header,
        usuarios_service_url=usuarios_service_url,
        timeout_seconds=timeout_seconds,
    )
    libro_id = _clean_positive_int(payload.get("libro_id"), "libro_id")
    dias_prestamo = _clean_dias_prestamo(payload.get("dias_prestamo"), default_days)

    active_loan = Prestamo.query.filter_by(
        libro_id=libro_id, estado=ESTADO_ACTIVO
    ).first()
    if active_loan is not None:
        raise ApiError(
            "BOOK_ALREADY_LOANED",
            "El libro ya tiene un prestamo activo.",
            409,
        )

    libro = _get_libro(
        libro_id,
        catalogo_service_url=catalogo_service_url,
        timeout_seconds=timeout_seconds,
    )
    _ensure_book_available(libro)

    now = datetime.now(UTC)
    prestamo = Prestamo()
    prestamo.usuario_id = usuario_id
    prestamo.libro_id = libro_id
    prestamo.fecha_prestamo = now
    prestamo.fecha_limite = now + timedelta(days=dias_prestamo)
    prestamo.estado = ESTADO_ACTIVO

    _set_libro_disponibilidad(
        libro_id,
        disponible=False,
        catalogo_service_url=catalogo_service_url,
        timeout_seconds=timeout_seconds,
    )

    try:
        db.session.add(prestamo)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        try:
            _set_libro_disponibilidad(
                libro_id,
                disponible=True,
                catalogo_service_url=catalogo_service_url,
                timeout_seconds=timeout_seconds,
            )
        except ApiError:
            pass
        raise ApiError(
            "LOAN_CREATION_FAILED",
            "No fue posible crear el prestamo.",
            500,
        ) from error

    return prestamo.to_dict()


def get_prestamo(
    prestamo_id: int,
    *,
    authorization_header: str | None,
    usuarios_service_url: str,
    timeout_seconds: float,
) -> dict[str, int | str | None]:
    usuario_id = _get_authenticated_user_id(
        authorization_header,
        usuarios_service_url=usuarios_service_url,
        timeout_seconds=timeout_seconds,
    )
    prestamo = Prestamo.query.filter_by(id=prestamo_id).first()
    if prestamo is None:
        raise ApiError("LOAN_NOT_FOUND", "Prestamo no encontrado.", 404)

    if prestamo.usuario_id != usuario_id:
        raise ApiError("FORBIDDEN", "No tienes permisos para este prestamo.", 403)

    return prestamo.to_dict()


def devolver_prestamo(
    prestamo_id: int,
    *,
    authorization_header: str | None,
    usuarios_service_url: str,
    catalogo_service_url: str,
    timeout_seconds: float,
) -> dict[str, int | str | None]:
    usuario_id = _get_authenticated_user_id(
        authorization_header,
        usuarios_service_url=usuarios_service_url,
        timeout_seconds=timeout_seconds,
    )
    prestamo = Prestamo.query.filter_by(id=prestamo_id).first()
    if prestamo is None:
        raise ApiError("LOAN_NOT_FOUND", "Prestamo no encontrado.", 404)

    if prestamo.usuario_id != usuario_id:
        raise ApiError("FORBIDDEN", "No tienes permisos para este prestamo.", 403)

    if prestamo.estado != ESTADO_ACTIVO:
        raise ApiError("LOAN_NOT_ACTIVE", "El prestamo ya fue devuelto.", 409)

    _set_libro_disponibilidad(
        prestamo.libro_id,
        disponible=True,
        catalogo_service_url=catalogo_service_url,
        timeout_seconds=timeout_seconds,
    )

    try:
        prestamo.fecha_devolucion = datetime.now(UTC)
        prestamo.estado = ESTADO_DEVUELTO
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        try:
            _set_libro_disponibilidad(
                prestamo.libro_id,
                disponible=False,
                catalogo_service_url=catalogo_service_url,
                timeout_seconds=timeout_seconds,
            )
        except ApiError:
            pass
        raise ApiError(
            "LOAN_RETURN_FAILED",
            "No fue posible registrar la devolucion.",
            500,
        ) from error

    return prestamo.to_dict()


def list_prestamos_by_usuario(
    *,
    authorization_header: str | None,
    usuarios_service_url: str,
    timeout_seconds: float,
) -> dict[str, list[dict[str, int | str | None]]]:
    usuario_id = _get_authenticated_user_id(
        authorization_header,
        usuarios_service_url=usuarios_service_url,
        timeout_seconds=timeout_seconds,
    )
    prestamos = (
        Prestamo.query.filter_by(usuario_id=usuario_id)
        .order_by(Prestamo.fecha_prestamo.desc())
        .all()
    )
    return {"items": [prestamo.to_dict() for prestamo in prestamos]}


def list_all_prestamos(
    *,
    authorization_header: str | None,
    usuarios_service_url: str,
    catalogo_service_url: str,
    timeout_seconds: float,
    page: int = 1,
    limit: int = 20,
    estado: str | None = None,
    fecha_prestamo_desde: str | None = None,
    fecha_prestamo_hasta: str | None = None,
    fecha_limite_desde: str | None = None,
    fecha_limite_hasta: str | None = None,
    libro_id: int | None = None,
    libro_titulo: str | None = None,
) -> dict[str, Any]:
    token = _extract_token_from_header(authorization_header)
    user_data = _request_json(
        "GET",
        f"{usuarios_service_url}/api/v1/auth/me",
        timeout_seconds=timeout_seconds,
        headers={"Authorization": f"Bearer {token}"},
    )
    payload = user_data.get("data")
    if not isinstance(payload, dict):
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "La respuesta de usuarios no incluye data valida.",
            503,
        )

    user_role = payload.get("rol", "").lower()
    if user_role != "admin":
        raise ApiError("FORBIDDEN", "No tienes permisos de administrador.", 403)

    query = Prestamo.query

    if estado:
        if estado not in ("activo", "devuelto"):
            raise ApiError(
                "VALIDATION_ERROR",
                "El estado debe ser 'activo' o 'devuelto'.",
                422,
            )
        query = query.filter_by(estado=estado)

    if fecha_prestamo_desde:
        try:
            from_dt = datetime.fromisoformat(
                fecha_prestamo_desde.replace("Z", "+00:00")
            )
            query = query.filter(Prestamo.fecha_prestamo >= from_dt)
        except ValueError:
            raise ApiError(
                "VALIDATION_ERROR",
                "fecha_prestamo_desde debe ser formato ISO8601.",
                422,
            )

    if fecha_prestamo_hasta:
        try:
            to_dt = datetime.fromisoformat(fecha_prestamo_hasta.replace("Z", "+00:00"))
            to_dt = to_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Prestamo.fecha_prestamo <= to_dt)
        except ValueError:
            raise ApiError(
                "VALIDATION_ERROR",
                "fecha_prestamo_hasta debe ser formato ISO8601.",
                422,
            )

    if fecha_limite_desde:
        try:
            from_dt = datetime.fromisoformat(fecha_limite_desde.replace("Z", "+00:00"))
            query = query.filter(Prestamo.fecha_limite >= from_dt)
        except ValueError:
            raise ApiError(
                "VALIDATION_ERROR",
                "fecha_limite_desde debe ser formato ISO8601.",
                422,
            )

    if fecha_limite_hasta:
        try:
            to_dt = datetime.fromisoformat(fecha_limite_hasta.replace("Z", "+00:00"))
            to_dt = to_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Prestamo.fecha_limite <= to_dt)
        except ValueError:
            raise ApiError(
                "VALIDATION_ERROR",
                "fecha_limite_hasta debe ser formato ISO8601.",
                422,
            )

    if libro_id:
        query = query.filter_by(libro_id=libro_id)

    total_items = query.count()
    total_pages = (total_items + limit - 1) // limit if limit > 0 else 0
    offset = (page - 1) * limit
    prestamos = (
        query.order_by(Prestamo.fecha_prestamo.desc()).offset(offset).limit(limit).all()
    )

    items = []
    for prestamo in prestamos:
        item = prestamo.to_dict()

        try:
            libro_data = _request_json(
                "GET",
                f"{catalogo_service_url}/api/v1/catalogo/libros/{prestamo.libro_id}",
                timeout_seconds=timeout_seconds,
            )
            libro_payload = libro_data.get("data")
            if isinstance(libro_payload, dict):
                titulo = libro_payload.get("titulo", "")
                if libro_titulo and libro_titulo.lower() not in titulo.lower():
                    total_items -= 1
                    continue
                item["libro_titulo"] = titulo
                item["libro_editorial"] = libro_payload.get("editorial", "")
                item["libro_categoria"] = libro_payload.get("categoria", "")
        except ApiError:
            item["libro_titulo"] = ""
            item["libro_editorial"] = ""
            item["libro_categoria"] = ""

        try:
            usuario_data = _request_json(
                "GET",
                f"{usuarios_service_url}/api/v1/auth/usuarios/{prestamo.usuario_id}",
                timeout_seconds=timeout_seconds,
            )
            usuario_payload = usuario_data.get("data")
            if isinstance(usuario_payload, dict):
                item["usuario_nombre"] = usuario_payload.get("nombre", "")
        except ApiError:
            item["usuario_nombre"] = ""

        items.append(item)

        items.append(item)

    return {
        "items": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }


def devolver_prestamo_admin(
    prestamo_id: int,
    *,
    authorization_header: str | None,
    usuarios_service_url: str,
    catalogo_service_url: str,
    timeout_seconds: float,
    forzar: bool = False,
) -> dict[str, Any]:
    token = _extract_token_from_header(authorization_header)
    user_data = _request_json(
        "GET",
        f"{usuarios_service_url}/api/v1/auth/me",
        timeout_seconds=timeout_seconds,
        headers={"Authorization": f"Bearer {token}"},
    )
    payload = user_data.get("data")
    if not isinstance(payload, dict):
        raise ApiError(
            "DEPENDENCY_INVALID_RESPONSE",
            "La respuesta de usuarios no incluye data valida.",
            503,
        )

    user_role = payload.get("rol", "").lower()
    if user_role != "admin":
        raise ApiError("FORBIDDEN", "No tienes permisos de administrador.", 403)

    prestamo = Prestamo.query.filter_by(id=prestamo_id).first()
    if prestamo is None:
        raise ApiError("LOAN_NOT_FOUND", "Prestamo no encontrado.", 404)

    if prestamo.estado == ESTADO_DEVUELTO and not forzar:
        raise ApiError("LOAN_ALREADY_RETURNED", "El prestamo ya fue devuelto.", 409)

    _set_libro_disponibilidad(
        prestamo.libro_id,
        disponible=True,
        catalogo_service_url=catalogo_service_url,
        timeout_seconds=timeout_seconds,
    )

    try:
        prestamo.fecha_devolucion = datetime.now(UTC)
        prestamo.estado = ESTADO_DEVUELTO
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        try:
            _set_libro_disponibilidad(
                prestamo.libro_id,
                disponible=False,
                catalogo_service_url=catalogo_service_url,
                timeout_seconds=timeout_seconds,
            )
        except ApiError:
            pass
        raise ApiError(
            "LOAN_RETURN_FAILED",
            "No fue posible registrar la devolucion.",
            500,
        ) from error

    result = prestamo.to_dict()

    try:
        libro_data = _request_json(
            "GET",
            f"{catalogo_service_url}/api/v1/catalogo/libros/{prestamo.libro_id}",
            timeout_seconds=timeout_seconds,
        )
        libro_payload = libro_data.get("data")
        if isinstance(libro_payload, dict):
            result["libro_titulo"] = libro_payload.get("titulo", "")
            result["libro_editorial"] = libro_payload.get("editorial", "")
            result["libro_categoria"] = libro_payload.get("categoria", "")
    except ApiError:
        result["libro_titulo"] = ""
        result["libro_editorial"] = ""
        result["libro_categoria"] = ""

    try:
        usuario_data = _request_json(
            "GET",
            f"{usuarios_service_url}/api/v1/auth/usuarios/{prestamo.usuario_id}",
            timeout_seconds=timeout_seconds,
        )
        usuario_payload = usuario_data.get("data")
        if isinstance(usuario_payload, dict):
            result["usuario_nombre"] = usuario_payload.get("nombre", "")
    except ApiError:
        result["usuario_nombre"] = ""

    return result
