"""
Middleware de autenticacion para el servicio de catalogo.

Este modulo proporciona el decorador 'auth_required' que valida tokens JWT
llamando al servicio de usuarios externo. A diferencia del servicio de usuarios,
el catalogo delega la validacion para mantener desacoplamiento.

Flujo de autenticacion:
    1. Extrae el token del header Authorization (formato: Bearer <token>).
    2. Llama al endpoint /api/v1/auth/me del servicio de usuarios.
    3. Recupera los datos del usuario y los adjunta a la peticion.
    4. Maneja errores de conexion o token invalido.

Configuracion:
    - USUARIOS_SERVICE_URL: URL del servicio de usuarios.
    - USUARIOS_SERVICE_TIMEOUT_SECONDS: Timeout para la validacion.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

import requests
from flask import current_app, request

from app.errors import ApiError

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


def _validate_token_with_usuarios_service(
    token: str,
    usuarios_service_url: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """
    Valida el token con el servicio de usuarios externo.

    Args:
        token: Token JWT a validar.
        usuarios_service_url: URL base del servicio de usuarios.
        timeout_seconds: Timeout para la peticion HTTP.

    Returns:
        Datos del usuario contenidos en la respuesta.

    Raises:
        ApiError: Si la validacion falla.
    """
    try:
        response = requests.get(
            f"{usuarios_service_url}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout_seconds,
        )
        if response.status_code == 401:
            raise ApiError("AUTH_REQUIRED", "Token invalido o expirado.", 401)
        if response.status_code != 200:
            raise ApiError(
                "AUTH_SERVICE_ERROR",
                f"Error al validar token: {response.status_code}",
                401,
            )
        data = response.json()
        return data.get("data", {})
    except requests.RequestException as e:
        current_app.logger.error("ErrorValidatingToken: %s", e)
        raise ApiError(
            "AUTH_SERVICE_UNAVAILABLE",
            "No se puede validar el token en este momento.",
            503,
        )


def auth_required(func: RouteHandler) -> RouteHandler:
    """Decorador que exige autenticacion para acceder al endpoint."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = _extract_bearer_token()
        usuarios_service_url = current_app.config["USUARIOS_SERVICE_URL"]
        timeout_seconds = current_app.config.get("USUARIOS_SERVICE_TIMEOUT_SECONDS", 5)

        user_data = _validate_token_with_usuarios_service(
            token,
            usuarios_service_url,
            timeout_seconds,
        )

        request.current_user = user_data  # type: ignore[attr-defined]

        return func(*args, **kwargs)

    return wrapper