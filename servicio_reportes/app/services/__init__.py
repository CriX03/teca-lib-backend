from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import case, func

from app.errors import ApiError
from app.extensions import db
from app.models import LibroAnalitico, PrestamoAnalitico, UsuarioAnalitico


ESTADO_ACTIVO = "activo"


def _normalize_limit(limit: int | None, *, default_limit: int, max_limit: int) -> int:
    if default_limit <= 0 or max_limit <= 0 or default_limit > max_limit:
        raise ApiError(
            "INVALID_REPORT_CONFIG",
            "Configuracion de limites de reportes invalida.",
            500,
        )

    if limit is None:
        return default_limit

    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ApiError(
            "VALIDATION_ERROR",
            "El parametro 'limit' debe ser un entero positivo.",
            422,
        )

    return min(limit, max_limit)


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC).isoformat()
    return value.astimezone(UTC).isoformat()


def _to_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def get_libros_mas_prestados(
    *,
    limit: int | None,
    default_limit: int,
    max_limit: int,
) -> dict[str, object]:
    normalized_limit = _normalize_limit(
        limit,
        default_limit=default_limit,
        max_limit=max_limit,
    )

    total_prestamos = func.count(PrestamoAnalitico.id).label("total_prestamos")
    ultimo_prestamo = func.max(PrestamoAnalitico.fecha_prestamo).label(
        "ultimo_prestamo"
    )

    rows = (
        PrestamoAnalitico.query.with_entities(
            PrestamoAnalitico.libro_id,
            LibroAnalitico.titulo,
            total_prestamos,
            ultimo_prestamo,
        )
        .join(LibroAnalitico, LibroAnalitico.id == PrestamoAnalitico.libro_id)
        .group_by(PrestamoAnalitico.libro_id, LibroAnalitico.titulo)
        .order_by(
            total_prestamos.desc(),
            ultimo_prestamo.desc(),
            PrestamoAnalitico.libro_id.asc(),
        )
        .limit(normalized_limit)
        .all()
    )

    items = [
        {
            "libro_id": row.libro_id,
            "titulo": row.titulo,
            "total_prestamos": int(row.total_prestamos),
            "ultimo_prestamo": _to_iso(row.ultimo_prestamo),
        }
        for row in rows
    ]
    return {"items": items, "limit": normalized_limit}


def get_prestamos_por_usuario(
    *,
    limit: int | None,
    default_limit: int,
    max_limit: int,
) -> dict[str, object]:
    normalized_limit = _normalize_limit(
        limit,
        default_limit=default_limit,
        max_limit=max_limit,
    )

    total_prestamos = func.count(PrestamoAnalitico.id).label("total_prestamos")
    prestamos_activos = func.sum(
        case((PrestamoAnalitico.estado == ESTADO_ACTIVO, 1), else_=0)
    ).label("prestamos_activos")
    ultimo_prestamo = func.max(PrestamoAnalitico.fecha_prestamo).label(
        "ultimo_prestamo"
    )

    rows = (
        PrestamoAnalitico.query.with_entities(
            PrestamoAnalitico.usuario_id,
            UsuarioAnalitico.nombre,
            UsuarioAnalitico.email,
            total_prestamos,
            prestamos_activos,
            ultimo_prestamo,
        )
        .join(UsuarioAnalitico, UsuarioAnalitico.id == PrestamoAnalitico.usuario_id)
        .group_by(
            PrestamoAnalitico.usuario_id,
            UsuarioAnalitico.nombre,
            UsuarioAnalitico.email,
        )
        .order_by(
            total_prestamos.desc(),
            prestamos_activos.desc(),
            PrestamoAnalitico.usuario_id.asc(),
        )
        .limit(normalized_limit)
        .all()
    )

    items = [
        {
            "usuario_id": row.usuario_id,
            "nombre": row.nombre,
            "email": row.email,
            "total_prestamos": int(row.total_prestamos),
            "prestamos_activos": int(row.prestamos_activos or 0),
            "ultimo_prestamo": _to_iso(row.ultimo_prestamo),
        }
        for row in rows
    ]
    return {"items": items, "limit": normalized_limit}


