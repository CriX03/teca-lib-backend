"""
Modelo de datos para roles de usuarios.

Este modulo define el esquema de la tabla 'roles' en la base de datos, que almacena los diferentes
roles existentes en el sistema de biblioteca. Los roles determinan los permisos y accesos
de cada usuario dentro de la plataforma.

Estructura de roles predefinidos:
    - admin: Acceso completo a todas las funcionalidades del sistema.
    - estudiante: Acceso a prestamos y consultas del catalogo.
    - docente: Acceso a prestamos y gestion de materiales academicos.

Relaciones:
    - Un rol puede tener multiples usuarios asociados (relacion uno a muchos).
"""

from datetime import datetime, timezone

from app.extensions import db


class Role(db.Model):
    """Definicion del modelo de rol de usuario."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True, index=True)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    usuarios = db.relationship("User", back_populates="rol", lazy="select")