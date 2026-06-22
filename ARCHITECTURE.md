"""Arquitectura Clean Architecture / Hexagonal del Sistema."""

# ARQUITECTURA - CLEAN ARCHITECTURE / HEXAGONAL

## 🎯 Principios

1. **Independencia de Frameworks** - La lógica de negocio NO depende de FastAPI, SQLAlchemy, etc.
2. **Testeable** - Cada capa puede testarse independientemente
3. **Mantenible** - Cambios en BD o API no afectan casos de uso
4. **Escalable** - Fácil agregar nuevas entidades y funcionalidades

## 📊 Flujo de Datos

```
┌─────────────┐
│   Cliente   │ (Browser Angular, etc)
│  (HTTP)     │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│    API LAYER (app/api/)              │
│  ┌────────────────────────────────┐  │
│  │  Routers (FastAPI)             │  │
│  │  - auth.py (POST /login)       │  │
│  │  - usuarios.py (GET, POST, etc)│  │
│  └────────────────┬───────────────┘  │
│                   │                   │
│  ┌────────────────▼───────────────┐  │
│  │  Schemas (Pydantic)            │  │
│  │  - UsuarioCreate (DTO entrada) │  │
│  │  - UsuarioResponse (DTO salida)│  │
│  └────────────────┬───────────────┘  │
│                   │                   │
│  ┌────────────────▼───────────────┐  │
│  │  Dependencies (FastAPI Depends)│  │
│  │  - get_current_user()          │  │
│  │  - get_auth_use_case()         │  │
│  └────────────────┬───────────────┘  │
│                   │                   │
│  ┌────────────────▼───────────────┐  │
│  │  Middleware                    │  │
│  │  - exception_handlers.py       │  │
│  │  - audit.py                    │  │
│  └────────────────┬───────────────┘  │
└────────────────┬──────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│   APPLICATION LAYER (app/application/)   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  Use Cases (Casos de Uso)        │   │
│  │  ┌────────────────────────────┐  │   │
│  │  │ AuthUseCase                │  │   │
│  │  │ - login()                  │  │   │
│  │  │ - registrar_usuario()      │  │   │
│  │  │ - cambiar_contrasena()     │  │   │
│  │  └────────────────────────────┘  │   │
│  │  ┌────────────────────────────┐  │   │
│  │  │ UsuarioUseCase             │  │   │
│  │  │ - listar_usuarios()        │  │   │
│  │  │ - obtener_usuario()        │  │   │
│  │  │ - actualizar_usuario()     │  │   │
│  │  └────────────────────────────┘  │   │
│  └──────────────────┬────────────────┘   │
│                     │                    │
│  ┌──────────────────▼────────────────┐   │
│  │  Interfaces / Puertos (Abstractas)│   │
│  │  ┌────────────────────────────┐   │   │
│  │  │ IUsuarioRepository         │   │   │
│  │  │ - get_by_id()              │   │   │
│  │  │ - get_by_correo()          │   │   │
│  │  │ - create()                 │   │   │
│  │  │ - update()                 │   │   │
│  │  │ - delete()                 │   │   │
│  │  └────────────────────────────┘   │   │
│  └──────────────────┬────────────────┘   │
└─────────────────────┼────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER (app/infrastructure/)
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  Repositories (Implementaciones) │   │
│  │  ┌────────────────────────────┐  │   │
│  │  │ UsuarioRepository          │  │   │
│  │  │ (implementa IUsuarioRepository)
│  │  │ - Usa SQLAlchemy ORM       │  │   │
│  │  │ - Queries parametrizadas   │  │   │
│  │  └────────────────────────────┘  │   │
│  └──────────────────┬────────────────┘   │
│                     │                    │
│  ┌──────────────────▼────────────────┐   │
│  │  DB Models (SQLAlchemy)          │   │
│  │  ┌────────────────────────────┐   │   │
│  │  │ UsuarioModel               │   │   │
│  │  │ - id, correo, rol, estado  │   │   │
│  │  │ - contrasena_hash          │   │   │
│  │  │ - timestamps               │   │   │
│  │  └────────────────────────────┘   │   │
│  └──────────────────┬────────────────┘   │
│                     │                    │
│  ┌──────────────────▼────────────────┐   │
│  │  Database Connection             │   │
│  │  - AsyncSession (async pool)     │   │
│  │  - SQLAlchemy Engine             │   │
│  └────────────────────────────────┘   │
└──────────────────────────────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │  PostgreSQL BD   │
            │ (RDBMS Externo)  │
            └──────────────────┘

┌──────────────────────────────────────────┐
│  DOMAIN LAYER (app/domain/)              │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  Entidades (Lógica Pura)         │   │
│  │  ┌────────────────────────────┐  │   │
│  │  │ Usuario (Dataclass)        │  │   │
│  │  │ - id, correo, nombre       │  │   │
│  │  │ - rol, estado              │  │   │
│  │  │ - métodos: is_admin()      │  │   │
│  │  │          puede_leer_lotes()│  │   │
│  │  └────────────────────────────┘  │   │
│  │  ┌────────────────────────────┐  │   │
│  │  │ Enums (Constantes)         │  │   │
│  │  │ - RolUsuario               │  │   │
│  │  │ - EstadoUsuario            │  │   │
│  │  └────────────────────────────┘  │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ⚠️ SIN dependencias de frameworks      │
│     (No importa FastAPI, SQLAlchemy)    │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  CORE LAYER (app/core/)                  │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  config.py - Settings            │   │
│  │  security.py - JWT, Hashing      │   │
│  │  logging.py - Logger             │   │
│  └──────────────────────────────────┘   │
│                                          │
│  (Compartido por todas las capas)       │
└──────────────────────────────────────────┘
```

