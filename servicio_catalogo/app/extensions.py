"""
Extensiones de Flask para el servicio de catalogo.

Este modulo inicializa las extensiones de Flask necesarias para el funcionamiento
del servicio de catalogo de libros, incluyendo SQLAlchemy para la ORM
y Flask-Migrate para gestion de migraciones de base de datos.

SQLAlchemy proporciona el mapeo objeto-relacional (ORM) para interactuar con la base de datos
PostgreSQL de manera programatica, permitiendo definir modelos de datos como clases Python.

Flask-Migrate gestiona los cambios del esquema de base de datos a traves de migraciones,
permitiendo versionar y aplicar evoluciones del modelo de datos de forma controlada.
"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()