"""Guía de Desarrollo - Estándares y Convenciones."""

# GUÍA DE DESARROLLO

## 📋 Estándares de Código

### 1. Type Hints Obligatorios

```python
# ✅ CORRECTO
def obtener_usuario(usuario_id: int) -> Optional[Usuario]:
    """Obtiene un usuario por ID."""
    pass

async def crear_lote(db: AsyncSession, lote: LoteCafe) -> LoteCafe:
    """Crea un nuevo lote de café."""
    pass

# ❌ INCORRECTO
def obtener_usuario(usuario_id):
    pass

def crear_lote(db, lote):
    pass
```

### 2. Docstrings en Todos los Métodos Públicos

```python
def cambiar_contrasena(
    self, usuario_id: int, contrasena_actual: str, contrasena_nueva: str
) -> bool:
    """Cambia la contraseña de un usuario.
    
    Verifica la contraseña actual antes de hacer el cambio.
    
    Args:
        usuario_id: ID del usuario.
        contrasena_actual: Contraseña actual (verificación).
        contrasena_nueva: Nueva contraseña.
        
    Returns:
        True si se cambió correctamente.
        
    Raises:
        ValueError: Si contraseña actual es incorrecta.
    """
    pass
```

### 3. Nombres de Variables

```python
# ✅ Nombres claros y descriptivos
usuario_admin = ...
fecha_inicio_lote = ...
temperatura_objetivo_celsius = ...

# ❌ Nombres cortos o ambiguos
u = ...
fi = ...
temp = ...
```

### 4. Imports Organizados

```python
# Orden: stdlib, third-party, local
import os
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.domain.entities.usuario import Usuario
from app.core.security import get_current_user
```

## 🏗️ Agregar Nueva Entidad

Pasos para agregar una nueva entidad (ej: Alerta):

### 1. Domain Layer

Crear `app/domain/entities/alerta.py`:

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class TipoAlerta(str, Enum):
    TEMPERATURA_ALTA = "temperatura_alta"
    HUMEDAD_BAJA = "humedad_baja"

