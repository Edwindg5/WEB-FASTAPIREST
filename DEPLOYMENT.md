"""Guía de Deployment para Producción."""

# DEPLOYMENT - GUÍA DE PRODUCCIÓN

## 🚀 Deployment con Docker

### 1. Pre-requisitos

- Docker instalado
- Servidor Linux/Mac/Windows con Docker
- Dominio configurado (ej: api.cafemonitoring.com)
- Certificado SSL/TLS

### 2. Preparar Imagen

```bash
# Build de la imagen
docker build -t cafe-api:1.0.0 .

# Tag para registry
docker tag cafe-api:1.0.0 mi-registry.com/cafe-api:1.0.0

# Push a registry
docker push mi-registry.com/cafe-api:1.0.0
```

### 3. Deploy con Docker Compose en Producción

Crear `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always
    networks:
      - cafe_network

  api-web:
    image: cafe-api:1.0.0
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "False"
      FRONTEND_URL: https://cafemonitoring.com
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: always
    networks:
      - cafe_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api-web
    restart: always
    networks:
      - cafe_network

volumes:
  postgres_data:

networks:
  cafe_network:
    driver: bridge
```

```bash
# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f api-web

# Detener
docker-compose -f docker-compose.prod.yml down
```

### 4. Configurar Nginx (Reverse Proxy)

Crear `nginx.conf`:

```nginx
upstream api_backend {
    server api-web:8000;
}

server {
    listen 80;
    server_name cafemonitoring.com www.cafemonitoring.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cafemonitoring.com www.cafemonitoring.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Para WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://api_backend;
    }
}
```

## 🔐 Variables de Entorno en Producción

Crear `.env.production`:

```bash
# NO incluir en repositorio
# Usar solo en servidor de producción

DATABASE_URL=postgresql+asyncpg://cafe_user:PASSWORD_SEGURA@postgres:5432/cafe_monitoring_db
SECRET_KEY=CLAVE_MUY_LARGA_Y_ALEATORIA_MINIMO_32_CARACTERES
DEBUG=False
FRONTEND_URL=https://cafemonitoring.com
LOG_LEVEL=WARNING
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Email (para alertas)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@cafemonitoring.com
SMTP_PASSWORD=APP_PASSWORD

# CORS
ALLOWED_HOSTS=cafemonitoring.com,www.cafemonitoring.com
```

Cargar en el servidor:
```bash
export $(cat .env.production | xargs)
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoreo y Logging

### 1. Logs Centralizados (ELK Stack)

```yaml
# En docker-compose.prod.yml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  environment:
    discovery.type: single-node

logstash:
  image: docker.elastic.co/logstash/logstash:8.0.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
  ports:
    - "5601:5601"
```

### 2. Health Checks

```bash
# Verificar que la API está corriendo
curl https://cafemonitoring.com/health

# Monitorear con cron (cada 5 minutos)
*/5 * * * * curl -f https://cafemonitoring.com/health || systemctl restart docker
```

### 3. Alertas con DataDog/New Relic

```python
# En app/core/logging.py
import logging
from datadog import initialize, api

ddtrace.patch_all()

# Automatic metrics y tracing
```

## 🔄 CI/CD con GitHub Actions

Crear `.github/workflows/deploy.yml`:

```yaml
name: Deploy API-Web

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: |
        docker build -t cafe-api:${{ github.sha }} .
        docker tag cafe-api:${{ github.sha }} cafe-api:latest
    
    - name: Push to Docker Registry
      run: |
        echo ${{ secrets.DOCKER_REGISTRY_PASSWORD }} | docker login -u ${{ secrets.DOCKER_REGISTRY_USER }} --password-stdin
        docker push cafe-api:${{ github.sha }}
        docker push cafe-api:latest
    
    - name: Deploy to Server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SERVER_SSH_KEY }}
        script: |
          cd /apps/cafe-api
          docker-compose pull
          docker-compose up -d
          docker-compose exec -T api-web alembic upgrade head
```

## 🗄️ Backup de Base de Datos

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Backup
docker exec cafe_monitoring_db pg_dump -U cafe_user cafe_monitoring_db | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Retener solo últimos 7 días
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completado: $BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
```

Ejecutar diariamente con cron:
```bash
0 2 * * * /scripts/backup-db.sh
```

## 📈 Escalabilidad

### Load Balancing con Nginx

```nginx
upstream api_backends {
    server api-web-1:8000;
    server api-web-2:8000;
    server api-web-3:8000;
}
```

### Multiple Instances con Docker Compose

```yaml
services:
  api-web:
    image: cafe-api:1.0.0
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=...
```

## 🔍 Seguridad

### 1. Certificado SSL/TLS

```bash
# Generar con Let's Encrypt
certbot certonly --standalone -d cafemonitoring.com -d www.cafemonitoring.com

# Auto-renovar
certbot renew --quiet --no-eff-email
```

### 2. WAF (Web Application Firewall)

Con AWS CloudFront o similar:
- Protección contra SQL injection
- XSS filtering
- Rate limiting
- DDoS protection

### 3. Secrets Management

Usar Hashicorp Vault o AWS Secrets Manager:

```python
# En lugar de variables de entorno
import hvac

client = hvac.Client(url='http://vault:8200', token=os.environ['VAULT_TOKEN'])
secrets = client.secrets.kv.read_secret_version(path='cafe-api/prod')
database_url = secrets['data']['data']['database_url']
```

## 📞 Support y Troubleshooting

### Aplicación no responde

```bash
# Ver logs
docker logs cafe_api_web

# Reiniciar
docker restart cafe_api_web

# Full restart
docker-compose -f docker-compose.prod.yml restart
```

### Base de datos desconectada

```bash
# Verificar postgres
docker logs cafe_monitoring_db

# Ejecutar migraciones
docker-compose exec api-web alembic upgrade head

# Backup antes de troubleshooting
docker exec cafe_monitoring_db pg_dump -U cafe_user cafe_monitoring_db > backup.sql
```

### Memoria/CPU alta

```bash
# Ver consumo
docker stats

# Limitar recursos en compose
services:
  api-web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## ✅ Checklist Pre-Deployment

- [ ] Variables de entorno configuradas
- [ ] Base de datos migrada (alembic upgrade head)
- [ ] Certificado SSL válido
- [ ] CORS configurado correctamente
- [ ] Rate limiting activado
- [ ] Logs centralizados setup
- [ ] Backups automáticos configurados
- [ ] Health checks funcionando
- [ ] Monitorio setup (DataDog, New Relic, etc)
- [ ] Planes de fallback documentados
