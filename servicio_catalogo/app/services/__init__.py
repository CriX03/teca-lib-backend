from __future__ import annotations

import re
from typing import Any

from sqlalchemy import func

from app.errors import ApiError
from app.extensions import db
from app.models import Autor, Categoria, Editorial, Libro

ISBN_PATTERN = re.compile(r"^[0-9Xx-]{10,17}$")


def _clean_nombre(value: Any, field_name: str = "nombre") -> str:
    if not isinstance(value, str):
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser texto.",
            422,
        )

    nombre = value.strip()
    if len(nombre) < 2 or len(nombre) > 120:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe tener entre 2 y 120 caracteres.",
            422,
        )

    return nombre


def _clean_titulo(value: Any) -> str:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "El campo 'titulo' debe ser texto.", 422)

    titulo = value.strip()
    if len(titulo) < 2 or len(titulo) > 255:
        raise ApiError(
            "VALIDATION_ERROR",
            "El campo 'titulo' debe tener entre 2 y 255 caracteres.",
            422,
        )

    return titulo


def _clean_isbn(value: Any) -> str:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "El campo 'isbn' debe ser texto.", 422)

    isbn = value.strip().upper()
    if not ISBN_PATTERN.match(isbn):
        raise ApiError(
            "VALIDATION_ERROR",
            "El ISBN debe tener formato valido (10-17 caracteres, digitos, X y guiones).",
            422,
        )

    return isbn


def _clean_id(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser un entero positivo.",
            422,
        )
    return value


def _parse_bool(value: Any, field_name: str = "disponibilidad") -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "si"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    raise ApiError(
        "VALIDATION_ERROR",
        f"El campo '{field_name}' debe ser booleano.",
        422,
    )


def _parse_pagination(page_value: str | None, per_page_value: str | None) -> tuple[int, int]:
    page = 1
    per_page = 20

    if page_value is not None:
        if not page_value.isdigit() or int(page_value) <= 0:
            raise ApiError("VALIDATION_ERROR", "El parametro 'page' debe ser positivo.", 422)
        page = int(page_value)

    if per_page_value is not None:
        if not per_page_value.isdigit() or int(per_page_value) <= 0:
            raise ApiError(
                "VALIDATION_ERROR",
                "El parametro 'per_page' debe ser positivo.",
                422,
            )
        per_page = min(int(per_page_value), 100)

    return page, per_page


def _build_paginated_response(items: list[dict[str, Any]], total: int, page: int, per_page: int) -> dict[str, Any]:
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }


def list_autores(*, nombre: str | None, page: int, per_page: int) -> dict[str, Any]:
    query = Autor.query
    if nombre:
        query = query.filter(func.lower(Autor.nombre).like(f"%{nombre.lower()}%"))

    total = query.count()
    autores = (
        query.order_by(Autor.nombre.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return _build_paginated_response([a.to_dict() for a in autores], total, page, per_page)


def create_autor(payload: dict[str, Any]) -> dict[str, Any]:
    nombre = _clean_nombre(payload.get("nombre"))
    existing = Autor.query.filter(func.lower(Autor.nombre) == nombre.lower()).first()
    if existing is not None:
        raise ApiError("AUTOR_ALREADY_EXISTS", "Ya existe un autor con ese nombre.", 409)

    autor = Autor(nombre=nombre)
    db.session.add(autor)
    db.session.commit()
    return autor.to_dict()


def get_autor(autor_id: int) -> dict[str, Any]:
    autor = Autor.query.filter_by(id=autor_id).first()
    if autor is None:
        raise ApiError("AUTOR_NOT_FOUND", "Autor no encontrado.", 404)
    return autor.to_dict()


def update_autor(autor_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    autor = Autor.query.filter_by(id=autor_id).first()
    if autor is None:
        raise ApiError("AUTOR_NOT_FOUND", "Autor no encontrado.", 404)

    nombre = _clean_nombre(payload.get("nombre"))
    existing = Autor.query.filter(func.lower(Autor.nombre) == nombre.lower(), Autor.id != autor_id).first()
    if existing is not None:
        raise ApiError("AUTOR_ALREADY_EXISTS", "Ya existe un autor con ese nombre.", 409)

    autor.nombre = nombre
    db.session.commit()
    return autor.to_dict()


def delete_autor(autor_id: int) -> None:
    autor = Autor.query.filter_by(id=autor_id).first()
    if autor is None:
        raise ApiError("AUTOR_NOT_FOUND", "Autor no encontrado.", 404)

    has_books = Libro.query.filter_by(autor_id=autor_id).first() is not None
    if has_books:
        raise ApiError(
            "AUTOR_IN_USE",
            "No se puede eliminar el autor porque tiene libros asociados.",
            409,
        )

    db.session.delete(autor)
    db.session.commit()


def list_editoriales(*, nombre: str | None, page: int, per_page: int) -> dict[str, Any]:
    query = Editorial.query
    if nombre:
        query = query.filter(func.lower(Editorial.nombre).like(f"%{nombre.lower()}%"))

    total = query.count()
    editoriales = (
        query.order_by(Editorial.nombre.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return _build_paginated_response(
        [e.to_dict() for e in editoriales], total, page, per_page
    )


def create_editorial(payload: dict[str, Any]) -> dict[str, Any]:
    nombre = _clean_nombre(payload.get("nombre"))
    existing = Editorial.query.filter(func.lower(Editorial.nombre) == nombre.lower()).first()
    if existing is not None:
        raise ApiError(
            "EDITORIAL_ALREADY_EXISTS",
            "Ya existe una editorial con ese nombre.",
            409,
        )

    editorial = Editorial(nombre=nombre)
    db.session.add(editorial)
    db.session.commit()
    return editorial.to_dict()


def get_editorial(editorial_id: int) -> dict[str, Any]:
    editorial = Editorial.query.filter_by(id=editorial_id).first()
    if editorial is None:
        raise ApiError("EDITORIAL_NOT_FOUND", "Editorial no encontrada.", 404)
    return editorial.to_dict()


def update_editorial(editorial_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    editorial = Editorial.query.filter_by(id=editorial_id).first()
    if editorial is None:
        raise ApiError("EDITORIAL_NOT_FOUND", "Editorial no encontrada.", 404)

    nombre = _clean_nombre(payload.get("nombre"))
    existing = Editorial.query.filter(
        func.lower(Editorial.nombre) == nombre.lower(),
        Editorial.id != editorial_id,
    ).first()
    if existing is not None:
        raise ApiError(
            "EDITORIAL_ALREADY_EXISTS",
            "Ya existe una editorial con ese nombre.",
            409,
        )

    editorial.nombre = nombre
    db.session.commit()
    return editorial.to_dict()


def delete_editorial(editorial_id: int) -> None:
    editorial = Editorial.query.filter_by(id=editorial_id).first()
    if editorial is None:
        raise ApiError("EDITORIAL_NOT_FOUND", "Editorial no encontrada.", 404)

    has_books = Libro.query.filter_by(editorial_id=editorial_id).first() is not None
    if has_books:
        raise ApiError(
            "EDITORIAL_IN_USE",
            "No se puede eliminar la editorial porque tiene libros asociados.",
            409,
        )

    db.session.delete(editorial)
    db.session.commit()


def list_categorias(*, nombre: str | None, page: int, per_page: int) -> dict[str, Any]:
    query = Categoria.query
    if nombre:
        query = query.filter(func.lower(Categoria.nombre).like(f"%{nombre.lower()}%"))

    total = query.count()
    categorias = (
        query.order_by(Categoria.nombre.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return _build_paginated_response(
        [c.to_dict() for c in categorias], total, page, per_page
    )


def create_categoria(payload: dict[str, Any]) -> dict[str, Any]:
    nombre = _clean_nombre(payload.get("nombre"))
    existing = Categoria.query.filter(func.lower(Categoria.nombre) == nombre.lower()).first()
    if existing is not None:
        raise ApiError(
            "CATEGORIA_ALREADY_EXISTS",
            "Ya existe una categoria con ese nombre.",
            409,
        )

    categoria = Categoria(nombre=nombre)
    db.session.add(categoria)
    db.session.commit()
    return categoria.to_dict()


def get_categoria(categoria_id: int) -> dict[str, Any]:
    categoria = Categoria.query.filter_by(id=categoria_id).first()
    if categoria is None:
        raise ApiError("CATEGORIA_NOT_FOUND", "Categoria no encontrada.", 404)
    return categoria.to_dict()


def update_categoria(categoria_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    categoria = Categoria.query.filter_by(id=categoria_id).first()
    if categoria is None:
        raise ApiError("CATEGORIA_NOT_FOUND", "Categoria no encontrada.", 404)

    nombre = _clean_nombre(payload.get("nombre"))
    existing = Categoria.query.filter(
        func.lower(Categoria.nombre) == nombre.lower(),
        Categoria.id != categoria_id,
    ).first()
    if existing is not None:
        raise ApiError(
            "CATEGORIA_ALREADY_EXISTS",
            "Ya existe una categoria con ese nombre.",
            409,
        )

    categoria.nombre = nombre
    db.session.commit()
    return categoria.to_dict()


def delete_categoria(categoria_id: int) -> None:
    categoria = Categoria.query.filter_by(id=categoria_id).first()
    if categoria is None:
        raise ApiError("CATEGORIA_NOT_FOUND", "Categoria no encontrada.", 404)

    has_books = Libro.query.filter_by(categoria_id=categoria_id).first() is not None
    if has_books:
        raise ApiError(
            "CATEGORIA_IN_USE",
            "No se puede eliminar la categoria porque tiene libros asociados.",
            409,
        )

    db.session.delete(categoria)
    db.session.commit()


def _get_existing_references(autor_id: int, editorial_id: int, categoria_id: int) -> tuple[Autor, Editorial, Categoria]:
    autor = Autor.query.filter_by(id=autor_id).first()
    if autor is None:
        raise ApiError("AUTOR_NOT_FOUND", "Autor no encontrado.", 422)

    editorial = Editorial.query.filter_by(id=editorial_id).first()
    if editorial is None:
        raise ApiError("EDITORIAL_NOT_FOUND", "Editorial no encontrada.", 422)

    categoria = Categoria.query.filter_by(id=categoria_id).first()
    if categoria is None:
        raise ApiError("CATEGORIA_NOT_FOUND", "Categoria no encontrada.", 422)

    return autor, editorial, categoria


def list_libros(
    *,
    titulo: str | None,
    isbn: str | None,
    autor_id: int | None,
    editorial_id: int | None,
    categoria_id: int | None,
    disponible: bool | None,
    page: int,
    per_page: int,
) -> dict[str, Any]:
    query = Libro.query
    if titulo:
        query = query.filter(func.lower(Libro.titulo).like(f"%{titulo.lower()}%"))
    if isbn:
        query = query.filter(Libro.isbn == isbn.upper())
    if autor_id is not None:
        query = query.filter(Libro.autor_id == autor_id)
    if editorial_id is not None:
        query = query.filter(Libro.editorial_id == editorial_id)
    if categoria_id is not None:
        query = query.filter(Libro.categoria_id == categoria_id)
    if disponible is not None:
        query = query.filter(Libro.disponibilidad.is_(disponible))

    total = query.count()
    libros = (
        query.order_by(Libro.fecha_creacion.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return _build_paginated_response(
        [libro.to_dict() for libro in libros],
        total,
        page,
        per_page,
    )


def create_libro(payload: dict[str, Any]) -> dict[str, Any]:
    titulo = _clean_titulo(payload.get("titulo"))
    isbn = _clean_isbn(payload.get("isbn"))
    autor_id = _clean_id(payload.get("autor_id"), "autor_id")
    editorial_id = _clean_id(payload.get("editorial_id"), "editorial_id")
    categoria_id = _clean_id(payload.get("categoria_id"), "categoria_id")
    disponibilidad = payload.get("disponibilidad", True)
    disponible = _parse_bool(disponibilidad)
    descripcion = payload.get("descripcion")

    existing = Libro.query.filter_by(isbn=isbn).first()
    if existing is not None:
        raise ApiError("ISBN_ALREADY_EXISTS", "Ya existe un libro con ese ISBN.", 409)

    _get_existing_references(autor_id, editorial_id, categoria_id)

    libro = Libro(
        titulo=titulo,
        isbn=isbn,
        autor_id=autor_id,
        editorial_id=editorial_id,
        categoria_id=categoria_id,
        disponibilidad=disponible,
        descripcion=descripcion,
    )
    db.session.add(libro)
    db.session.commit()
    return libro.to_dict()


def get_libro(libro_id: int) -> dict[str, Any]:
    libro = Libro.query.filter_by(id=libro_id).first()
    if libro is None:
        raise ApiError("LIBRO_NOT_FOUND", "Libro no encontrado.", 404)
    return libro.to_dict()


def update_libro(libro_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    libro = Libro.query.filter_by(id=libro_id).first()
    if libro is None:
        raise ApiError("LIBRO_NOT_FOUND", "Libro no encontrado.", 404)

    titulo = _clean_titulo(payload.get("titulo"))
    isbn = _clean_isbn(payload.get("isbn"))
    autor_id = _clean_id(payload.get("autor_id"), "autor_id")
    editorial_id = _clean_id(payload.get("editorial_id"), "editorial_id")
    categoria_id = _clean_id(payload.get("categoria_id"), "categoria_id")
    disponible = _parse_bool(payload.get("disponibilidad", libro.disponibilidad))
    descripcion = payload.get("descripcion", libro.descripcion)

    existing = Libro.query.filter(Libro.isbn == isbn, Libro.id != libro_id).first()
    if existing is not None:
        raise ApiError("ISBN_ALREADY_EXISTS", "Ya existe un libro con ese ISBN.", 409)

    _get_existing_references(autor_id, editorial_id, categoria_id)

    libro.titulo = titulo
    libro.isbn = isbn
    libro.autor_id = autor_id
    libro.editorial_id = editorial_id
    libro.categoria_id = categoria_id
    libro.disponibilidad = disponible
    libro.descripcion = descripcion

    db.session.commit()
    return libro.to_dict()


def update_disponibilidad(libro_id: int, disponibilidad: Any) -> dict[str, Any]:
    libro = Libro.query.filter_by(id=libro_id).first()
    if libro is None:
        raise ApiError("LIBRO_NOT_FOUND", "Libro no encontrado.", 404)

    libro.disponibilidad = _parse_bool(disponibilidad)
    db.session.commit()
    return libro.to_dict()


def delete_libro(libro_id: int) -> None:
    libro = Libro.query.filter_by(id=libro_id).first()
    if libro is None:
        raise ApiError("LIBRO_NOT_FOUND", "Libro no encontrado.", 404)

    db.session.delete(libro)
    db.session.commit()


def parse_catalog_query_params(params: dict[str, str]) -> dict[str, Any]:
    page, per_page = _parse_pagination(params.get("page"), params.get("per_page"))

    def parse_optional_int(name: str) -> int | None:
        value = params.get(name)
        if value is None:
            return None
        if not value.isdigit() or int(value) <= 0:
            raise ApiError("VALIDATION_ERROR", f"El parametro '{name}' debe ser positivo.", 422)
        return int(value)

    disponible_value = params.get("disponible")
    disponible = None if disponible_value is None else _parse_bool(disponible_value, "disponible")

    return {
        "titulo": params.get("titulo"),
        "isbn": params.get("isbn"),
        "autor_id": parse_optional_int("autor_id"),
        "editorial_id": parse_optional_int("editorial_id"),
        "categoria_id": parse_optional_int("categoria_id"),
        "disponible": disponible,
        "page": page,
        "per_page": per_page,
    }


def parse_simple_list_query_params(params: dict[str, str]) -> dict[str, Any]:
    page, per_page = _parse_pagination(params.get("page"), params.get("per_page"))
    nombre = params.get("nombre")
    return {
        "nombre": nombre,
        "page": page,
        "per_page": per_page,
    }