def get_retrasos(
    *,
    limit: int | None,
    default_limit: int,
    max_limit: int,
) -> dict[str, object]:
    normalized_limit = _normalize_limit(
        limit,
        default_limit=default_limit,
        max_limit=max_limit,
    )
    now_utc = datetime.now(UTC)

    rows = (
        PrestamoAnalitico.query.with_entities(
            PrestamoAnalitico.id,
            PrestamoAnalitico.usuario_id,
            UsuarioAnalitico.nombre,
            PrestamoAnalitico.libro_id,
            LibroAnalitico.titulo,
            PrestamoAnalitico.estado,
            PrestamoAnalitico.fecha_prestamo,
            PrestamoAnalitico.fecha_limite,
            PrestamoAnalitico.fecha_devolucion,
        )
        .join(UsuarioAnalitico, UsuarioAnalitico.id == PrestamoAnalitico.usuario_id)
        .join(LibroAnalitico, LibroAnalitico.id == PrestamoAnalitico.libro_id)
        .filter(
            PrestamoAnalitico.fecha_limite
            < func.coalesce(PrestamoAnalitico.fecha_devolucion, now_utc)
        )
        .order_by(PrestamoAnalitico.fecha_limite.asc(), PrestamoAnalitico.id.asc())
        .limit(normalized_limit)
        .all()
    )

    items = []
    for row in rows:
        fecha_corte = (
            row.fecha_devolucion if row.fecha_devolucion is not None else now_utc
        )
        dias_retraso = max(
            (_to_utc_datetime(fecha_corte) - _to_utc_datetime(row.fecha_limite)).days,
            0,
        )
        items.append(
            {
                "prestamo_id": row.id,
                "usuario_id": row.usuario_id,
                "usuario_nombre": row.nombre,
                "libro_id": row.libro_id,
                "libro_titulo": row.titulo,
                "estado": row.estado,
                "fecha_prestamo": _to_iso(row.fecha_prestamo),
                "fecha_limite": _to_iso(row.fecha_limite),
                "fecha_devolucion": _to_iso(row.fecha_devolucion),
                "dias_retraso": dias_retraso,
            }
        )
    return {"items": items, "limit": normalized_limit}


def _clean_positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser un entero positivo.",
            422,
        )
    return value


def _clean_text(value: Any, field_name: str, max_len: int) -> str:
    if not isinstance(value, str):
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' es obligatorio y debe ser texto.",
            422,
        )
    clean = value.strip()
    if not clean:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' es obligatorio y debe ser texto.",
            422,
        )
    if len(clean) > max_len:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' no puede superar {max_len} caracteres.",
            422,
        )
    return clean


def _clean_iso_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser una fecha ISO8601 valida.",
            422,
        )
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{field_name}' debe ser una fecha ISO8601 valida.",
            422,
        ) from error
    return _to_utc_datetime(parsed)


def _extract_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = payload.get(key, [])
    if not isinstance(items, list):
        raise ApiError(
            "VALIDATION_ERROR",
            f"El campo '{key}' debe ser una lista.",
            422,
        )
    for item in items:
        if not isinstance(item, dict):
            raise ApiError(
                "VALIDATION_ERROR",
                f"Cada elemento de '{key}' debe ser un objeto.",
                422,
            )
    return items


def sync_usuarios(items: list[dict[str, Any]]) -> dict[str, int]:
    created = 0
    updated = 0
    for item in items:
        user_id = _clean_positive_int(item.get("id"), "id")
        nombre = _clean_text(item.get("nombre"), "nombre", 255)
        email = _clean_text(item.get("email"), "email", 255).lower()

        user = UsuarioAnalitico.query.filter_by(id=user_id).first()
        if user is None:
            if UsuarioAnalitico.query.filter_by(email=email).first() is not None:
                raise ApiError(
                    "CONFLICT",
                    f"El email '{email}' ya existe con otro usuario.",
                    409,
                )
            user = UsuarioAnalitico()
            user.id = user_id
            user.nombre = nombre
            user.email = email
            db.session.add(user)
            created += 1
        else:
            other_by_email = UsuarioAnalitico.query.filter(
                UsuarioAnalitico.email == email,
                UsuarioAnalitico.id != user_id,
            ).first()
            if other_by_email is not None:
                raise ApiError(
                    "CONFLICT",
                    f"El email '{email}' ya existe con otro usuario.",
                    409,
                )
            user.nombre = nombre
            user.email = email
            updated += 1

    db.session.commit()
    return {"created": created, "updated": updated}


