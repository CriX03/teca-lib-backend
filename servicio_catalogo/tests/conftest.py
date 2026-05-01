from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = b"x"

    def json(self) -> dict[str, Any]:
        return self._payload


@pytest.fixture(autouse=True)
def mock_usuarios_service(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 5,
    ) -> _FakeResponse:
        del timeout
        token = (headers or {}).get("Authorization", "")

        if url.endswith("/api/v1/auth/me"):
            if not token.startswith("Bearer "):
                return _FakeResponse(
                    401,
                    {
                        "success": False,
                        "error": {
                            "code": "MISSING_AUTH_HEADER",
                            "message": "Falta el header Authorization.",
                        },
                    },
                )
            return _FakeResponse(
                200,
                {
                    "success": True,
                    "data": {"id": 1, "nombre": "Test User", "email": "test@test.com", "rol": "admin"},
                },
            )

        return _FakeResponse(
            404,
            {"success": False, "error": {"code": "NOT_FOUND", "message": "Not found"}},
        )

    import app.middlewares.auth as auth_module
    monkeypatch.setattr(auth_module.requests, "get", fake_get)


@pytest.fixture(autouse=True)
def clean_database():
    from app.extensions import db

    yield
    with db.engine.begin() as conn:
        for table in reversed(db.metadata.sorted_tables):
            conn.execute(table.delete())