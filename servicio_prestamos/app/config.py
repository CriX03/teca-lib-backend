"""
Configuracion centralizada del servicio de prestamos.

Este modulo define las variables de configuracion necesarias para el funcionamiento
del servicio de prestamos de libros. Los valores se cargan desde variables de entorno.

Variables de entorno:
    SERVICE_NAME: Nombre identificador del servicio (default: servicio_prestamos).
    PORT: Puerto donde escuchara la aplicacion (default: 5000).
    DATABASE_URL: URL de conexion a PostgreSQL.
    USUARIOS_SERVICE_URL: URL del servicio de usuarios.
    CATALOGO_SERVICE_URL: URL del servicio de catalogo.
    EXTERNAL_SERVICES_TIMEOUT_SECONDS: Timeout para llamadas externas.
    PRESTAMO_DIAS_POR_DEFECTO: Dias de duracion de un prestamo (default: 14).
    INTERNAL_SERVICE_SECRET: Clave para comunicacion interna.
"""

import os


class Config:
    """Clase de configuracion que carga variables de entorno."""

    SERVICE_NAME = os.getenv("SERVICE_NAME", "servicio_prestamos")
    PORT = int(os.getenv("PORT", "5000"))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://teca_user:teca_password@localhost:5432/prestamos_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    USUARIOS_SERVICE_URL = os.getenv("USUARIOS_SERVICE_URL", "http://servicio_usuarios:5000")
    CATALOGO_SERVICE_URL = os.getenv("CATALOGO_SERVICE_URL", "http://servicio_catalogo:5000")
    EXTERNAL_SERVICES_TIMEOUT_SECONDS = float(
        os.getenv("EXTERNAL_SERVICES_TIMEOUT_SECONDS", "5")
    )
    PRESTAMO_DIAS_POR_DEFECTO = int(os.getenv("PRESTAMO_DIAS_POR_DEFECTO", "14"))
    INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "")