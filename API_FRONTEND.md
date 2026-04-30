# API Documentacion - Teca Biblioteca (Frontend Guide)

## Descripcion General
Backend de biblioteca personal basado en microservicios con autenticacion JWT.
Esta guia esta orientada para el desarrollo de proyectos frontend que consuman este backend.

---

## 1. Arquitectura y URLs Base

### Servicios y Puertos

| Servicio | Puerto | URL Base | Base de Datos |
|----------|--------|----------|---------------|
| servicio_usuarios | 5001 | http://localhost:5001 | usuarios_db |
| servicio_catalogo | 5002 | http://localhost:5002 | catalogo_db |
| servicio_prestamos | 5003 | http://localhost:5003 | prestamos_db |
| servicio_notificaciones | 5004 | http://localhost:5004 | notificaciones_db |
| servicio_reportes | 5005 | http://localhost:5005 | reportes_db |

### Consideraciones para Produccion
- En desarrollo: todos los servicios en localhost
- En produccion: configurar un gateway/API gateway o nginx como reverse proxy
- Los puertos internos de Docker no deben ser expuestos directamente en produccion

---

## 2. Autenticacion JWT

### Flujo de Autenticacion

1. **Registro**: El usuario se registra y obtiene sus credenciales
2. **Login**: Envia email y contrasena, recibe un token JWT
3. **Acceso Protegido**: Incluye el token en el header Authorization: Bearer <token>

### Estructura del Token

El token JWT contiene:
- **sub**: ID del usuario
- **rol**: Rol del usuario (estudiante, docente, admin)
- **iat**: Issued at (timestamp)
- **exp**: Expiracion (60 minutos por defecto)

### Configuracion Recomendada para Frontend (Axios)

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor para agregar token automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) config.headers.Authorization = 'Bearer ' + token;
  return config;
});

// Manejo de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Ejemplo con React Query

```javascript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';

const queryClient = new QueryClient();

const api = axios.create({ baseURL: 'http://localhost:5001' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) config.headers.Authorization = 'Bearer ' + token;
  return config;
});

// Hooks personalizados
const useLogin = () => {
  return useMutation(async ({ email, password }) => {
    const response = await api.post('/api/v1/auth/login', { email, password });
    localStorage.setItem('auth_token', response.data.data.access_token);
    return response.data;
  });
};

const useLibros = (params) => {
  return useQuery(['libros', params], () => 
    axios.get('http://localhost:5002/api/v1/catalogo/libros', { params }).then(r => r.data)
  );
};
```

---

## 3. Formato de Respuestas

### Respuesta Exitosa

```json
{
  "success": true,
  "data": { ... },
  "message": "Descripcion de la operacion"
}
```

**Codigos de estado HTTP:**
- **200 OK**: Operacion exitosa
- **201 Created**: Recurso creado correctamente

### Respuesta de Error

```json
{
  "success": false,
  "error": {
    "code": "CODIGO_ERROR",
    "message": "Descripcion del error"
  }
}
```

**Codigos de estado HTTP:**
- **400 Bad Request**: Datos invalidos en la solicitud
- **401 Unauthorized**: Falta autenticacion o token invalido
- **403 Forbidden**: Acceso denegado (sin permisos)
- **404 Not Found**: Recurso no encontrado
- **409 Conflict**: Conflicto de datos (duplicado)
- **422 Unprocessable Entity**: Validacion fallida
- **500 Internal Server Error**: Error del servidor
- **503 Service Unavailable**: Servicio externo no disponible

---

## 4. Servicio: Usuarios (Puerto 5001)

**URL Base:** http://localhost:5001/api/v1/auth

### Endpoints Publicos

#### POST /api/v1/auth/registro
Registrar nuevo usuario.

**Request:**
```json
{
  "nombre": "Juan Perez",
  "email": "juan@ejemplo.com",
  "contrasena": "password123"
}
```

**Validaciones:**
- nombre: Requerido, 2-120 caracteres
- email: Requerido, formato email valido, unico en el sistema
- contrasena: Requerido, texto

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "nombre": "Juan Perez",
    "email": "juan@ejemplo.com",
    "rol": "estudiante",
    "fecha_creacion": "2024-01-15T10:30:00+00:00"
  },
  "message": "Usuario registrado correctamente."
}
```

---

#### POST /api/v1/auth/login
Iniciar sesion.

**Request:**
```json
{
  "email": "juan@ejemplo.com",
  "contrasena": "password123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "message": "Autenticacion exitosa."
}
```

**Instrucciones para el Frontend:**
```javascript
// Guardar token
localStorage.setItem('auth_token', response.data.data.access_token);

// Obtener expiration time
const expiresIn = response.data.data.expires_in; // 3600 segundos

// Opcional: guardar expiration time
const expirationTime = Date.now() + (expiresIn * 1000);
localStorage.setItem('token_expiration', expirationTime);

