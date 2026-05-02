"""
Modelos de datos del servicio de prestamos.

Este modulo define los esquemas de tablas del servicio de prestamos, incluyendo:
    - Prestamo: Representa un prestamo de libro a un usuario.

Cada prestamo incluye referencias al usuario y libro, fechas de prestamo, limite y devolucion,
y un estado que indica si esta activo, devuelto o vencido.
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models.bootstrap import BootstrapRecord


class Prestamo(db.Model):
    """
    Modelo de prestamo de libro.

    Representa el prestamo de un libro a un usuario. Un prestamo tiene:
    - usuario_id: ID del usuario que toma el prestamo.
    - libro_id: ID del libro prestado.
    - fecha_prestamo: Fecha en que se realizo el prestamo.
    - fecha_devolucion: Fecha en que se devolvio el libro (null si aun no se devuelve).
    - fecha_limite: Fecha maxima para devolver.
    - estado: Puede ser 'activo', 'devuelto' o 'vencido'.
    """

    __tablename__ = "prestamos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    libro_id = db.Column(db.Integer, nullable=False, index=True)
    fecha_prestamo = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    fecha_devolucion = db.Column(db.DateTime(timezone=True), nullable=True)
    fecha_limite = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    estado = db.Column(db.String(30), nullable=False, default="activo", index=True)

    def to_dict(self) -> dict[str, int | str | None]:
        """Convierte el prestamo a diccionario."""
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "libro_id": self.libro_id,
            "fecha_prestamo": self.fecha_prestamo.isoformat(),
            "fecha_devolucion": (
                self.fecha_devolucion.isoformat()
                if self.fecha_devolucion is not None
                else None
            ),
            "fecha_limite": self.fecha_limite.isoformat(),
            "estado": self.estado,
        }


__all__ = ["BootstrapRecord", "Prestamo"]