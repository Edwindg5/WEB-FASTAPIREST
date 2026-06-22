"""Índice de Documentación del Proyecto."""

# 📚 ÍNDICE DE DOCUMENTACIÓN

## 🚀 Comenzar Aquí

1. **[README.md](README.md)** - Descripción general del proyecto, características, endpoints implementados
2. **[SETUP.md](SETUP.md)** - Guía rápida para levantar el proyecto localmente

## 🏗️ Arquitectura y Diseño

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Explicación detallada de Clean Architecture, flujo de datos, patrones
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Estándares de código, cómo agregar nuevas entidades, workflow

## 💻 Uso de la API

- **[EJEMPLOS_API.md](EJEMPLOS_API.md)** - Ejemplos completos de todos los endpoints (curl, Angular, etc)

## 🚢 Deployment

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guía completa para producción (Docker, Nginx, CI/CD, monitoreo)

## 📁 Estructura del Proyecto

```
api-web/
├── README.md                 ← Comienza aquí
├── ARCHITECTURE.md           ← Entiende el diseño
├── SETUP.md                  ← Configuración local
├── DEVELOPMENT.md            ← Estándares y cómo extender
├── DEPLOYMENT.md             ← Deploy a producción
├── EJEMPLOS_API.md           ← Ejemplos de uso
├── .env.example              ← Variables de entorno
├── requirements.txt          ← Dependencias Python
├── Dockerfile                ← Imagen Docker
├── docker-compose.yml        ← Stack completo
├── alembic.ini              ← Config migraciones
├── app/
│   ├── main.py              ← Punto de entrada FastAPI
│   ├── domain/
│   │   └── entities/        ← Entidades puras del negocio
│   ├── application/
│   │   ├── use_cases/       ← Lógica de negocio
│   │   └── interfaces/      ← Puertos abstractos
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── models/      ← Modelos SQLAlchemy
│   │   │   ├── repositories/← Adaptadores concretos
│   │   │   └── database.py  ← Conexión BD
│   │   └── mqtt/            ← Cliente IoT (opcional)
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routers/     ← Endpoints FastAPI
│   │   │   └── schemas/     ← DTOs Pydantic
│   │   └── middleware/      ← Auditoría, errores
│   └── core/
│       ├── config.py        ← Configuración
│       ├── security.py      ← JWT, hashing
│       └── logging.py       ← Logs
├── tests/
│   ├── test_security.py     ← Tests unitarios
│   ├── test_endpoints.py    ← Tests integración
│   └── conftest.py          ← Fixtures pytest
└── database/
    └── init.sql             ← Script SQL inicial
```

## 🎯 Endpoints Disponibles

### Autenticación (RF-02)
- `POST /api/v1/auth/login` - Login con JWT
- `POST /api/v1/auth/refresh` - Renovar access token
- `POST /api/v1/auth/logout` - Logout

### Usuarios (RF-01)
- `POST /api/v1/usuarios/` - Crear usuario (Admin)
- `GET /api/v1/usuarios/` - Listar usuarios (Admin, paginado)
- `GET /api/v1/usuarios/{id}` - Obtener usuario específico
- `PUT /api/v1/usuarios/{id}` - Actualizar usuario (Admin)
- `DELETE /api/v1/usuarios/{id}` - Eliminar usuario (Admin)
- `POST /api/v1/usuarios/{id}/cambiar-contrasena` - Cambiar contraseña

## 🔐 Seguridad Implementada

✅ Autenticación JWT (access + refresh tokens)
✅ Hashing bcrypt para contraseñas
✅ Validación Pydantic en todos los inputs
✅ Queries parametrizadas (SQLAlchemy ORM)
✅ Middleware de auditoría
✅ CORS restrictivo
✅ Exception handlers centralizados
✅ Rate limiting ready (slowapi)
✅ Type hints obligatorios

## 📊 Tablas de Base de Datos

Creadas con SQLAlchemy + SQL init script:

