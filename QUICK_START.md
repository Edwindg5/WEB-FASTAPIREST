"""Guía RÁPIDA - Probar conexión a BD PostgreSQL."""

# ⚡ PRUEBA RÁPIDA - 5 MINUTOS

## PASO 1: Editar .env (ya está creado)

Abrir: `.env`

```env
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/cafe_monitoring_db
```

Reemplazar `TU_PASSWORD` con tu contraseña de PostgreSQL

## PASO 2: Verificar PostgreSQL corriendo

Windows PowerShell (como Admin):
```powershell
Get-Service postgresql*
```

Debe mostrar: `Running`

Si está "Stopped":
```powershell
Start-Service postgresql-x64-XX  # XX = versión
```

## PASO 3: Crear base de datos

Windows Command Prompt:
```bash
psql -U postgres
```

Ingresa tu contraseña de PostgreSQL

Dentro de psql:
```sql
CREATE DATABASE cafe_monitoring_db;
\c cafe_monitoring_db
\i database/init.sql
\dt
```

## PASO 4: Probar conexión desde Python

Terminal en la carpeta api-web:
```bash
python test_db_connection.py
```

Debe mostrar:
```
✅ Conexión exitosa!
📊 PostgreSQL: PostgreSQL XX on ...
```

## PASO 5: Instalar dependencias

```bash
pip install -r requirements.txt
```

## PASO 6: Ejecutar migraciones

```bash
alembic upgrade head
```

## PASO 7: Iniciar API

```bash
uvicorn app.main:app --reload
```

Debe mostrar:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## PASO 8: Probar Swagger

Abrir en navegador:
```
http://localhost:8000/docs
```

---

## ⚠️ SI FALLA LA CONEXIÓN

### Error 1: "Connection refused"
```
❌ Error: could not connect to server: Connection refused
```

**Solución:**
1. Verificar PostgreSQL corriendo (Paso 2)
2. Verificar puerto 5432 correcto
3. Verificar host: localhost

### Error 2: "password authentication failed"
```
❌ Error: password authentication failed for user "postgres"
```

**Solución:**
1. Verificar contraseña en .env DATABASE_URL
2. Probar contraseña en pgAdmin (ya abierto en tus imágenes)
3. Si olvidaste contraseña, resetear PostgreSQL

### Error 3: "database cafe_monitoring_db does not exist"
```
❌ Error: FATAL: database "cafe_monitoring_db" does not exist
```

**Solución:**
1. Ir a Paso 3: Crear base de datos
2. O usar pgAdmin para crear:
   - Right-click en "Databases"
   - Create → Database
   - Name: cafe_monitoring_db
   - Click Save
   - Ejecutar script: database/init.sql

---

## 🔧 SCRIPT AUTOMÁTICO (RECOMENDADO)

Windows PowerShell (Admin):
```powershell
.\setup.ps1
```

Hace automáticamente:
- ✅ Verifica PostgreSQL corriendo
- ✅ Crea BD si no existe
- ✅ Ejecuta script SQL
- ✅ Crea .env si falta
- ✅ Instala dependencias Python

---

## 📋 CHECKLIST ANTES DE EMPEZAR

- [ ] PostgreSQL instalado y corriendo (ver Paso 2)
- [ ] Contraseña de postgres correcta en .env
- [ ] Base de datos cafe_monitoring_db creada (ver Paso 3)
- [ ] Archivo .env con DATABASE_URL
- [ ] requirements.txt instalado (pip install -r requirements.txt)
- [ ] test_db_connection.py pasa (muestra conexión OK)
- [ ] uvicorn corriendo sin errores
- [ ] Swagger accesible en http://localhost:8000/docs

---

## 🚀 CUANDO TODO FUNCIONA

1. Swagger carga en navegador
2. Ver endpoints: /auth/login, /usuarios, etc
3. Crear tabla de prueba en pgAdmin
4. Hacer primer login

---

## 📞 CONTACTO CON BASE DE DATOS

pgAdmin 4 (ya abierto en tus imágenes):
- Host: localhost
- Port: 5432
- User: postgres
- Password: (tu contraseña)

O desde terminal:
```bash
psql -U postgres -h localhost -d cafe_monitoring_db
```

Comandos útiles:
```sql
SELECT * FROM usuarios;          -- Ver usuarios
SELECT * FROM tablas;            -- Ver todas las tablas (si existe)
\l                               -- Listar BD
\dt                              -- Listar tablas
\du                              -- Listar usuarios
```
