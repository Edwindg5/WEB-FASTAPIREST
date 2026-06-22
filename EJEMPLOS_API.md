"""Ejemplos de uso de los endpoints de la API."""

# EJEMPLOS DE USO DE API

## 1. Health Check

```bash
curl http://localhost:8000/health

Response:
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development"
}
```

## 2. Autenticación (RF-02)

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "admin@cafemonitoring.local",
    "contrasena": "AdminPassword123"
  }'

Response (200 OK):
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "usuario_id": 1,
  "correo": "admin@cafemonitoring.local",
  "nombre_completo": "Administrador del Sistema",
  "rol": "admin"
}

Error (401 Unauthorized):
{
  "detail": "Credenciales inválidas"
}
```

### Usar Token en Requests

**En headers:**
```
Authorization: Bearer {access_token}
```

**Ejemplos:**
```bash
# Listar usuarios
curl -H "Authorization: Bearer eyJ0eXA..." \
  "http://localhost:8000/api/v1/usuarios/"

# Obtener detalles de usuario
curl -H "Authorization: Bearer eyJ0eXA..." \
  "http://localhost:8000/api/v1/usuarios/1"
```

### Refresh Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'

Response (200 OK):
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Logout

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer eyJ0eXA..."

Response (200 OK):
{
  "message": "Logout exitoso"
}

Nota: En JWT sin sesiones en servidor, es principalmente informativo.
El cliente debe descartar el token.
```

## 3. Gestión de Usuarios (RF-01)

### Crear Usuario (Solo Admin)

```bash
curl -X POST "http://localhost:8000/api/v1/usuarios/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "supervisor@example.com",
    "nombre_completo": "Juan Pérez García",
    "rol": "supervisor",
    "contrasena": "SuperPassword123"
  }'

Response (201 Created):
{
  "id": 2,
  "correo": "supervisor@example.com",
  "nombre_completo": "Juan Pérez García",
  "rol": "supervisor",
  "estado": "activo",
  "created_at": "2024-06-20T10:30:00",
  "updated_at": "2024-06-20T10:30:00",
  "ultimo_login": null
}

Error (400 Bad Request):
{
  "detail": "El usuario con correo 'supervisor@example.com' ya existe"
}

Error (403 Forbidden):
{
  "detail": "Se requieren permisos de administrador"
}
```

### Listar Usuarios (Solo Admin)

```bash
curl -H "Authorization: Bearer {admin_token}" \
  "http://localhost:8000/api/v1/usuarios/?skip=0&limit=10"

Response (200 OK):
{
  "total": 5,
  "skip": 0,
  "limit": 10,
  "items": [
    {
      "id": 1,
      "correo": "admin@cafemonitoring.local",
      "nombre_completo": "Administrador",
      "rol": "admin",
      "estado": "activo",
      "created_at": "2024-06-20T08:00:00",
      "updated_at": "2024-06-20T08:00:00",
      "ultimo_login": "2024-06-20T10:15:00"
    },
    {
      "id": 2,
      "correo": "supervisor@example.com",
      "nombre_completo": "Juan Pérez García",
      "rol": "supervisor",
      "estado": "activo",
      "created_at": "2024-06-20T10:30:00",
      "updated_at": "2024-06-20T10:30:00",
      "ultimo_login": null
    }
  ]
}
```

### Obtener Usuario Específico

```bash
# Obtener mis datos
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/usuarios/1"

# Admin puede obtener datos de cualquier usuario
curl -H "Authorization: Bearer {admin_token}" \
  "http://localhost:8000/api/v1/usuarios/2"

Response (200 OK):
{
  "id": 2,
  "correo": "supervisor@example.com",
  "nombre_completo": "Juan Pérez García",
  "rol": "supervisor",
  "estado": "activo",
  "created_at": "2024-06-20T10:30:00",
  "updated_at": "2024-06-20T10:30:00",
  "ultimo_login": null
}

Error (403 Forbidden):
{
  "detail": "No tiene permisos para ver este usuario"
}

Error (404 Not Found):
{
  "detail": "Usuario no encontrado"
}
```

### Actualizar Usuario (Solo Admin)

```bash
curl -X PUT "http://localhost:8000/api/v1/usuarios/2" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_completo": "Juan Carlos Pérez García",
    "rol": "admin",
    "estado": "activo"
  }'

Response (200 OK):
{
  "id": 2,
  "correo": "supervisor@example.com",
  "nombre_completo": "Juan Carlos Pérez García",
  "rol": "admin",
  "estado": "activo",
  "created_at": "2024-06-20T10:30:00",
  "updated_at": "2024-06-20T11:00:00",
  "ultimo_login": null
}
```

### Eliminar Usuario (Solo Admin)

