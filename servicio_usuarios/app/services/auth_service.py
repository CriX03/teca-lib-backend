from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import ApiError
from app.extensions import db
from app.models import Role, User

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PASSWORD_UPPERCASE = re.compile(r"[A-Z]")
PASSWORD_LOWERCASE = re.compile(r"[a-z]")
PASSWORD_DIGIT = re.compile(r"\d")
PASSWORD_SYMBOL = re.compile(r"[^A-Za-z0-9]")


def _clean_nombre(value: Any) -> str:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "El campo 'nombre' debe ser texto.", 422)

    nombre = value.strip()
    if len(nombre) < 2 or len(nombre) > 120:
        raise ApiError(
            "VALIDATION_ERROR",
            "El campo 'nombre' debe tener entre 2 y 120 caracteres.",
            422,
        )

    return nombre


def _clean_email(value: Any) -> str:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "El campo 'email' debe ser texto.", 422)

    email = value.strip().lower()
    if len(email) > 255 or not EMAIL_PATTERN.match(email):
        raise ApiError("VALIDATION_ERROR", "El email no tiene un formato valido.", 422)

    return email


def _clean_password(value: Any) -> str:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "El campo 'contrasena' debe ser texto.", 422)

    password = value.strip()
    if len(password) < 8 or len(password) > 72:
        raise ApiError(
            "VALIDATION_ERROR",
            "La contrasena debe tener entre 8 y 72 caracteres.",
            422,
        )

    if not PASSWORD_UPPERCASE.search(password):
        raise ApiError(
            "VALIDATION_ERROR",
            "La contrasena debe incluir al menos una letra mayuscula.",
            422,
        )

    if not PASSWORD_LOWERCASE.search(password):
        raise ApiError(
            "VALIDATION_ERROR",
            "La contrasena debe incluir al menos una letra minuscula.",
            422,
        )

    if not PASSWORD_DIGIT.search(password):
        raise ApiError(
            "VALIDATION_ERROR",
            "La contrasena debe incluir al menos un numero.",
            422,
        )

    if not PASSWORD_SYMBOL.search(password):
        raise ApiError(
            "VALIDATION_ERROR",
            "La contrasena debe incluir al menos un simbolo.",
            422,
        )

    return password


def _clean_role_name(value: Any, allowed_roles: tuple[str, ...]) -> str:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "El campo 'rol' debe ser texto.", 422)

    role_name = value.strip().lower()
    if role_name not in allowed_roles:
        raise ApiError(
            "VALIDATION_ERROR",
            f"Rol no valido. Roles permitidos: {', '.join(allowed_roles)}.",
            422,
        )

    return role_name


def register_user(
    payload: dict[str, Any], allowed_roles: tuple[str, ...]
) -> dict[str, str | int]:
    nombre = _clean_nombre(payload.get("nombre"))
    email = _clean_email(payload.get("email"))
    password = _clean_password(payload.get("contrasena"))
    role_name = _clean_role_name(payload.get("rol"), allowed_roles)

    existing_user = User.query.filter_by(email=email).first()
    if existing_user is not None:
        raise ApiError(
            "EMAIL_ALREADY_EXISTS", "Ya existe un usuario con este email.", 409
        )

    role = Role.query.filter_by(nombre=role_name).first()
    if role is None:
        raise ApiError("ROLE_NOT_FOUND", "El rol solicitado no existe.", 422)

    password_hash = generate_password_hash(password)
    user = User(nombre=nombre, email=email, contrasena=password_hash, rol_id=role.id)

    db.session.add(user)
    db.session.commit()

    return user.to_dict()


def _generate_access_token(
    *,
    user: User,
    jwt_secret: str,
    jwt_algorithm: str,
    expires_minutes: int,
    issuer: str,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "rol": user.rol.nombre,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "iss": issuer,
    }

    return str(jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm))


def login_user(
    payload: dict[str, Any],
    *,
    jwt_secret: str,
    jwt_algorithm: str,
    expires_minutes: int,
    issuer: str,
) -> dict[str, Any]:
    email = _clean_email(payload.get("email"))
    password = payload.get("contrasena")
    if not isinstance(password, str):
        raise ApiError("VALIDATION_ERROR", "El campo 'contrasena' debe ser texto.", 422)

    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.contrasena, password):
        raise ApiError("INVALID_CREDENTIALS", "Credenciales invalidas.", 401)

    token = _generate_access_token(
        user=user,
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        expires_minutes=expires_minutes,
        issuer=issuer,
    )

    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": expires_minutes * 60,
        "usuario": user.to_dict(),
    }


def decode_access_token(
    token: str,
    *,
    jwt_secret: str,
    jwt_algorithm: str,
    issuer: str,
) -> dict[str, Any]:
    try:
        decoded: dict[str, Any] = jwt.decode(
            token,
            jwt_secret,
            algorithms=[jwt_algorithm],
            issuer=issuer,
            options={"require": ["exp", "iat", "sub", "rol"]},
        )
        return decoded
    except jwt.ExpiredSignatureError as error:
        raise ApiError("TOKEN_EXPIRED", "El token ha expirado.", 401) from error
    except jwt.InvalidTokenError as error:
        raise ApiError("INVALID_TOKEN", "El token no es valido.", 401) from error


def get_user_by_id(user_id: int) -> dict[str, Any]:
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        raise ApiError("USER_NOT_FOUND", "Usuario no encontrado.", 404)
    return user.to_dict()
