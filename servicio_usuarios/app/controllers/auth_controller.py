from __future__ import annotations

from typing import Any

from flask import Response, current_app, jsonify, request

from app.errors import ApiError
from app.middlewares.auth import auth_required
from app.middlewares.roles import roles_required
from app.services.auth_service import get_user_by_id, login_user, register_user


def _extract_json() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(
            "INVALID_REQUEST_BODY",
            "El cuerpo de la peticion debe ser JSON valido.",
            400,
        )
    return data


def register() -> tuple[Response, int]:
    payload = _extract_json()
    user_data = register_user(payload, current_app.config["DEFAULT_ROLES"])

    return (
        jsonify(
            {
                "success": True,
                "data": user_data,
                "message": "Usuario registrado correctamente.",
            }
        ),
        201,
    )


def login() -> tuple[Response, int]:
    payload = _extract_json()
    token_data = login_user(
        payload,
        jwt_secret=current_app.config["JWT_SECRET_KEY"],
        jwt_algorithm=current_app.config["JWT_ALGORITHM"],
        expires_minutes=current_app.config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"],
        issuer=current_app.config["SERVICE_NAME"],
    )

    return (
        jsonify(
            {
                "success": True,
                "data": token_data,
                "message": "Autenticacion exitosa.",
            }
        ),
        200,
    )


@auth_required
def me() -> tuple[Response, int]:
    current_user = getattr(request, "current_user", None)
    if current_user is None:
        raise ApiError(
            "AUTH_REQUIRED", "Debes autenticarte para acceder a este recurso.", 401
        )

    user_data = current_user.to_dict()
    return (
        jsonify(
            {
                "success": True,
                "data": user_data,
                "message": "Usuario autenticado.",
            }
        ),
        200,
    )


@auth_required
@roles_required("admin")
def admin_check() -> tuple[Response, int]:
    return (
        jsonify(
            {
                "success": True,
                "data": {"authorized": True},
                "message": "Permiso de administrador valido.",
            }
        ),
        200,
    )


def get_user_by_id_controller(user_id: int) -> tuple[Response, int]:
    user_data = get_user_by_id(user_id)
    return (
        jsonify(
            {
                "success": True,
                "data": user_data,
                "message": "Usuario obtenido.",
            }
        ),
        200,
    )
