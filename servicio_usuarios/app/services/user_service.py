from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.user import User


def list_all_users(*, page: int = 1, limit: int = 100) -> dict[str, Any]:
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