// Verificar si el token esta proximo a expirar
const isTokenExpired = () => {
  const expiration = localStorage.getItem('token_expiration');
  return !expiration || Date.now() > parseInt(expiration);
};
```

---

### Endpoints Protegidos

#### GET /api/v1/auth/me
Obtener usuario actual.

**Headers:** Authorization: Bearer <token>

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "nombre": "Juan Perez",
    "email": "juan@ejemplo.com",
    "rol": "estudiante",
    "fecha_creacion": "2024-01-15T10:30:00+00:00"
  },
  "message": "Usuario autenticado."
}
```

**Errores:**
- **401**: Token invalido o expirado
- **404**: Usuario no encontrado

---

#### GET /api/v1/auth/admin/check
Verificar permisos de admin.

**Headers:** Authorization: Bearer <token>
**Requiere:** Rol admin

**Response (200):**
```json
{
  "success": true,
  "data": { "authorized": true },
  "message": "Permiso de administrador valido."
}
```

**Error (403):**
```json
{
  "success": false,
  "error": { "code": "FORBIDDEN", "message": "No tienes permisos de administrador." }
}
```

---

## 5. Servicio: Catalogo (Puerto 5002)

**URL Base:** http://localhost:5002/api/v1/catalogo

### Endpoints - Autores

| Metodo | Endpoint | Auth | Descripcion |
|--------|----------|------|-------------|
| GET | /autores | No | Listar autores |
| POST | /autores | Si | Crear autor |
| GET | /autores/:id | No | Obtener autor |
| PUT | /autores/:id | Si | Actualizar autor |
| DELETE | /autores/:id | Si | Eliminar autor |

**Query Parameters:**
- nombre: Filtrar por nombre (busqueda parcial)
- page: Numero de pagina (default: 1)
- per_page: Elementos por pagina (default: 20, max: 100)

#### GET /autores (ejemplo)
```
GET /api/v1/catalogo/autores?nombre=garcia&page=1&per_page=10
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "nombre": "Gabriel Garcia Marquez", "fecha_creacion": "2024-01-15T10:30:00+00:00" }
    ],
    "pagination": { "page": 1, "per_page": 10, "total": 25, "total_pages": 3 }
  },
  "message": "Autores obtenidos correctamente."
}
```

#### POST /autores (crear - requiere auth)
**Headers:** Authorization: Bearer <token>

**Body:**
```json
{
  "nombre": "Nuevo Autor"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": { "id": 2, "nombre": "Nuevo Autor", "fecha_creacion": "2024-01-15T12:00:00+00:00" },
  "message": "Autor creado correctamente."
}
```

**Errores:**
- **409**: Autor duplicado (ya existe uno con ese nombre)
- **422**: Nombre invalido (menos de 2 o mas de 120 caracteres)

#### DELETE /autores/:id
**Errores:**
- **409**: Autor en uso (tiene libros asociados)

---

### Endpoints - Editoriales
Mismo patron que Autores.

### Endpoints - Categorias
Mismo patron que Autores.

### Endpoints - Libros

| Metodo | Endpoint | Auth | Descripcion |
|--------|----------|------|-------------|
| GET | /libros | No | Listar libros |
| POST | /libros | Si | Crear libro |
| GET | /libros/:id | No | Obtener libro |
| PUT | /libros/:id | Si | Actualizar libro |
| PATCH | /libros/:id/disponibilidad | Si | Actualizar disponibilidad |
| DELETE | /libros/:id | Si | Eliminar libro |

**Query Parameters:**
- titulo: Filtrar por titulo (busqueda parcial)
- isbn: Filtrar por ISBN exacto
- autor_id: Filtrar por ID de autor
- editorial_id: Filtrar por ID de editorial
- categoria_id: Filtrar por ID de categoria
- disponible: Filtrar por disponibilidad (true/false)
- page: Numero de pagina (default: 1)
- per_page: Elementos por pagina (default: 20, max: 100)

#### GET /libros (ejemplo)
```
GET /api/v1/catalogo/libros?titulo=cien&disponible=true&page=1&per_page=20
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "titulo": "Cien Anos de Soledad",
        "isbn": "978-006088328-7",
        "autor_id": 1,
        "editorial_id": 1,
        "categoria_id": 1,
        "disponibilidad": true,
        "fecha_creacion": "2024-01-15T10:30:00+00:00",
        "autor": "Gabriel Garcia Marquez",
        "editorial": "Editorial Planeta",
        "categoria": "Novela"
      }
    ],
    "pagination": { "page": 1, "per_page": 20, "total": 10, "total_pages": 1 }
  },
  "message": "Libros obtenidos correctamente."
}
```

#### POST /libros (crear libro - requiere auth)
**Headers:** Authorization: Bearer <token>

**Body:**
```json
{
  "titulo": "El Principito",
  "isbn": "978-015601219-3",
  "autor_id": 2,
  "editorial_id": 3,
  "categoria_id": 4,
  "disponibilidad": true
}
```

**Validaciones:**
- titulo: Requerido, 2-255 caracteres
- isbn: Requerido, formato valido (10-17 digitos, X, guiones), unico
- autor_id: Requerido, debe existir en la base de datos
- editorial_id: Requerido, debe existir
- categoria_id: Requerido, debe existir
- disponibilidad: Opcional, default true

