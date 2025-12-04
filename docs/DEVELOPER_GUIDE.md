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
- `ai.ragu.rag` – Retrieval-augmented generation orchestration (single + multi-version queries).
- `ai.ragu.storage` – Redis-backed persistence:
  - `SessionService` – User session management with TTL
  - `SettingsStorageService` – System, Confluence, and LLM provider settings
  - `HistoryStorageService` – Query history in sorted sets
  - `FavoritesStorageService` – Favorite queries
  - `CacheService` – Cache management and clearing
- `ai.ragu.tasks` – In-memory scrape + progress simulation (Kafka-ready).
- `ai.ragu.security` – Cookie-based sessions, API key/basic auth, Redis rate limiting filters.

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

### Health & Metrics
- Liveness/readiness: `GET /q/health`, `/q/health/live`, `/q/health/ready` (includes Redis/Kafka/Qdrant checks).
- Metrics: Micrometer Prometheus registry at `/q/metrics` with key instruments:
  - `ragu_embedding_requests`, `ragu_embedding.chunks`
  - `ragu_query_requests`, `ragu_query.sources`
  - `ragu_scrape.tasks` (counters for enqueue/success/cancel) + `ragu.scrape.duration`
  - Timer gauges for embedding/query latency (`ragu.embedding.duration`, `ragu.query.duration`)
- Configure via `application.properties`: `quarkus.micrometer.export.prometheus.*`.

### Logging
- Structured JSON logs are enabled by default (`quarkus.log.console.json=true`). Override with `LOG_JSON=false` when tailing locally.
- Adjust verbosity via `LOG_LEVEL` environment variable. All logs share the `service` field for downstream aggregation (e.g., Loki).

### Authentication & Rate Limiting
- **Session Management**: `SessionService` stores user sessions in Redis with configurable TTL (default 24 hours). Sessions are created on login and validated via `RAGU_SESSION` cookie.
- **Auth Methods**: Supports cookie-based sessions (recommended), API key (`X-API-Key` header), and HTTP Basic auth.
- **Rate Limiting**: `RateLimiterService` uses Redis-backed fixed windows; profiles are configurable via `RATE_LIMIT_READ_PER_MINUTE` and `RATE_LIMIT_WRITE_PER_MINUTE`.
- **Filters**: Use `@RequiresAuth` for read endpoints and `@RequiresWriteAuth` for mutating routes; both invoke `AuthService#checkAccess`.
- **Storage**: All settings (system, Confluence, LLM providers), query history, and favorites are persisted in Redis via the `ai.ragu.storage` package.

See `docs/DOCKER_GUIDE.md#observability--monitoring` for Prometheus/Loki compose profiles and `docs/CUTOVER_RUNBOOK.md` for rollout monitoring steps.

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

