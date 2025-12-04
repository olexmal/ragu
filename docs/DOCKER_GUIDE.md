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

```bash
cd java-backend
./mvnw clean package -DskipTests
cd ..
docker compose up --build backend redis frontend-dev
```

Access:
- Frontend: http://localhost:4200
- Backend API: http://localhost:8080

### Production Mode

```bash
cd java-backend
./mvnw clean package -DskipTests
cd ..
docker compose up --build backend frontend-prod redis -d
```

Access:
- Frontend: http://localhost:80
- Backend API: http://localhost:8080

## Ollama Configuration

### Option 1: External Ollama (Default)

Use Ollama running on your host machine:

1. Ensure Ollama is running on your host
2. Configure `OLLAMA_URL` (or `OLLAMA_BASE_URL`) in `.env`:
   ```bash
   OLLAMA_URL=http://host.docker.internal:11434   # macOS/Windows
   OLLAMA_URL=http://172.17.0.1:11434             # Linux Docker bridge
   ```

### Option 2: Containerized Ollama

Run Ollama in a Docker container:

```bash
docker compose --profile with-ollama up
```

This will:
- Start Ollama container
- Pre-pull required models (mistral, nomic-embed-text)
- Configure backend to use containerized Ollama

**Note:** First run will take longer as models are downloaded.

## Service Architecture

### Core Services

1. **backend** - Quarkus JVM API server
   - Port: 8080
   - Health: http://localhost:8080/health

2. **redis** - Redis server (required)
   - Port: 6379
   - Data persisted in `redis_data` volume
   - Used for: sessions, settings storage, query history, favorites, rate limiting, and embedding cache

3. **frontend-dev** - Angular development server
   - Port: 4200
   - Hot reload enabled
   - Only active in dev mode

4. **frontend-prod** - Nginx serving built Angular app
   - Port: 80
   - Proxies `/api/*` to backend
   - Only active in prod mode

5. **ollama** (optional profile `with-ollama`)
   - Port: 11434
   - Only active with `--profile with-ollama`
   - Models persisted in `ollama_data` volume

## Observability & Monitoring

### Built-in Endpoints

- **Liveness/Readiness**: `http://localhost:8080/q/health` (includes `/ready` and `/live` sub-paths)
- **Metrics (Micrometer/Prometheus)**: `http://localhost:8080/q/metrics`
- **Structured Logs**: Enabled by default (`quarkus.log.console.json=true`). Override via `LOG_JSON=false` or change verbosity with `LOG_LEVEL=DEBUG`.

You can validate locally:

```bash
curl http://localhost:8080/q/health/ready | jq
curl http://localhost:8080/q/metrics | head
docker compose logs -f backend | jq .
```

### Optional Prometheus & Loki Stack

Add the following services to `docker-compose.yml` (or a secondary compose file) to capture metrics and logs:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./ops/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
    profiles: ["monitoring"]

  loki:
    image: grafana/loki:2.9.5
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    profiles: ["monitoring"]
```

Sample `ops/prometheus.yml`:

```yaml
global:
  scrape_interval: 10s
scrape_configs:
  - job_name: "ragu-backend"
    static_configs:
      - targets: ["backend:8080"]
```

Then launch everything:

```bash
docker compose --profile monitoring up prometheus loki
```

Grafana can be layered on top (point it at `http://localhost:9090` for Prometheus and `http://localhost:3100` for Loki).

## Docker Compose Files

All services are defined in `docker-compose.yml`. Profiles are used for optional services (e.g., `--profile with-ollama`). Development vs production behavior is controlled by the targets you `docker compose up` (e.g., `frontend-dev` vs `frontend-prod`) and the environment variables you pass.

## Helper Commands

- Start dev stack: `docker compose up --build backend redis frontend-dev`
- Start prod stack: `docker compose up --build backend frontend-prod redis -d`
- Include Ollama container: `docker compose --profile with-ollama up`
- Stop all services: `docker compose down`
- Tail logs: `docker compose logs -f backend`

## Environment Variables

Create `.env` file from template:
```bash
cp .env.docker .env
```

Key variables:

**Dependencies:**
- `OLLAMA_BASE_URL` - Ollama server URL (default `http://host.docker.internal:11434`)
- `REDIS_URL` - Redis connection string (default `redis://redis:6379/0`)
- `QDRANT_URL` - Qdrant vector database URL (default `http://qdrant:6333`)

