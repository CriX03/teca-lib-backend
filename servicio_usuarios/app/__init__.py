import os
import time

from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.errors.handlers import register_error_handlers
from app.extensions import db, migrate
from app.models import BootstrapRecord, Role
from app.routes import register_routes


def _ensure_default_roles(default_roles: tuple[str, ...]) -> None:
    for role_name in default_roles:
        existing_role = Role.query.filter_by(nombre=role_name).first()
        if existing_role is None:
            db.session.add(Role(nombre=role_name))


def _initialize_database(app: Flask) -> None:
    max_attempts = int(os.getenv("DB_INIT_MAX_ATTEMPTS", "30"))
    delay_seconds = float(os.getenv("DB_INIT_DELAY_SECONDS", "2"))

    with app.app_context():
        for attempt in range(1, max_attempts + 1):
            try:
                db.create_all()

                _ensure_default_roles(app.config["DEFAULT_ROLES"])

                service_name = app.config["SERVICE_NAME"]
                record = BootstrapRecord.query.filter_by(service_name=service_name).first()
                if record is None:
                    db.session.add(BootstrapRecord(service_name=service_name))

                db.session.commit()

                return
            except SQLAlchemyError as error:
                db.session.rollback()
                app.logger.warning(
                    "Database initialization attempt %s/%s failed: %s",
                    attempt,
                    max_attempts,
                    error,
                )
                if attempt == max_attempts:
                    raise
                time.sleep(delay_seconds)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=["http://localhost:5173", "http://localhost:5174"])

    db.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)
    register_routes(app)
    _initialize_database(app)

    return app