**Errores:**
- **409**: ISBN duplicado
- **422**: Datos invalidos (autor_id, editorial_id o categoria_id no existen)

#### PATCH /libros/:id/disponibilidad (actualizar disponibilidad)
**Headers:** Authorization: Bearer <token>

**Body:**
```json
{
  "disponibilidad": false
}
```

**Respuesta:**
```json
{
  "success": true,
  "data": { "id": 1, "disponibilidad": false },
  "message": "Disponibilidad actualizada correctamente."
}
```

---

## 6. Servicio: Prestamos (Puerto 5003)

**URL Base:** http://localhost:5003/api/v1/prestamos
**Todos los endpoints requieren autenticacion**

### Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | / | Crear prestamo |
| GET | /mis-prestamos | Listar mis prestamos |
| GET | /:id | Obtener prestamo especifico |
| POST | /:id/devolucion | Registrar devolucion |

#### POST / (crear prestamo)
**Headers:** Authorization: Bearer <token>

**Body:**
```json
{
  "libro_id": 1,
  "dias_prestamo": 14
}
```

**Parametros:**
- libro_id: **Requerido**, ID del libro a prestar
- dias_prestamo: Opcional, dias (default: 14, max: 60)

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "usuario_id": 1,
    "libro_id": 1,
    "fecha_prestamo": "2024-01-15T10:30:00+00:00",
    "fecha_devolucion": null,
    "fecha_limite": "2024-01-29T10:30:00+00:00",
    "estado": "activo"
  },
  "message": "Prestamo creado correctamente."
}
```

**Errores comunes:**
- **BOOK_NOT_AVAILABLE (409)**: El libro no esta disponible
- **BOOK_ALREADY_LOANED (409)**: El libro ya tiene un prestamo activo
- **422**: libro_id invalido

**Instrucciones de manejo en Frontend:**
```javascript
const handlePrestamo = async (libroId) => {
  try {
    const response = await prestamoService.createPrestamo(libroId, 14);
    // Mostrar mensaje de exito
    // Actualizar estado del libro
  } catch (error) {
    if (error.code === 'BOOK_NOT_AVAILABLE') {
      // Mostrar: "El libro no esta disponible actualmente"
    } else if (error.code === 'BOOK_ALREADY_LOANED') {
      // Mostrar: "El libro ya esta prestado"
    }
  }
};
```

---

#### GET /mis-prestamos
**Headers:** Authorization: Bearer <token>

**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "usuario_id": 1,
        "libro_id": 1,
        "fecha_prestamo": "2024-01-15T10:30:00+00:00",
        "fecha_devolucion": null,
        "fecha_limite": "2024-01-29T10:30:00+00:00",
        "estado": "activo"
      },
      {
        "id": 2,
        "usuario_id": 1,
        "libro_id": 2,
        "fecha_prestamo": "2024-01-10T10:30:00+00:00",
        "fecha_devolucion": "2024-01-20T10:30:00+00:00",
        "fecha_limite": "2024-01-24T10:30:00+00:00",
        "estado": "devuelto"
      }
    ]
  },
  "message": "Prestamos obtenidos correctamente."
}
```

**Estados posibles:**
- **activo**: Prestamo vigente, pendiente de devolucion
- **devuelto**: Prestamo已完成 (devuelto)

---

#### GET /:id (obtener prestamo especifico)
**Headers:** Authorization: Bearer <token>

**Parametros de URL:**
- id: ID del prestamo

**Errores:**
- **404**: Prestamo no encontrado
- **403**: No tienes permisos para ver este prestamo (pertenece a otro usuario)

---

#### POST /:id/devolucion (devolver prestamo)
**Headers:** Authorization: Bearer <token>

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "usuario_id": 1,
    "libro_id": 1,
    "fecha_prestamo": "2024-01-15T10:30:00+00:00",
    "fecha_devolucion": "2024-01-20T10:30:00+00:00",
    "fecha_limite": "2024-01-29T10:30:00+00:00",
    "estado": "devuelto"
  },
  "message": "Devolucion registrada correctamente."
}
```

**Errores:**
- **404**: Prestamo no encontrado
- **403**: No tienes permisos
- **409**: El prestamo ya fue devuelto (estado no es activo)

**Logica de negocio:**
- Al devolver, automaticamente se actualiza la disponibilidad del libro a true
- Se registra la fecha de devolucion actual

---

## 7. Servicio: Notificaciones (Puerto 5004)

**URL Base:** http://localhost:5004/api/v1/notificaciones
**Todos los endpoints requieren autenticacion**

### Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | / | Crear notificacion manual |
| POST | /recordatorios/48h | Crear recordatorio 48h |
| GET | /:id | Obtener notificacion |
| POST | /process-queue | Procesar cola de envios |

#### POST / (crear notificacion manual)
**Headers:** Authorization: Bearer <token>

**Body:**
```json
{
  "usuario_id": 1,
  "prestamo_id": 1,
  "tipo": "recordatorio",
  "destinatario_email": "usuario@ejemplo.com",
  "asunto": "Recordatorio de devolucion",
  "mensaje": "Tu prestamo vence pronto, por favor devuelve el libro a tiempo.",
  "fecha_programada": "2024-01-20T10:00:00Z",
  "max_reintentos": 3
}
```

**Parametros:**
- usuario_id: Requerido
- prestamo_id: Opcional
- tipo: Opcional, default "general", max 50 caracteres
- destinatario_email: Requerido, email valido
- asunto: Requerido, max 255 caracteres
- mensaje: Requerido, max 10000 caracteres
- fecha_programada: Opcional, default ahora, formato ISO8601
- max_reintentos: Opcional, default 3, max 20

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "usuario_id": 1,
    "prestamo_id": 1,
    "tipo": "recordatorio",
    "destinatario_email": "usuario@ejemplo.com",
    "asunto": "Recordatorio de devolucion",
    "mensaje": "Tu prestamo vence pronto...",
    "fecha_envio": null,
    "fecha_programada": "2024-01-20T10:00:00+00:00",
    "estado": "pendiente",
    "reintentos": 0,
    "max_reintentos": 3,
    "proximo_reintento": null,
    "ultimo_error": null
  },
  "message": "Notificacion creada correctamente."
}
```