## 📋 Ejemplo: Flujo de Login

```
1. Cliente HTTP
   POST /api/v1/auth/login
   {
     "correo": "admin@example.com",
     "contrasena": "secretpassword"
   }

2. API Layer (Pydantic valida DTO)
   api/v1/routers/auth.py::login()
   - Recibe LoginRequest validado
   - Inyecta AuthUseCase

3. Application Layer (Lógica pura)
   application/use_cases/auth_use_case.py::AuthUseCase.login()
   - Llama a repository.get_by_correo()
   - Verifica contraseña con verify_password()
   - Genera JWT con create_access_token()
   - Retorna (access_token, refresh_token, Usuario)

4. Infrastructure Layer (Adaptadores)
   infrastructure/db/repositories/usuario_repository.py::UsuarioRepository.get_by_correo()
   - Ejecuta query SQLAlchemy parametrizada
   - SELECT FROM usuarios WHERE correo = $1
   - Mapea modelo BD a entidad de dominio
   - Retorna Usuario

5. Domain Layer (Objeto puro)
   domain/entities/usuario.py::Usuario
   - Dataclass sin estado mutable
   - Solo datos y métodos de lógica pura

6. Response
   LoginResponse (Pydantic DTO salida)
   {
     "access_token": "eyJ0eXA...",
     "refresh_token": "eyJ0eXA...",
     "token_type": "bearer",
     "usuario_id": 1,
     "correo": "admin@example.com",
     "rol": "admin"
   }

   ✅ Response retorna al cliente HTTP
```

## 🔌 Inyección de Dependencias

FastAPI Depends() se usa en cada capa:

```python
# En el router (API Layer)
async def crear_usuario(
    usuario_create: UsuarioCreate,  # DTO validado por Pydantic
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),  # Inyectado
    current_user: Dict = Depends(get_current_admin_user),  # Seguridad
):
    # Usar auth_use_case (que tiene el repository inyectado)
    usuario = await auth_use_case.registrar_usuario(...)
```

FastAPI automáticamente resuelve:
- `get_auth_use_case()` → Crea `UsuarioRepository(db)` → `AuthUseCase(repo)`
- `get_db()` → Crea sesión async de la BD
- `get_current_user()` → Valida JWT del header Authorization

## 🔄 Patrones

### Repository Pattern
```
IUsuarioRepository (interfaz abstracta)
  ↑
  └─ UsuarioRepository (implementación concreta)
       ├─ async create(usuario: Usuario)
       ├─ async get_by_id(id: int)
       ├─ async get_by_correo(correo: str)
       └─ _map_to_domain(db_model) → Usuario
```

### Mapeo Bidireccional
```
DTO (Pydantic)        Entity (Domain)        Model (SQLAlchemy)
UsuarioCreate    →    Usuario    ←→    UsuarioModel
(entrada)        |    (lógica)     |    (persistencia)
                 └──────────────────┘
                 
- DTOs validados por Pydantic
- Entidades de dominio puras
- Modelos SQLAlchemy para persistencia
```

## 🔐 Seguridad en Capas

```
API Layer:
  - CORS middleware
  - HTTPException handlers
  - Validation Pydantic
  - JWT extraction
  
Application Layer:
  - Verificación de roles (is_admin())
  - Validación de reglas de negocio
  - Queries siempre parametrizadas
  
Infrastructure Layer:
  - Preparadas statements (SQLAlchemy ORM)
  - Connection pooling
  - Encrypted passwords (bcrypt)
  
Domain Layer:
  - Lógica pura sin side effects
  - Métodos de autorización
```

## 📈 Escalabilidad

Para agregar una nueva entidad (ej: Sensor):

1. **Domain**: `domain/entities/sensor.py` (Entidad pura)
2. **Infrastructure**: 
   - `infrastructure/db/models/sensor.py` (Modelo ORM)
   - `infrastructure/db/repositories/sensor_repository.py` (Implementación)
3. **Application**:
   - `application/interfaces/sensor_repository.py` (Puerto)
   - `application/use_cases/sensor_use_case.py` (Casos de uso)
4. **API**:
   - `api/v1/schemas/sensor.py` (DTOs)
   - `api/v1/routers/sensor.py` (Endpoints)

**Ventaja**: Cambio en BD de Sensor = Solo cambiar UsuarioRepository, el resto del sistema no se afecta.

## 🧪 Testing

Cada capa es testeable independientemente:

```python
# Test de Entidad (Domain)
def test_usuario_is_admin():
    usuario = Usuario(rol=RolUsuario.ADMIN)
    assert usuario.is_admin()

# Test de Casos de Uso (Application)
@pytest.mark.asyncio
async def test_login_use_case():
    mock_repo = AsyncMock(spec=IUsuarioRepository)
    auth = AuthUseCase(mock_repo)
    token, refresh, user = await auth.login(...)

# Test de Endpoints (API)
async def test_login_endpoint(client):
    response = client.post("/api/v1/auth/login", json=...)
    assert response.status_code == 200
```

## 🎯 Beneficios

✅ **Independencia de tecnología** - Cambiar de PostgreSQL a MongoDB sin tocar casos de uso
✅ **Testeable** - Mock repositorio sin necesidad de BD real
✅ **Mantenible** - Cambios localizados por capa
✅ **Reusable** - Casos de uso pueden usarse en CLI, gRPC, GraphQL, etc.
✅ **Escalable** - Fácil agregar nuevas entidades
✅ **Seguro** - Validación en cada capa