**Authentication & Sessions:**
- `AUTH_ENABLED` - Enable authentication (default `false`)
- `AUTH_USERNAME` / `AUTH_PASSWORD` - Basic auth credentials
- `AUTH_API_KEY` - API key for authentication
- `SESSION_TTL_MINUTES` - Session timeout in minutes (default `1440` = 24 hours)
- `SESSION_COOKIE_NAME` - Session cookie name (default `RAGU_SESSION`)

**Rate Limiting:**
- `RATE_LIMIT_READ_PER_MINUTE` - Read operations per minute (default `60`)
- `RATE_LIMIT_WRITE_PER_MINUTE` - Write operations per minute (default `30`)

**CORS:**
- `CORS_ORIGINS` - Allowed origins for CORS (default `http://localhost:4200,http://localhost:8080`)

## Data Persistence

Current named volumes:

- `redis_data` - Redis persistence
- `ollama_data` - Ollama models (only when the optional Ollama container is enabled)

Use `docker compose down -v` to remove volumes.

## Manual Docker Compose Commands

### Start Services

```bash
# Development
docker compose up --build backend redis frontend-dev

# Production
docker compose up --build backend frontend-prod redis -d

# With Ollama profile
docker compose --profile with-ollama up
```

### Stop Services

```bash
docker compose down
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

### Rebuild Images

```bash
docker compose build backend
docker compose build frontend-dev
docker compose build --no-cache backend
```

### Scale Services

```bash
# Scale backend replicas (production)
docker compose up -d --scale backend=3
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
   docker compose logs -f backend
   ```

### Backend Can't Connect to Redis

1. Check Redis is running:
   ```bash
   docker compose ps redis
   ```

2. Check Redis logs:
   ```bash
   docker compose logs -f redis
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

If running Ollama inside WSL2, configure it to listen on all interfaces (`/etc/systemd/system/ollama.service` → `Environment="OLLAMA_HOST=0.0.0.0"`), restart the service, grab the WSL IP (`ip addr show eth0 | grep "inet "`), set `OLLAMA_BASE_URL=http://<WSL_IP>:11434`, and `docker compose restart backend`.

**Containerized Ollama:**
1. Check Ollama container is running:
   ```bash
   docker compose ps ollama
   ```

2. Check Ollama logs:
   ```bash
   docker compose logs -f ollama
   ```

3. Verify models are pulled:
   ```bash
   docker compose exec ollama ollama list
   ```

### Volume Permission Issues

If you encounter permission errors with volumes:

```bash
# Fix ownership (Linux)
sudo chown -R $USER:$USER logs web-ui/dist

# Or run containers with your user ID
docker compose run --user $(id -u):$(id -g) backend
```

## Development Workflow

### Hot Reload

For the fastest feedback loop run services locally:

- **Backend**: `cd java-backend && ./mvnw quarkus:dev`
- **Frontend**: `cd web-ui && npm start`

Docker is still useful for bringing up supporting services (Redis, Ollama).

### Debugging

1. Attach to running container:
   ```bash
   docker compose exec backend sh
   ```

2. View real-time logs:
   ```bash
   docker compose logs -f backend
   ```

3. Check service health:
   ```bash
   curl http://localhost:8080/health
   ```

## Production Deployment

### Build Images

```bash
cd java-backend
./mvnw clean package -DskipTests
cd ..
docker compose build backend frontend-prod
```

### Start Production Services

```bash
docker compose up --build backend frontend-prod redis -d
```

### Update Services

```bash
git pull
cd java-backend && ./mvnw clean package -DskipTests && cd ..
docker compose up --build backend frontend-prod redis -d
```

### Backup Data

```bash
# Backup Redis
docker run --rm -v ragu_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data
```

### Restore Data

```bash
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
2. **Set resource limits**: Configure `deploy.resources` and `restart` policies in `docker-compose.yml`
3. **Regular backups**: Backup volumes before major updates
4. **Monitor logs**: `docker compose logs -f backend`
5. **Health checks**: All services have health check endpoints
6. **Environment variables**: Use `.env` file for configuration
7. **Separate dev/prod**: Use `frontend-dev` vs `frontend-prod` services and appropriate env variables

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [RAGU Scalability Roadmap](docs/SCALABILITY_ROADMAP.md)
- [RAGU Developer Guide](docs/DEVELOPER_GUIDE.md)

