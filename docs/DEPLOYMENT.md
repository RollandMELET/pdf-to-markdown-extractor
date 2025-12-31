# Deployment Guide (Feature #128)

## PDF-to-Markdown Extractor - Production Deployment

---

## 🐳 Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

### Quick Deploy

```bash
# Clone repository
git clone https://github.com/RollandMELET/pdf-to-markdown-extractor.git
cd pdf-to-markdown-extractor

# Create production environment file
cp .env.example .env.production
nano .env.production  # Edit with production values

# Build and start
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Check services
docker-compose -f docker-compose.prod.yml ps
```

---

## ☁️ Coolify Deployment

Coolify-compatible deployment:

1. **Create new project** in Coolify
2. **Add repository**: `https://github.com/RollandMELET/pdf-to-markdown-extractor`
3. **Select**: Docker Compose deployment
4. **Configure** environment variables
5. **Deploy**

### Environment Variables for Coolify

```env
API_PORT=8000
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
DEFAULT_EXTRACTION_STRATEGY=parallel_local

# Optional
MISTRAL_API_KEY=your-key-here
API_KEY=your-api-key-for-authentication
```

---

## 🖥️ VPS Deployment

### 1. Server Requirements

- **OS**: Ubuntu 22.04 LTS
- **RAM**: 8GB minimum
- **CPU**: 4 cores recommended
- **Disk**: 50GB
- **Ports**: 8000 (API), 8501 (Streamlit), 6379 (Redis)

### 2. Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
```

### 3. Deploy Application

```bash
# Clone repository
git clone https://github.com/RollandMELET/pdf-to-markdown-extractor.git
cd pdf-to-markdown-extractor

# Setup environment
cp .env.example .env
nano .env  # Edit configuration

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f api
```

### 4. Configure Nginx (Optional)

```nginx
server {
    listen 80;
    server_name pdf-extractor.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /streamlit {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔒 Security Configuration

### API Key Authentication (Feature #113)

```env
API_KEY=your-secure-api-key-here
```

Clients must include header:
```
X-API-Key: your-secure-api-key-here
```

### Rate Limiting (Feature #112)

Default: 10 requests/minute per IP
Configure in `src/api/routes/extraction.py`

### CORS Configuration (Feature #120)

Edit `src/api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Job Status

```bash
curl http://localhost:8000/api/v1/status/{job_id}
```

### Docker Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f redis
```

### Resource Usage

```bash
# Check container stats
docker stats pdf-extractor-api pdf-extractor-worker
```

---

## 🔄 Updates & Maintenance

### Update to Latest Version

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.prod.yml up -d --build

# Verify services
docker-compose ps
```

### Database Cleanup (Feature #127)

Old jobs are automatically cleaned after 7 days.

Manual cleanup:
```bash
docker-compose exec api python -c "
from src.core.job_tracker import JobTracker
tracker = JobTracker()
# Cleanup logic here
"
```

---

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs api

# Restart services
docker-compose restart

# Rebuild
docker-compose up -d --build
```

### High Memory Usage

- Reduce `max_workers` in parallel extraction
- Limit concurrent Celery workers
- Increase worker memory limit in docker-compose.yml

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

---

## 📈 Performance Tuning

### For High Volume

Edit `docker-compose.prod.yml`:

```yaml
worker:
  deploy:
    replicas: 3  # Scale workers
    resources:
      limits:
        memory: 8G
      reservations:
        memory: 4G
```

### For GPU Acceleration

```yaml
worker:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

## 🔗 Additional Resources

- **Docker Documentation**: https://docs.docker.com
- **Coolify**: https://coolify.io
- **Nginx**: https://nginx.org/en/docs

---

**For support, open an issue on GitHub**
