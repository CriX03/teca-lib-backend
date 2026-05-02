"""
Modelo de datos para usuarios del sistema.

Este modulo define el esquema de la tabla 'usuarios' en la base de datos, que almacena la informacion
de todos los usuarios registrados en el sistema de biblioteca. Cada usuario representa una persona
con acceso al sistema, identificada por su rol especifico.

Campos:
    - id: Identificador unico del usuario.
    - nombre: Nombre completo del usuario.
    - email: Correo electronico unico del usuario ( sirve como identificador de login).
    - contrasena: Hash de la contrasena del usuario ( nunca se almacena en texto plano).
    - rol_id: Referencia al rol del usuario (determina permisos de acceso).
    - fecha_creacion: Fecha y hora de registro del usuario.

Relaciones:
    - Cada usuario tiene un rol asociado (relacion muchos a uno con Role).
"""

from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    """Definicion del modelo de usuario del sistema."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    contrasena = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, index=True)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    rol = db.relationship("Role", back_populates="usuarios", lazy="joined")

    def to_dict(self) -> dict[str, str | int]:
        """Convierte el usuario a un diccionario con datos serializables."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
        }