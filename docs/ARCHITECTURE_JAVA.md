# Java 21 Backend Architecture

## Context & Goals
- **Objective**: Replace the Flask/Celery stack with a single Quarkus 3.x service that exposes the same API surface, improves throughput, and unlocks JVM-native deployment.
- **Compatibility**: Every endpoint enumerated in `features/new_vision/phase0-audit.md` must remain feature-compatible so the Angular frontend can switch between Python and Java backends via a feature flag.
- **Guiding principles**: reactive-first (RESTEasy Reactive & Kafka), shared DTO contracts, and stateless web tier backed by Redis/Qdrant/Kafka.

## Service Topology
| Concern | Technology | Rationale |
| --- | --- | --- |
| HTTP & streaming APIs | Quarkus RESTEasy Reactive + SSE | Unified transport layer handling REST + SSE for real-time scrape progress |
| Prompt orchestration | LangChain4j + DJL | JVM-native equivalent of LangChain to reuse chaining patterns |
| Vector storage | Qdrant (managed via `QdrantVectorService`) | Cloud-ready alternative to Chroma with filters, payload schema, and horizontal scaling |
| Messaging & background work | Apache Kafka (simulated in-memory initially) | Replaces Celery queues; topics: `scrape-requests`, `scrape-progress`, `embedding-events` |
| Cache/session/rate limits/storage | Redis (Quarkus Redis client) | Session management, rate limiting, settings storage, query history, favorites, and embedding cache |
| Document enrichment | Apache Tika + OpenNLP | JVM equivalents for PDF/HTML parsing and chunk metadata enrichment |
| Auth & throttling | Cookie-based sessions + Redis rate limiter | Session cookies (`RAGU_SESSION`) with Redis-backed validation, API-key/Basic auth fallback, configurable rate limits |

## Module Breakdown
1. **Document Processor** (`ai.ragu.document`): wraps Tika/OpenNLP, normalizes metadata (source file, version, chunk index) and emits chunk DTOs.
2. **Embedding Service** (`ai.ragu.embedding`): DJL/LangChain4j provider implementations with Redis caching and pluggable models (Ollama/OpenAI/Azure).
3. **Vector Layer** (`ai.ragu.vector`): `QdrantVectorService` mirrors Python `generate_collection_name`, handles upsert/search, and supports collection lifecycle operations.
4. **RAG Service** (`ai.ragu.rag`): orchestrates retrieval + answer generation, supports single and multi-version queries. Automatically records query history to Redis.
5. **Storage Services** (`ai.ragu.storage`): Redis-backed persistence layer:
   - `SessionService`: manages user sessions with TTL
   - `SettingsStorageService`: stores system, Confluence, and LLM provider settings
   - `HistoryStorageService`: query history in sorted sets (by timestamp)
   - `FavoritesStorageService`: favorite queries in Redis sets
   - `CacheService`: cache management and clearing
6. **Tasks** (`ai.ragu.tasks`): In-memory scrape pipeline simulation; `ScrapeTaskService` manages async URL scraping with SSE progress streams.
7. **Security** (`ai.ragu.security`): `SessionService` for cookie-based auth, `AuthService` for credential validation, `RateLimiterService` for Redis-backed rate limiting.
8. **API Resources** (`ai.ragu.api`): REST classes grouped by domain (embedding, query, collections, history, settings, auth, confluence, cache) matching original Flask routes.

## Configuration Surface
`application.properties` stores defaults for:
- **Redis**: `quarkus.redis.host/port`, connection pooling
- **Kafka**: `kafka.bootstrap.servers`, topic names (simulated initially)
- **Qdrant**: `ragu.dependencies.qdrant`, `ragu.qdrant.api-key`
- **Model providers**: `ragu.llm.provider`, `ragu.embedding.provider`, `ragu.embedding.model`
- **Authentication**: `ragu.auth.enabled`, `ragu.auth.username/password`, `ragu.auth.session-ttl-minutes`, `ragu.auth.session-cookie-name`
- **Rate limiting**: `ragu.rate-limit.read.per-minute`, `ragu.rate-limit.write.per-minute`
- **CORS**: `quarkus.http.cors.origins` (env: `CORS_ORIGINS`), `quarkus.http.cors.access-control-allow-credentials=true`

Secrets provided via environment variables or Kubernetes secrets; Quarkus config profiles map to `dev`, `test`, `prod`.

## API Parity Plan
The audit produced the canonical endpoint list. Each set maps to a Quarkus resource:
| Flask route | Java resource | Status | Notes |
| --- | --- | --- | --- |
| `/embed`, `/embed-batch` | `EmbedResource`, `EmbedBatchResource` | ✅ Implemented | Multipart handling via RESTEasy; `/embed-batch` returns 501 stub |
| `/embed-url`, `/embed-url/status`, `/embed-url/stream`, `/embed-url/cancel` | `EmbedUrlResource` | ✅ Implemented | REST + SSE endpoints with in-memory task simulation |
| `/query` | `QueryResource` | ✅ Implemented | Single-version query with automatic history recording |
| `/query/multi-version` | `QueryResource` | ✅ Implemented | Merges results from multiple collections by score |
| `/query/compare` | `QueryResource` | ✅ Implemented | Returns grouped results by version for comparison |
| `/collections*` | `CollectionsResource` | ✅ Implemented | CRUD over Qdrant collections with version resolution |
| `/history`, `/history/search`, `/history/export` | `HistoryResource` | ✅ Implemented | Redis sorted sets with search and CSV/JSON export |
| `/favorites` | `FavoritesResource` | ✅ Implemented | Redis sets for favorite queries |
| `/auth/login`, `/auth/logout`, `/auth/status` | `AuthResource` | ✅ Implemented | Cookie-based sessions (`RAGU_SESSION`) with Redis backend |
| `/settings/system`, `/settings/confluence`, `/settings/llm-providers` | `SettingsResource` | ✅ Implemented | Redis-backed JSON storage for all settings |
| `/settings/llm-providers/test`, `/settings/llm-providers/models` | `SettingsResource` | ✅ Implemented | Stub validation and static model lists |
| `/confluence/test` | `ConfluenceResource` | ✅ Implemented | URL validation stub (SDK integration pending) |
| `/confluence/fetch`, `/confluence/import` | `ConfluenceResource` | ⏳ Stub (501) | Requires Confluence SDK integration |
| `/cache/clear` | `CacheResource` | ✅ Implemented | Clears `ragu:cache:*` and `ragu:embedding:*` keys |
| `/stats` | `StatsResource` | ⏳ Stub | Returns placeholder metrics |

## Observability & Operations
- Micrometer metrics exported via Prometheus (`/q/metrics`) covering embedding/query/scrape latency & counters; OTLP tracing remains optional.
- Structured JSON logs enabled by default; `LOG_LEVEL`/`LOG_JSON` env vars control verbosity/format for Loki or Cloud Logging.
- Health routes (`/q/health`, `/q/health/ready`, `/q/health/live`) include Redis, Kafka, Qdrant, and provider checks.
- Kafka dead-letter topics capture failed background tasks.
- Docker Compose profiles ship optional Prometheus/Loki stacks; Quarkus native image remains an optimization for prod.

