# mypy: disable-error-code=name-defined

from __future__ import annotations

from datetime import datetime, timezone

from app.extensions import db
from app.models.bootstrap import BootstrapRecord

ESTADO_PENDIENTE = "pendiente"
ESTADO_REINTENTO = "reintento"
ESTADO_ENVIADA = "enviada"
ESTADO_FALLIDA = "fallida"


class Notificacion(db.Model):
    __tablename__ = "notificaciones"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    prestamo_id = db.Column(db.Integer, nullable=True, index=True)
    tipo = db.Column(db.String(50), nullable=False, default="general", index=True)
    destinatario_email = db.Column(db.String(255), nullable=False, index=True)
    asunto = db.Column(db.String(255), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    fecha_programada = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    estado = db.Column(db.String(30), nullable=False, default=ESTADO_PENDIENTE, index=True)
    reintentos = db.Column(db.Integer, nullable=False, default=0)
    max_reintentos = db.Column(db.Integer, nullable=False, default=3)
    proximo_reintento = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    ultimo_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.Index(
            "ix_notificaciones_estado_programada_reintento",
            "estado",
            "fecha_programada",
            "proximo_reintento",
        ),
    )

    def to_dict(self) -> dict[str, int | str | None]:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "prestamo_id": self.prestamo_id,
            "tipo": self.tipo,
            "destinatario_email": self.destinatario_email,
            "asunto": self.asunto,
            "mensaje": self.mensaje,
            "fecha_envio": self.fecha_envio.isoformat() if self.fecha_envio is not None else None,
            "fecha_programada": self.fecha_programada.isoformat(),
            "estado": self.estado,
            "reintentos": self.reintentos,
            "max_reintentos": self.max_reintentos,
            "proximo_reintento": (
                self.proximo_reintento.isoformat()
                if self.proximo_reintento is not None
                else None
            ),
            "ultimo_error": self.ultimo_error,
        }


__all__ = [
    "BootstrapRecord",
    "ESTADO_ENVIADA",
    "ESTADO_FALLIDA",
    "ESTADO_PENDIENTE",
    "ESTADO_REINTENTO",
    "Notificacion",
]
