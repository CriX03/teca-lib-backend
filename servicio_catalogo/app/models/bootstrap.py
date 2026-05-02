"""
Modelo de registro de bootstrap del servicio.

Este modulo define la tabla 'bootstrap_records' utilizada para rastrear qué servicios
han sido inicializados en la base de datos. El servicio verifica la existencia de este
registro para determinar si debe crear las tablas iniciales y datos por defecto.

Uso:
    - Se crea un registro con el nombre del servicio al inicializar.
    - Permite verificar si el servicio ya fue configurado previamente.
    - Facilita la deteccion de ejecuciones multiples en el mismo entorno.
"""

from datetime import datetime, timezone

from app.extensions import db


class BootstrapRecord(db.Model):
    """Modelo para registrar la inicializacion de servicios."""

    __tablename__ = "bootstrap_records"

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )