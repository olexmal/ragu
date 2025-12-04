# Developer Guide

> This document explains how to work with the Java 21 Quarkus backend and Angular frontend. Python-specific guidance now lives in `docs/archive/` should we ever need to reference it.

## 1. Repository Layout

```
ragu/
├── java-backend/         # Quarkus service
│   ├── src/main/java/ai/ragu
│   ├── src/main/resources/application.properties
│   └── src/main/docker/  # JVM/native Dockerfiles
├── web-ui/               # Angular 19 app
├── docs/                 # Living documentation
└── docker-compose.yml    # Backend + Redis + Qdrant (optional) + frontend
```

## 2. Backend Architecture (Java 21 + Quarkus)

```
┌───────────────┐
│ REST Clients  │  (frontend, CLI, automations)
└─────┬─────────┘
      │ REST/SSE/gRPC
┌─────▼───────────────────────────┐
│ API Layer (RESTEasy Reactive)   │
│  ai.ragu.api.*                  │
│  - DTO validation               │
│  - Auth filters (API key/basic) │
│  - Rate limiting (Redis)        │
└─────┬───────────────────┬───────┘
      │                   │
┌─────▼──────┐     ┌──────▼─────┐
│ Services   │     │ Kafka Tasks │
│ document/, │     │ tasks/      │
│ embedding/,│     │ ScrapeTask  │
│ rag/, etc. │     │ progress    │
└─────┬──────┘     └──────┬─────┘
      │                   │
┌─────▼───────────────────────────────┐
│ Vector & Cache Layer                │
│ ai.ragu.vector.*, ai.ragu.embedding │
│  - Qdrant adapter                   │
│  - Redis caching                    │
└─────────────────────────────────────┘
```

### Key modules
- `ai.ragu.api.model.*` – Records mirroring the Python payloads.
- `ai.ragu.document` – Apache Tika + OpenNLP chunking pipeline.
- `ai.ragu.embedding` – Abstraction for LangChain4j/DJL embeddings with caching.
- `ai.ragu.vector` – Collection name generator + Qdrant adapter.
- `ai.ragu.rag` – Retrieval-augmented generation orchestration.
- `ai.ragu.tasks` – Kafka-ready scrape + progress simulation.
- `ai.ragu.security` – API key/basic auth + Redis rate limiting filters.

### Configuration
`application.properties` exposes every knob. Override via `-D`, env vars, or Docker Compose.

```
quarkus.http.port=8080
ragu.dependencies.redis=${REDIS_URL:redis://redis:6379/0}
ragu.auth.enabled=${AUTH_ENABLED:false}
ragu.vector.qdrant.url=${QDRANT_URL:http://qdrant:6333}
```

## 3. Local Backend Development

```bash
cd java-backend
./mvnw quarkus:dev
```

- Hot reload, Swagger UI at `/q/swagger-ui`, OpenAPI at `/q/openapi`.
- Dev Services boot Redis automatically; set `-Dquarkus.devservices.enabled=false` if you prefer a real instance.
- Use `export JAVA_HOME=/.jdk/jdk-21.0.5+11` if the system default isn’t Java 21.

### Testing

```bash
./mvnw test
```

- Unit tests live beside production packages under `src/test/java`.
- Add RestAssured tests for API flows and Testcontainers for Redis/Qdrant coverage.

### Packaging

```bash
./mvnw clean package -DskipTests
# or native image (requires GraalVM)
./mvnw clean package -Pnative -DskipTests
```

Artifacts land in `target/`.

## 4. Frontend (Angular 19)

```bash
cd web-ui
npm install
npm start        # http://localhost:4200
npm run build    # prod bundle in dist/
```

- Communicates with the Quarkus API via `/api`.
- SSE endpoints (progress streams) are handled through the Angular services in `core/services`.

## 5. Running the Whole Stack

```bash
docker compose up --build
```

Services:
- `backend`: Quarkus JVM image (`java-backend/src/main/docker/Dockerfile.jvm`).
- `redis`: Rate limiting + cache store.
- `frontend-dev` / `frontend-prod`: Choose dev server vs static site.
- Optional: add `qdrant` service if you want persistent vectors locally.

Environment variables go in `.env` (see `README.md` for the matrix).

## 6. Observability & Auth

- Quarkus `/q/health`, `/q/metrics`, `/q/trace` are enabled in dev; lock them down behind auth in prod.
- Rate limiting profiles live in `ai.ragu.security.RateLimitProfile`.
- `AuthService` reads `AUTH_USERNAME`, `AUTH_PASSWORD`, `AUTH_API_KEY`.
- Micrometer integration is planned for Phase 7; add dependencies under `<dependencies>` in `pom.xml` when ready.

## 7. Contribution Workflow

1. Branch from `features/new_vision/java-backend` (or current feature branch).
2. Implement code + tests.
3. Run `./mvnw test` and `npm test` (if UI touched).
4. Update docs (this guide, README, DOCKER_GUIDE, API_REFERENCE).
5. Submit PR referencing the migration plan checkbox you addressed.

## 8. Troubleshooting

| Issue | Check |
| --- | --- |
| Maven cannot find Java 21 | Verify `echo $JAVA_HOME` and run `java -version`. |
| Redis connection errors | Ensure `REDIS_URL` matches `docker-compose.yml` service name. |
| SSE timeouts | Confirm Kafka simulation is enabled (`ragu.scrape.simulated=true`) or wire real Kafka cluster. |
| Rate limiting denies requests | Inspect Redis keys `rate:read:*` and `rate:write:*`. |

For anything tied to the deprecated Python stack, consult `docs/archive/`—we keep it purely for historical context.

