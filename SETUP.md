"""Configuración y guía para ejecutar la API localmente."""

# GUÍA DE CONFIGURACIÓN LOCAL

## 1. Variables de Entorno (.env)

Crear archivo `.env` en la raíz del proyecto:

```env
# Base de Datos PostgreSQL
DATABASE_URL=postgresql://cafe_user:cafe_secure_password_123@localhost:5432/cafe_monitoring_db

# JWT Security
SECRET_KEY=tu-clave-super-secreta-cambiar-en-produccion-minimo-32-caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# FastAPI
APP_TITLE=API Web - Sistema Monitoreo Secado Café
APP_VERSION=1.0.0
DEBUG=True

# CORS - Frontend Angular
FRONTEND_URL=http://localhost:4200

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO

# Base de Datos Postgresql (docker-compose)
POSTGRES_USER=cafe_user
POSTGRES_PASSWORD=cafe_secure_password_123
POSTGRES_DB=cafe_monitoring_db
```

## 2. Opciones de Ejecución

### Opción A: Docker Compose (Recomendado)

```bash
# Levantar todos los servicios (PostgreSQL + API)
docker-compose up -d

# Ver logs
docker-compose logs -f api-web

# Detener servicios
docker-compose down
```

Base de datos estará en: `localhost:5432`
API estará en: `http://localhost:8000`

### Opción B: PostgreSQL Local + API Local

**1. Instalar PostgreSQL**
- Windows: https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql`
- Linux: `sudo apt install postgresql postgresql-contrib`

**2. Crear base de datos**
```bash
# Conectarse a PostgreSQL
psql -U postgres

# En la terminal de PostgreSQL:
CREATE USER cafe_user WITH PASSWORD 'cafe_secure_password_123';
CREATE DATABASE cafe_monitoring_db OWNER cafe_user;
GRANT ALL PRIVILEGES ON DATABASE cafe_monitoring_db TO cafe_user;
\\q
```

**3. Ejecutar script SQL**
```bash
psql -U cafe_user -d cafe_monitoring_db -f database/init.sql
```

**4. Instalar dependencias Python**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate (Windows)

pip install -r requirements.txt
```

**5. Ejecutar la API**
```bash
uvicorn app.main:app --reload
```

API estará en: `http://localhost:8000`

## 3. Validar que Todo Funciona

```bash
# Health check
curl http://localhost:8000/health

# Ver documentación Swagger
# Abrir: http://localhost:8000/docs

# Probar login (primero insert usuario en BD)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"correo":"admin@cafemonitoring.local","contrasena":"AdminPassword123"}'
```

## 4. Crear Usuario Admin en BD (Manual)

```bash
# Conectarse a la BD
psql -U cafe_user -d cafe_monitoring_db

# Insertar usuario admin (contraseña será hasheada en la app)
INSERT INTO usuarios (correo, nombre_completo, rol, estado, contrasena_hash)
VALUES (
    'admin@cafemonitoring.local',
    'Administrador del Sistema',
    'admin',
    'activo',
    '\$2b\$12\$5qPNj4R7L5qPNj4R7L5qPNj4R7L5qPNj4R7L5qPNj4R7L5qPNj4R7L'
);
```

Nota: El hash anterior es un placeholder. Para un usuario real, crear vía endpoint POST /api/v1/usuarios/

## 5. Ejecutar Migraciones Alembic

```bash
# Ver estado actual
alembic current

# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head
```

## 6. Ejecutar Tests

```bash
# Todos los tests
pytest

# Con output detallado
pytest -v

# Con cobertura
pytest --cov=app

# Solo un archivo
pytest tests/test_security.py -v
```

## 7. Endpoints Rápidos para Probar

### Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "correo": "admin@cafemonitoring.local",
  "contrasena": "AdminPassword123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "usuario_id": 1,
  "correo": "admin@cafemonitoring.local",
  "nombre_completo": "Administrador del Sistema",
  "rol": "admin"
}
```

### Usar Token en Requests Posteriores
```bash
Authorization: Bearer {access_token}
```

### Crear Usuario (Requiere Admin)
```bash
POST /api/v1/usuarios/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "correo": "supervisor@example.com",
  "nombre_completo": "Juan Pérez",
  "rol": "supervisor",
  "contrasena": "SuperPassword123"
}
```

### Listar Usuarios
```bash
GET /api/v1/usuarios/?skip=0&limit=10
Authorization: Bearer {access_token}
```

## 8. Troubleshooting

**Error: "could not translate host name 'postgres' to address"**
- Usar IP 127.0.0.1 en lugar de 'localhost' en DATABASE_URL

**Error: "permission denied for schema public"**
- Verificar que POSTGRES_USER tiene permisos: `GRANT ALL ON SCHEMA public TO cafe_user;`

**Error: "module 'app' has no attribute 'main'"**
- Asegurar que la estructura de carpetas es correcta
- Verificar que .env está en la carpeta raíz

**Base de datos lenta con Docker**
- Aumentar memoria asignada a Docker Desktop
- Usar volumen persistente en docker-compose.yml

## 9. Logs y Debugging

Los logs se escriben en stdout por defecto:

```bash
# Aumentar nivel de log
LOG_LEVEL=DEBUG

# Ver logs de SQLAlchemy
SQLALCHEMY_ECHO=True
```

Middleware de auditoría registra acciones en tabla `audit_log` (ver logs en terminal).
