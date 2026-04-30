# API Documentacion - Teca Biblioteca

## Descripcion General

Backend de biblioteca personal basado en microservicios. Autenticacion JWT integrada en todos los endpoints protegidos.

## URLs Base

| Servicio | Puerto | URL |
|----------|--------|-----|
| servicio_usuarios | 5001 | http://localhost:5001 |
| servicio_catalogo | 5002 | http://localhost:5002 |
| servicio_prestamos | 5003 | http://localhost:5003 |
| servicio_notificaciones | 5004 | http://localhost:5004 |
| servicio_reportes | 5005 | http://localhost:5005 |
| Mailhog (UI) | 8025 | http://localhost:8025 |

## Autenticacion

Todos los endpoints requieren el header `Authorization: Bearer <token>` excepto losendpointspublicos.

### Estandar de Respuesta

**Exito:**
```json
{
  "success": true,
  "data": {},
  "message": "Descripcion del resultado"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "CODIGO_ERROR",
    "message": "Descripcion del error"
  }
}
```

---

## Servicio: Usuarios (Puerto 5001)

### Endpoints Publicos

#### POST /api/v1/auth/registro
Registrar nuevo usuario.

**Request:**
```json
{
  "nombre": "string",
  "email": "string",
  "contrasena": "string",
  "rol": "estudiante" | "docente" | "admin"
}
```

**Response:** 201

#### POST /api/v1/auth/login
Iniciar sesion.

**Request:**
```json
{
  "email": "string",
  "contrasena": "string"
}
```

