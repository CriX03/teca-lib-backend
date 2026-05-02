"""
Middleware de autenticacion JWT para el servicio de usuarios.

Este modulo proporciona el decorador 'auth_required' que verifica la presencia y validez
de un token JWT en el header Authorization de las peticiones. Protege endpoints
que requieren autenticacion de usuario.

Flujo de autenticacion:
    1. Extrae el token del header Authorization (formato: Bearer <token>).
    2. Decodifica y valida el token usando la configuracion JWT.
    3. Recupera el usuario asociado del token.
    4. Adjunta el usuario al objeto request para uso en endpoints.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request

from app.errors import ApiError
from app.models import User
from app.services.auth_service import decode_access_token

RouteHandler = Callable[..., Any]


def _extract_bearer_token() -> str:
    """Extrae el token JWT del header Authorization."""
    authorization = request.headers.get("Authorization", "").strip()
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


def auth_required(func: RouteHandler) -> RouteHandler:
    """Decorador que exige autenticacion JWT para acceder al endpoint."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = _extract_bearer_token()
        claims = decode_access_token(
            token,
            jwt_secret=current_app.config["JWT_SECRET_KEY"],
            jwt_algorithm=current_app.config["JWT_ALGORITHM"],
            issuer=current_app.config["SERVICE_NAME"],
        )

        user_id = claims.get("sub")
        if not isinstance(user_id, str) or not user_id.isdigit():
            raise ApiError("INVALID_TOKEN", "El token no contiene un usuario valido.", 401)

        user = User.query.filter_by(id=int(user_id)).first()
        if user is None:
            raise ApiError("USER_NOT_FOUND", "Usuario no encontrado.", 401)

        request.current_user = user  # type: ignore[attr-defined]
        request.current_claims = claims  # type: ignore[attr-defined]

        return func(*args, **kwargs)

    return wrapper