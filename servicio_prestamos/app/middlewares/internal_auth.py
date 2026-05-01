from functools import wraps
from typing import Any, Callable

from flask import current_app, request

from app.errors import ApiError

RouteHandler = Callable[..., Any]


def internal_secret_required(func: RouteHandler) -> RouteHandler:
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
