# mypy: disable-error-code=name-defined

from datetime import datetime, timezone

from app.extensions import db
from app.models.bootstrap import BootstrapRecord


class Autor(db.Model):
    __tablename__ = "autores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True, index=True)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    libros = db.relationship("Libro", back_populates="autor", lazy="select")

    def to_dict(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
        }


class Editorial(db.Model):
    __tablename__ = "editoriales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True, index=True)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    libros = db.relationship("Libro", back_populates="editorial", lazy="select")

    def to_dict(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
        }


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True, index=True)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    libros = db.relationship("Libro", back_populates="categoria", lazy="select")

    def to_dict(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
        }


class Libro(db.Model):
    __tablename__ = "libros"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False, index=True)
    isbn = db.Column(db.String(32), nullable=False, unique=True, index=True)
    autor_id = db.Column(db.Integer, db.ForeignKey("autores.id"), nullable=False, index=True)
    editorial_id = db.Column(
        db.Integer,
        db.ForeignKey("editoriales.id"),
        nullable=False,
        index=True,
    )
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id"),
        nullable=False,
        index=True,
    )
    disponibilidad = db.Column(db.Boolean, nullable=False, default=True, index=True)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    autor = db.relationship("Autor", back_populates="libros", lazy="joined")
    editorial = db.relationship("Editorial", back_populates="libros", lazy="joined")
    categoria = db.relationship("Categoria", back_populates="libros", lazy="joined")

    def to_dict(self) -> dict[str, str | int | bool]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "isbn": self.isbn,
            "autor_id": self.autor_id,
            "editorial_id": self.editorial_id,
            "categoria_id": self.categoria_id,
            "disponibilidad": self.disponibilidad,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "autor": self.autor.nombre,
            "editorial": self.editorial.nombre,
            "categoria": self.categoria.nombre,
        }


__all__ = [
    "Autor",
    "BootstrapRecord",
    "Categoria",
    "Editorial",
    "Libro",
]
