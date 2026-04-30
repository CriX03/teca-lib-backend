# AGENTS.md
## Proposito
Este documento define como deben trabajar los agentes de codigo en este repositorio.
Objetivo: construir y mantener un backend de biblioteca personal basado en microservicios.

## Rol del agente
- Actuar como ingeniero backend senior y arquitecto de software.
- Trabajar en modo autonomo, con decisiones razonables y trazables.
- Priorizar codigo limpio, modular, mantenible y testeable.
- No implementar frontend ni UI.

## Contexto funcional
El sistema debe cubrir:
- Gestion de catalogo de libros.
- Gestion de prestamos (prestar y devolver).
- Autenticacion de usuarios con roles.
- Envio de notificaciones por email.
- Generacion de reportes analiticos.

## Stack tecnologico obligatorio
- Python 3.10+
- Flask
- PostgreSQL
- SQLAlchemy (ORM obligatorio)
- JWT para autenticacion
- Docker y Docker Compose
- Calidad: pytest + ruff + mypy

## Arquitectura de microservicios
Servicios obligatorios:
1. servicio_usuarios
2. servicio_catalogo
3. servicio_prestamos
4. servicio_notificaciones
5. servicio_reportes
Capas obligatorias por servicio: `routes -> controllers -> services -> models`.

## Estructura minima por servicio
- `app/__init__.py`, `app/config.py`, `app/extensions.py`
- `app/routes/`, `app/controllers/`, `app/services/`, `app/models/`, `app/errors/`
- `migrations/`, `tests/`, `Dockerfile`, `requirements.txt` o `pyproject.toml`

## Base de datos y migraciones (critico)
- Motor obligatorio: PostgreSQL.
- ORM obligatorio: SQLAlchemy.
- No crear la base de datos manualmente.
- Crear tablas automaticamente al levantar el sistema.
- Usar migraciones con Flask-Migrate/Alembic.
- Toda evolucion de esquema debe versionarse.
- Definir claves foraneas, unicidad e indices donde aplique.

## Modelos minimos obligatorios
- Usuario: `id`, `nombre`, `email` (unico), `contrasena`, `rol_id`, `fecha_creacion`.
- Rol: `id`, `nombre` (admin, estudiante, docente).
- Libro: `id`, `titulo`, `isbn` (unico), `autor_id`, `editorial_id`, `categoria_id`, `disponibilidad`, `fecha_creacion`.
- Autor: `id`, `nombre`.
- Editorial: `id`, `nombre`.
- Categoria: `id`, `nombre`.
- Prestamo: `id`, `usuario_id`, `libro_id`, `fecha_prestamo`, `fecha_devolucion`, `fecha_limite`, `estado`.
- Notificacion: `id`, `usuario_id`, `prestamo_id`, `mensaje`, `fecha_envio`, `estado`.
Reglas de modelado:
- Normalizar relaciones y mantener integridad referencial.
- Permitir extensibilidad con campos auditables cuando aporte valor.
- Optimizar consultas para reportes con indices adecuados.

## Seguridad
- Autenticacion con JWT.
- Control de acceso por roles (RBAC).
- Contrasenas cifradas (ejemplo: bcrypt).
- Validacion de inputs en todos los endpoints.
- Nunca exponer secretos en el repositorio.

## Contratos API
- Respuestas JSON estandarizadas.
- Exito sugerido: `{"success": true, "data": ..., "message": "..."}`
- Error sugerido: `{"success": false, "error": {"code": "...", "message": "..."}}`
- Usar HTTP: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `500`.

## Build, lint y test
Usar comandos reproducibles desde la raiz o desde cada servicio.
Entorno local:
- `python -m venv .venv`
- Linux/macOS: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- `pip install -r requirements.txt`
Calidad de codigo:
- Lint: `ruff check .`
- Formato (check): `ruff format --check .`
- Formato (fix): `ruff format .`
- Tipos: `mypy .`
Tests con pytest:
- Todos los tests: `pytest -q`
- Un archivo: `pytest tests/test_usuarios.py -q`
- Un test puntual: `pytest tests/test_usuarios.py::test_crear_usuario -q`
- Por expresion: `pytest -k "prestamo and vencido" -q`
- Cobertura: `pytest --cov=app --cov-report=term-missing`
Docker Compose:
- Levantar todo: `docker compose up --build`
- Levantar en background: `docker compose up -d --build`
- Ver logs: `docker compose logs -f servicio_usuarios`
- Tests en servicio: `docker compose exec servicio_usuarios pytest -q`
- Un test en servicio: `docker compose exec servicio_usuarios pytest tests/test_auth.py::test_login_ok -q`
- Aplicar migraciones: `docker compose exec servicio_usuarios flask db upgrade`
- Apagar stack: `docker compose down`

## Guia de estilo de codigo
Imports:
- Orden: libreria estandar, terceros, locales.
- Mantener imports absolutos y evitar ciclos.
- No usar imports comodin.
Formato y estructura:
- Seguir PEP 8; longitud recomendada 88-100.
- Usar `ruff format` como formateador principal.
- Mantener funciones pequenas y de responsabilidad unica.
Tipos y contratos:
- Type hints obligatorios en funciones publicas de controllers y services.
- Tipar parametros y retornos.
- Evitar `Any` salvo justificacion explicita.
Nombres:
- `snake_case` para funciones, variables y modulos.
- `PascalCase` para clases y modelos.
- `UPPER_SNAKE_CASE` para constantes.
- Rutas orientadas a recursos de dominio.
Errores, logging y SQLAlchemy:
- Implementar manejador global de errores por servicio.
- No filtrar trazas internas al cliente; loguear contexto tecnico util en servidor.
- Declarar relaciones explicitas con `ForeignKey` y `relationship`.
- Definir constraints de unicidad e integridad.
- Evitar N+1 queries con estrategias de carga apropiadas.

## Reglas Docker
- Cada microservicio debe tener `Dockerfile` propio.
- Debe existir `docker-compose.yml` con los 5 servicios y PostgreSQL.
- Usar red interna de Compose para comunicacion entre servicios.
- Configurar secretos y settings por variables de entorno.

## Plan de trabajo (sprints)
Seguir estrictamente este orden y no avanzar sin cerrar el sprint anterior:
1. Arquitectura
2. Base + Docker
3. Usuarios
4. Catalogo
5. Prestamos
6. Notificaciones
7. Reportes
8. Integracion
Criterio de cierre por sprint:
- Funcionalidad implementada y validada.
- Tests relevantes en verde.
- Migraciones aplicables actualizadas.
- Documentacion tecnica minima al dia.

## Criterios de exito
- Todos los servicios levantan con Docker Compose.
- JWT funcional en flujo real.
- CRUD de libros funcional.
- Prestamos actualizan disponibilidad del libro.
- Notificaciones operativas.
- Reportes correctos y verificables.

## Reglas Cursor y Copilot
Durante este analisis no se detectaron:
- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`
Si aparecen en el futuro, sus reglas deben incorporarse y respetarse con prioridad alta.
