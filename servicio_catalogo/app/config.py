import os


class Config:
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