```bash
curl -X DELETE "http://localhost:8000/api/v1/usuarios/2" \
  -H "Authorization: Bearer {admin_token}"

Response (204 No Content)
# Sin cuerpo de respuesta

Error (404 Not Found):
{
  "detail": "Usuario no encontrado"
}
```

### Cambiar Contraseña

```bash
curl -X POST "http://localhost:8000/api/v1/usuarios/1/cambiar-contrasena" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "contrasena_actual": "AdminPassword123",
    "contrasena_nueva": "NuevaPassword456"
  }'

Response (200 OK):
{
  "message": "Contraseña cambiada exitosamente"
}

Error (400 Bad Request):
{
  "detail": "Contraseña actual incorrecta"
}

Error (403 Forbidden):
{
  "detail": "Solo puede cambiar su propia contraseña"
}
```

## 4. Validación Pydantic - Errores

```bash
# Email inválido
curl -X POST "http://localhost:8000/api/v1/usuarios/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "no-es-un-email",
    "nombre_completo": "Test",
    "rol": "supervisor",
    "contrasena": "TestPassword123"
  }'

Response (422 Unprocessable Entity):
{
  "detail": "Error de validación",
  "errors": [
    {
      "field": "correo",
      "message": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}

# Contraseña muy corta
curl -X POST "http://localhost:8000/api/v1/usuarios/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "test@example.com",
    "nombre_completo": "Test",
    "rol": "supervisor",
    "contrasena": "short"
  }'

Response (422 Unprocessable Entity):
{
  "detail": "Error de validación",
  "errors": [
    {
      "field": "contrasena",
      "message": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}

# Campo faltante
curl -X POST "http://localhost:8000/api/v1/usuarios/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_completo": "Test",
    "rol": "supervisor",
    "contrasena": "TestPassword123"
  }'

Response (422 Unprocessable Entity):
{
  "detail": "Error de validación",
  "errors": [
    {
      "field": "correo",
      "message": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 5. Documentación en Swagger

Abrir en navegador:
```
http://localhost:8000/docs
```

Desde Swagger puedes:
- Ver todos los endpoints
- Probar los endpoints (con Authorization)
- Ver esquemas Pydantic
- Descargar OpenAPI JSON

## 6. Integración con Angular (Frontend)

### En un servicio Angular:

```typescript
// auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000/api/v1';
  private tokenSubject = new BehaviorSubject<string | null>(null);

  constructor(private http: HttpClient) {}

  login(correo: string, contrasena: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login`, {
      correo,
      contrasena
    });
  }

  logout(): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/logout`, {});
  }

  refresh(refreshToken: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/refresh`, {
      refresh_token: refreshToken
    });
  }

  getUsuarios(skip = 0, limit = 10): Observable<any> {
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${this.getAccessToken()}`
    });
    return this.http.get(
      `${this.apiUrl}/usuarios?skip=${skip}&limit=${limit}`,
      { headers }
    );
  }

  getAccessToken(): string {
    return localStorage.getItem('access_token') || '';
  }

  saveTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }
}

// En un componente:
export class LoginComponent {
  constructor(private authService: AuthService) {}

  onLogin(correo: string, contrasena: string) {
    this.authService.login(correo, contrasena).subscribe(
      (response) => {
        this.authService.saveTokens(
          response.access_token,
          response.refresh_token
        );
        // Redirigir a dashboard
      },
      (error) => {
        console.error('Login error:', error);
      }
    );
  }
}

// Interceptor para agregar token automáticamente:
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.authService.getAccessToken();
    if (token) {
      req = req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
    }
    return next.handle(req);
  }
}
```

## 7. Paginación

```bash
# Primeros 10 usuarios
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/usuarios/?skip=0&limit=10"

# Siguiente página (usuarios 10-20)
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/usuarios/?skip=10&limit=10"

# Parámetros:
# - skip: Registros a saltar (default: 0)
# - limit: Registros a retornar, máximo 100 (default: 10)
```

## 8. Códigos de Estado HTTP

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| 200 | OK | GET usuario exitoso |
| 201 | Created | POST usuario creado |
| 204 | No Content | DELETE exitoso |
| 400 | Bad Request | Datos inválidos |
| 401 | Unauthorized | Token inválido/expirado |
| 403 | Forbidden | Sin permisos |
| 404 | Not Found | Usuario no existe |
| 422 | Validation Error | Error de Pydantic |
| 500 | Server Error | Error interno |

## 9. Manejo de Errores en el Cliente

```typescript
// En Angular
this.authService.login(correo, contrasena).subscribe(
  (response) => {
    // Éxito (200-201)
    console.log('Login exitoso');
  },
  (error) => {
    // Error
    if (error.status === 401) {
      console.log('Credenciales inválidas');
    } else if (error.status === 422) {
      // Mostrar errores de validación
      console.log('Errores de validación:', error.error.errors);
    } else if (error.status === 500) {
      console.log('Error interno del servidor');
    }
  }
);
```
