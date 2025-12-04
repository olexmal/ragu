# API Reference

Complete reference for all RAGU (Retrieval-Augmented Generation Universal) API endpoints.

## Base URL

```
http://localhost:8080
```

(Configurable via `API_HOST` and `API_PORT` environment variables)

---

## Authentication

The backend supports multiple authentication methods:

### 1. Session-Based Authentication (Recommended)

After logging in via `/auth/login`, the server sets a `RAGU_SESSION` cookie that is automatically included in subsequent requests.

```bash
# Login
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}' \
  -c cookies.txt

# Subsequent requests use the cookie
curl http://localhost:8080/query \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"query": "How to use this API?"}'
```

### 2. API Key Authentication

Include the API key in the request header:

```
X-API-Key: your-api-key-here
```

### 3. Basic Authentication

Use HTTP Basic Auth with username and password:

```bash
curl -u admin:changeme http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

**Authentication Configuration:**
- `AUTH_ENABLED=false`: No authentication required (default)
- `AUTH_ENABLED=true`: Authentication required based on endpoint annotations
- Write operations (POST/PUT/DELETE) always require authentication when enabled
- Read operations (GET) may be public depending on configuration

Sessions are stored in Redis with a configurable TTL (`SESSION_TTL_MINUTES`, default 1440 = 24 hours).

---

## Endpoints

### Health & Status

#### `GET /health`

High-level service status (used by dashboards/UI).

**Response:**
```json
{
  "status": "initializing",
  "service": "RAGU Java Backend",
  "llmProvider": "pending",
  "dependencies": {
    "redis": "redis://localhost:6379/0",
    "kafka": "localhost:9092",
    "qdrant": "http://localhost:6333"
  }
}
```

#### `GET /q/health`

Quarkus health group. Sub-paths:
- `/q/health/live` – liveness
- `/q/health/ready` – readiness (checks Redis/Kafka/Qdrant reachability)

#### `GET /q/metrics`

Micrometer Prometheus metrics (e.g., `ragu_embedding_requests`, `ragu_query_requests`, `ragu_scrape_tasks`, associated timers).

---

### Embedding

#### `POST /embed`

Embed a single file into the vector database.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): File to embed
- `version` (optional): Version string for collection naming
- `overwrite` (optional): Set to "true" to replace existing collection

**Example:**
```bash
curl -X POST http://localhost:8080/embed \
  -F "file=@documentation.pdf" \
  -F "version=1.2.3"
```

**Response:**
```json
{
  "message": "File embedded successfully",
  "version": "1.2.3",
  "mode": "incremental",
  "filename": "documentation.pdf"
}
```

#### `POST /embed-batch`

Embed multiple files from a directory.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `directory` (required): Directory path containing files to embed
- `version` (optional): Version string
- `overwrite` (optional): Set to "true" to replace existing collection

**Response:**
```json
{
  "message": "Batch embedding completed",
  "results": {
    "success": 10,
    "failed": 0,
    "errors": []
  },
  "version": "1.2.3"
}
```

#### `POST /confluence/test`

Test Confluence connection with provided settings.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "url": "https://your-domain.atlassian.net",
  "instance_type": "cloud",
  "api_token": "your-token",
  "username": "your-email@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection test successful (stub validation)",
  "url": "https://your-domain.atlassian.net",
  "instance_type": "cloud"
}
```

**Note:** Currently returns a stub validation. Full SDK integration for actual Confluence connection testing is pending.

#### `POST /confluence/import`

Import a Confluence page to the vector database.

**Note:** This endpoint returns `501 Not Implemented` and requires Confluence SDK integration.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "page_id": "123456",
  "version": "1.2.3",
  "overwrite": false
}
```

**Parameters:**
- `page_id` (required): Confluence page ID (numeric) or full Confluence URL
- `version` (optional): Version string for collection naming
- `overwrite` (optional): If `true`, replace existing collection (default: `false`)

**Example:**
```bash
# Using page ID
curl -X POST http://localhost:8080/confluence/import \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "123456",
    "version": "1.2.3"
  }'

