# Java 21 Migration Plan

## Phase 0 – Preparation & Architecture
- [x] **Audit codebase**: Inventory current Flask endpoints, Celery workflows, LangChain usage, and Chroma data under `src/` to understand parity requirements.
- [x] **Target stack**: Finalize infrastructure stack (Quarkus, LangChain4j, Kafka, Redis, Qdrant) and document decisions in `docs/ARCHITECTURE_JAVA.md` (new file).

## Phase 1 – Quarkus Skeleton & Core Config
- [x] **Bootstrap Quarkus**: Create a new Quarkus 3.x project (`/java-backend`) with RESTEasy Reactive, LangChain4j, Redis, Kafka, and Qdrant extensions configured via `application.properties`.
- [x] **Shared models**: Define DTOs/records mirroring Python payloads (e.g., `EmbedRequest`, `QueryResponse`).

## Phase 2 – Document & Embedding Services
- [x] **Document processor**: Implement Apache Tika + OpenNLP based document chunker (`document-processor/DocumentProcessor.java`).
- [x] **Embedding service**: Implement DJL/LangChain4j embedding provider with Redis caching (`embedding/EmbeddingService.java`) and expose gRPC endpoints for internal consumers.

## Phase 3 – Vector & Query Layer
- [x] **Vector adapter**: Build Qdrant client wrapper (`vector/QdrantVectorService.java`) that mirrors the Python `generate_collection_name` logic for upsert/search.
- [x] **RAG service**: Implement LangChain4j-based retrieval-augmented generation pipeline (`rag/RagService.java`) reusing prompt logic from `src/query.py`, with a REST endpoint `/query`.

## Phase 4 – Background Tasks & Messaging
- [x] **Scrape pipeline**: Replace Celery with Kafka by defining topics (`scrape-requests`, `scrape-progress`) and implementing Quarkus reactive consumers/producers (`tasks/ScrapeTaskProcessor.java`).
- [x] **Progress APIs**: Create SSE/gRPC streaming endpoints mirroring `/embed-url/stream/<id>` behavior using Kafka progress events.

## Phase 5 – API Surface & Feature Parity
- [x] **API porting**: Reimplement Flask endpoints (`/embed`, `/embed-url`, `/collections`, `/settings`) as Quarkus resources under `/api`, ensuring request validation and rate limiting.
- [x] **Auth & rate limiting**: Port authentication logic (`requires_auth`, `requires_write_auth`) and configure Quarkus rate limiting backed by Redis.

## Phase 6 – Cut Python Backend
- [x] **Retire Flask services**: Removed all Python services from Docker Compose, deleted the legacy backend sources, and pointed tooling/scripts at the Quarkus service only.
- [x] **Docs & scripts cleanup**: Updated README, QUICKSTART, DOCKER_GUIDE, SCALABILITY_ROADMAP, DEVELOPER_GUIDE, and Browser MCP docs to reflect the Java-only stack.

## Phase 7 – Testing, Observability & Rollout
- [x] **Test suite**: Added `PhaseSevenIntegrationTest` (RestAssured) plus Micrometer-aware unit tests to exercise /embed, /query, and /embed-url flows; wired simple test configs for faster scrape simulation.
- [x] **Observability**: Enabled Micrometer Prometheus registry, JSON logging, `/q/health` endpoints, and updated `docs/DOCKER_GUIDE.md` with metrics/logging instructions and optional Prometheus/Loki profile.
- [x] **Cutover**: Authored `docs/CUTOVER_RUNBOOK.md` detailing staged rollout, monitoring, and rollback steps for switching fully to the Quarkus backend.

