"""
Servicio de consultas de usuarios.

Este modulo proporciona funciones de consulta de alto nivel para recuperar
listas de usuarios desde la base de datos. Formatea los resultados para
su consumo por clientes API con soporte de paginacion.

Paginacion:
    - Parametros: page (pagina actual), limit (elementos por pagina).
    - Retorna metadatos de paginacion: total, page, per_page, pages.
"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.user import User


def list_all_users(*, page: int = 1, limit: int = 100) -> dict[str, Any]:
    """
    Recupera una lista paginada de todos los usuarios.

    Args:
        page: Numero de pagina a consultar (default: 1).
        limit: Maximo de usuarios por pagina (default: 100, max: 1000).

    Returns:
        Diccionario con items y metadatos de paginacion.
    """
    pagination = User.query.order_by(User.id.asc()).paginate(
        page=page, per_page=limit, error_out=False
    )
    items = [u.to_dict() for u in pagination.items]
    return {
        "items": items,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }