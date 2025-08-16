# Deployment Guide - Customer Feedback Dashboard

## Overview

Panduan lengkap untuk deploy Customer Feedback Dashboard ke production dengan berbagai pilihan platform.

## Prerequisites

- Docker & Docker Compose
- Domain dan SSL certificate
- Accounts untuk:
  - Supabase (database)
  - HuggingFace (sentiment analysis)
  - IBM Watson NLU (entity extraction)
  - Replicate (IBM Granite model)
  - IBM Orchestrate (automation)

## Platform Options

### 1. Railway (Recommended)

Railway menyediakan deploy yang mudah dengan PostgreSQL managed database.

#### Setup Database

1. Create new project di Railway
2. Add PostgreSQL service
3. Copy connection string

#### Deploy Backend

1. Fork repository
2. Connect Railway ke GitHub repo
3. Add environment variables:
   ```
   DATABASE_URL=postgresql://...
   SUPABASE_URL=...
   HUGGINGFACE_API_TOKEN=...
   # ... other env vars
   ```
4. Deploy akan otomatis

#### Deploy Frontend

1. Add new service untuk frontend
2. Set build command: `npm run build`
3. Set start command: `npm run preview`
4. Add environment variables:
   ```
   VITE_BACKEND_URL=https://your-backend.railway.app
   VITE_SUPABASE_URL=...
   ```

### 2. Fly.io

#### Preparation

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login
```

#### Backend Deployment

```bash
cd backend

# Create fly.toml
cat > fly.toml << EOF
app = "cfd-backend"

[build]
  dockerfile = "Dockerfile"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

[env]
  PORT = "8000"
EOF

# Deploy
flyctl deploy
```

#### Frontend Deployment

```bash
cd frontend

# Create fly.toml
cat > fly.toml << EOF
app = "cfd-frontend"

[build]
  dockerfile = "Dockerfile.prod"

[[services]]
  http_checks = []
  internal_port = 3000
  processes = ["app"]
  protocol = "tcp"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
EOF

# Deploy
flyctl deploy
```

### 3. DigitalOcean App Platform

#### Setup

1. Create new app dari GitHub
2. Configure services:
   - Backend: Python service
   - Frontend: Static site
   - Database: Managed PostgreSQL

#### Environment Configuration

Set di App Platform dashboard:

```
SUPABASE_URL=...
HUGGINGFACE_API_TOKEN=...
# ... other variables
```

### 4. VPS Manual Deployment

#### Server Setup (Ubuntu 20.04+)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

#### Application Setup

```bash
# Clone repository
git clone https://github.com/your-username/customer-feedback-dashboard.git
cd customer-feedback-dashboard

# Setup environment
cp env.example .env
# Edit .env with production values

# Build and start
docker-compose -f docker-compose.prod.yml up -d
```

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/cfd
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cfd /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL
sudo certbot --nginx -d yourdomain.com
```

## Production Configuration

### Environment Variables

```bash
# Production .env
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-production-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-production-service-key

# Security
BACKEND_SECRET_KEY=very-secure-random-key-change-this
RATE_LIMIT_PER_MINUTE=30

# AI Services
HUGGINGFACE_API_TOKEN=your-production-token
IBM_WATSON_NLU_API_KEY=your-production-key
REPLICATE_API_TOKEN=your-production-token
IBM_ORCHESTRATE_API_KEY=your-production-key

# Redis (for production)
REDIS_URL=redis://your-redis-instance:6379
```

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    restart: unless-stopped
    depends_on:
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### Production Dockerfiles

#### Backend Production Dockerfile

```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### Frontend Production Dockerfile

```dockerfile
# frontend/Dockerfile.prod
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

FROM nginx:alpine

# Copy build files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

#### Nginx Configuration for Frontend

```nginx
# frontend/nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 3000;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Enable gzip compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

        # Handle client-side routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }
}
```

## Database Setup

### Supabase Production Setup

1. Create production project di Supabase
2. Run database schema:
   ```sql
   -- Copy content from database/schema.sql
   ```
3. Configure RLS policies
4. Setup environment variables

### Migration Strategy

```bash
# Create migration script
cat > migrate.sql << EOF
-- Add any schema changes here
ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS source_metadata JSONB DEFAULT '{}';
-- ...
EOF

# Apply migration via Supabase SQL editor or CLI
```

## Monitoring & Logging

### Application Monitoring

```bash
# Setup monitoring with Docker
docker-compose -f docker-compose.monitoring.yml up -d
```

### Logging Configuration

```python
# backend/logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('app.log', maxBytes=10000000, backupCount=5),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

### Health Checks

```bash
# Setup health check monitoring
curl -f https://yourdomain.com/api/health || alert_system
```

## Security Checklist

### SSL/TLS

- [ ] SSL certificate installed and configured
- [ ] HTTPS redirect enabled
- [ ] HSTS header configured

### Application Security

- [ ] Environment variables secured
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] CSP headers implemented
- [ ] Input validation in place

### Database Security

- [ ] RLS policies enabled
- [ ] Database credentials secured
- [ ] Connection encryption enabled

### API Security

- [ ] JWT tokens properly secured
- [ ] API rate limiting enabled
- [ ] Request validation implemented

## Backup Strategy

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Supabase backup via pg_dump
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$DATE.sql

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/backup_$DATE.sql s3://your-backup-bucket/
```

### Application Backup

- Code: Git repository backup
- Environment: Secure environment variables backup
- Logs: Log rotation and archive

## Performance Optimization

### Backend Optimization

```python
# Add to main.py
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Frontend Optimization

- Enable gzip compression
- Implement code splitting
- Optimize images and assets
- Use CDN for static assets

### Database Optimization

- Index optimization
- Query optimization
- Connection pooling

## Scaling Considerations

### Horizontal Scaling

- Load balancer configuration
- Multiple backend instances
- Redis clustering for session storage

### Vertical Scaling

- CPU and memory optimization
- Database performance tuning

### Auto-scaling

```yaml
# Kubernetes example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cfd-backend
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cfd-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**

   ```bash
   # Check connection
   docker-compose logs backend | grep -i database
   ```

2. **API Rate Limiting**

   ```bash
   # Check Redis
   docker-compose exec redis redis-cli monitor
   ```

3. **Frontend Build Issues**
   ```bash
   # Clear cache and rebuild
   docker-compose build --no-cache frontend
   ```

### Debugging Commands

```bash
# View logs
docker-compose logs -f [service]

# Shell access
docker-compose exec [service] /bin/bash

# Database access
docker-compose exec postgres psql -U username -d database

# Redis access
docker-compose exec redis redis-cli
```

## Rollback Strategy

### Quick Rollback

```bash
# Rollback to previous version
git checkout previous-stable-tag
docker-compose down
docker-compose up -d
```

### Database Rollback

```bash
# Restore from backup
psql $DATABASE_URL < backup_file.sql
```

---

Untuk support lebih lanjut, silakan buka issue di repository atau kontak tim development.
