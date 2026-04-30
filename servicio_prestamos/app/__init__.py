import os
import time

from flask import Flask
from flask_cors import CORS
from flask import request
from flask import make_response
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.errors.handlers import register_error_handlers
from app.extensions import db, migrate
from app.models import BootstrapRecord
from app.routes import register_routes


def _initialize_database(app: Flask) -> None:
    max_attempts = int(os.getenv("DB_INIT_MAX_ATTEMPTS", "30"))
    delay_seconds = float(os.getenv("DB_INIT_DELAY_SECONDS", "2"))

    with app.app_context():
        for attempt in range(1, max_attempts + 1):
            try:
                db.create_all()

                service_name = app.config["SERVICE_NAME"]
                record = BootstrapRecord.query.filter_by(service_name=service_name).first()
                if record is None:
                    record = BootstrapRecord()
                    record.service_name = service_name
                    db.session.add(record)
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

    cors_origins = ["http://localhost:5173", "http://localhost:5174"]
    CORS(app, resources={r"/*": {"origins": cors_origins}}, supports_credentials=True)

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", cors_origins[0])
            response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,PATCH,OPTIONS")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response

    db.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)
    register_routes(app)
    _initialize_database(app)

    return app
