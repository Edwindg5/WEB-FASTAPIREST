# Sistema Inteligente de Monitoreo del Secado de Café - API Web

## 📋 Descripción del Proyecto

Microservicio **FastAPI** desarrollado siguiendo principios de **Clean Architecture** para el sistema inteligente de monitoreo del secado de café. Consumido por frontend Angular, con soporte para roles Administrador y Supervisor.

## 🏗️ Arquitectura

Implementación de **Clean Architecture / Hexagonal** con separación clara de capas:

- **`domain/`** - Entidades puras sin dependencias de frameworks
- **`application/`** - Casos de uso, lógica de negocio, interfaces/puertos
- **`infrastructure/`** - Adaptadores concretos (DB con SQLAlchemy, repositorios, MQTT)
- **`api/`** - Routers de FastAPI, schemas Pydantic (DTOs), dependencias, middleware

## 📁 Estructura de Carpetas

```
api-web/
├── app/
│   ├── domain/
│   │   └── entities/              # Entidades de negocio puras
│   │       └── usuario.py
│   ├── application/
│   │   ├── use_cases/             # Casos de uso (lógica)
│   │   │   └── auth_use_case.py
│   │   └── interfaces/            # Puertos/Interfaces abstractas
│   │       ├── repository.py
│   │       └── usuario_repository.py
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── models/            # Modelos SQLAlchemy
│   │   │   │   └── usuario.py
│   │   │   ├── repositories/      # Implementación concreta Repository
│   │   │   │   └── usuario_repository.py
│   │   │   └── database.py        # Conexión y sesiones
│   │   └── mqtt/                  # Cliente MQTT (opcional)
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routers/           # Endpoints FastAPI
│   │   │   │   ├── auth.py
│   │   │   │   └── usuarios.py
│   │   │   └── schemas/           # DTOs Pydantic
│   │   │       ├── auth.py
│   │   │       └── usuario.py
│   │   ├── middleware/            # Middlewares
│   │   │   ├── audit.py          # Auditoría
│   │   │   └── exception_handlers.py  # Manejo centralizado de errores
│   │   └── dependencies.py        # Inyección de dependencias
│   ├── core/
│   │   ├── config.py              # Configuración (desde .env)
│   │   ├── security.py            # JWT, hashing, autenticación
│   │   └── logging.py             # Logging centralizado
│   └── main.py                    # Punto de entrada de la app
├── tests/
│   ├── conftest.py               # Fixtures pytest
│   ├── test_security.py          # Tests de seguridad
│   └── test_endpoints.py         # Tests de endpoints
├── alembic/
│   ├── env.py                    # Configuración Alembic
│   └── versions/                 # Migraciones de BD
├── database/
│   └── init.sql                  # Script SQL inicial
├── requirements.txt              # Dependencias Python
├── Dockerfile                    # Contenedor Docker
├── docker-compose.yml            # Orquestación Docker
├── .env.example                  # Plantilla de variables de entorno
├── alembic.ini                   # Configuración Alembic
└── README.md                     # Este archivo
```

## 🔐 Características de Seguridad

✅ **Autenticación JWT** con expiración configurable
- Access token: Corta duración (30 min por defecto)
- Refresh token: Larga duración (7 días)

✅ **Hashing de contraseñas** con bcrypt (passlib)

✅ **Rate limiting** con slowapi por IP y usuario autenticado

✅ **Validación estricta** de inputs con Pydantic (sin confianza en datos del cliente)

✅ **Queries parametrizadas** siempre vía SQLAlchemy ORM (NUNCA SQL con f-strings)

✅ **Middleware de auditoría** que registra acciones críticas en tabla `audit_log`

✅ **CORS restrictivo** - Solo dominio del frontend Angular

✅ **Variables sensibles** desde `.env` (NUNCA hardcodeadas)

✅ **Manejo centralizado de errores** sin exposición de stack traces

## 🚀 Inicio Rápido

### Requisitos

- Python 3.11+
- PostgreSQL 14+
- Docker y Docker Compose (opcional)

### Instalación Local

1. **Clonar y navegar al proyecto**
```bash
cd api-web
```

2. **Crear archivo `.env` desde plantilla**
```bash
cp .env.example .env
# Editar .env con valores reales
```

3. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Configurar base de datos**
```bash
# Crear BD PostgreSQL
createdb -U cafe_user cafe_monitoring_db

# Ejecutar migraciones Alembic
alembic upgrade head

# O ejecutar script SQL directamente
psql -U cafe_user -d cafe_monitoring_db -f database/init.sql
```

6. **Ejecutar aplicación**
```bash
uvicorn app.main:app --reload
```

Acceder a:
- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Con Docker Compose

```bash
docker-compose up -d
```

Verificar:
```bash
curl http://localhost:8000/health
```

## 📝 Endpoints Implementados

### Autenticación (RF-02)

- `POST /api/v1/auth/login` - Login de usuario
- `POST /api/v1/auth/refresh` - Renovar access token
- `POST /api/v1/auth/logout` - Logout

### Usuarios (RF-01)

- `POST /api/v1/usuarios/` - Crear usuario (Admin)
- `GET /api/v1/usuarios/` - Listar usuarios con paginación (Admin)
- `GET /api/v1/usuarios/{id}` - Obtener detalles usuario
- `PUT /api/v1/usuarios/{id}` - Actualizar usuario (Admin)
- `DELETE /api/v1/usuarios/{id}` - Eliminar usuario (Admin)
- `POST /api/v1/usuarios/{id}/cambiar-contrasena` - Cambiar contraseña

## 🔌 Patrón Repository

Interfaz abstracta en `application/interfaces/`, implementación concreta en `infrastructure/db/repositories/`:

```python
# Puerto (interfaz)
class IUsuarioRepository(IRepository):
    async def get_by_correo(self, correo: str) -> Optional[Usuario]:
        pass

# Adaptador (implementación)
class UsuarioRepository(IUsuarioRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
```

## 📊 Entidades (Modelos)

Creadas con SQLAlchemy ORM. Migraciones con Alembic:

- `usuarios` - Usuarios del sistema
- `sensores` - Sensores IoT
- `lotes_cafe` - Lotes en proceso de secado
- `lecturas_ambientales` - Datos de sensores
- `modelos_ml` - Modelos de ML disponibles
- `predicciones` - Predicciones generadas
- `alertas` - Alertas por anomalías
- `recomendaciones` - Recomendaciones automáticas
- `historial_eventos` - Eventos por lote
- `reportes` - Reportes generados
- `audit_log` - Auditoría de acciones

## 🧪 Tests

Tests unitarios con pytest:

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app

# Solo tests de seguridad
pytest tests/test_security.py -v

# Solo tests de endpoints
pytest tests/test_endpoints.py -v
```

## 📚 Documentación Automática

FastAPI genera documentación automática:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Todos los endpoints están documentados con docstrings que generan descripciones automáticas.

## 🔄 Migraciones de BD con Alembic

```bash
# Crear migración automática
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver estado actual
alembic current
```

## 🛠️ Variables de Entorno

Ver `.env.example` para lista completa:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/cafe_db
SECRET_KEY=tu-clave-super-secreta
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:4200
DEBUG=False
```

## 🔗 Dependencias Principales

- **fastapi** - Framework web
- **sqlalchemy** - ORM para BD
- **asyncpg** - Driver PostgreSQL async
- **pydantic** - Validación de datos
- **python-jose** - JWT tokens
- **passlib** - Hashing de contraseñas
- **slowapi** - Rate limiting
- **alembic** - Migraciones de BD
- **pytest** - Testing

Ver `requirements.txt` para versiones exactas.

## 🚢 Deployment

### Con Docker

```bash
# Build
docker build -t cafe-api:latest .

# Run
docker run -p 8000:8000 --env-file .env cafe-api:latest
```

### Con Gunicorn (producción)

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## 📞 Próximos Pasos

- [ ] Implementar entidades adicionales (RF-03+)
- [ ] WebSocket para monitoreo en tiempo real (RF-07)
- [ ] Integración con ml-service (RF-08)
- [ ] Generación de QR (RF-04)
- [ ] Reportes PDF/Excel (RF-12, RF-13, RF-14)
- [ ] Cliente MQTT para IoT
- [ ] Aumentar cobertura de tests
- [ ] Implementar rate limiting global
- [ ] Cache con Redis

## 📝 Licencia

Proyecto académico - Sistema Monitoreo Secado Café

## ✍️ Autor

Arquitecto de Software - Fast API + Clean Architecture