class SeveridadAlerta(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

@dataclass
class Alerta:
    id: Optional[int] = None
    lote_id: int = 0
    tipo: TipoAlerta = TipoAlerta.TEMPERATURA_ALTA
    severidad: SeveridadAlerta = SeveridadAlerta.MEDIA
    mensaje: str = ""
    # ... más campos
```

### 2. Infrastructure Layer - Model

Crear `app/infrastructure/db/models/alerta.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.infrastructure.db.models.usuario import Base
from app.domain.entities.alerta import TipoAlerta, SeveridadAlerta

class AlertaModel(Base):
    __tablename__ = "alertas"
    
    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lotes_cafe.id"))
    tipo = Column(Enum(TipoAlerta), nullable=False)
    # ... más columnas
```

### 3. Application Layer - Interface

Crear `app/application/interfaces/alerta_repository.py`:

```python
from abc import abstractmethod
from typing import Optional, List
from app.application.interfaces.repository import IRepository
from app.domain.entities.alerta import Alerta

class IAlerraRepository(IRepository):
    @abstractmethod
    async def get_by_lote(self, lote_id: int) -> List[Alerta]:
        pass

    @abstractmethod
    async def get_no_resueltas(self) -> List[Alerta]:
        pass
```

### 4. Infrastructure Layer - Repository

Crear `app/infrastructure/db/repositories/alerta_repository.py`:

```python
from app.application.interfaces.alerta_repository import IAlerraRepository
from app.infrastructure.db.models.alerta import AlertaModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class AlertaRepository(IAlerraRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_lote(self, lote_id: int) -> List[Alerta]:
        result = await self.db.execute(
            select(AlertaModel).where(AlertaModel.lote_id == lote_id)
        )
        return [self._map_to_domain(m) for m in result.scalars().all()]
```

### 5. Application Layer - Use Case

Crear `app/application/use_cases/alerta_use_case.py`:

```python
from app.application.interfaces.alerta_repository import IAlerraRepository

class AlertaUseCase:
    def __init__(self, alerta_repo: IAlerraRepository):
        self.alerta_repo = alerta_repo
    
    async def listar_alertas_por_lote(self, lote_id: int) -> List[Alerta]:
        return await self.alerta_repo.get_by_lote(lote_id)
```

### 6. API Layer - Schema

Crear `app/api/v1/schemas/alerta.py`:

```python
from pydantic import BaseModel
from app.domain.entities.alerta import TipoAlerta, SeveridadAlerta

class AlertaBase(BaseModel):
    lote_id: int
    tipo: TipoAlerta
    severidad: SeveridadAlerta
    mensaje: str

class AlertaCreate(AlertaBase):
    pass

class AlertaResponse(AlertaBase):
    id: int
    
    class Config:
        from_attributes = True
```

### 7. API Layer - Router

Crear `app/api/v1/routers/alertas.py`:

```python
from fastapi import APIRouter, Depends
from app.api.v1.schemas.alerta import AlertaResponse

router = APIRouter(prefix="/alertas", tags=["Alertas"])

@router.get("/{lote_id}", response_model=List[AlertaResponse])
async def listar_alertas_por_lote(
    lote_id: int,
    alerta_use_case: AlertaUseCase = Depends(get_alerta_use_case)
):
    """Lista todas las alertas de un lote."""
    return await alerta_use_case.listar_alertas_por_lote(lote_id)
```

### 8. Registrar Router en main.py

```python
# En app/main.py
from app.api.v1.routers import alertas

app.include_router(alertas.router, prefix="/api/v1")
```

### 9. Agregar Tests

Crear `tests/test_alertas.py`:

```python
import pytest
from app.domain.entities.alerta import Alerta, TipoAlerta

def test_crear_alerta():
    alerta = Alerta(
        lote_id=1,
        tipo=TipoAlerta.TEMPERATURA_ALTA,
        mensaje="Temperatura por encima de lo esperado"
    )
    assert alerta.lote_id == 1
    assert alerta.tipo == TipoAlerta.TEMPERATURA_ALTA
```

## 🧪 Testing

### Tests Unitarios

```python
# tests/test_entities.py - Testear dominio
import pytest
from app.domain.entities.usuario import Usuario, RolUsuario

def test_usuario_is_admin():
    usuario = Usuario(rol=RolUsuario.ADMIN)
    assert usuario.is_admin()
```

### Tests de Casos de Uso

```python
# tests/test_use_cases.py - Mock del repositorio
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.auth_use_case import AuthUseCase

@pytest.mark.asyncio
async def test_login_success():
    mock_repo = AsyncMock()
    mock_repo.get_by_correo.return_value = Usuario(
        id=1, correo="test@example.com", contrasena_hash="hashed"
    )
    
    auth = AuthUseCase(mock_repo)
    # Test...
```

### Tests de Endpoints (Integración)

```python
# tests/test_endpoints.py - Cliente HTTP
async def test_login_endpoint(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"correo": "admin@test.local", "contrasena": "AdminPassword123"}
    )
    assert response.status_code == 200
```

Ejecutar tests:
```bash
pytest                          # Todos
pytest -v                       # Verboso
pytest -k "test_usuario"        # Solo usuario
pytest --cov=app                # Con cobertura
```

## 📝 Commits

### Convención de Commit Messages

```
feat: Agregar endpoint de alertas
fix: Corregir validación de email
refactor: Reorganizar imports en auth.py
test: Agregar tests para usuario
docs: Actualizar README
chore: Actualizar requirements.txt

Formato: <tipo>: <descripción>

Tipos:
- feat: Nueva característica
- fix: Corregir bug
- refactor: Cambios sin afectar funcionalidad
- test: Agregar/modificar tests
- docs: Cambios en documentación
- chore: Cambios en herramientas, deps, config
```

## 🔍 Code Review Checklist

Antes de hacer PR:

- [ ] Type hints en todo el código
- [ ] Docstrings en funciones públicas
- [ ] Tests para la nueva funcionalidad
- [ ] Pasa todos los tests (pytest)
- [ ] Sin errores de linting
- [ ] Clean Architecture respetada
- [ ] Validación Pydantic utilizada
- [ ] Queries parametrizadas (nunca f-strings)
- [ ] Manejo de errores apropiado
- [ ] Variables de entorno, no hardcoded

## 🚀 Workflow Local

1. **Crear rama**
```bash
git checkout -b feat/nueva-funcionalidad
```

2. **Desarrollar con reload automático**
```bash
uvicorn app.main:app --reload
```

3. **Verificar documentación automática**
```
Abrir http://localhost:8000/docs
```

4. **Ejecutar tests**
```bash
pytest -v
```

5. **Linting (opcional pero recomendado)**
```bash
black app/
flake8 app/
```

6. **Commit y push**
```bash
git add .
git commit -m "feat: agregar nueva funcionalidad"
git push origin feat/nueva-funcionalidad
```

7. **Crear PR en GitHub**
   - Descripción clara
   - Tests incluidos
   - Screenshots si aplica

## 📚 Referencias Útiles

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [Pydantic](https://docs.pydantic.dev)
- [Python Type Hints](https://peps.python.org/pep-0586)
- [Clean Architecture](https://blog.cleancoder.com)

## 🐛 Debugging

### Logs detallados
```python
# En .env
LOG_LEVEL=DEBUG
SQLALCHEMY_ECHO=True
```

### Print debugging (temporal)
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Usuario ID: {usuario.id}")
logger.info(f"Login exitoso: {usuario.correo}")
logger.warning(f"Rate limit cerca: {rate_limit}%")
logger.error(f"Error en BD: {error}")
```

### Debugger de Python
```python
import pdb
pdb.set_trace()  # Breakpoint

# Comandos: n, s, c, l, p variable, w
```

### VSCode Debugging
Crear `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload"],
            "jinja": true
        }
    ]
}
```

## ⚠️ Errores Comunes

1. **Import circular**
   - Mover imports a nivel de función si es necesario

2. **Async/await inconsistencia**
   - Toda función async debe ser await-da
   - async def requiere async for/await

3. **Validación olvidada**
   - SIEMPRE usar Pydantic para DTO entrada
   - Nunca confiar en datos del cliente

4. **SQLAlchemy query wrong**
   - ✅ Usar `select()` con WHERE parametrizado
   - ❌ NUNCA hacer `query(f"... WHERE id = {id}")`

5. **Contraseña hasheada dos veces**
   - Hash solo al registrar/cambiar contraseña
   - Al login: hash de entrada VS hash almacenado
