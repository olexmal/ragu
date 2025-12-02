# Docker Guide for RAGU

Complete guide for running RAGU using Docker Compose.

## Prerequisites

- Docker 20.10 or later
- Docker Compose 2.0 or later (or `docker compose` plugin)

Verify installation:
```bash
docker --version
docker compose version
```

## Quick Start

### Development Mode

Start all services with hot reload:
```bash
./scripts/docker-start.sh dev
```

This starts:
- Backend API (Flask dev server with hot reload)
- Frontend (Angular dev server)
- Redis (for Celery and rate limiting)
- Celery Worker (background jobs)

Access:
- Frontend: http://localhost:4200
- Backend API: http://localhost:8080

### Production Mode

Start all services in production mode:
```bash
./scripts/docker-start.sh prod
```

This starts:
- Backend API (Gunicorn with multiple workers)
- Frontend (Nginx serving built Angular app)
- Redis
- Celery Worker

Access:
- Frontend: http://localhost:80
- Backend API: http://localhost:8080

## Ollama Configuration

### Option 1: External Ollama (Default)

Use Ollama running on your host machine:

1. Ensure Ollama is running on your host
2. Start services normally:
   ```bash
   ./scripts/docker-start.sh dev
   ```
3. Configure `OLLAMA_URL` in `.env`:
   ```bash
   OLLAMA_URL=http://host.docker.internal:11434
   ```

### Option 2: Containerized Ollama

Run Ollama in a Docker container:

```bash
./scripts/docker-start.sh dev container
```

This will:
- Start Ollama container
- Pre-pull required models (mistral, nomic-embed-text)
- Configure backend to use containerized Ollama

**Note:** First run will take longer as models are downloaded.

## Service Architecture

### Core Services

1. **backend** - Flask/Gunicorn API server
   - Port: 8080
   - Health: http://localhost:8080/health

2. **redis** - Redis server for Celery and rate limiting
   - Port: 6379
   - Data persisted in `redis_data` volume

3. **celery-worker** - Background job processor
   - Processes web scraping and other async tasks
   - Connects to Redis for job queue

4. **frontend-dev** - Angular development server
   - Port: 4200
   - Hot reload enabled
   - Only active in dev mode

5. **frontend-prod** - Nginx serving built Angular app
   - Port: 80
   - Proxies `/api/*` to backend
   - Only active in prod mode

### Optional Services

6. **ollama** - Ollama LLM server (optional)
   - Port: 11434
   - Only active with `--profile with-ollama`
   - Models persisted in `ollama_data` volume

## Docker Compose Files

### Base Configuration

`docker-compose.yml` - Base configuration for all services
- Service definitions
- Volume mounts
- Network configuration
- Health checks

### Development Overrides

`docker-compose.dev.yml` - Development-specific settings
- Hot reload for backend (mounts `src/` directory)
- Development frontend service
- Debug logging enabled

### Production Overrides

`docker-compose.prod.yml` - Production-specific settings
- Gunicorn for backend
- Production frontend with Nginx
- Resource limits
- Optimized settings

## Helper Scripts

### Start Services

```bash
# Development mode
./scripts/docker-start.sh dev

# Production mode
./scripts/docker-start.sh prod

# With containerized Ollama
./scripts/docker-start.sh dev container
```

### Stop Services

```bash
./scripts/docker-stop.sh
```

### View Logs

```bash
# All services
./scripts/docker-logs.sh

# Specific service
./scripts/docker-logs.sh backend

# Follow logs
./scripts/docker-logs.sh backend -f
```

### Reset Everything

**WARNING:** This deletes all data volumes!

```bash
./scripts/docker-reset.sh
```

## Environment Variables

Create `.env` file from template:
```bash
cp .env.docker .env
```

Key variables:
- `OLLAMA_URL` - Ollama server URL
- `REDIS_URL` - Redis connection string
- `FLASK_DEBUG` - Enable debug mode (True/False)
- `USE_REDIS_RATE_LIMITING` - Use Redis for rate limiting (true/false)

## Data Persistence

All data is persisted in Docker volumes:

- `chroma_data` - ChromaDB vector database
- `redis_data` - Redis data
- `logs` - Application logs
- `rag_settings` - Application settings
- `rag_cache` - Query cache data
- `rag_history` - Query history data
- `rag_monitoring` - Monitoring and analytics data
- `ollama_data` - Ollama models (if containerized)
- `temp_files` - Temporary upload files

Volumes persist across container restarts. To remove all data, use `./scripts/docker-reset.sh`.

## Manual Docker Compose Commands

### Start Services

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up -d

# With Ollama
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev --profile with-ollama up
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Rebuild Images

```bash
# Rebuild all
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache backend
```

### Scale Services

```bash
# Scale backend workers (production)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up -d --scale backend=3

# Scale Celery workers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up -d --scale celery-worker=2
```

## Troubleshooting

### Services Won't Start