**Estados de notificacion:**
- **pendiente**: Esperando ser enviada
- **reintento**: En espera de reintento (fallo anterior, reintentara)
- **enviada**: Enviada exitosamente
- **fallida**: Fallo despues de todos los reintentos

---

#### POST /recordatorios/48h (crear recordatorio 48h)
**Headers:** Authorization: Bearer <token>

**Body:**
```json
{
  "usuario_id": 1,
  "prestamo_id": 1,
  "destinatario_email": "usuario@ejemplo.com",
  "fecha_limite": "2024-01-25T10:00:00Z",
  "libro_titulo": "Cien Anos de Soledad"
}
```

**Parametros:**
- usuario_id: Requerido
- prestamo_id: Requerido
- destinatario_email: Requerido
- fecha_limite: Requerido, fecha ISO8601 de la fecha limite del prestamo
- libro_titulo: Opcional, default "el libro prestado"

**Logica:** Crea una notificacion programada para 48 horas antes de la fecha limite.

---

#### GET /:id (obtener notificacion)
**Headers:** Authorization: Bearer <token>

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "estado": "enviada",
    "fecha_envio": "2024-01-20T10:00:00+00:00",
    "reintentos": 0
  }
}
```

---

#### POST /process-queue (procesar cola de envios)
**Headers:** Authorization: Bearer <token>

**Uso:** Procesa manualmente las notificaciones pendientes (el worker lo hace automaticamente cada 30 segundos).

**Response:**
```json
{
  "success": true,
  "data": {
    "processed": 5,
    "sent": 4,
    "failed": 1
  },
  "message": "Cola procesada correctamente."
}
```

---

## 8. Servicio: Reportes (Puerto 5005)

**URL Base:** http://localhost:5005/api/v1/reportes
**Todos los endpoints requieren autenticacion con rol admin**

### Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | /libros-mas-prestados | Top libros mas prestados |
| GET | /prestamos-por-usuario | Prestamos por usuario |
| GET | /retrasos | Lista de retrasos |
| POST | /sync/usuarios | Sincronizar usuarios |
| POST | /sync/libros | Sincronizar libros |
| POST | /sync/prestamos | Sincronizar prestamos |
| POST | /sync/lote | Sincronizacion completa |

**Query Parameters (GET):**
- limit: Numero de resultados (default: 10, max: 100)

---

#### GET /libros-mas-prestados?limit=10
**Headers:** Authorization: Bearer <token>

**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "libro_id": 1,
        "titulo": "Cien Anos de Soledad",
        "total_prestados": 15,
        "ultimo_prestamo": "2024-01-20T10:30:00+00:00"
      },
      {
        "libro_id": 2,
        "titulo": "El Principito",
        "total_prestados": 12,
        "ultimo_prestamo": "2024-01-19T15:00:00+00:00"
      }
    ],
    "limit": 10
  },
  "message": "Reporte de libros mas prestados generado correctamente."
}
```

---

#### GET /prestamos-por-usuario?limit=10
**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "usuario_id": 1,
        "nombre": "Juan Perez",
        "email": "juan@ejemplo.com",
        "total_prestados": 8,
        "prestamos_activos": 2,
        "ultimo_prestamo": "2024-01-20T10:30:00+00:00"
      }
    ],
    "limit": 10
  },
  "message": "Reporte de prestamos por usuario generado correctamente."
}
```

---

#### GET /retrasos?limit=10
**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "prestamo_id": 1,
        "usuario_id": 1,
        "usuario_nombre": "Juan Perez",
        "libro_id": 1,
        "libro_titulo": "Cien Anos de Soledad",
        "estado": "activo",
        "fecha_prestamo": "2024-01-10T10:00:00+00:00",
        "fecha_limite": "2024-01-24T10:00:00+00:00",
        "fecha_devolucion": null,
        "dias_retraso": 5
      }
    ],
    "limit": 10
  },
  "message": "Reporte de retrasos generado correctamente."
}
```

---

#### Endpoints de Sincronizacion (Analytics)

Estos endpoints permiten sincronizar datos de otros servicios hacia la base de datos de reportes para analisis.

**POST /sync/usuarios**
**Body:**
```json
{
  "items": [
    { "id": 1, "nombre": "Juan Perez", "email": "juan@ejemplo.com" },
    { "id": 2, "nombre": "Maria Garcia", "email": "maria@ejemplo.com" }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": { "created": 2, "updated": 0 },
  "message": "Usuarios analiticos sincronizados correctamente."
}
```

---

**POST /sync/libros**
**Body:**
```json
{
  "items": [
    { "id": 1, "titulo": "Cien Anos de Soledad" },
    { "id": 2, "titulo": "El Principito" }
  ]
}
```

---

**POST /sync/prestamos**
**Body:**
```json
{
  "items": [
    {
      "id": 1,
      "usuario_id": 1,
      "libro_id": 1,
      "fecha_prestamo": "2024-01-10T10:00:00Z",
      "fecha_limite": "2024-01-24T10:00:00Z",
      "fecha_devolucion": null,
      "estado": "activo"
    }
  ]
}
```

**Notas:**
- fecha_prestamo y fecha_limite: Requeridos, formato ISO8601
- fecha_devolucion: Opcional, null si no ha sido devuelto
- estado: Default "activo", valores posibles: "activo", "devuelto"

---

**POST /sync/lote (sincronizacion completa)**
**Body:**
```json
{
  "usuarios": [
    { "id": 1, "nombre": "Juan Perez", "email": "juan@ejemplo.com" }
  ],
  "libros": [
    { "id": 1, "titulo": "Cien Anos de Soledad" }
  ],
  "prestamos": [
    {
      "id": 1,
      "usuario_id": 1,
      "libro_id": 1,
      "fecha_prestamo": "2024-01-10T10:00:00Z",
      "fecha_limite": "2024-01-24T10:00:00Z",
      "estado": "activo"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "usuarios": { "created": 1, "updated": 0 },
    "libros": { "created": 1, "updated": 0 },
    "prestamos": { "created": 1, "updated": 0 }
  },
  "message": "Sincronizacion analitica por lote completada."
}
```

---

## 9. Codigos de Error Comunes

| Codigo | HTTP | Descripcion |
|--------|------|-------------|
| MISSING_AUTH_HEADER | 401 | Falta el header Authorization |
| INVALID_AUTH_HEADER | 401 | Formato de token invalido (no es "Bearer") |
| INVALID_TOKEN | 401 | Token no valido o expirado |
| USER_NOT_FOUND | 401 | Usuario no encontrado |
| FORBIDDEN | 403 | Sin permisos para acceder al recurso |
| VALIDATION_ERROR | 422 | Error de validacion de datos |
| INVALID_REQUEST_BODY | 400 | JSON invalido o estructura incorrecta |
| AUTOR_NOT_FOUND | 404 | Autor no encontrado |
| AUTOR_ALREADY_EXISTS | 409 | Autor duplicado |
| AUTOR_IN_USE | 409 | Autor tiene libros asociados |
| EDITORIAL_NOT_FOUND | 404 | Editorial no encontrada |
| EDITORIAL_ALREADY_EXISTS | 409 | Editorial duplicada |
| CATEGORIA_NOT_FOUND | 404 | Categoria no encontrada |
| CATEGORIA_ALREADY_EXISTS | 409 | Categoria duplicada |
| LIBRO_NOT_FOUND | 404 | Libro no encontrado |
| ISBN_ALREADY_EXISTS | 409 | ISBN duplicado |
| LOAN_NOT_FOUND | 404 | Prestamo no encontrado |
| LOAN_NOT_ACTIVE | 409 | El prestamo ya fue devuelto |
| BOOK_NOT_AVAILABLE | 409 | El libro no esta disponible |
| BOOK_ALREADY_LOANED | 409 | El libro ya tiene un prestamo activo |
| NOTIFICATION_NOT_FOUND | 404 | Notificacion no encontrada |
| FK_NOT_FOUND | 409 | Referencia foranea no encontrada |
| DEPENDENCY_UNAVAILABLE | 503 | Servicio externo no disponible |
| INTERNAL_SERVER_ERROR | 500 | Error interno del servidor |

---

## 10. Health Checks

| Servicio | Endpoint | Descripcion |
|----------|----------|-------------|
| servicio_usuarios | GET http://localhost:5001/health | Verifica estado del servicio |
| servicio_catalogo | GET http://localhost:5002/health | Verifica estado del servicio |
| servicio_prestamos | GET http://localhost:5003/health | Verifica estado del servicio |
| servicio_notificaciones | GET http://localhost:5004/health | Verifica estado del servicio |
| servicio_reportes | GET http://localhost:5005/health | Verifica estado del servicio |

