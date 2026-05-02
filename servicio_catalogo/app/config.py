"""
Configuracion centralizada del servicio de catalogo.

Este modulo define las variables de configuracion necesarias para el funcionamiento
del servicio de catalogo de libros. Los valores se cargan desde variables de entorno
con valores por defecto seguros para desarrollo.

Variables de entorno:
    SERVICE_NAME: Nombre identificador del servicio (default: servicio_catalogo).
    PORT: Puerto donde escuchara la aplicacion (default: 5000).
    DATABASE_URL: URL de conexion a PostgreSQL.
    USUARIOS_SERVICE_URL: URL del servicio de usuarios para validacion de tokens.
    USUARIOS_SERVICE_TIMEOUT_SECONDS: Timeout para llamadas al servicio de usuarios.
    INTERNAL_SERVICE_SECRET: Clave para comunicacion interna entre servicios.
"""

import os


class Config:
    """Clase de configuracion que carga variables de entorno."""

    SERVICE_NAME = os.getenv("SERVICE_NAME", "servicio_catalogo")
    PORT = int(os.getenv("PORT", "5000"))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://teca_user:teca_password@localhost:5432/catalogo_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    USUARIOS_SERVICE_URL = os.getenv("USUARIOS_SERVICE_URL", "http://localhost:5001")
    USUARIOS_SERVICE_TIMEOUT_SECONDS = int(os.getenv("USUARIOS_SERVICE_TIMEOUT_SECONDS", "5"))
    INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "")