"""Script SQL para inicialización de base de datos.

Ejecutar con:
    psql -U cafe_user -d cafe_monitoring_db -a -f database/init.sql
"""

-- Crear extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    correo VARCHAR(255) UNIQUE NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL DEFAULT 'supervisor' CHECK (rol IN ('admin', 'supervisor', 'tecnico')),
    estado VARCHAR(50) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    contrasena_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP NULL,
    INDEX idx_usuarios_correo (correo),
    INDEX idx_usuarios_rol (rol)
);

-- Tabla: sensores
CREATE TABLE IF NOT EXISTS sensores (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    tipo_sensor VARCHAR(50) NOT NULL, -- temperatura, humedad, co2, etc
    ubicacion VARCHAR(255),
    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'dañado')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sensores_codigo (codigo)
);

-- Tabla: lotes_cafe
CREATE TABLE IF NOT EXISTS lotes_cafe (
    id SERIAL PRIMARY KEY,
    codigo_qr VARCHAR(255) UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    estado VARCHAR(50) DEFAULT 'en_progreso' CHECK (estado IN ('en_progreso', 'completado', 'cancelado')),
    fecha_inicio DATE NOT NULL,
    fecha_fin_estimada DATE,
    fecha_fin_real DATE,
    temperatura_objetivo DECIMAL(5, 2),
    humedad_objetivo DECIMAL(5, 2),
    created_by INTEGER NOT NULL REFERENCES usuarios(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_lotes_codigo_qr (codigo_qr),
    INDEX idx_lotes_estado (estado)
);

-- Tabla: lecturas_ambientales
CREATE TABLE IF NOT EXISTS lecturas_ambientales (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_cafe(id),
    sensor_id INTEGER NOT NULL REFERENCES sensores(id),
    temperatura DECIMAL(6, 2),
    humedad DECIMAL(6, 2),
    co2 DECIMAL(8, 2),
    presion DECIMAL(8, 2),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_lecturas_lote (lote_id),
    INDEX idx_lecturas_timestamp (timestamp)
);

-- Tabla: modelos_ml
CREATE TABLE IF NOT EXISTS modelos_ml (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    descripcion TEXT,
    tipo_prediccion VARCHAR(50) NOT NULL, -- calidad_final, tiempo_optimo, etc
    accuracy DECIMAL(5, 4),
    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'entrenando')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_modelos_nombre (nombre)
);

-- Tabla: predicciones
CREATE TABLE IF NOT EXISTS predicciones (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_cafe(id),
    modelo_id INTEGER NOT NULL REFERENCES modelos_ml(id),
    prediccion_valor DECIMAL(8, 4),
    confianza DECIMAL(5, 4),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_predicciones_lote (lote_id)
);

-- Tabla: alertas
CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_cafe(id),
    tipo VARCHAR(50) NOT NULL, -- temperatura_alta, humedad_baja, etc
    severidad VARCHAR(50) DEFAULT 'media' CHECK (severidad IN ('baja', 'media', 'alta', 'critica')),
    mensaje TEXT NOT NULL,
    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'resuelta', 'ignorada')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_alertas_lote (lote_id),
    INDEX idx_alertas_estado (estado)
);

-- Tabla: recomendaciones
CREATE TABLE IF NOT EXISTS recomendaciones (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_cafe(id),
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    accion_recomendada TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_recomendaciones_lote (lote_id)
);

-- Tabla: historial_eventos
CREATE TABLE IF NOT EXISTS historial_eventos (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_cafe(id),
    tipo_evento VARCHAR(50) NOT NULL, -- inicio, etapa, finalizacion, etc
    descripcion TEXT,
    usuario_id INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_historial_lote (lote_id)
);

-- Tabla: reportes
CREATE TABLE IF NOT EXISTS reportes (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_cafe(id),
    tipo VARCHAR(50) NOT NULL, -- diario, final, comparativo, etc
    formato VARCHAR(10) NOT NULL, -- pdf, excel
    archivo_url VARCHAR(500),
    generado_por INTEGER NOT NULL REFERENCES usuarios(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_reportes_lote (lote_id)
);

-- Tabla: audit_log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    accion VARCHAR(255) NOT NULL,
    entidad_tipo VARCHAR(50),
    entidad_id INTEGER,
    valores_anteriores JSONB,
    valores_nuevos JSONB,
    ip_cliente VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_usuario (usuario_id),
    INDEX idx_audit_timestamp (created_at)
);

-- Índices adicionales para performance
CREATE INDEX idx_lotes_created_by ON lotes_cafe(created_by);
CREATE INDEX idx_lecturas_sensor ON lecturas_ambientales(sensor_id);
CREATE INDEX idx_predicciones_modelo ON predicciones(modelo_id);

-- Insertar usuario admin por defecto (contraseña será hasheada en la app)
-- En producción, cambiar estas credenciales
INSERT INTO usuarios (correo, nombre_completo, rol, estado, contrasena_hash)
VALUES (
    'admin@cafemonitoring.local',
    'Administrador',
    'admin',
    'activo',
    '$2b$12$7J.VJq7.6K8.K7K7K7K7KuL7K8.K7K7K7K7K7K7K7K7K7K7K7K7K7K' -- Placeholder, cambiar en BD
)
ON CONFLICT (correo) DO NOTHING;

-- Comentarios en tablas
COMMENT ON TABLE usuarios IS 'Usuarios del sistema con roles: admin, supervisor, tecnico';
COMMENT ON TABLE sensores IS 'Sensores IoT para medir temperatura, humedad, CO2, etc';
COMMENT ON TABLE lotes_cafe IS 'Lotes de cafe en proceso de secado';
COMMENT ON TABLE lecturas_ambientales IS 'Lecturas de sensores por lote y timestamp';
COMMENT ON TABLE predicciones IS 'Predicciones generadas por modelos ML';
COMMENT ON TABLE alertas IS 'Alertas generadas cuando se salen de rangos';
COMMENT ON TABLE recomendaciones IS 'Recomendaciones automaticas para el operador';
COMMENT ON TABLE historial_eventos IS 'Historial de eventos/cambios por lote';
COMMENT ON TABLE reportes IS 'Reportes generados en PDF/Excel';
COMMENT ON TABLE audit_log IS 'Log de auditoría con todas las acciones críticas';
