"""
Modelo de registro de bootstrap del servicio.

Este modulo define la tabla 'bootstrap_records' utilizada para rastrear qué servicios
han sido inicializados en la base de datos.
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