**Response:** 200
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "message": "Autenticacion exitosa."
}
```

### Endpoints Protegidos

#### GET /api/v1/auth/me
Obtener usuario actual.

**Headers:** `Authorization: Bearer <token>`

**Response:** 200

#### GET /api/v1/auth/admin/check
Verificar permisos de admin.

**Headers:** `Authorization: Bearer <token>`

**Response:** 200

---

## Servicio: Catalogo (Puerto 5002)

Todos los endpoints requieren `Authorization: Bearer <token>`.

### Autores

| Metodo | Endpoint | Descripcion |
|-------|----------|-------------|
| GET | /api/v1/catalogo/autores | Listar autores |
| POST | /api/v1/catalogo/autores | Crear autor |
| GET | /api/v1/catalogo/autores/{id} | Obtener autor |
| PUT | /api/v1/catalogo/autores/{id} | Actualizar autor |
| DELETE | /api/v1/catalogo/autores/{id} | Eliminar autor |

### Editoriales

| Metodo | Endpoint | Descripcion |
|-------|----------|-------------|
| GET | /api/v1/catalogo/editoriales | Listar editoriales |
| POST | /api/v1/catalogo/editoriales | Crear editorial |
| GET | /api/v1/catalogo/editoriales/{id} | Obtener editorial |
| PUT | /api/v1/catalogo/editoriales/{id} | Actualizar editorial |
| DELETE | /api/v1/catalogo/editoriales/{id} | Eliminar editorial |

### Categorias

| Metodo | Endpoint | Descripcion |
|-------|----------|-------------|
| GET | /api/v1/catalogo/categorias | Listar categorias |
| POST | /api/v1/catalogo/categorias | Crear categoria |
| GET | /api/v1/catalogo/categorias/{id} | Obtener categoria |
| PUT | /api/v1/catalogo/categorias/{id} | Actualizar categoria |
| DELETE | /api/v1/catalogo/categorias/{id} | Eliminar categoria |

### Libros

| Metodo | Endpoint | Descripcion |
|-------|----------|-------------|
| GET | /api/v1/catalogo/libros | Listar libros (filtros por query) |
| POST | /api/v1/catalogo/libros | Crear libro |
| GET | /api/v1/catalogo/libros/{id} | Obtener libro |
| PUT | /api/v1/catalogo/libros/{id} | Actualizar libro |
| PATCH | /api/v1/catalogo/libros/{id}/disponibilidad | Actualizar disponibilidad |
| DELETE | /api/v1/catalogo/libros/{id} | Eliminar libro |

**Query Params para /libros:**
- `disponible`: true/false (filtro disponibilidad)
- `categoria_id`: int
- `autor_id`: int
- `editorial_id`: int
- `search`: string (busqueda en titulo/isbn)
- `limit`: int (default 10)
- `offset`: int (default 0)

**Request crear libro:**
```json
{
  "titulo": "string",
  "isbn": "string",
  "autor_id": int,
  "editorial_id": int,
  "categoria_id": int
}
```

**Request disponibilidad:**
```json
{
  "disponibilidad": true
}
```

---

## Servicio: Prestamos (Puerto 5003)

Todos los endpoints requieren `Authorization: Bearer <token>`.

| Metodo | Endpoint | Descripcion |
|-------|----------|-------------|
| POST | /api/v1/prestamos | Crear prestamo |
| GET | /api/v1/prestamos/mis-prestamos | Listar mis prestamos |
| GET | /api/v1/prestamos/{id} | Obtener prestamo |
| POST | /api/v1/prestamos/{id}/devolucion | Registrar devolucion |

**Request crear prestamo:**
```json
{
  "libro_id": int,
  "dias": int (opcional, default 14)
}
```

**Response prestamo:**
```json
{
  "id": int,
  "libro_id": int,
  "usuario_id": int,
  "fecha_prestamo": "datetime",
  "fecha_limite": "datetime",
  "fecha_devolucion": "datetime | null",
  "estado": "activo" | "devuelto" | "vencido"
}
```

---

## Servicio: Notificaciones (Puerto 5004)

Todos los endpoints requieren `Authorization: Bearer <token>`.

| Metodo | Endpoint | Descripcion |
|-------|----------|-------------|
| POST | /api/v1/notificaciones | Crear notificacion |
| POST | /api/v1/notificaciones/recordatorios/48h | Crear recordatorio 48h |
| GET | /api/v1/notificaciones/{id} | Obtener notificacion |
| POST | /api/v1/notificaciones/process-queue | Procesar cola de envios |

**Request crear notificacion:**
```json
{
  "usuario_id": int,
  "prestamo_id": int,
  "mensaje": "string",
  "tipo": "recordatorio" | "aviso" | "alerta"
}
```

---

## Servicio: Reportes (Puerto 5005)

Todos los endpoints requieren `Authorization: Bearer <token>`.

| Metodo | Endpoint | Descripcion |
|-------|----------|-------------|
| GET | /api/v1/reportes/libros-mas-prestados | Top libros mas prestados |
| GET | /api/v1/reportes/prestamos-por-usuario | Prestamos por usuario |
| GET | /api/v1/reportes/retrasos | Lista de retrasos |
| POST | /api/v1/reportes/sync/usuarios | Sincronizar usuarios |
| POST | /api/v1/reportes/sync/libros | Sincronizar libros |
| POST | /api/v1/reportes/sync/prestamos | Sincronizar prestamos |
| POST | /api/v1/reportes/sync/lote | Sincronizacion completa |

**Query Params:**
- `limit`: int (default 10, max 100)
- `offset`: int

---

## Códigos de Error

| Codigo | HTTP | Descripcion |
|--------|------|-------------|
| MISSING_AUTH_HEADER | 401 | Falta header Authorization |
| INVALID_AUTH_HEADER | 401 | Header invalido |
| AUTH_REQUIRED | 401 | Token invalido o expirado |
| USER_NOT_FOUND | 404 | Usuario no encontrado |
| INVALID_REQUEST_BODY | 400 | JSON invalido |
| RESOURCE_NOT_FOUND | 404 | Recurso no encontrado |
| INTERNAL_SERVER_ERROR | 500 | Error interno |
| AUTH_SERVICE_UNAVAILABLE | 503 | Servicio auth no disponible |

---

## Health Checks

| Servicio | Endpoint |
|----------|----------|
| servicio_usuarios | GET /health |
| servicio_catalogo | GET /health |
| servicio_prestamos | GET /health |
| servicio_notificaciones | GET /health |
| servicio_reportes | GET /health |

---

## Ejemplo de Flujo Completo

```bash
# 1. Registrar usuario
curl -X POST http://localhost:5001/api/v1/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Juan","email":"juan@test.com","contrasena":"pass123","rol":"estudiante"}'

# 2. Login
curl -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"juan@test.com","contrasena":"pass123"}'

# GuardarToken...

# 3. Crear autor (con token)
curl -X POST http://localhost:5002/api/v1/catalogo/autores \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Gabriel Garcia Marquez"}'

# 4. Crear libro
curl -X POST http://localhost:5002/api/v1/catalogo/libros \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Cien Anos de Soledad","isbn":"978-0060934412","autor_id":1,"editorial_id":1,"categoria_id":1}'

# 5. Crear prestamo
curl -X POST http://localhost:5003/api/v1/prestamos \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"libro_id":1}'

# 6. Registrar devolucion
curl -X POST http://localhost:5003/api/v1/prestamos/1/devolucion \
  -H "Authorization: Bearer <token>"
```