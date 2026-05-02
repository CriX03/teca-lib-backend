"""
Modulo de exportacion de servicios.

Este archivo actua como punto de acceso unificado para todas las funciones
de servicio disponibles en el modulo. Re-exporta las funciones publicas de:
    - auth_service: Funciones de autenticacion y gestion de usuarios.
    - health_service: Verificaciones de salud del servicio.
    - user_service: Consultas de listado de usuarios.

Beneficios:
    - Facilita el acceso a funciones sin conocer la estructura interna.
    - Permite cambiar la organizacion interna sin afectar consumidores.
    - Define una API publica clara para los controllers.

Ejemplo de uso:
    from app.services import login_user, register_user, list_all_users
"""

from app.services.auth_service import decode_access_token, login_user, register_user
from app.services.health_service import check_health
from app.services.user_service import list_all_users


__all__ = ["check_health", "decode_access_token", "list_all_users", "login_user", "register_user"]