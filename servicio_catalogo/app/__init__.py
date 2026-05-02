"""
Punto de creacion de la aplicacion Flask para el servicio de catalogo.

Este modulo es el entry point principal de la aplicacion. Proporciona la funcion 'create_app()'
que inicializa y configura todos los componentes necesarios:
    - Instancia Flask y su configuracion.
    - Extensiones (SQLAlchemy, CORS, Migrate).
    - Manejadores de errores personalizados.
    - Rutas de la API.
    - Inicializacion de la base de datos.

El proceso de inicializacion incluye:
    - Creacion automatica de tablas (solo si no existen).
    - Registro de bootstrap del servicio.

Manejo de reconexion:
    - Implementa reintentos automaticos para la conexion a la base de datos.
    - Facilita el inicio del servicio cuando PostgreSQL esta arrancando.
"""

import os
import time

from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.errors.handlers import register_error_handlers
from app.extensions import db, migrate
from app.models import BootstrapRecord
from app.routes import register_routes


def _initialize_database(app: Flask) -> None:
    """
    Inicializa la base de datos con reintentos automaticos.

    Proceso:
        1. Intenta crear todas las tablas.
        2. Crea el registro de bootstrap del servicio.
        3. Reintenta en caso de error de conexion (hasta DB_INIT_MAX_ATTEMPTS).

    Args:
        app: Instancia de la aplicacion Flask.
    """
    max_attempts = int(os.getenv("DB_INIT_MAX_ATTEMPTS", "30"))
    delay_seconds = float(os.getenv("DB_INIT_DELAY_SECONDS", "2"))

    with app.app_context():
        for attempt in range(1, max_attempts + 1):
            try:
                db.create_all()

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
    """
    Crea y configura la aplicacion Flask del servicio.

    Pasos de inicializacion:
        1. Crear instancia Flask con la configuracion.
        2. Habilitar CORS para origenes de desarrollo.
        3. Inicializar SQLAlchemy y Migrate.
        4. Registrar manejadores de errores.
        5. Registrar todas las rutas.
        6. Inicializar base de datos.

    Returns:
        Instancia configurada de la aplicacion Flask.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=["http://localhost:5173", "http://localhost:5174"])

    db.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)
    register_routes(app)
    _initialize_database(app)

    return app