| Tabla | Descripción | Estado |
|-------|-------------|--------|
| usuarios | Usuarios del sistema | ✅ Completa |
| sensores | Sensores IoT | Ready |
| lotes_cafe | Lotes en secado | Ready |
| lecturas_ambientales | Datos de sensores | Ready |
| modelos_ml | Modelos ML disponibles | Ready |
| predicciones | Predicciones generadas | Ready |
| alertas | Alertas por anomalías | Ready |
| recomendaciones | Recomendaciones automáticas | Ready |
| historial_eventos | Eventos por lote | Ready |
| reportes | Reportes PDF/Excel | Ready |
| audit_log | Auditoría de acciones | Ready |

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app

# Específicos
pytest tests/test_security.py -v
pytest tests/test_endpoints.py -v
```

## 🚀 Quick Start

```bash
# 1. Clonary instalar
cd api-web
pip install -r requirements.txt

# 2. Variables de entorno
cp .env.example .env
# Editar .env con valores reales

# 3. Base de datos
# Opción A: Docker
docker-compose up -d

# Opción B: PostgreSQL local
psql -U postgres -c "CREATE USER cafe_user WITH PASSWORD 'secure';"
psql -U postgres -c "CREATE DATABASE cafe_monitoring_db OWNER cafe_user;"
psql -U cafe_user -d cafe_monitoring_db -f database/init.sql

# 4. Ejecutar API
uvicorn app.main:app --reload

# 5. Acceder a documentación
# http://localhost:8000/docs
```

## 📖 Pasos Siguientes

### Para continuar el desarrollo:

1. **Implementar más entidades** (siguiendo el patrón en DEVELOPMENT.md)
   - Sensores (RF-15)
   - Lotes (RF-03)
   - Lecturas ambientales

2. **Agregar funcionalidades avanzadas**
   - QR (RF-04, RF-05)
   - WebSocket para RT (RF-07)
   - Integración ML (RF-08)
   - Reportes PDF/Excel (RF-12, RF-13, RF-14)

3. **Aumentar cobertura de tests**
   - Tests para cada nuevo use case
   - Tests de integración end-to-end

4. **Deployment**
   - Configurar en servidor usando DEPLOYMENT.md
   - Setup de CI/CD con GitHub Actions

## 🔗 Links Útiles

- [FastAPI Official Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [Pydantic](https://docs.pydantic.dev)
- [Python Async](https://docs.python.org/3/library/asyncio.html)
- [Clean Architecture](https://blog.cleancoder.com)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

## ❓ FAQs

**P: ¿Por qué Clean Architecture?**
R: Permite cambiar DB, framework o agregar nuevos adaptadores sin afectar la lógica de negocio. Facilita testing y mantenimiento a largo plazo.

**P: ¿Por qué async?**
R: Mejor performance bajo carga. Uvicorn maneja múltiples conexiones concurrentes eficientemente.

**P: ¿Cómo agregar una nueva entidad?**
R: Ver DEVELOPMENT.md - sección "Agregar Nueva Entidad". Seguir los 8 pasos: Domain → Infrastructure → Application → API.

**P: ¿Dónde pongo lógica de negocio?**
R: En use_cases (application layer), NO en routers. Los routers solo orquestan.

**P: ¿Por qué no usar SQL puro?**
R: SQLAlchemy ORM previene SQL injection, proporciona type safety y es agnóstico a la BD.

## 📞 Soporte

- Revisar documentación completa en archivos .md
- Ver ejemplos en EJEMPLOS_API.md
- Troubleshooting en DEPLOYMENT.md

## ✅ Checklist Implementación

- [x] Estructura Clean Architecture
- [x] Autenticación JWT
- [x] CRUD Usuarios
- [x] Exception handlers
- [x] Middleware auditoría
- [x] Tests básicos
- [x] Documentación completa
- [x] Docker setup
- [x] Alembic migrations
- [ ] Más entidades (RF-03+)
- [ ] WebSocket (RF-07)
- [ ] QR (RF-04, RF-05)
- [ ] Reportes (RF-12+)
- [ ] Integración ML (RF-08)
