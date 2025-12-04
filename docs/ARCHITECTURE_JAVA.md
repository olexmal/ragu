# Java 21 Backend Architecture

## Context & Goals
- **Objective**: Replace the Flask/Celery stack with a single Quarkus 3.x service that exposes the same API surface, improves throughput, and unlocks JVM-native deployment.
- **Compatibility**: Every endpoint enumerated in `features/new_vision/phase0-audit.md` must remain feature-compatible so the Angular frontend can switch between Python and Java backends via a feature flag.
- **Guiding principles**: reactive-first (RESTEasy Reactive & Kafka), shared DTO contracts, and stateless web tier backed by Redis/Qdrant/Kafka.

## Service Topology
| Concern | Technology | Rationale |
| --- | --- | --- |
| HTTP & streaming APIs | Quarkus RESTEasy Reactive + SSE + gRPC | Unified transport layer handling REST + SSE + optional gRPC for internal clients |
| Prompt orchestration | LangChain4j + DJL | JVM-native equivalent of LangChain to reuse chaining patterns |
| Vector storage | Qdrant (managed via `QdrantVectorService`) | Cloud-ready alternative to Chroma with filters, payload schema, and horizontal scaling |
| Messaging & background work | Apache Kafka (reactive messaging) | Replaces Celery queues; topics: `scrape-requests`, `scrape-progress`, `embedding-events` |
| Cache/session/rate limits | Redis (Quarkus Redis client & `io.quarkus.redis.job`) | Mirrors Flask session+limiter behavior while remaining externalized |
| Document enrichment | Apache Tika + OpenNLP | JVM equivalents for PDF/HTML parsing and chunk metadata enrichment |
| Auth & throttling | Quarkus Security + Redis-backed rate limiter | Reimplements `requires_auth`/`requires_write_auth` semantics with RBAC and config-driven toggles |

## Module Breakdown
1. **Document Processor** (`document-processor`): wraps Tika/OpenNLP, normalizes metadata (source file, version, chunk index) and emits chunk DTOs.
2. **Embedding Service** (`embedding`): DJL/LangChain4j provider implementations with Redis caching and pluggable models (Ollama/OpenAI/Azure). Exposes gRPC for internal consumers and Kafka for batch ingest confirmations.
3. **Vector Layer** (`vector`): `QdrantVectorService` mirrors Python `generate_collection_name`, handles upsert/search, and supports collection lifecycle operations.
4. **RAG Service** (`rag`): orchestrates retrieval + answer generation, reusing prompt templates from `src/query.py`. Publishes query telemetry to Redis and Kafka.
5. **Tasks** (`tasks`): Kafka-driven scrape pipeline; `ScrapeTaskProcessor` consumes `scrape-requests`, fetches URLs, emits progress to `scrape-progress`, and hands chunks off to the embedding service.
6. **API Resources** (`api`): REST classes grouped by domain (embedding, query, collections, history, settings, auth, confluence, code extraction) matching Flask routes.

## Configuration Surface
- `application.properties` stores defaults for Redis (`quarkus.redis.host/port`), Kafka (`kafka.bootstrap.servers`, topic names), Qdrant (`qdrant.url`, `qdrant.api-key`), and model providers (e.g., `ragu.llm.provider=openrouter`).
- Secrets provided via environment variables or Kubernetes secrets; Quarkus config profiles map to `dev`, `test`, `prod`.
- Feature flag `ragu.api.use-java-backend` enables gradual cutover.

## API Parity Plan
The audit produced the canonical endpoint list. Each set maps to a Quarkus resource:
| Flask route | Java resource | Notes |
| --- | --- | --- |
| `/embed`, `/embed-batch` | `EmbeddingResource` | Multipart handling delegated to Vert.x body reader; chunking via Document Processor |
| `/embed-url`, `/embed-url/status`, `/embed-url/stream`, `/embed-url/cancel` | `EmbedUrlResource` | REST + SSE endpoints backed by Kafka task IDs |
| `/query`, `/query/multi-version`, `/query/compare`, `/stats` | `QueryResource` | Multi-version flows rely on LangChain4j ensemble retrievers |
| `/collections*` | `CollectionsResource` | CRUD over Qdrant collections with version sanitization |
| `/history*`, `/favorites` | `HistoryResource` | Query history stored in Redis Streams or PostgreSQL (pluggable) |
| `/auth*` | `AuthResource` | Session cookies replaced with JWT + refresh tokens |
| `/settings*`, `/confluence*`, `/extract-code` | `SettingsResource`, `ConfluenceResource`, `CodeResource` | Mirror validation logic; extraction uses JVM parser |

## Observability & Operations
- Micrometer metrics exported via Prometheus (`/q/metrics`) covering embedding/query/scrape latency & counters; OTLP tracing remains optional.
- Structured JSON logs enabled by default; `LOG_LEVEL`/`LOG_JSON` env vars control verbosity/format for Loki or Cloud Logging.
- Health routes (`/q/health`, `/q/health/ready`, `/q/health/live`) include Redis, Kafka, Qdrant, and provider checks.
- Kafka dead-letter topics capture failed background tasks.
- Docker Compose profiles ship optional Prometheus/Loki stacks; Quarkus native image remains an optimization for prod.