# Using Confluence URL
curl -X POST http://localhost:8080/confluence/import \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title",
    "version": "1.2.3"
  }'
```

**Response:**
```json
{
  "message": "Confluence page 123456 imported successfully",
  "filename": "confluence-page-123456.md",
  "version": "1.2.3",
  "mode": "incremental"
}
```

**Note:** Confluence settings must be configured in Settings before importing pages. The system uses `confluence-markdown-exporter` to convert Confluence pages to Markdown before embedding.

#### `POST /embed-url`

Start a background job to scrape and embed content from a URL. This endpoint runs asynchronously via the Kafka-backed task pipeline (locally simulated by `ScrapeTaskService`).

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Rate Limit:** 10 requests per minute

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "url": "https://docs.example.com",
  "collection_name": "Angular",
  "version": "v19",
  "max_depth": 3,
  "overwrite": false
}
```

**Parameters:**
- `url` (required): Starting URL to scrape
- `collection_name` (optional): Base name for the collection (e.g., 'Angular', 'React')
- `version` (optional): Version string (e.g., 'v19', '2.0')
- `max_depth` (optional): Maximum crawl depth (default: 3)
- `overwrite` (optional): If `true`, replace existing collection (default: `false`)

**Response (202 Accepted):**
```json
{
  "message": "URL scraping and embedding job started",
  "task_id": "abc123-def456-...",
  "status_url": "/embed-url/status/abc123-def456-..."
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/embed-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://v19.angular.dev",
    "collection_name": "Angular",
    "version": "v19",
    "max_depth": 2
  }'
```

#### `GET /embed-url/status/{task_id}`

Retrieve task progress (polling endpoint).

```json
{
  "task_id": "abc123",
  "state": "PROGRESS",
  "message": "Scraping in progress 60%",
  "progress": 60,
  "url": "https://docs.example.com",
  "metadata": null,
  "error": null
}
```

#### `GET /embed-url/stream/{task_id}`

Server-Sent Events stream mirroring `/embed-url/status`. Each event is a JSON `TaskStatusResponse`. Useful for the Angular UI.

```
GET /embed-url/stream/abc123
Accept: text/event-stream
```

#### `POST /embed-url/cancel/{task_id}`

Cancel a pending task. Returns the final `TaskStatusResponse` with `state="REVOKED"`.

### Querying

#### `POST /query`

Query the documentation using natural language.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "query": "How do I use the UserService class?",
  "version": "1.2.3",
  "k": 3,
  "simple": false
}
```

**Parameters:**
- `query` (required): Natural language question
- `version` (optional): Version to query
- `k` (optional): Number of documents to retrieve (default: 3)
- `simple` (optional): Use simple query mode (faster, default: false)

**Response:**
```json
{
  "answer": "UserService provides methods for...",
  "query": "How do I use the UserService class?",
  "sources": [
    {
      "content": "UserService class documentation...",
      "metadata": {
        "source_file": "path/to/file",
        "version": "1.2.3"
      }
    }
  ],
  "source_count": 3
}
```

#### `POST /query/multi-version`

Query documentation across multiple versions simultaneously. Results are merged and ranked by relevance score.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "query": "How does UserService work?",
  "versions": ["v1.2.3", "v1.3.0"],
  "k": 3
}
```

**Response:**
```json
{
  "answer": "Merged results from 2 versions with 6 total sources.",
  "query": "How does UserService work?",
  "sources": [
    {
      "content": "UserService handles...",
      "metadata": {"version": "v1.3.0", "file_path": "user-service.md"}
    }
  ],
  "source_count": 6,
  "stats": {}
}
```

**Note:** The query is automatically recorded in history with a `multi:v1.2.3,v1.3.0` collection identifier.

#### `POST /query/compare`

