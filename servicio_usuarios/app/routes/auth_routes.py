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
    return register()


@users_bp.post("/login")
def login_endpoint():
    return login()


@users_bp.get("/me")
def me_endpoint():
    return me()


@users_bp.get("/admin/check")
def admin_check_endpoint():
    return admin_check()


@users_bp.get("/usuarios")
@internal_secret_required
def list_users_endpoint():
    return list_users_controller()


@users_bp.get("/usuarios/<int:user_id>")
def get_user_by_id_endpoint(user_id: int):
    return get_user_by_id_controller(user_id)
