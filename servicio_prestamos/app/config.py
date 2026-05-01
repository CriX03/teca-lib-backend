import os


class Config:
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