Compare answers across different versions. Results are returned grouped by version.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "query": "How do I create a user?",
  "versions": ["v1.2.3", "v1.3.0", "v2.0.0"],
  "k": 3
}
```

**Response:**
```json
{
  "query": "How do I create a user?",
  "versions": ["v1.2.3", "v1.3.0", "v2.0.0"],
  "results_by_version": {
    "v1.2.3": [
      {
        "content": "In v1.2.3, create users via...",
        "metadata": {"version": "v1.2.3", "file_path": "api.md"}
      }
    ],
    "v1.3.0": [...],
    "v2.0.0": [...]
  },
  "total_sources": 9
}
```

**Note:** The query is automatically recorded in history with a `compare:v1.2.3,v1.3.0,v2.0.0` collection identifier.

---

### Collections

#### `GET /collections`

List all available collections.

**Response:**
```json
{
  "collections": [
    {
      "name": "common-model-docs-v1.2.3",
      "count": 150
    }
  ],
  "total": 1
}
```

#### `GET /collections/<version>`

Get information about a specific versioned collection.

**Response:**
```json
{
  "name": "common-model-docs-v1.2.3",
  "count": 150,
  "version": "1.2.3"
}
```

#### `DELETE /collections/<version>`

Delete a specific versioned collection.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Response:**
```json
{
  "message": "Collection common-model-docs-v1.2.3 deleted successfully",
  "version": "1.2.3"
}
```

---

### History & Favorites

#### `GET /history`

Get query history from Redis sorted set (newest first).

**Query Parameters:**
- `limit` (optional): Number of entries (default: 50, max: 200)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "history": [
    {
      "id": "uuid-1234",
      "query": "How does UserService work?",
      "answer": "Placeholder answer synthesized...",
      "source_count": 3,
      "collection_name": "common-model-docs-v1.2.3",
      "timestamp": "2025-12-04T10:00:00.000Z"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

**Note:** Query history is automatically recorded after every `/query` request.

#### `GET /history/search?q=<term>`

Search query history by matching query or answer text.

**Query Parameters:**
- `q` (required): Search term (case-insensitive substring match)
- `limit` (optional): Maximum results (default: 20, max: 100)

**Response:**
```json
{
  "results": [
    {
      "id": "uuid-1234",
      "query": "UserService methods",
      "answer": "...",
      "source_count": 3,
      "collection_name": "common-model-docs-v1.2.3",
      "timestamp": "2025-12-04T10:00:00.000Z"
    }
  ],
  "total": 5,
  "query": "UserService"
}
```

#### `GET /history/export?format=json|csv`

Export query history in JSON or CSV format.

**Query Parameters:**
- `format`: Export format - 'json' or 'csv' (default: 'json')

**CSV Response Headers:**
```
id,query,answer,source_count,collection_name,timestamp
```

**JSON Response:**
```json
{
  "history": [...]
}
```

#### `GET /favorites`

Get list of favorite queries from Redis set.

**Response:**
```json
{
  "favorites": [
    "How does UserService work?",
    "What methods are available in UserService?"
  ],
  "total": 2
}
```

#### `POST /favorites`

Add a query to favorites.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Request Body:**
```json
{
  "query": "How does UserService work?"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Added to favorites",
  "query": "How does UserService work?"
}
```

#### `DELETE /favorites?query=<text>`

Remove a query from favorites.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Query Parameters:**
- `query` (required): Query text to remove

**Example:**
```bash
curl -X DELETE "http://localhost:8080/favorites?query=How%20does%20UserService%20work%3F"
```

**Response:**
```json
{
  "success": true,
  "message": "Removed from favorites",
  "query": "How does UserService work?"
}
```

If not found:
```json
{
  "success": false,
  "message": "Not found in favorites",
  "query": "How does UserService work?"
}
```

---

### Settings & Configuration

#### `GET /settings/system`

Get system settings (e.g., system name).

**Response:**
```json
{
  "systemName": "RAGU"
}
```

#### `POST /settings/system`

Save system settings.

**Request Body:**
```json
{
  "system_name": "My Custom RAG System"
}
```

**Response:**
```json
{
  "success": true,
  "message": "System settings saved"
}
```

#### `GET /settings/confluence`

Get Confluence integration settings.

**Response:**
```json
{
  "enabled": false,
  "url": "",
  "instance_type": "cloud",
  "api_token": "",
  "username": "",
  "password": "",
  "page_ids": [],
  "auto_sync": false,
  "sync_interval": 3600
}
```

#### `POST /settings/confluence`

Save Confluence integration settings.

**Request Body:**
```json
{
  "enabled": true,
  "url": "https://your-domain.atlassian.net",
  "instance_type": "cloud",
  "api_token": "your-token",
  "page_ids": ["123456"],
  "auto_sync": false,
  "sync_interval": 3600
}
```

**Response:**
```json
{
  "success": true,
  "message": "Confluence settings saved"
}
```

#### `GET /settings/llm-providers`

Get all LLM and embedding provider configurations.

**Response:**
```json
{
  "llm_providers": {
    "ollama_1": {
      "enabled": true,
      "is_active": true,
      "type": "ollama",
      "model": "mistral",
      "base_url": "http://localhost:11434"
    }
  },
  "embedding_providers": {
    "ollama_embed_1": {
      "enabled": true,
      "is_active": true,
      "type": "ollama",
      "model": "nomic-embed-text",
      "base_url": "http://localhost:11434"
    }
  }
}
```

#### `POST /settings/llm-providers`

Save LLM and embedding provider configurations.

**Request Body:**
```json
{
  "llm_providers": {...},
  "embedding_providers": {...}
}
```

**Response:**
```json
{
  "success": true,
  "message": "LLM provider settings saved"
}
```

#### `GET /settings/llm-providers/active`

Get the currently active LLM and embedding providers.

**Response:**
```json
{
  "llm": {
    "type": "ollama",
    "model": "mistral"
  },
  "embedding": {
    "type": "ollama",
    "model": "nomic-embed-text"
  }
}
```

#### `GET /settings/llm-providers/models`

Get available models for a provider type.

**Query Parameters:**
- `provider_type` (required): Provider type (e.g., "ollama", "openai", "anthropic")
- `category` (optional): "llm" or "embedding" (default: "llm")
- `api_key` (optional): API key for cloud providers

**Response:**
```json
{
  "models": [
    {
      "id": "mistral",
      "name": "Mistral 7B",
      "context_length": 8192
    }
  ]
}
```

#### `POST /settings/llm-providers/test`

Test a provider configuration.

**Request Body:**
```json
{
  "type": "openai",
  "category": "llm",
  "config": {
    "api_key": "sk-...",
    "model": "gpt-4"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection successful (stub validation)",
  "test_response": "Provider configuration appears valid"
}
```

---

### Cache Management

#### `POST /cache/clear`

Clear all cached embeddings and query results from Redis.

**Response:**
```json
{
  "success": true,
  "message": "Cache cleared successfully",
  "cleared": 42
}
```

#### `GET /cache/stats`

Get cache statistics.

**Response:**
```json
{
  "cache_size": 42,
  "message": "Cache statistics"
}
```

---

### Statistics & Monitoring

#### `GET /stats`

Get system statistics.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 7)

**Response:**
```json
{
  "query_stats": {
    "total_queries": 150,
    "unique_queries": 45,
    "avg_response_time": 2.3,
    "cache_hit_rate": 35.5,
    "top_queries": [...]
  },
  "embedding_stats": {
    "total_embeddings": 10,
    "successful": 10,
    "failed": 0,
    "total_chunks": 1500,
    "avg_duration": 5.2
  },
  "cache_stats": {
    "entries": 25,
    "max_size": 100,
    "total_size_mb": 2.5,
    "ttl_seconds": 3600
  }
}
```

---

### Cache Management

#### `POST /cache/clear`

Clear the query cache.

**Authentication:** Required if `AUTH_REQUIRED_FOR=all`

**Response:**
```json
{
  "message": "Cache cleared successfully"
}
```

---

### Code Extraction

#### `POST /extract-code`

Extract code examples from text or documentation.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "text": "Documentation with code examples...",
  "language": "java"
}
```

**Response:**
```json
{
  "total_blocks": 3,
  "languages": ["java", "text"],
  "blocks": [
    {
      "code": "public class UserService {...}",
      "language": "java",
      "type": "class",
      "length": 150,
      "highlighted": "**public** **class** UserService {...}"
    }
  ]
}
```

---

### Authentication

#### `POST /auth/login`

Login with username and password. Sets a `RAGU_SESSION` cookie for subsequent requests.

**Content-Type:** `application/json`

**Parameters:**
- `username` (required): Username
- `password` (required): Password

**Example:**
```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}' \
  -c cookies.txt
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "username": "admin"
}
```

**Error Response (401):**
```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

#### `POST /auth/logout`

Logout and invalidate the current session.

**Example:**
```bash
curl -X POST http://localhost:8080/auth/logout \
  -b cookies.txt
```

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

#### `GET /auth/status`

Get authentication configuration and current session status.

**Example:**
```bash
curl http://localhost:8080/auth/status -b cookies.txt
```

**Response:**
```json
{
  "enabled": true,
  "authenticated": true,
  "username": "admin",
  "apiKeyConfigured": false
}
```

When not authenticated:
```json
{
  "enabled": true,
  "authenticated": false,
  "username": "",
  "apiKeyConfigured": false
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description"
}
```

**HTTP Status Codes:**
- `200` - Success
- `202` - Accepted (async operation started)
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (invalid API key)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
- `503` - Service Unavailable (Ollama not available or Celery not configured)
- `504` - Gateway Timeout (operation timed out)

---

## Rate Limiting

Rate limiting is implemented using Flask-Limiter with Redis backend:

**Default Limits:**
- `/embed-url`: 10 requests per minute
- `/embed-url/status/*`: Exempt from rate limiting (for polling)
- `/embed-url/stream/*`: Exempt from rate limiting (SSE connections)
- Other endpoints: No default limits (configurable)

**Configuration:**
```bash
# .env
USE_REDIS_RATE_LIMITING=true
REDIS_URL=redis://localhost:6379/0
```

**Rate Limit Response (429):**
```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

For additional rate limiting, consider using a reverse proxy (nginx) in front of the API

---

## Best Practices

1. **Use Version Parameters**: Always specify version when querying to ensure accurate results
2. **Enable Caching**: Keep `USE_CACHE=true` for better performance
3. **Monitor Usage**: Regularly check `/stats` to understand usage patterns
4. **Enable Authentication**: For production, enable authentication with `AUTH_ENABLED=true`
5. **Batch Operations**: Use `/embed-batch` for multiple files instead of multiple `/embed` calls
6. **Error Handling**: Always check HTTP status codes and handle errors appropriately

---

## Examples

### Complete Workflow

```bash
# 1. Embed documentation
curl -X POST http://localhost:8080/embed \
  -F "file=@docs.pdf" \
  -F "version=1.2.3"

# 2. Query it
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I use UserService?", "version": "1.2.3"}'

# 3. Check statistics
curl http://localhost:8080/stats

# 4. Export history
curl http://localhost:8080/history/export?format=csv > history.csv
```

### With Authentication

```bash
# Configure an API key (e.g., in .env or docker compose)
export RAGU_AUTH_ENABLED=true
export RAGU_AUTH_API_KEY=super-secret-key

# Use in requests
curl -X POST http://localhost:8080/embed \
  -H "X-API-Key: your-key-here" \
  -F "file=@docs.pdf"
```

---

For more information, see:
- [README.md](../README.md) - User guide
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Developer documentation
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide

