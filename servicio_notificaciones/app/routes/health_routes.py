from flask import Blueprint

from app.controllers.health_controller import health


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_endpoint():
    return health()
