# Java Migration – Phase 0 Audit

This document captures the initial inventory requested in Phase 0 of `features/new_vision/java-migration-plan.md`. It covers the Python stack elements that must reach parity in the new Java 21 implementation.

## Flask API Surface (`src/app.py`)

### Embedding & ingestion
- `POST /embed` – single file upload with secure temp storage, optional `version`/`collection_name`, overwrite flag, and timeout-wrapped call into `embed_file`. Protected by `requires_write_auth` and rate-limited.
- `POST /embed-batch` – iterates over a server-side directory path and queues every supported document via `embed_directory`.
- `POST /embed-url` – kicks off async scraping via Celery (`scrape_and_embed_url_task`) and returns `task_id`.
- `GET /embed-url/status/<task_id>` – single poll status from Celery backend.
- `GET /embed-url/stream/<task_id>` – SSE stream with polling + auth fallback for clients that cannot send cookies.
- `POST /embed-url/cancel/<task_id>` – revokes Celery task by ID.

### Querying & retrieval
- `POST /query` – primary RAG endpoint with optional `collection_name`, `version`, `k`, and `simple` mode toggle plus 30s timeout.
- `POST /query/multi-version` and `POST /query/compare` – fan queries across multiple documentation versions via `multi_version_query.py`.
- `GET /history`, `GET /history/search`, `GET /history/export` – query log management with pagination and export helpers.
- `GET|POST|DELETE /favorites` – manage starred queries (write auth required).
- `GET /stats` and `POST /cache/clear` – expose monitoring metrics and reset the query cache.

### Collections & document management
- `GET /collections` – list persisted collections (counts guarded against Chroma errors).
- `GET /collections/<version>` – resolves version vs. name and returns metadata.
- `DELETE /collections/<version>` – removes a collection with the same version deconfliction logic.
- `GET /collections/<version>/documents` & `DELETE /collections/<version>/documents/<doc_id>` – enumerate and prune individual chunks.

### Authentication, settings, and utilities
- `/auth/login|logout|status` – session-based auth with `requires_auth`/`requires_write_auth`.
- `/settings/confluence`, `/settings/system`, `/settings/llm-providers` (+ `/active`, `/models`, `/test`) – CRUD + validation for configuration data persisted on disk.
- `/confluence/test|fetch|import` – integration entrypoints for Confluence ingestion.
- `POST /extract-code` – code block extractor utility with optional language filter.
- `GET /health` – touches active LLM provider and auth status.

## Celery Workflows (`src/tasks.py`, `src/celery_app.py`)
- Only long-running workflow today is `scrape_and_embed_url_task`.
- Broker/backend is Redis (`REDIS_URL`), using JSON serialization, UTC scheduling, and task annotations for a 4h hard limit specific to this task.
- Workflow stages:
  1. Scrape with `WebScraper`, wrapping `_fetch_page` to emit `PROGRESS` updates.
  2. Persist each scraped page as temp Markdown and call `embed_file`, toggling `overwrite` only for the first page.
  3. Emits granular progress (0–10% scrape, 10–100% embedding), tracks successes/failures per page, and supports cancellation via `AsyncResult`.
- SSE endpoint relies on Celery task state to push live updates; parity requires Kafka events (per Phase 4) to expose equivalent metadata (`state`, `status`, `progress`, `url`, `result`).

## LangChain Usage
- `src/embed.py` – loaders (`PyPDFLoader`, `UnstructuredHTMLLoader`, `TextLoader`), `RecursiveCharacterTextSplitter`, and `Chroma.from_documents` for incremental updates with metadata enrichment (source, version, format). Embeddings are resolved via `EmbeddingProviderFactory` backed by settings/LLM providers.
- `src/query.py` – LCEL pipeline combining `MultiQueryRetriever`, `RunnablePassthrough`, `PromptTemplate`, and provider-specific LLMs. Includes optional cache hits (`get_cache`) and monitoring hooks.
- `src/multi_version_query.py` – extends the query chain to compare or ensemble across multiple versions with `EnsembleRetriever`.
- `src/llm_providers.py` – central factory for LLM/embedding providers (Ollama, OpenRouter, OpenAI, Anthropic, Azure, Google) using LangChain driver packages. Enforces provider-specific validation, default models, and test endpoints.
- `src/get_vector_db.py` – connection pooling for Chroma retrievers, ensuring each collection uses the correct embedding function instance.

## Chroma Data & Collection Semantics
- Persistent storage lives under `CHROMA_PATH` (default `./chroma`). Environment defaults: `COLLECTION_NAME=common-model-docs`, `TEXT_EMBEDDING_MODEL=nomic-embed-text`.
- `utils.generate_collection_name` sanitizes names, normalizes version suffixes (always `-vX`), and prevents duplicates when the filesystem path already includes version info.
- `embed_file` supports overwrite vs. incremental add, auto-detects document format, and logs to the embedding monitor (`monitoring.get_embedding_monitor`).
- `get_vector_db` caches collection handles by `(collection, path)` while `get_or_create_collection` exposes a boolean so ingestion paths know whether to append or recreate.
- Collection metadata stored in Chroma chunks include `source_file`, `file_format`, optional `version`, page numbers, chunk indexes, etc., which downstream endpoints rely on for `list_collection_documents`.

## Recommended Next Steps
1. Move this audit into `docs/ARCHITECTURE_JAVA.md` as the “current state” baseline when drafting the Quarkus target design.
2. Mirror the SSE contract (`status`, `progress`, `url`, `result/error`) when designing Kafka topics in Phase 4.
3. Extract the endpoint list above into a shared OpenAPI/contract doc so the frontend toggles between Python/Java backends seamlessly during the dual-run period.