def sync_libros(items: list[dict[str, Any]]) -> dict[str, int]:
    created = 0
    updated = 0
    for item in items:
        libro_id = _clean_positive_int(item.get("id"), "id")
        titulo = _clean_text(item.get("titulo"), "titulo", 255)

        libro = LibroAnalitico.query.filter_by(id=libro_id).first()
        if libro is None:
            libro = LibroAnalitico()
            libro.id = libro_id
            libro.titulo = titulo
            db.session.add(libro)
            created += 1
        else:
            libro.titulo = titulo
            updated += 1

    db.session.commit()
    return {"created": created, "updated": updated}


def sync_prestamos(items: list[dict[str, Any]]) -> dict[str, int]:
    created = 0
    updated = 0
    for item in items:
        prestamo_id = _clean_positive_int(item.get("id"), "id")
        usuario_id = _clean_positive_int(item.get("usuario_id"), "usuario_id")
        libro_id = _clean_positive_int(item.get("libro_id"), "libro_id")

        if UsuarioAnalitico.query.filter_by(id=usuario_id).first() is None:
            raise ApiError(
                "FK_NOT_FOUND",
                f"No existe usuario_analitico con id={usuario_id}.",
                409,
            )
        if LibroAnalitico.query.filter_by(id=libro_id).first() is None:
            raise ApiError(
                "FK_NOT_FOUND",
                f"No existe libro_analitico con id={libro_id}.",
                409,
            )

        fecha_prestamo = _clean_iso_datetime(item.get("fecha_prestamo"), "fecha_prestamo")
        fecha_limite = _clean_iso_datetime(item.get("fecha_limite"), "fecha_limite")
        fecha_devolucion_raw = item.get("fecha_devolucion")
        fecha_devolucion = (
            _clean_iso_datetime(fecha_devolucion_raw, "fecha_devolucion")
            if fecha_devolucion_raw is not None
            else None
        )
        estado = _clean_text(item.get("estado", "activo"), "estado", 30).lower()

        prestamo = PrestamoAnalitico.query.filter_by(id=prestamo_id).first()
        if prestamo is None:
            prestamo = PrestamoAnalitico()
            prestamo.id = prestamo_id
            prestamo.usuario_id = usuario_id
            prestamo.libro_id = libro_id
            prestamo.fecha_prestamo = fecha_prestamo
            prestamo.fecha_limite = fecha_limite
            prestamo.fecha_devolucion = fecha_devolucion
            prestamo.estado = estado
            db.session.add(prestamo)
            created += 1
        else:
            prestamo.usuario_id = usuario_id
            prestamo.libro_id = libro_id
            prestamo.fecha_prestamo = fecha_prestamo
            prestamo.fecha_limite = fecha_limite
            prestamo.fecha_devolucion = fecha_devolucion
            prestamo.estado = estado
            updated += 1

    db.session.commit()
    return {"created": created, "updated": updated}


def sync_lote(payload: dict[str, Any]) -> dict[str, dict[str, int]]:
    usuarios_items = _extract_items(payload, "usuarios")
    libros_items = _extract_items(payload, "libros")
    prestamos_items = _extract_items(payload, "prestamos")

    if usuarios_items or libros_items or prestamos_items:
        PrestamoAnalitico.query.delete()
        UsuarioAnalitico.query.delete()
        LibroAnalitico.query.delete()
        db.session.commit()

    result_usuarios = sync_usuarios(usuarios_items) if usuarios_items else {"created": 0, "updated": 0}
    result_libros = sync_libros(libros_items) if libros_items else {"created": 0, "updated": 0}
    result_prestamos = sync_prestamos(prestamos_items) if prestamos_items else {"created": 0, "updated": 0}

    return {
        "usuarios": result_usuarios,
        "libros": result_libros,
        "prestamos": result_prestamos,
    }


__all__ = [
    "get_libros_mas_prestados",
    "get_prestamos_por_usuario",
    "get_retrasos",
    "sync_libros",
    "sync_lote",
    "sync_prestamos",
    "sync_usuarios",
]
