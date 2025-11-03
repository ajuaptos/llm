# Docker Deployment Guide

This guide explains how to run Local-AI-RAG using Docker.

## 📋 Prerequisites

1. **Docker & Docker Compose**
   - [Install Docker Desktop](https://docs.docker.com/get-docker/)
   - Docker Compose is included with Docker Desktop

2. **Ollama** (running on host machine)
   - [Install Ollama](https://ollama.ai)
   - Start Ollama: `ollama serve`

3. **Required Models**
   ```bash
   ollama pull llama3.2:3b
   ollama pull llama3.2:1b
   ollama pull nomic-embed-text
   ```

## 🚀 Quick Start

### Using the Build Script (Recommended)

```bash
# Make script executable
chmod +x docker-build.sh

# Build and run
./docker-build.sh
```

### Using Make

```bash
# Build and start
make docker-start

# Or step by step
make docker-build
make docker-up
```

### Manual Docker Compose

```bash
# Build image
docker build -t local-ai-rag:latest .

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🏗️ Docker Architecture

```
┌─────────────────────────────────┐
│     Host Machine (macOS)        │
│                                 │
│  ┌──────────────────────────┐  │
│  │  Ollama Service          │  │
│  │  Port: 11434             │  │
│  └──────────────────────────┘  │
│              ↕                  │
│  ┌──────────────────────────┐  │
│  │  Docker Container        │  │
│  │  local-ai-rag            │  │
│  │                          │  │
│  │  - FastAPI App           │  │
│  │  - Python 3.11           │  │
│  │  - ChromaDB              │  │
│  │  Port: 8000              │  │
│  └──────────────────────────┘  │
│              ↕                  │
│  ┌──────────────────────────┐  │
│  │  Volume: ./data          │  │
│  │  - app.db (SQLite)       │  │
│  │  - chroma/ (vectors)     │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables

The Docker container uses environment variables defined in `docker-compose.yml`. To customize:

1. **Edit docker-compose.yml** directly, or
2. **Create .env file** with overrides:

```bash
# .env
GOOGLE_API_KEY=your_actual_api_key
GOOGLE_CSE_ID=your_actual_cse_id
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Connecting to Host Ollama

The container connects to Ollama on the host machine using `host.docker.internal`:

```yaml
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

This works automatically on:
- ✅ Docker Desktop (macOS)
- ✅ Docker Desktop (Windows)
- ⚠️ Linux: May need `--add-host=host.docker.internal:host-gateway`

## 📦 Volume Mounts

The application persists data in volumes:

```yaml
volumes:
  - ./data:/app/data              # Database and ChromaDB
  - ./frontend:/app/frontend      # Frontend files (dev)
```

**Data Location:**
- SQLite database: `./data/app.db`
- ChromaDB vectors: `./data/chroma/`

## 🎮 Docker Commands

### Basic Operations

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

### Container Management

```bash
# Shell access
docker exec -it local-ai-rag bash

# View container stats
docker stats local-ai-rag

# Inspect container
docker inspect local-ai-rag

# View container processes
docker top local-ai-rag
```

### Image Management

```bash
# List images
docker images | grep local-ai-rag

# Remove image
docker rmi local-ai-rag:latest

# Rebuild from scratch
docker build --no-cache -t local-ai-rag:latest .
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect aifirewall_data

# Remove volumes (deletes all data!)
docker-compose down -v
```

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs local-ai-rag

# Check if port is in use
lsof -i :8000

# Rebuild
docker-compose down
docker-compose up -d --build
```

### Cannot Connect to Ollama

```bash
# Check Ollama on host
curl http://localhost:11434/api/tags

# Test from container
docker exec -it local-ai-rag curl http://host.docker.internal:11434/api/tags

# Verify network
docker exec -it local-ai-rag cat /etc/hosts | grep host.docker.internal
```

### Permission Issues

```bash
# Fix data directory ownership
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

### Database Locked

```bash
# Stop containers
docker-compose down

# Remove database lock
rm -f ./data/app.db-wal ./data/app.db-shm

# Restart
docker-compose up -d
```

### Out of Disk Space

```bash
# Check disk usage
docker system df

# Clean unused resources
docker system prune -a

# Remove old images
docker image prune -a
```

## 🔐 Security Considerations

### Production Deployment

1. **Use secrets for sensitive data:**
   ```yaml
   secrets:
     google_api_key:
       external: true
   ```

2. **Enable HTTPS:**
   - Use reverse proxy (nginx, Traefik)
   - Add SSL certificates

3. **Limit container resources:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

4. **Run as non-root user:**
   ```dockerfile
   USER appuser
   ```

5. **Use read-only filesystem:**
   ```yaml
   read_only: true
   tmpfs:
     - /tmp
   ```

## 📊 Monitoring

### Health Checks

The container includes automatic health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

Check health status:
```bash
docker inspect --format='{{.State.Health.Status}}' local-ai-rag
```

### Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f local-ai-rag

# Save logs to file
docker-compose logs > app.log
```

## 🚀 Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml local-ai-rag

# List services
docker service ls

# Scale service
docker service scale local-ai-rag_local-ai-rag=3
```

### Using Kubernetes

Convert docker-compose to k8s:
```bash
kompose convert
```

## 🔄 Updates & Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Or with zero downtime
docker-compose up -d --no-deps --build local-ai-rag
```

### Backup Data

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz ./data

# Backup with Docker
docker run --rm -v aifirewall_data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/data-backup.tar.gz /data
```

### Restore Data

```bash
# Extract backup
tar -xzf backup-YYYYMMDD.tar.gz

# Restart containers
docker-compose restart
```

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama API endpoint |
| `OLLAMA_MAIN_MODEL` | `llama3.2:3b` | Main LLM model |
| `OLLAMA_SCOUT_MODEL` | `llama3.2:1b` | Scout model |
| `EMBEDDING_PROVIDER` | `ollama` | Embedding provider |
| `VECTOR_DB_TYPE` | `chromadb` | Vector database type |
| `FIREWALL_ENABLED` | `true` | Enable AI firewall |
| `SCOUT_ENABLED` | `true` | Enable search scout |
| `RAG_TOP_K` | `5` | Documents to retrieve |

## 🎯 Best Practices

1. **Always use volumes** for data persistence
2. **Set resource limits** in production
3. **Use health checks** for monitoring
4. **Enable logging** for debugging
5. **Regular backups** of data directory
6. **Update base images** regularly
7. **Use .dockerignore** to reduce image size
8. **Multi-stage builds** for smaller images

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
