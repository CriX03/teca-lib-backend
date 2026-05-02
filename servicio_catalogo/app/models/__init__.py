"""
Modelos de datos del servicio de catalogo.

Este modulo define los esquemas de todas las tablas del servicio de catalogo de libros,
incluyendo: Autor, Editorial, Categoria y Libro.

Relaciones entre modelos:
    - Autor (1) -> (N) Libro: Un autor puede tener multiples libros.
    - Editorial (1) -> (N) Libro: Una editorial puede publicar multiples libros.
    - Categoria (1) -> (N) Libro: Una categoria puede contener multiples libros.

Cada modelo incluye el metodo to_dict() para.serializacion JSON.
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models.bootstrap import BootstrapRecord


class Autor(db.Model):
    """
    Modelo de autor de libros.

    Representa a los autores de los libros en el catalogo.
    Cada autor tiene un nombre unico y puede haber escrito multiples libros.
    """

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
        """Convierte el autor a un diccionario con datos serializables."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
        }


class Editorial(db.Model):
    """
    Modelo de editorial de libros.

    Representa a las editorialess publicadoras de libros en el catalogo.
    Cada editorial tiene un nombre unico y puede haber publicado multiples libros.
    """

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
        """Convierte la editorial a un diccionario con datos serializables."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
        }


class Categoria(db.Model):
    """
    Modelo de categoria de libros.

    Representa las categorias o generos literarios de los libros en el catalogo.
    Cada categoria tiene un nombre unico y puede contener multiples libros.
    """

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
        """Convierte la categoria a un diccionario con datos serializables."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
        }


class Libro(db.Model):
    """
    Modelo de libro del catalogo.

    Representa un libro en el sistema de biblioteca. Cada libro tiene:
    - titulo: Nombre del libro.
    - isbn: Codigo unico internacional de libro.
    - Referencias a autor, editorial y categoria.
    - disponibilidad: Indica si el libro puede ser prestado.

    Relaciones:
    - Un libro tiene un autor (relacion muchos a uno).
    - Un libro tiene una editorial (relacion muchos a uno).
    - Un libro tiene una categoria (relacion muchos a uno).
    """

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
        """Convierte el libro a un diccionario con datos serializables."""
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