"""
Manejadores de errores personalizados del servicio.

Este modulo registra los manejo de errores de la aplicacion Flask, convirtiendo excepciones
en respuestas JSON estandarizadas. Proporciona una interface consistente para errores
tanto de la API personalizada como de excepciones HTTP standard.

Errores manejados:
    - ApiError: Errores personalizados de la aplicacion.
    - HTTPException: Errores standard de Werkzeug (404, 405, etc.).
    - Exception: Errores inesperados del servidor (solo se logsuea el detalle).
"""

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

from app.errors import ApiError


def register_error_handlers(app: Flask) -> None:
    """Registra los manejadores de errores en la aplicacion Flask."""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError) -> tuple[Response, int]:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": error.code,
                        "message": error.message,
                    },
                }
            ),
            error.status_code,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> tuple[Response, int]:
        status_code = error.code if error.code is not None else 500
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": error.name.upper().replace(" ", "_"),
                        "message": error.description,
                    },
                }
            ),
            status_code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception) -> tuple[Response, int]:
        app.logger.exception("Unhandled exception: %s", error)
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred.",
                    },
                }
            ),
            500,
        )