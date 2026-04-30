from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

from app.errors import ApiError


def register_error_handlers(app: Flask) -> None:
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