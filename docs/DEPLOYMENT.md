# NeuroCode Deployment Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose (for containerized deployment)
- Neo4j 5.x (or use Docker)

---

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials

# Initialize database
python ../scripts/init_database.py

# Start server
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start dev server
npm run dev
```

### Neo4j (Docker)

```bash
docker run -d \
  --name neurocode-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15-community
```

---

## Docker Compose (Recommended)

```bash
cd docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Neo4j Browser: http://localhost:7474

---

## Production Deployment

### Environment Variables

**Backend:**
```env
ENVIRONMENT=production
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secure-password>
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Frontend:**
```env
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
```

### Build Frontend

```bash
cd frontend
npm run build
# Output in dist/
```

### Run Backend with Gunicorn

```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /var/www/neurocode/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Neo4j
curl http://localhost:7474
```

---

## Troubleshooting

### Neo4j Connection Failed
- Verify Neo4j is running: `docker ps`
- Check credentials in `.env`
- Ensure port 7687 is accessible

### Frontend Build Errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 20+)

### Slow Performance
- Run benchmarks: `python scripts/benchmark.py`
- Check Neo4j memory settings
- Increase backend workers
