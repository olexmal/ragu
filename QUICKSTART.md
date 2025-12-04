# 🚀 Quick Start Guide

Get RAGU (Retrieval-Augmented Generation Universal) running with the new Quarkus backend in just a few minutes.

---

## 🐳 Docker Quick Start

**Prerequisites:** Docker, Docker Compose, Java 21 (to build the backend), Ollama installed on the host.

```bash
git clone <repository-url>
cd ragu

# Build the backend once
cd java-backend
./mvnw clean package -DskipTests
cd ..

# Launch backend + Redis + Angular dev frontend
docker compose up --build backend redis frontend-dev
```

Service URLs:
- Backend API: http://localhost:8080
- Frontend (dev): http://localhost:4200
- Frontend (prod): `docker compose up --build backend frontend-prod redis -d` → http://localhost:80

To stop everything:

```bash
docker compose down
```

For advanced Docker usage see [docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md).

---

## ⚡ Manual Setup

### 1. Install Ollama and Models

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama --version
ollama pull mistral
ollama pull nomic-embed-text
```

### 2. Run the Backend (Development)

```bash
cd ragu/java-backend
./mvnw quarkus:dev
# API available at http://localhost:8080
```

### 3. Run the Backend (Production Style)

```bash
cd ragu/java-backend
./mvnw clean package
java -jar target/quarkus-app/quarkus-run.jar
```

### 4. Run the Web UI

```bash
cd ragu/web-ui
npm install
npm start   # http://localhost:4200
```

### 5. Test the API

```bash
curl http://localhost:8080/health

echo "UserService handles user CRUD." > test.txt
curl -X POST http://localhost:8080/embed -F "file=@test.txt"

curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What does UserService do?"}'

# Observability quick check
curl http://localhost:8080/q/health/ready | jq
curl http://localhost:8080/q/metrics | head
```

### 6. Run Tests

```bash
# Backend
cd ragu/java-backend
./mvnw test    # includes PhaseSevenIntegrationTest (embed/query/scrape)

# Frontend
cd ../web-ui
npm test
```

---

## 📝 Common Workflows

### Upload Your First Document

```bash
curl -X POST http://localhost:8080/embed \
  -F "file=@your-docs.pdf" \
  -F "version=1.0.0"
```

### Import from Confluence

```bash
curl -X POST http://localhost:8080/confluence/import \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "123456",
    "version": "1.0.0",
    "overwrite": false
  }'
```

### Query Documentation

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I use UserService?",
    "version": "1.0.0",
    "k": 3
  }'
```

### Check System Status

```bash
curl http://localhost:8080/health
curl http://localhost:8080/stats
```

### List Collections

```bash
curl http://localhost:8080/collections
```

---

## 🔧 Configuration

```bash
cp .env.example .env
# Update values such as:
#   RAGU_AUTH_ENABLED=true
#   RAGU_AUTH_API_KEY=super-secret
#   RAGU_DEPENDENCIES_REDIS=redis://redis:6379/0
```

To point the web UI to a different API URL, edit `web-ui/src/environments/environment.ts`.

---

## 🆘 Troubleshooting

- **Backend won’t start**
  - Ensure Java 21 is installed (`java -version`)
  - Run `./mvnw clean package -DskipTests` from `java-backend`
  - Check that port 8080 is free (`lsof -i :8080`)

- **No query results**
  - Make sure you have embedded documents (Collections page)
  - Check backend logs for errors while embedding

- **Docker backend fails to build**
  - Run `cd java-backend && ./mvnw clean package -DskipTests` before `docker compose up --build`
  - Clean `java-backend/target` if needed

- **Ollama connectivity issues**
  - Verify `ollama list` works on the host
  - For Docker, set `OLLAMA_BASE_URL=http://host.docker.internal:11434` (macOS/Windows) or use your host IP on Linux/WSL2
  - Test from the container: `docker compose exec backend curl $OLLAMA_BASE_URL/api/tags`

---

You’re ready to explore RAGU! For deeper guidance see the [README](README.md) or the [API reference](docs/API_REFERENCE.md).
