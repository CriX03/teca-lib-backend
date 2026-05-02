"""
Configuracion centralizada del servicio de notificaciones.

Este modulo define las variables de configuracion necesarias para el funcionamiento
del servicio de notificaciones por email.

Variables de entorno:
    SERVICE_NAME: Nombre del servicio.
    DATABASE_URL: URL de conexion a PostgreSQL.
    USUARIOS_SERVICE_URL: URL del servicio de usuarios.
    SMTP_HOST, SMTP_PORT: Servidor de email.
    SMTP_* : Configuracion de autenticacion SMTP.
    MAX_REINTENTOS_ENVIO: Reintentos para mensajes fallidos.
    NOTIFICATIONS_WORKER_*: Configuracion del proceso en segundo plano.
"""

import os


class Config:
    """Clase de configuracion que carga variables de entorno."""

    SERVICE_NAME = os.getenv("SERVICE_NAME", "servicio_notificaciones")
    PORT = int(os.getenv("PORT", "5000"))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://teca_user:teca_password@localhost:5432/notificaciones_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    USUARIOS_SERVICE_URL = os.getenv("USUARIOS_SERVICE_URL", "http://localhost:5001")
    USUARIOS_SERVICE_TIMEOUT_SECONDS = int(os.getenv("USUARIOS_SERVICE_TIMEOUT_SECONDS", "5"))
    SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    SMTP_TIMEOUT_SECONDS = float(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@teca.local")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Teca Biblioteca")

    MAX_REINTENTOS_ENVIO = int(os.getenv("MAX_REINTENTOS_ENVIO", "3"))
    RETRY_BASE_DELAY_MINUTES = int(os.getenv("RETRY_BASE_DELAY_MINUTES", "5"))
    NOTIFICATIONS_WORKER_ENABLED = (
        os.getenv("NOTIFICATIONS_WORKER_ENABLED", "true").lower() == "true"
    )
    NOTIFICATIONS_WORKER_INTERVAL_SECONDS = int(
        os.getenv("NOTIFICATIONS_WORKER_INTERVAL_SECONDS", "30")
    )
    NOTIFICATIONS_WORKER_BATCH_SIZE = int(
        os.getenv("NOTIFICATIONS_WORKER_BATCH_SIZE", "50")
    )