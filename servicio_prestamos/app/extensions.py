"""
Extensiones de Flask para el servicio de prestamos.

Este modulo inicializa las extensiones SQLAlchemy y Flask-Migrate
necesarias para el funcionamiento del servicio.
"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()