**Response tipico:**
```json
{
  "status": "healthy",
  "service": "servicio_usuarios"
}
```

**Uso recomendado:** Verificar disponibilidad antes de realizar llamadas, o en un panel de monitoreo.

---

## 11. Guia de Implementacion Frontend

### Configuracion Base con Axios

```javascript
// services/api.js
import axios from 'axios';

const createApi = (baseURL) => {
  const api = axios.create({
    baseURL,
    timeout: 10000, // 10 segundos
    headers: { 'Content-Type': 'application/json' },
  });

  // Interceptor de peticion - agregar token
  api.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('auth_token');
      if (token) config.headers.Authorization = 'Bearer ' + token;
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Interceptor de respuesta - manejar errores
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response) {
        const { status, data } = error.response;
        
        switch (status) {
          case 401:
            // Token expirado o invalido
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
            break;
          case 403:
            // Sin permisos
            console.error('Sin permisos:', data.error.message);
            break;
          case 404:
            // Recurso no encontrado
            console.error('No encontrado:', data.error.message);
            break;
          case 500:
            // Error del servidor
            console.error('Error del servidor');
            break;
        }
      }
      return Promise.reject(error);
    }
  );

  return api;
};

// Configuracion de servicios
const apiUsuarios = createApi('http://localhost:5001');
const apiCatalogo = createApi('http://localhost:5002');
const apiPrestamos = createApi('http://localhost:5003');
const apiNotificaciones = createApi('http://localhost:5004');
const apiReportes = createApi('http://localhost:5005');

export { apiUsuarios, apiCatalogo, apiPrestamos, apiNotificaciones, apiReportes };
```

---

### Servicios de Autenticacion

```javascript
// services/auth.js
import { apiUsuarios } from './api';

export const authService = {
  async login(email, password) {
    const response = await apiUsuarios.post('/api/v1/auth/login', { 
      email, 
      contrasena: password 
    });
    const { access_token } = response.data.data;
    localStorage.setItem('auth_token', access_token);
    return response.data;
  },

  async register(nombre, email, password) {
    return (
      await apiUsuarios.post('/api/v1/auth/registro', { 
        nombre, 
        email, 
        contrasena: password 
      })
    ).data;
  },

  async getMe() {
    return (await apiUsuarios.get('/api/v1/auth/me')).data;
  },

  async checkAdmin() {
    return (await apiUsuarios.get('/api/v1/auth/admin/check')).data;
  },

  logout() {
    localStorage.removeItem('auth_token');
  },

  isAuthenticated() {
    return !!localStorage.getItem('auth_token');
  },

  getToken() {
    return localStorage.getItem('auth_token');
  },
};
```

---

### Servicios de Catalogo

```javascript
// services/catalogo.js
import { apiCatalogo } from './api';

const CATALOGO_URL = '/api/v1/catalogo';

export const autorService = {
  async list(params = {}) {
    return (await apiCatalogo.get(CATALOGO_URL + '/autores', { params })).data;
  },
  async get(id) {
    return (await apiCatalogo.get(CATALOGO_URL + '/autores/' + id)).data;
  },
  async create(nombre) {
    return (await apiCatalogo.post(CATALOGO_URL + '/autores', { nombre })).data;
  },
  async update(id, nombre) {
    return (await apiCatalogo.put(CATALOGO_URL + '/autores/' + id, { nombre })).data;
  },
  async delete(id) {
    return (await apiCatalogo.delete(CATALOGO_URL + '/autores/' + id)).data;
  },
};

export const editorialService = {
  async list(params = {}) {
    return (await apiCatalogo.get(CATALOGO_URL + '/editoriales', { params })).data;
  },
  async get(id) {
    return (await apiCatalogo.get(CATALOGO_URL + '/editoriales/' + id)).data;
  },
  async create(nombre) {
    return (await apiCatalogo.post(CATALOGO_URL + '/editoriales', { nombre })).data;
  },
  async update(id, nombre) {
    return (await apiCatalogo.put(CATALOGO_URL + '/editoriales/' + id, { nombre })).data;
  },
  async delete(id) {
    return (await apiCatalogo.delete(CATALOGO_URL + '/editoriales/' + id)).data;
  },
};

export const categoriaService = {
  async list(params = {}) {
    return (await apiCatalogo.get(CATALOGO_URL + '/categorias', { params })).data;
  },
  async get(id) {
    return (await apiCatalogo.get(CATALOGO_URL + '/categorias/' + id)).data;
  },
  async create(nombre) {
    return (await apiCatalogo.post(CATALOGO_URL + '/categorias', { nombre })).data;
  },
  async update(id, nombre) {
    return (await apiCatalogo.put(CATALOGO_URL + '/categorias/' + id, { nombre })).data;
  },
  async delete(id) {
    return (await apiCatalogo.delete(CATALOGO_URL + '/categorias/' + id)).data;
  },
};

export const libroService = {
  async list(params = {}) {
    return (await apiCatalogo.get(CATALOGO_URL + '/libros', { params })).data;
  },
  async get(id) {
    return (await apiCatalogo.get(CATALOGO_URL + '/libros/' + id)).data;
  },
  async create(libro) {
    return (await apiCatalogo.post(CATALOGO_URL + '/libros', libro)).data;
  },
  async update(id, libro) {
    return (await apiCatalogo.put(CATALOGO_URL + '/libros/' + id, libro)).data;
  },
  async updateDisponibilidad(id, disponibilidad) {
    return (
      await apiCatalogo.patch(CATALOGO_URL + '/libros/' + id + '/disponibilidad', {
        disponibilidad,
      })
    ).data;
  },
  async delete(id) {
    return (await apiCatalogo.delete(CATALOGO_URL + '/libros/' + id)).data;
  },
};
```

