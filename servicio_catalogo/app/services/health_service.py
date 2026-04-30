from sqlalchemy import text

from app.extensions import db


def check_health(service_name: str) -> dict[str, str]:
    db.session.execute(text("SELECT 1"))

    return {
        "service": service_name,
        "status": "ok",
        "database": "up",
    }
