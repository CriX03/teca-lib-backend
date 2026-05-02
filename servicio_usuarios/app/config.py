"""
Configuracion centralizada del servicio de usuarios.

Este modulo define las variables de configuracion necesarias para el funcionamiento
del servicio de autenticacion y gestion de usuarios. Los valores se cargan desde
variables de entorno con valores por defecto seguros para desarrollo.

Variables de entorno:
    SERVICE_NAME: Nombre identificador del servicio (default: servicio_usuarios).
    PORT: Puerto donde escuchara la aplicacion (default: 5000).
    SECRET_KEY: Clave secreta para sesiones Flask.
    DATABASE_URL: URL de conexion a PostgreSQL.
    JWT_SECRET_KEY: Clave secreta para firmar tokens JWT.
    JWT_ALGORITHM: Algoritmo de firma JWT (default: HS256).
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: Tiempo de validez del token en minutos (default: 60).
    INTERNAL_SERVICE_SECRET: Clave para comunicacion interna entre servicios.
"""

import os


class Config:
    """Clase de configuracion que carga variables de entorno."""

    SERVICE_NAME = os.getenv("SERVICE_NAME", "servicio_usuarios")
    PORT = int(os.getenv("PORT", "5000"))
    SECRET_KEY = os.getenv("SECRET_KEY", "teca-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://teca_user:teca_password@localhost:5432/usuarios_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "teca-jwt-dev-secret")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60")
    )
    DEFAULT_ROLES = ("admin", "estudiante", "docente")
    INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "")