from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import request

from app.errors import ApiError

RouteHandler = Callable[..., Any]


def roles_required(*allowed_roles: str) -> Callable[[RouteHandler], RouteHandler]:
    normalized_roles = {role.strip().lower() for role in allowed_roles}

    def decorator(func: RouteHandler) -> RouteHandler:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user = getattr(request, "current_user", None)
            if current_user is None:
                raise ApiError(
                    "AUTH_REQUIRED",
                    "Debes autenticarte para acceder a este recurso.",
                    401,
                )

            user_role = current_user.rol.nombre.lower()
            if user_role not in normalized_roles:
                raise ApiError(
                    "FORBIDDEN",
                    "No tienes permisos para acceder a este recurso.",
                    403,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
