# Teca Lib - Backend de Biblioteca en Microservicios

Backend de biblioteca personal construido con arquitectura de microservicios en Python y Flask.

## Tabla de contenidos

- [Descripcion](#descripcion)
- [Objetivos funcionales](#objetivos-funcionales)
- [Arquitectura](#arquitectura)
- [Stack tecnologico](#stack-tecnologico)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Servicios y puertos](#servicios-y-puertos)
- [Como funciona el proyecto](#como-funciona-el-proyecto)
- [Requisitos previos](#requisitos-previos)
- [Puesta en marcha con Docker Compose (recomendado)](#puesta-en-marcha-con-docker-compose-recomendado)
- [Configuracion por variables de entorno](#configuracion-por-variables-de-entorno)
- [Ejecucion local por servicio (sin Docker)](#ejecucion-local-por-servicio-sin-docker)
- [Documentacion de API](#documentacion-de-api)
- [Flujo de prueba rapido](#flujo-de-prueba-rapido)
- [Calidad de codigo y testing](#calidad-de-codigo-y-testing)
- [Migraciones y base de datos](#migraciones-y-base-de-datos)
- [Troubleshooting](#troubleshooting)
- [Roadmap por sprints](#roadmap-por-sprints)
- [Contribucion](#contribucion)

## Descripcion

Teca Lib implementa un backend desacoplado para gestionar una biblioteca personal. El sistema separa responsabilidades por dominio (usuarios, catalogo, prestamos, notificaciones y reportes) y expone APIs REST con respuestas JSON estandarizadas.

Este repositorio esta preparado para ejecutarse en entorno local con Docker Compose, incluyendo PostgreSQL y Mailhog para pruebas de correo.

## Objetivos funcionales

- Gestion de usuarios con autenticacion JWT y roles.
- Gestion de catalogo de libros (autores, editoriales, categorias y libros).
- Gestion de prestamos y devoluciones.
- Envio de notificaciones por email.
- Generacion de reportes analiticos.

## Arquitectura

El proyecto sigue un enfoque de microservicios. Cada servicio mantiene su propia base de datos PostgreSQL y su propia aplicacion Flask.

```text
Cliente/API Consumer
        |
        v
-------------------------------------------------------------
| servicio_usuarios | servicio_catalogo | servicio_prestamos |
| servicio_notificaciones | servicio_reportes                |
-------------------------------------------------------------
        |                          |
        v                          v
   PostgreSQL (multiples DB)    Mailhog (SMTP dev)
```

Patron interno por servicio:

`routes -> controllers -> services -> models`

## Stack tecnologico

- Python 3.10+
- Flask
- SQLAlchemy + Flask-Migrate
- PostgreSQL
- JWT (PyJWT)
- Docker y Docker Compose
- pytest, ruff, mypy

## Estructura del repositorio

```text
.
|- API.md
|- docker-compose.yml
|- postgres/
|  `- init-multiple-databases.sh
|- servicio_usuarios/
|- servicio_catalogo/
|- servicio_prestamos/
|- servicio_notificaciones/
`- servicio_reportes/
```

Cada microservicio incluye su propia estructura base:

- `app/__init__.py`, `app/config.py`, `app/extensions.py`
- `app/routes/`, `app/controllers/`, `app/services/`, `app/models/`, `app/errors/`
- `migrations/`, `tests/`, `Dockerfile`, `requirements.txt`

## Servicios y puertos

| Servicio | Puerto host | URL local |
|---|---:|---|
| servicio_usuarios | 5001 | http://localhost:5001 |
| servicio_catalogo | 5002 | http://localhost:5002 |
| servicio_prestamos | 5003 | http://localhost:5003 |
| servicio_notificaciones | 5004 | http://localhost:5004 |
| servicio_reportes | 5005 | http://localhost:5005 |
| PostgreSQL | 5432 | postgresql://localhost:5432 |
| Mailhog UI | 8025 | http://localhost:8025 |

## Como funciona el proyecto

1. **Autenticacion y autorizacion**
   - `servicio_usuarios` gestiona registro/login y emite tokens JWT.
   - Los demas servicios validan autenticacion para endpoints protegidos.

2. **Catalogo y disponibilidad**
   - `servicio_catalogo` mantiene datos bibliograficos y estado de disponibilidad de libros.

3. **Prestamos**
   - `servicio_prestamos` crea prestamos y registra devoluciones.
   - Durante el flujo, consulta servicios externos (usuarios/catalogo) para validar reglas de negocio.

4. **Notificaciones**
   - `servicio_notificaciones` crea y procesa envios de email.
   - En desarrollo, los correos se visualizan en Mailhog.

5. **Reportes**
   - `servicio_reportes` consume/sincroniza informacion de otros servicios para generar reportes agregados.

6. **Inicializacion de base de datos**
   - Al iniciar cada servicio, se ejecuta `db.create_all()` con reintentos.
   - Esto facilita el arranque cuando PostgreSQL aun esta levantando.

## Requisitos previos

- Docker 24+ y Docker Compose v2
- Git
- (Opcional para ejecucion sin Docker) Python 3.10+

## Puesta en marcha con Docker Compose (recomendado)

Desde la raiz del repositorio:

```bash
docker compose up --build
```

En segundo plano:

```bash
docker compose up -d --build
```

Ver logs:

```bash
docker compose logs -f servicio_usuarios
```

Detener todo:

```bash
docker compose down
```

Comprobar health checks (ejemplo):

```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
curl http://localhost:5004/health
curl http://localhost:5005/health
```

## Configuracion por variables de entorno

Puedes usar los archivos `.env.example` de cada servicio como referencia:

- `servicio_usuarios/.env.example`
- `servicio_catalogo/.env.example`
- `servicio_prestamos/.env.example`
- `servicio_notificaciones/.env.example`
- `servicio_reportes/.env.example`

Variables clave por dominio:

- **Base de datos:** `DATABASE_URL`
- **JWT (usuarios/prestamos):** `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`
- **Integracion interna entre servicios:** `*_SERVICE_URL`, `INTERNAL_SERVICE_SECRET`
- **Notificaciones SMTP:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM_EMAIL`, `SMTP_*`
- **Reportes:** `REPORTES_DEFAULT_LIMIT`, `REPORTES_MAX_LIMIT`, `REPORTES_SYNC_*`

> Importante: en entornos reales, no uses secretos por defecto. Configura valores seguros mediante variables de entorno o secretos del orquestador.

## Ejecucion local por servicio (sin Docker)

Ejemplo general (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Ejemplo general (Linux/macOS):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Repite el proceso dentro de cada carpeta `servicio_*`.

## Documentacion de API

La documentacion funcional de endpoints esta en:

- `API.md`

Incluye:

- Endpoints por servicio.
- Estandar de respuestas de exito/error.
- Codigos de error frecuentes.
- Flujo completo de ejemplo con `curl`.

## Flujo de prueba rapido

1. Registrar usuario en `servicio_usuarios`.
2. Hacer login y obtener token JWT.
3. Crear autor/editorial/categoria/libro en `servicio_catalogo`.
4. Crear prestamo en `servicio_prestamos`.
5. Registrar devolucion.
6. Consultar Mailhog para validar correos.
7. Consultar endpoints de `servicio_reportes`.

Los ejemplos `curl` completos estan en `API.md`.

## Calidad de codigo y testing

Desde la raiz del servicio correspondiente:

```bash
ruff check .
ruff format --check .
mypy .
pytest -q
```

Con Docker Compose (ejemplo):

```bash
docker compose exec servicio_usuarios pytest -q
```

## Migraciones y base de datos

- Motor de BD: PostgreSQL.
- ORM: SQLAlchemy.
- Migraciones: Flask-Migrate/Alembic.
- Arranque inicial: cada servicio crea tablas si no existen.

Aplicar migraciones en un servicio (ejemplo):

```bash
docker compose exec servicio_usuarios flask db upgrade
```

## Troubleshooting

- **Puertos ocupados:** cambia mapeos en `docker-compose.yml`.
- **PostgreSQL no responde al inicio:** espera a `healthcheck` o revisa logs de `postgres`.
- **401/403 en endpoints:** verifica header `Authorization: Bearer <token>` y expiracion del JWT.
- **Sin correos visibles:** valida que `mailhog` este arriba y abre `http://localhost:8025`.
- **Errores de comunicacion entre servicios:** revisa `*_SERVICE_URL` e `INTERNAL_SERVICE_SECRET`.

## Roadmap por sprints

Orden objetivo del proyecto:

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
- Migraciones actualizadas.
- Documentacion tecnica minima al dia.

## Contribucion

Para colaborar:

1. Crea una rama desde `master`.
2. Implementa cambios por servicio/dominio.
3. Ejecuta lint, tipos y tests.
4. Abre PR con descripcion clara del cambio.

Si propones cambios de contrato API, actualiza tambien `API.md`.
