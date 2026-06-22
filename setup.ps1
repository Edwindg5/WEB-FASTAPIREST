# Script PowerShell para configurar PostgreSQL y la BD
# Ejecutar como Administrador: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🚀 CONFIGURADOR - Sistema Monitoreo Café" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar PostgreSQL
Write-Host "1️⃣  Verificando PostgreSQL..." -ForegroundColor Yellow
$pgService = Get-Service postgresql* -ErrorAction SilentlyContinue

if ($pgService) {
    Write-Host "   ✅ Servicio PostgreSQL encontrado: $($pgService.Name)" -ForegroundColor Green
    
    if ($pgService.Status -eq "Running") {
        Write-Host "   ✅ PostgreSQL está CORRIENDO" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  PostgreSQL NO está corriendo. Iniciando..." -ForegroundColor Yellow
        Start-Service $pgService.Name
        Start-Sleep -Seconds 3
        Write-Host "   ✅ PostgreSQL iniciado" -ForegroundColor Green
    }
} else {
    Write-Host "   ❌ PostgreSQL no encontrado" -ForegroundColor Red
    Write-Host "   📦 Instalar desde: https://www.postgresql.org/download/windows/" -ForegroundColor Cyan
    exit
}

Write-Host ""

# 2. Probar conexión psql
Write-Host "2️⃣  Probando conexión a PostgreSQL..." -ForegroundColor Yellow

try {
    # Buscar psql
    $psqlPath = (Get-Command psql -ErrorAction SilentlyContinue).Source
    if (-not $psqlPath) {
        $psqlPath = "C:\Program Files\PostgreSQL\15\bin\psql.exe"
    }
    
    if (Test-Path $psqlPath) {
        Write-Host "   ✅ psql encontrado en: $psqlPath" -ForegroundColor Green
        
        # Test simple
        $result = & $psqlPath -U postgres -h localhost -c "SELECT version();" 2>&1
        
        if ($result -match "PostgreSQL") {
            Write-Host "   ✅ Conexión a PostgreSQL OK" -ForegroundColor Green
            Write-Host "   📊 $($result[2])" -ForegroundColor Gray
        } else {
            Write-Host "   ⚠️  No se pudo conectar" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  psql no encontrado en ruta estándar" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Error al probar conexión" -ForegroundColor Yellow
}

Write-Host ""

# 3. Crear BD si no existe
Write-Host "3️⃣  Verificando base de datos cafe_monitoring_db..." -ForegroundColor Yellow

try {
    $dbCheck = & $psqlPath -U postgres -h localhost -c "\l" 2>&1 | Select-String "cafe_monitoring_db"
    
    if ($dbCheck) {
        Write-Host "   ✅ BD cafe_monitoring_db ya existe" -ForegroundColor Green
    } else {
        Write-Host "   🔄 Creando BD cafe_monitoring_db..." -ForegroundColor Cyan
        & $psqlPath -U postgres -h localhost -c "CREATE DATABASE cafe_monitoring_db;" 2>&1
        Write-Host "   ✅ BD creada" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error al crear BD" -ForegroundColor Red
}

Write-Host ""

# 4. Ejecutar script SQL
Write-Host "4️⃣  Ejecutando script de inicialización SQL..." -ForegroundColor Yellow

$sqlScript = "database\init.sql"
if (Test-Path $sqlScript) {
    try {
        & $psqlPath -U postgres -d cafe_monitoring_db -h localhost -f $sqlScript 2>&1 | Select-Object -Last 5 | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        Write-Host "   ✅ Script SQL ejecutado" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Error ejecutando script: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Script no encontrado: $sqlScript" -ForegroundColor Red
}

Write-Host ""

# 5. Verificar archivo .env
Write-Host "5️⃣  Verificando archivo .env..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "   ✅ Archivo .env existe" -ForegroundColor Green
    
    # Mostrar DATABASE_URL
    $dbUrl = Get-Content ".env" | Select-String "DATABASE_URL"
    Write-Host "   📋 $dbUrl" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Archivo .env no existe" -ForegroundColor Yellow
    Write-Host "   🔄 Creando .env desde .env.example..." -ForegroundColor Cyan
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "   ✅ .env creado" -ForegroundColor Green
    } else {
        Write-Host "   ❌ .env.example no encontrado" -ForegroundColor Red
    }
}

Write-Host ""

# 6. Instalar dependencias Python (opcional)
Write-Host "6️⃣  Python y dependencias..." -ForegroundColor Yellow

$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Python instalado: $pythonCheck" -ForegroundColor Green
    
    Write-Host "   🔄 Instalando requirements..." -ForegroundColor Cyan
    python -m pip install -r requirements.txt --quiet 2>&1 | Out-Null
    Write-Host "   ✅ Dependencias instaladas" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python no instalado" -ForegroundColor Red
    Write-Host "   📦 Descargar de: https://www.python.org" -ForegroundColor Cyan
}

Write-Host ""

# 7. Resumen final
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-Host ""
Write-Host "🚀 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Probar conexión BD:" -ForegroundColor Yellow
Write-Host "   python test_db_connection.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  Iniciar la API:" -ForegroundColor Yellow
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  Acceder a documentación:" -ForegroundColor Yellow
Write-Host "   http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "4️⃣  Consultar BD (pgAdmin):" -ForegroundColor Yellow
Write-Host "   http://localhost:5050" -ForegroundColor Gray
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
