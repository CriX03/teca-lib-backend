from flask import Flask
from flask import Blueprint

from app.controllers import (
    create_autor_controller,
    create_categoria_controller,
    create_editorial_controller,
    create_libro_controller,
    delete_autor_controller,
    delete_categoria_controller,
    delete_editorial_controller,
    delete_libro_controller,
    get_autor_controller,
    get_categoria_controller,
    get_editorial_controller,
    get_libro_controller,
    list_autores_controller,
    list_categorias_controller,
    list_editoriales_controller,
    list_libros_controller,
    update_autor_controller,
    update_categoria_controller,
    update_disponibilidad_controller,
    update_editorial_controller,
    update_libro_controller,
)
from app.middlewares.auth import auth_required
from app.middlewares.internal_auth import internal_secret_required
from app.routes.health_routes import health_bp


catalog_bp = Blueprint("catalog", __name__, url_prefix="/api/v1/catalogo")


@catalog_bp.get("/autores")
def list_autores_endpoint():
    return list_autores_controller()


@catalog_bp.post("/autores")
@auth_required
def create_autor_endpoint():
    return create_autor_controller()


@catalog_bp.get("/autores/<int:autor_id>")
def get_autor_endpoint(autor_id: int):
    return get_autor_controller(autor_id)


@catalog_bp.put("/autores/<int:autor_id>")
@auth_required
def update_autor_endpoint(autor_id: int):
    return update_autor_controller(autor_id)


@catalog_bp.delete("/autores/<int:autor_id>")
@auth_required
def delete_autor_endpoint(autor_id: int):
    return delete_autor_controller(autor_id)


@catalog_bp.get("/editoriales")
def list_editoriales_endpoint():
    return list_editoriales_controller()


@catalog_bp.post("/editoriales")
@auth_required
def create_editorial_endpoint():
    return create_editorial_controller()


@catalog_bp.get("/editoriales/<int:editorial_id>")
def get_editorial_endpoint(editorial_id: int):
    return get_editorial_controller(editorial_id)


@catalog_bp.put("/editoriales/<int:editorial_id>")
@auth_required
def update_editorial_endpoint(editorial_id: int):
    return update_editorial_controller(editorial_id)


@catalog_bp.delete("/editoriales/<int:editorial_id>")
@auth_required
def delete_editorial_endpoint(editorial_id: int):
    return delete_editorial_controller(editorial_id)


@catalog_bp.get("/categorias")
def list_categorias_endpoint():
    return list_categorias_controller()


@catalog_bp.post("/categorias")
@auth_required
def create_categoria_endpoint():
    return create_categoria_controller()


@catalog_bp.get("/categorias/<int:categoria_id>")
def get_categoria_endpoint(categoria_id: int):
    return get_categoria_controller(categoria_id)


@catalog_bp.put("/categorias/<int:categoria_id>")
@auth_required
def update_categoria_endpoint(categoria_id: int):
    return update_categoria_controller(categoria_id)


@catalog_bp.delete("/categorias/<int:categoria_id>")
@auth_required
def delete_categoria_endpoint(categoria_id: int):
    return delete_categoria_controller(categoria_id)


@catalog_bp.get("/libros")
@auth_required
def list_libros_endpoint():
    return list_libros_controller()


@catalog_bp.post("/libros")
@auth_required
def create_libro_endpoint():
    return create_libro_controller()


@catalog_bp.get("/libros/<int:libro_id>")
def get_libro_endpoint(libro_id: int):
    return get_libro_controller(libro_id)


@catalog_bp.put("/libros/<int:libro_id>")
@auth_required
def update_libro_endpoint(libro_id: int):
    return update_libro_controller(libro_id)


@catalog_bp.patch("/libros/<int:libro_id>/disponibilidad")
def update_disponibilidad_endpoint(libro_id: int):
    return update_disponibilidad_controller(libro_id)


@catalog_bp.delete("/libros/<int:libro_id>")
@auth_required
def delete_libro_endpoint(libro_id: int):
    return delete_libro_controller(libro_id)


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(catalog_bp)