---

### Servicios de Prestamos

```javascript
// services/prestamos.js
import { apiPrestamos } from './api';

const PRESTAMOS_URL = '/api/v1/prestamos';

export const prestamoService = {
  async create(libroId, diasPrestamo = 14) {
    return (
      await apiPrestamos.post(PRESTAMOS_URL, {
        libro_id: libroId,
        dias_prestamo: diasPrestamo,
      })
    ).data;
  },

  async list() {
    return (await apiPrestamos.get(PRESTAMOS_URL + '/mis-prestamos')).data;
  },

  async get(id) {
    return (await apiPrestamos.get(PRESTAMOS_URL + '/' + id)).data;
  },

  async devolver(id) {
    return (await apiPrestamos.post(PRESTAMOS_URL + '/' + id + '/devolucion')).data;
  },
};
```

---

### Servicios de Notificaciones

```javascript
// services/notificaciones.js
import { apiNotificaciones } from './api';

const NOTIFICACIONES_URL = '/api/v1/notificaciones';

export const notificacionService = {
  async create(data) {
    return (await apiNotificaciones.post(NOTIFICACIONES_URL, data)).data;
  },

  async createRecordatorio48h(data) {
    return (
      await apiNotificaciones.post(
        NOTIFICACIONES_URL + '/recordatorios/48h',
        data
      )
    ).data;
  },

  async get(id) {
    return (await apiNotificaciones.get(NOTIFICACIONES_URL + '/' + id)).data;
  },

  async processQueue() {
    return (await apiNotificaciones.post(NOTIFICACIONES_URL + '/process-queue'))
      .data;
  },
};
```

---

### Servicios de Reportes

```javascript
// services/reportes.js
import { apiReportes } from './api';

const REPORTES_URL = '/api/v1/reportes';

export const reporteService = {
  async getLibrosMasPrestados(limit = 10) {
    return (
      await apiReportes.get(REPORTES_URL + '/libros-mas-prestados', {
        params: { limit },
      })
    ).data;
  },

  async getPrestamosPorUsuario(limit = 10) {
    return (
      await apiReportes.get(REPORTES_URL + '/prestamos-por-usuario', {
        params: { limit },
      })
    ).data;
  },

  async getRetrasos(limit = 10) {
    return (
      await apiReportes.get(REPORTES_URL + '/retrasos', {
        params: { limit },
      })
    ).data;
  },

  async syncUsuarios(items) {
    return (
      await apiReportes.post(REPORTES_URL + '/sync/usuarios', { items })
    ).data;
  },

  async syncLibros(items) {
    return (
      await apiReportes.post(REPORTES_URL + '/sync/libros', { items })
    ).data;
  },

  async syncPrestamos(items) {
    return (
      await apiReportes.post(REPORTES_URL + '/sync/prestamos', { items })
    ).data;
  },

  async syncLote(data) {
    return (await apiReportes.post(REPORTES_URL + '/sync/lote', data)).data;
  },
};
```

---

### Ejemplo de Uso con React Hooks

```javascript
// components/LoginForm.jsx
import { useState } from 'react';
import { authService } from '../services/auth';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await authService.login(email, password);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Error de autenticacion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Contrasena"
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? 'Iniciando...' : 'Iniciar Sesion'}
      </button>
    </form>
  );
}

// components/LibroList.jsx
import { useState, useEffect } from 'react';
import { libroService } from '../services/catalogo';

export function LibroList() {
  const [libros, setLibros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtro, setFiltro] = useState('');

  useEffect(() => {
    loadLibros();
  }, [filtro]);

  const loadLibros = async () => {
    setLoading(true);
    try {
      const params = filtro ? { titulo: filtro } : {};
      const response = await libroService.list(params);
      setLibros(response.data.items);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <input
        type="text"
        value={filtro}
        onChange={(e) => setFiltro(e.target.value)}
        placeholder="Buscar libros..."
      />
      <ul>
        {libros.map((libro) => (
          <li key={libro.id}>
            {libro.titulo} - {libro.autor} - 
            {libro.disponibilidad ? 'Disponible' : 'No disponible'}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 12. Ejemplo de Flujo Completo

### Paso 1: Registrar usuario
```bash
curl -X POST http://localhost:5001/api/v1/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Juan","email":"juan@test.com","contrasena":"pass123"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "nombre": "Juan",
    "email": "juan@test.com",
    "rol": "estudiante"
  }
}
```

### Paso 2: Login (obtener token)
```bash
curl -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"juan@test.com","contrasena":"pass123"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Guardar token:** `TOKEN="eyJhbGciOiJIUzI1NiIs..."`

