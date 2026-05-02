"""
Rutas de autenticacion del servicio de usuarios.

Este modulo define los endpoints de la API relacionados con la autenticacion y gestion
de usuarios. Agrupa las rutas bajo el blueprint 'users' con el prefijo '/api/v1/auth'.

Endpoints agrupados:
    - POST /api/v1/auth/registro: Registro de nuevos usuarios.
    - POST /api/v1/auth/login: Inicio de sesion.
    - GET /api/v1/auth/me: Usuario actual ( requiere autenticacion).
    - GET /api/v1/auth/admin/check: Verificacion de permisos admin.
    - GET /api/v1/auth/usuarios: Listado de usuarios ( requiere internal secret).
    - GET /api/v1/auth/usuarios/<id>: Obtener usuario por ID.
"""

from flask import Blueprint

from app.controllers.auth_controller import (
    admin_check,
    get_user_by_id_controller,
    list_users_controller,
    login,
    me,
    register,
)
from app.middlewares.internal_auth import internal_secret_required

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/auth")


@users_bp.post("/registro")
def register_endpoint():
    """Endpoint para registrar un nuevo usuario en el sistema."""
    return register()


@users_bp.post("/login")
def login_endpoint():
    """Endpoint para iniciar sesion y obtener token JWT."""
    return login()


@users_bp.get("/me")
def me_endpoint():
    """Endpoint para obtener el usuario autenticado actual."""
    return me()


@users_bp.get("/admin/check")
def admin_check_endpoint():
    """Endpoint para verificar permisos de administrador."""
    return admin_check()


@users_bp.get("/usuarios")
@internal_secret_required
def list_users_endpoint():
    """Endpoint para listar usuarios ( requiere secret interno)."""
    return list_users_controller()


@users_bp.get("/usuarios/<int:user_id>")
def get_user_by_id_endpoint(user_id: int):
    """Endpoint para obtener un usuario especifico por su ID."""
    return get_user_by_id_controller(user_id)