# Docker Quick Reference - Local-AI-RAG

## 🚀 Quick Start

```bash
# One-command start
./docker-build.sh

# Or with Make
make docker-start
```

## 📦 Common Commands

### Build & Run
```bash
docker build -t local-ai-rag .                    # Build image
docker-compose up -d                               # Start in background
docker-compose up                                  # Start with logs
docker-compose up -d --build                       # Rebuild and start
```

### Stop & Remove
```bash
docker-compose down                                # Stop containers
docker-compose down -v                             # Stop and remove volumes
docker-compose stop                                # Stop without removing
```

### Logs & Monitoring
```bash
docker-compose logs -f                             # Follow all logs
docker-compose logs -f local-ai-rag               # Follow app logs
docker-compose logs --tail=50                      # Last 50 lines
docker stats local-ai-rag                         # Resource usage
```

### Container Access
```bash
docker exec -it local-ai-rag bash                 # Shell access
docker exec -it local-ai-rag python               # Python REPL
docker exec local-ai-rag curl localhost:8000/health  # Test endpoint
```

### Restart & Reload
```bash
docker-compose restart                             # Restart all
docker-compose restart local-ai-rag               # Restart app only
docker-compose up -d --no-deps --build local-ai-rag  # Zero-downtime update
```

## 🔍 Debugging

### Check Status
```bash
docker ps                                          # Running containers
docker-compose ps                                  # Service status
docker inspect local-ai-rag                       # Full details
docker top local-ai-rag                           # Running processes
```

### Test Connectivity
```bash
# Test Ollama from container
docker exec local-ai-rag curl http://host.docker.internal:11434/api/tags

# Test app health
curl http://localhost:8000/health

# Check inside container
docker exec -it local-ai-rag bash
curl http://localhost:8000/health
```

### View Logs for Errors
```bash
docker-compose logs local-ai-rag | grep -i error
docker-compose logs local-ai-rag | grep -i exception
docker-compose logs --tail=100 local-ai-rag
```

## 🧹 Cleanup

```bash
# Remove containers only
docker-compose down

# Remove containers and volumes (data loss!)
docker-compose down -v

# Clean everything
docker system prune -a
docker volume prune

# Remove specific image
docker rmi local-ai-rag:latest
```

## 📊 Data Management

### Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz ./data

# Backup database only
cp ./data/app.db ./data/app.db.backup
```

### Restore
```bash
# Restore from backup
tar -xzf backup-YYYYMMDD.tar.gz
docker-compose restart
```

## 🔧 Troubleshooting

### Container won't start
```bash
docker-compose down
docker-compose up -d --build
docker-compose logs
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

### Ollama not connecting
```bash
# Check Ollama on host
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Database locked
```bash
docker-compose down
rm -f ./data/*.db-wal ./data/*.db-shm
docker-compose up -d
```

## 🎯 Make Commands

```bash
make help              # Show all commands
make docker-build      # Build image
make docker-up         # Start containers
make docker-down       # Stop containers
make docker-logs       # View logs
make docker-shell      # Open shell
make docker-restart    # Restart
make status            # Check system status
make clean-docker      # Clean Docker resources
```

## 🌐 Access Points

- **Web UI:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Stats:** http://localhost:8000/api/stats

## ⚙️ Environment Variables

Edit `.env` or `docker-compose.yml`:

```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434
GOOGLE_API_KEY=your_key
GOOGLE_CSE_ID=your_id
FIREWALL_ENABLED=true
SCOUT_ENABLED=true
```

## 📝 Notes

- **Data persists** in `./data` directory
- **Ollama must run** on host machine
- **Models required:** llama3.2:3b, llama3.2:1b, nomic-embed-text
- **Health checks** run every 30 seconds
- **Logs** available via `docker-compose logs`

## 🆘 Getting Help

```bash
docker-compose --help
docker --help
make help
```

---
**Quick Start:** `./docker-build.sh` → Open http://localhost:8000
