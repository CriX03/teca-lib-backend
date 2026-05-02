"""
Controlador de autenticacion y gestion de usuarios.

Este modulo mapea las peticiones HTTP a llamadas de los servicios de negocio.
Valida el formato de las peticiones, extrae los datos y форматatea las respuestas
en el esquema JSON estandarizado del proyecto.

Endpoints disponibles:
    - POST /api/v1/auth/registro: Registrar nuevo usuario.
    - POST /api/v1/auth/login: Autenticar usuario.
    - GET /api/v1/auth/me: Obtener usuario actual (requiere auth).
    - GET /api/v1/auth/admin/check: Verificar rol admin (requiere auth y admin).
    - GET /api/v1/auth/usuarios: Listar usuarios (requiere internal secret).
    - GET /api/v1/auth/usuarios/<id>: Obtener usuario por ID.

Respuestas:
    - Exito: {"success": true, "data": ..., "message": "..."}
    - Error: {"success": false, "error": {"code": ..., "message": ...}}
"""

from __future__ import annotations

from typing import Any

from flask import Response, current_app, jsonify, request

from app.errors import ApiError
from app.middlewares.auth import auth_required
from app.middlewares.roles import roles_required
from app.services.auth_service import get_user_by_id, login_user, register_user


def _extract_json() -> dict[str, Any]:
    """Extrae y valida el cuerpo JSON de la peticion."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(
            "INVALID_REQUEST_BODY",
            "El cuerpo de la peticion debe ser JSON valido.",
            400,
        )
    return data


def register() -> tuple[Response, int]:
    """
    Controlador para el registro de nuevos usuarios.

    Proceso:
        1. Extrae el JSON de la peticion.
        2. Llama al servicio de registro.
        3. Retorna respuesta exitosa con codigo 201.

    Returns:
        Tupla con respuesta JSON y codigo de estado HTTP.
    """
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
    """
    Controlador para el inicio de sesion de usuarios.

    Proceso:
        1. Extrae el JSON de la peticion.
        2. Valida credenciales y genera token JWT.
        3. Retorna token y datos del usuario.

    Returns:
        Tupla con respuesta JSON y codigo de estado HTTP.
    """
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
    """
    Controlador para obtener el usuario autenticado actual.

    Requiere: Token JWT valido en el header Authorization.

    Returns:
        Tupla con datos del usuario actual y codigo 200.
    """
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
    """
    Controlador para verificar permisos de administrador.

    Requiere: Token JWT y rol de administrador.

    Returns:
        Respuesta exitosa confirmando acceso de admin.
    """
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
    """
    Controlador para obtener un usuario por su ID.

    Args:
        user_id: Identificador del usuario a buscar.

    Returns:
        Tupla con datos del usuario encontrado.
    """
    user_data = get_user_by_id(user_id)
    return (
        jsonify(
            {
                "success": True,
                "data": user_data,
                "message": "Usuario obtenuido.",
            }
        ),
        200,
    )


def list_users_controller() -> tuple[Response, int]:
    """
    Controlador para listar usuarios con paginacion.

    Query params:
        - page: Numero de pagina (default: 1).
        - per_page: Elementos por pagina (default: 100, max: 1000).

    Returns:
        Tupla con lista de usuarios y metadatos de paginacion.
    """
    from flask import request

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 100, type=int), 1000)

    from app.services import list_all_users

    data = list_all_users(page=page, limit=per_page)
    return (
        jsonify(
            {
                "success": True,
                "data": data,
                "message": "Usuarios obtenidos.",
            }
        ),
        200,
    )