from __future__ import annotations

import time
from typing import Any

import requests
from flask import current_app

from app.services import sync_lote


def _get_headers(app: Any) -> dict[str, str]:
    secret = app.config.get("INTERNAL_SERVICE_SECRET", "")
    if secret:
        return {"X-Internal-Secret": secret}
    return {}


def _fetch_json(url: str, timeout: int, headers: dict[str, str]) -> list[dict[str, Any]]:
    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", {})
        items = data.get("items", [])
        if not isinstance(items, list):
            return []
        return items
    except requests.RequestException:
        current_app.logger.exception("Error fetching %s", url)
        return []


def _fetch_all_prestamos(
    base_url: str, timeout: int, headers: dict[str, str]
) -> list[dict[str, Any]]:
    all_items: list[dict[str, Any]] = []
    page = 1
    while True:
        url = f"{base_url}/api/v1/prestamos/admin/todos?page={page}&per_page=100"
        items = _fetch_json(url, timeout, headers)
        if not items:
            break
        all_items.extend(items)
        page += 1
    return all_items


def _fetch_all_usuarios(
    base_url: str, timeout: int, headers: dict[str, str]
) -> list[dict[str, Any]]:
    url = f"{base_url}/api/v1/auth/usuarios?per_page=1000"
    return _fetch_json(url, timeout, headers)


def _fetch_all_libros(
    base_url: str, timeout: int, headers: dict[str, str]
) -> list[dict[str, Any]]:
    url = f"{base_url}/api/v1/catalogo/libros?per_page=1000"
    return _fetch_json(url, timeout, headers)


def run_sync_cycle(app: Any) -> None:
    with app.app_context():
        usuarios_url = app.config["USUARIOS_SERVICE_URL"]
        catalogo_url = app.config["CATALOGO_SERVICE_URL"]
        prestamos_url = app.config["PRESTAMOS_SERVICE_URL"]
        timeout = int(app.config.get("REPORTES_SYNC_TIMEOUT_SECONDS", 10))
        headers = _get_headers(app)

        current_app.logger.info("Starting reportes sync cycle...")

        usuarios = _fetch_all_usuarios(usuarios_url, timeout, headers)
        libros = _fetch_all_libros(catalogo_url, timeout, headers)
        prestamos = _fetch_all_prestamos(prestamos_url, timeout, headers)

        if not usuarios and not libros and not prestamos:
            current_app.logger.warning("No data fetched from external services.")
            return

        payload: dict[str, Any] = {}
        if usuarios:
            payload["usuarios"] = [
                {
                    "id": u.get("id"),
                    "nombre": u.get("nombre", ""),
                    "email": u.get("email", ""),
                }
                for u in usuarios
            ]
        if libros:
            payload["libros"] = [
                {
                    "id": l.get("id"),
                    "titulo": l.get("titulo", ""),
                }
                for l in libros
            ]
        if prestamos:
            payload["prestamos"] = [
                {
                    "id": p.get("id"),
                    "usuario_id": p.get("usuario_id"),
                    "libro_id": p.get("libro_id"),
                    "fecha_prestamo": p.get("fecha_prestamo"),
                    "fecha_limite": p.get("fecha_limite"),
                    "fecha_devolucion": p.get("fecha_devolucion"),
                    "estado": p.get("estado", "activo"),
                }
                for p in prestamos
            ]

        try:
            result = sync_lote(payload)
            current_app.logger.info("Sync completed: %s", result)
        except Exception:
            current_app.logger.exception("Error during sync_lote execution.")


def _run_worker_loop(app: Any) -> None:
    interval = int(app.config.get("REPORTES_SYNC_INTERVAL_SECONDS", 300))
    while True:
        try:
            run_sync_cycle(app)
        except Exception:
            current_app.logger.exception("Reportes worker iteration failed.")
        time.sleep(interval)


def start_sync_worker(app: Any) -> None:
    if not app.config.get("REPORTES_WORKER_ENABLED", True):
        app.logger.info("Reportes sync worker disabled by configuration.")
        return

    import threading

    thread = threading.Thread(
        target=_run_worker_loop,
        args=(app,),
        name="reportes-sync-worker",
        daemon=True,
    )
    thread.start()
    app.logger.info("Reportes sync worker started.")