### Paso 3: Crear autor (con token)
```bash
curl -X POST http://localhost:5002/api/v1/catalogo/autores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Gabriel Garcia Marquez"}'
```

### Paso 4: Crear editorial
```bash
curl -X POST http://localhost:5002/api/v1/catalogo/editoriales \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Editorial Planeta"}'
```

### Paso 5: Crear categoria
```bash
curl -X POST http://localhost:5002/api/v1/catalogo/categorias \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Novela"}'
```

### Paso 6: Crear libro
```bash
curl -X POST http://localhost:5002/api/v1/catalogo/libros \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Cien Anos de Soledad",
    "isbn": "978-0060934412",
    "autor_id": 1,
    "editorial_id": 1,
    "categoria_id": 1
  }'
```

### Paso 7: Verificar disponibilidad del libro
```bash
curl -X GET http://localhost:5002/api/v1/catalogo/libros/1 \
  -H "Content-Type: application/json"
```

### Paso 8: Crear prestamo
```bash
curl -X POST http://localhost:5003/api/v1/prestamos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"libro_id": 1}'
```

### Paso 9: Ver mis prestamos
```bash
curl -X GET http://localhost:5003/api/v1/prestamos/mis-prestamos \
  -H "Authorization: Bearer $TOKEN"
```

### Paso 10: Devolver prestamo
```bash
curl -X POST http://localhost:5003/api/v1/prestamos/1/devolucion \
  -H "Authorization: Bearer $TOKEN"
```

---

## 13. Configuracion de Desarrollo

### Variables de Entorno Recomendadas

```env
# Frontend (.env.local)
REACT_APP_API_USUARIOS=http://localhost:5001
REACT_APP_API_CATALOGO=http://localhost:5002
REACT_APP_API_PRESTAMOS=http://localhost:5003
REACT_APP_API_NOTIFICACIONES=http://localhost:5004
REACT_APP_API_REPORTES=http://localhost:5005

# Produccion (ajustar segun deploy)
REACT_APP_API_BASE=https://api.biblioteca.com

# Opcional: timeout configuracion
REACT_APP_API_TIMEOUT=10000
```

### Configuracion con Vite

```javascript
// vite.config.js
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
});
```

### Configuracion con Next.js

```javascript
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5001/api/:path*',
      },
    ];
  },
};
```

---

## 14. Mejores Practicas para Frontend

### Manejo de Fechas
- Todas las fechas se envian en formato ISO8601 con timezone UTC (Z o +00:00)
- El frontend debe convertir a la timezone local del usuario para mostrar
- Usar librerias como date-fns o moment para parsing

```javascript
// Ejemplo de conversion
import { format, parseISO } from 'date-fns';

const fechaUTC = '2024-01-15T10:30:00+00:00';
const fechaLocal = format(parseISO(fechaUTC), 'dd/MM/yyyy HH:mm');
// Resultado: "15/01/2024 10:30"
```

### Validaciones del Lado del Frontend
- Realizar validacion basica antes de enviar para mejorar UX
- Validar formato de email
- Validar longitud de campos
- Mostrar mensajes de error claros al usuario
- Manejar estados de carga (loading)

### Manejo de Errores
- Siempre mostrar el mensaje del servidor al usuario
- Manejar errores de red (sin conexion)
- Implementar reintentos automaticos para operaciones idempotentes
- Usar notificaciones/toasts para errores

### Optimizacion de Rendimiento
- Implementar paginacion en listas grandes
- Usar caching (React Query, SWR)
- Implementar debounce en busquedas
- Lazy loading para imagenes (si aplica)

### Seguridad
- Nunca almacenar contrasenas en localStorage
- Implementar logout automatico en inactividad
- Sanitizar datos antes de mostrar (XSS)
- Usar HTTPS en produccion

---

## 15. Notas de Implementacion

### Autenticacion entre Servicios
- El servicio de Prestamos y Reportes necesitan verificar tokens con el servicio de Usuarios
- El token debe incluirse en todos los headers de Authorization
- El servicio de Prestamos obtiene el usuario_id del token, no del body

### Relaciones entre Servicios
- Los prestamos dependen del catalogo (libros) y usuarios
- Los reportes pueden funcionar de manera independiente o sincronizada
- Las notificaciones se relacionan con usuarios y prestamos

### Testing
- Verificar que los endpoints publicos funcionen sin token
- Verificar que los endpoints protegidos requieran token valido
- Probar casos de error (404, 409, etc.)
- Probar flujos completos (registro -> login -> prestamo -> devolucion)

---

Esta documentacion proporciona toda la informacion necesaria para consumir los servicios backend desde cualquier proyecto frontend (React, Vue, Angular, etc.).
