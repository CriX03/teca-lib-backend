# mypy: disable-error-code=name-defined

from __future__ import annotations

from datetime import datetime, timezone

from app.extensions import db
from app.models.bootstrap import BootstrapRecord


class PrestamoAnalitico(db.Model):
    __tablename__ = "prestamos_analiticos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios_analiticos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    libro_id = db.Column(
        db.Integer,
        db.ForeignKey("libros_analiticos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_prestamo = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    fecha_devolucion = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    fecha_limite = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    estado = db.Column(db.String(30), nullable=False, default="activo", index=True)

    usuario = db.relationship("UsuarioAnalitico", back_populates="prestamos")
    libro = db.relationship("LibroAnalitico", back_populates="prestamos")

    __table_args__ = (
        db.Index(
            "ix_prestamos_analiticos_usuario_estado_fecha",
            "usuario_id",
            "estado",
            "fecha_prestamo",
        ),
        db.Index(
            "ix_prestamos_analiticos_libro_estado_fecha",
            "libro_id",
            "estado",
            "fecha_prestamo",
        ),
        db.Index(
            "ix_prestamos_analiticos_retrasos",
            "estado",
            "fecha_limite",
            "fecha_devolucion",
        ),
    )


class LibroAnalitico(db.Model):
    __tablename__ = "libros_analiticos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False, index=True)
    prestamos = db.relationship("PrestamoAnalitico", back_populates="libro")


class UsuarioAnalitico(db.Model):
    __tablename__ = "usuarios_analiticos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    prestamos = db.relationship("PrestamoAnalitico", back_populates="usuario")


__all__ = [
    "BootstrapRecord",
    "LibroAnalitico",
    "PrestamoAnalitico",
    "UsuarioAnalitico",
]
