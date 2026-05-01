import os


class Config:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "servicio_reportes")
    PORT = int(os.getenv("PORT", "5000"))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://teca_user:teca_password@localhost:5432/reportes_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    USUARIOS_SERVICE_URL = os.getenv("USUARIOS_SERVICE_URL", "http://localhost:5001")
    CATALOGO_SERVICE_URL = os.getenv("CATALOGO_SERVICE_URL", "http://localhost:5002")
    PRESTAMOS_SERVICE_URL = os.getenv("PRESTAMOS_SERVICE_URL", "http://localhost:5003")
    USUARIOS_SERVICE_TIMEOUT_SECONDS = int(os.getenv("USUARIOS_SERVICE_TIMEOUT_SECONDS", "5"))
    CATALOGO_SERVICE_TIMEOUT_SECONDS = int(os.getenv("CATALOGO_SERVICE_TIMEOUT_SECONDS", "5"))
    PRESTAMOS_SERVICE_TIMEOUT_SECONDS = int(os.getenv("PRESTAMOS_SERVICE_TIMEOUT_SECONDS", "5"))
    REPORTES_DEFAULT_LIMIT = int(os.getenv("REPORTES_DEFAULT_LIMIT", "10"))
    REPORTES_MAX_LIMIT = int(os.getenv("REPORTES_MAX_LIMIT", "100"))
    REPORTES_WORKER_ENABLED = os.getenv("REPORTES_WORKER_ENABLED", "true").lower() == "true"
    REPORTES_SYNC_INTERVAL_SECONDS = int(os.getenv("REPORTES_SYNC_INTERVAL_SECONDS", "300"))
    REPORTES_SYNC_TIMEOUT_SECONDS = int(os.getenv("REPORTES_SYNC_TIMEOUT_SECONDS", "10"))
    INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "")
