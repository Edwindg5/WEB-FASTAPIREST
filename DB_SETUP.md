"""Guía rápida para configurar PostgreSQL local."""

# CONFIGURACIÓN POSTGRESQL LOCAL

## 1. Verificar que PostgreSQL está corriendo

En Windows:
- Abrir Services (services.msc)
- Buscar "PostgreSQL" 
- Verificar que esté "Running"

O desde PowerShell:
```powershell
# Ver status
Get-Service postgresql*

# Iniciar si está stopped
Start-Service postgresql-x64-XX
```

En Linux/Mac:
```bash
sudo systemctl status postgresql
# o
brew services list | grep postgres
```

## 2. Conectarse con psql (Terminal de PostgreSQL)

Windows (si PostgreSQL está en Program Files):
```bash
psql -U postgres -h localhost -p 5432
```

Se pedirá contraseña (la que pusiste al instalar PostgreSQL)

## 3. Crear Base de Datos

Dentro de psql:
```sql
-- Ver si existe
\l

-- Crear BD
CREATE DATABASE cafe_monitoring_db;

-- Conectarse a la nueva BD
\c cafe_monitoring_db

-- Ver tablas
\dt
```

## 4. Insertar Datos Iniciales

Ejecutar script SQL:
```bash
psql -U postgres -d cafe_monitoring_db -f database/init.sql
```

O dentro de psql:
```sql
\i database/init.sql
```

## 5. Configuración .env

```env
DATABASE_URL=postgresql://postgres:TU_CONTRASEÑA@localhost:5432/cafe_monitoring_db
```

Donde:
- `postgres` = usuario por defecto de PostgreSQL
- `TU_CONTRASEÑA` = la contraseña que pusiste al instalar
- `localhost` = tu máquina
- `5432` = puerto por defecto PostgreSQL
- `cafe_monitoring_db` = nombre de BD

## 6. Probar conexión desde Python

```bash
cd api-web
python test_db_connection.py
```

Debe mostrar:
```
✅ Conexión exitosa!
📊 PostgreSQL: PostgreSQL X.X on ...
```

## 7. Errores Comunes

**"Connection refused"**
- PostgreSQL no está corriendo
- Puerto incorrecto (5432 por defecto)

**"password authentication failed"**
- Contraseña incorrecta en .env
- Usuario incorrecto (por defecto: postgres)

**"database cafe_monitoring_db does not exist"**
- Crear BD con CREATE DATABASE cafe_monitoring_db

**"psql: command not found" (Linux/Mac)**
- PostgreSQL no instalado
- Instalar: `brew install postgresql` (Mac) o `sudo apt install postgresql` (Linux)

## 8. Interfaz Gráfica (pgAdmin)

Ya tienes abierto pgAdmin4 en las imágenes.

Conectarse a cafe_db:
1. Derecha clic en "Servers" → "Create" → "Server"
2. Name: "cafe_monitoring"
3. Connection tab:
   - Host: localhost
   - Port: 5432
   - Username: postgres
   - Password: (tu contraseña)
4. Click Save

Luego ejecutar script init.sql:
1. Abrir SQL Editor
2. Copiar contenido de database/init.sql
3. Ejecutar (F5 o botón play)

## 9. Comandos Útiles en psql

```sql
\l              -- Listar bases de datos
\dt             -- Listar tablas
\du             -- Listar usuarios/roles
\d usuarios     -- Ver estructura de tabla
\q             -- Salir
SELECT * FROM usuarios;  -- Ver datos
```
