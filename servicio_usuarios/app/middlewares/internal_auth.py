"""
Middleware de autenticacion para comunicacion interna entre servicios.

Este modulo proporciona el decorador 'internal_secret_required' que verifica una clave
secreta compartida entre servicios del sistema. Se utiliza para proteger endpoints
que deben ser accesibles solo por otros microservicios internos, no por clientes externos.

Uso:
    - Proteger endpoints de sincronizacion entre servicios.
    - Verificar que las peticiones provengan de servicios autorizados.
    - El header 'X-Internal-Secret' debe contener la clave configurada.

Configuracion:
    - INTERNAL_SERVICE_SECRET: Variable de entorno que define la clave compartida.
"""

from functools import wraps
from typing import Any, Callable

from flask import current_app, request

from app.errors import ApiError

RouteHandler = Callable[..., Any]


def internal_secret_required(func: RouteHandler) -> RouteHandler:
    """Decorador que verifica la clave de autentificacion interna."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        secret = request.headers.get("X-Internal-Secret", "")
        expected = current_app.config.get("INTERNAL_SERVICE_SECRET", "")
        if not expected:
            return func(*args, **kwargs)
        if secret != expected:
            raise ApiError(
                "UNAUTHORIZED",
                "Internal service secret required.",
                401,
            )
        return func(*args, **kwargs)

    return wrapper