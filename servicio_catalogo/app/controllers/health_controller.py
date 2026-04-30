from flask import Response, current_app, jsonify
from sqlalchemy.exc import SQLAlchemyError

from app.services.health_service import check_health


def health() -> tuple[Response, int]:
    try:
        data = check_health(current_app.config["SERVICE_NAME"])
    except SQLAlchemyError:
        current_app.logger.exception("Health check failed due to database error.")
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "DATABASE_UNAVAILABLE",
                        "message": "Database connection is not available.",
                    },
                }
            ),
            503,
        )

    return (
        jsonify(
            {
                "success": True,
                "data": data,
                "message": "Service healthy.",
            }
        ),
        200,
    )