1. Check Docker is running:
   ```bash
   docker ps
   ```

2. Check port availability:
   ```bash
   # Linux/Mac
   lsof -i :8080
   
   # Windows
   netstat -ano | findstr :8080
   ```

3. View service logs:
   ```bash
   ./scripts/docker-logs.sh backend
   ```

### Backend Can't Connect to Redis

1. Check Redis is running:
   ```bash
   docker-compose ps redis
   ```

2. Check Redis logs:
   ```bash
   ./scripts/docker-logs.sh redis
   ```

3. Verify `REDIS_URL` in `.env`:
   ```bash
   REDIS_URL=redis://redis:6379/0
   ```

### Frontend Can't Connect to Backend

1. Check backend is running:
   ```bash
   curl http://localhost:8080/health
   ```

2. Verify CORS settings in backend
3. Check nginx configuration (production mode)

### Ollama Connection Issues

**External Ollama:**
1. Ensure Ollama is running on host:
   ```bash
   ollama list
   ```

2. Use `host.docker.internal` for Docker Desktop:
   ```bash
   OLLAMA_URL=http://host.docker.internal:11434
   ```

3. For Linux, may need to use host IP:
   ```bash
   OLLAMA_URL=http://172.17.0.1:11434
   ```

**WSL2 with Ollama:**

If running Ollama in WSL2 (not Windows), Docker containers can't reach `localhost:11434` directly. You need to configure Ollama to listen on all interfaces:

1. Run the configuration script:
   ```bash
   ./scripts/configure-ollama-wsl.sh
   ```

2. Find your WSL IP address:
   ```bash
   ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
   ```

3. Update `.env` with your WSL IP:
   ```bash
   OLLAMA_BASE_URL=http://172.20.x.x:11434
   ```

4. Restart containers:
   ```bash
   docker compose restart backend celery-worker
   ```

See [QUICKSTART.md](../QUICKSTART.md#configuring-ollama-in-wsl-for-docker-containers) for detailed instructions.

**Containerized Ollama:**
1. Check Ollama container is running:
   ```bash
   docker-compose ps ollama
   ```

2. Check Ollama logs:
   ```bash
   ./scripts/docker-logs.sh ollama
   ```

3. Verify models are pulled:
   ```bash
   docker-compose exec ollama ollama list
   ```

### Volume Permission Issues

If you encounter permission errors with volumes:

```bash
# Fix ownership (Linux)
sudo chown -R $USER:$USER chroma logs .rag_settings

# Or run containers with your user ID
docker-compose run --user $(id -u):$(id -g) backend
```

## Development Workflow

### Hot Reload

In development mode, code changes are automatically reloaded:

- **Backend**: Flask dev server reloads on Python file changes
- **Frontend**: Angular dev server reloads on TypeScript/HTML changes

### Debugging

1. Attach to running container:
   ```bash
   docker-compose exec backend bash
   ```

2. View real-time logs:
   ```bash
   ./scripts/docker-logs.sh -f
   ```

3. Check service health:
   ```bash
   curl http://localhost:8080/health
   ```

## Production Deployment

### Build Images

```bash
# Build all images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Build specific service
docker-compose build frontend-prod
```

### Start Production Services

```bash
./scripts/docker-start.sh prod
```

### Update Services

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up -d --build
```

### Backup Data

```bash
# Backup ChromaDB
docker run --rm -v ragu_chroma_data:/data -v $(pwd):/backup alpine tar czf /backup/chroma_backup.tar.gz /data

# Backup Redis
docker run --rm -v ragu_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data
```

### Restore Data

```bash
# Restore ChromaDB
docker run --rm -v ragu_chroma_data:/data -v $(pwd):/backup alpine tar xzf /backup/chroma_backup.tar.gz -C /

# Restore Redis
docker run --rm -v ragu_redis_data:/data -v $(pwd):/backup alpine tar xzf /backup/redis_backup.tar.gz -C /
```

## Integration with Scalability Phases

Phase 0 (Docker) provides the foundation for all scalability improvements:

- **Phase 1**: Redis and Celery already containerized
- **Phase 2**: Easy to add more services (monitoring, caching)
- **Phase 3**: Load balancing with multiple backend instances

See [docs/SCALABILITY_ROADMAP.md](docs/SCALABILITY_ROADMAP.md) for details.

## Best Practices

1. **Use volumes for persistence**: Never store data in containers
2. **Set resource limits**: Use `docker-compose.prod.yml` for production
3. **Regular backups**: Backup volumes before major updates
4. **Monitor logs**: Use `docker-logs.sh` to monitor service health
5. **Health checks**: All services have health check endpoints
6. **Environment variables**: Use `.env` file for configuration
7. **Separate dev/prod**: Use different compose files for different environments

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [RAGU Scalability Roadmap](docs/SCALABILITY_ROADMAP.md)
- [RAGU Developer Guide](docs/DEVELOPER_GUIDE.md)

