# Web UI ↔ Backend Compatibility Checklist

Track the gaps discovered between the Angular web UI and the new Quarkus backend. Leave a box unchecked until the backend behavior matches what the UI expects out of the box.

- [x] **Port alignment** – Quarkus now reads `QUARKUS_HTTP_PORT` with an `8080` default, matching the SPA and docker-compose wiring for zero-config local setups.
- [x] **CORS with credentials** – Enabled `Access-Control-Allow-Credentials` and configured explicit origins (`http://localhost:4200,http://localhost:8080`) via `CORS_ORIGINS` env var in `application.properties`.
- [x] **Authentication contract** – `/auth/login` now returns `{ success: true, username, message }` and mints a `RAGU_SESSION` cookie; `/auth/status` exposes `authenticated` and `username` flags based on Redis-backed session validation.
- [x] **Settings/Confluence APIs** – Created `SettingsStorageService` with Redis persistence; all `/settings/*` and `/settings/llm-providers/*` endpoints now read/write to Redis. `/confluence/test` validates URL format and returns stub success; `/confluence/fetch|import` remain 501 (require SDK integration).
- [x] **History & Favorites** – Created `HistoryStorageService` (Redis sorted set) and `FavoritesStorageService` (Redis set); `/history`, `/history/search`, `/history/export`, and `/favorites` endpoints are now fully functional. Query history is automatically recorded in `RagService`.
- [x] **Cache clear & monitoring stats** – Created `CacheService`; `/cache/clear` now flushes `ragu:cache:*` and `ragu:embedding:*` keys from Redis and returns cleared count. Added `/cache/stats` for cache size inspection.
- [x] **Multi-version query helpers** – Created `MultiVersionQueryRequest` model; `/query/multi-version` merges results from multiple collections by score, `/query/compare` returns grouped results by version. Both endpoints are fully implemented in `RagService`.

_Context: requested after verifying the UI against the Quarkus migration on branch `feature/java-migration-execution` (Dec 2025)._

## Implementation Summary

**New files created:**
- `java-backend/src/main/java/ai/ragu/security/SessionService.java` – Redis-backed session management
- `java-backend/src/main/java/ai/ragu/storage/SettingsStorageService.java` – Settings persistence
- `java-backend/src/main/java/ai/ragu/storage/HistoryStorageService.java` – Query history storage
- `java-backend/src/main/java/ai/ragu/storage/FavoritesStorageService.java` – Favorites storage
- `java-backend/src/main/java/ai/ragu/storage/CacheService.java` – Cache management
- `java-backend/src/main/java/ai/ragu/api/model/MultiVersionQueryRequest.java` – Multi-version query DTO

**Modified files:**
- `java-backend/src/main/resources/application.properties` – CORS credentials, session config
- `java-backend/src/main/java/ai/ragu/security/AuthService.java` – Session integration
- `java-backend/src/main/java/ai/ragu/api/AuthResource.java` – Cookie-based login/logout
- `java-backend/src/main/java/ai/ragu/api/SettingsResource.java` – Redis-backed settings
- `java-backend/src/main/java/ai/ragu/api/ConfluenceResource.java` – Test endpoint stub
- `java-backend/src/main/java/ai/ragu/api/HistoryResource.java` – Full history functionality
- `java-backend/src/main/java/ai/ragu/api/FavoritesResource.java` – Full favorites functionality
- `java-backend/src/main/java/ai/ragu/api/CacheResource.java` – Cache clear implementation
- `java-backend/src/main/java/ai/ragu/api/QueryResource.java` – Multi-version endpoints
- `java-backend/src/main/java/ai/ragu/rag/RagService.java` – History recording, multi-version queries
