#!/usr/bin/env python3
"""Script to perform initial sync of data to servicio_reportes.

Usage:
    python -m scripts.sync_initial_data

Environment variables:
    REPORTES_SERVICE_URL (default: http://localhost:5005)
    USUARIOS_SERVICE_URL (default: http://localhost:5001)
    CATALOGO_SERVICE_URL (default: http://localhost:5002)
    PRESTAMOS_SERVICE_URL (default: http://localhost:5003)
    AUTH_TOKEN (required): JWT token with admin privileges
"""

import os
import sys
import time

import requests

REPORTES_URL = os.getenv("REPORTES_SERVICE_URL", "http://localhost:5005")
USUARIOS_URL = os.getenv("USUARIOS_SERVICE_URL", "http://localhost:5001")
CATALOGO_URL = os.getenv("CATALOGO_SERVICE_URL", "http://localhost:5002")
PRESTAMOS_URL = os.getenv("PRESTAMOS_SERVICE_URL", "http://localhost:5003")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

TIMEOUT = 10


def _headers() -> dict[str, str]:
    if not AUTH_TOKEN:
        print("ERROR: AUTH_TOKEN environment variable is required.")
        sys.exit(1)
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}


def _fetch_all(url: str, endpoint: str, params: dict | None = None) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        p = params.copy() if params else {}
        p["page"] = page
        p["per_page"] = 100
        try:
            resp = requests.get(f"{url}{endpoint}", params=p, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            batch = data.get("items", [])
            if not batch:
                break
            items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        except requests.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            break
    return items


def main() -> None:
    print("Starting initial data sync to servicio_reportes...")
    print(f"Reportes URL: {REPORTES_URL}")
    print(f"Usuarios URL: {USUARIOS_URL}")
    print(f"Catalogo URL: {CATALOGO_URL}")
    print(f"Prestamos URL: {PRESTAMOS_URL}")

    headers = _headers()

    print("\nFetching usuarios...")
    usuarios = _fetch_all(USUARIOS_URL, "/api/v1/usuarios")
    print(f"  Found {len(usuarios)} usuarios")

    print("Fetching libros...")
    libros = _fetch_all(CATALOGO_URL, "/api/v1/libros")
    print(f"  Found {len(libros)} libros")

    print("Fetching prestamos...")
    prestamos = _fetch_all(PRESTAMOS_URL, "/api/v1/prestamos")
    print(f"  Found {len(prestamos)} prestamos")

    payload = {}
    if usuarios:
        payload["usuarios"] = [
            {"id": u["id"], "nombre": u.get("nombre", ""), "email": u.get("email", "")}
            for u in usuarios
        ]
    if libros:
        payload["libros"] = [
            {"id": l["id"], "titulo": l.get("titulo", "")} for l in libros
        ]
    if prestamos:
        payload["prestamos"] = [
            {
                "id": p["id"],
                "usuario_id": p["usuario_id"],
                "libro_id": p["libro_id"],
                "fecha_prestamo": p.get("fecha_prestamo"),
                "fecha_limite": p.get("fecha_limite"),
                "fecha_devolucion": p.get("fecha_devolucion"),
                "estado": p.get("estado", "activo"),
            }
            for p in prestamos
        ]

    print("\nSending data to reportes service...")
    try:
        resp = requests.post(
            f"{REPORTES_URL}/api/v1/reportes/sync/lote",
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"Sync successful: {result}")
    except requests.RequestException as e:
        print(f"ERROR during sync: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

    print("\nVerifying reports...")
    time.sleep(1)

    for endpoint in ["libros-mas-prestados", "prestamos-por-usuario", "retrasos"]:
        try:
            resp = requests.get(
                f"{REPORTES_URL}/api/v1/reportes/{endpoint}",
                headers=headers,
                timeout=TIMEOUT,
            )
            data = resp.json()
            items = data.get("data", {}).get("items", [])
            print(f"  /{endpoint}: {len(items)} items")
        except requests.RequestException as e:
            print(f"  /{endpoint}: ERROR - {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
