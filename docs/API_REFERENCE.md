# API Reference

Complete reference for all RAG System API endpoints.

## Base URL

```
http://localhost:8080
```

(Configurable via `API_HOST` and `API_PORT` environment variables)

---

## Authentication

If authentication is enabled, include the API key in the request header:

```
X-API-Key: your-api-key-here
```

**Authentication Modes:**
- `AUTH_REQUIRED_FOR=all`: All endpoints require authentication
- `AUTH_REQUIRED_FOR=write`: Only write operations require authentication
- `AUTH_ENABLED=false`: No authentication required

---

## Endpoints

### Health & Status

#### `GET /health`

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "RAG API",
  "ollama_available": true,
  "enabled": false,
  "required_for": "write"
}
```

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

---

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

Query documentation across multiple versions simultaneously.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "query": "How does UserService work?",
  "versions": ["1.2.3", "1.3.0"],
  "k": 3
}
```

**Response:**
```json
{
  "result": "Combined answer from multiple versions...",
  "query": "How does UserService work?",
  "versions_queried": ["1.2.3", "1.3.0"],
  "sources_by_version": {
    "1.2.3": [...],
    "1.3.0": [...]
  },
  "total_sources": 6,
  "response_time": 2.5
}
```

#### `POST /query/compare`

Compare answers across different versions.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "query": "How do I create a user?",
  "versions": ["1.2.3", "1.3.0", "2.0.0"],
  "k": 3
}
```

**Response:**
```json
{
  "query": "How do I create a user?",
  "versions_compared": ["1.2.3", "1.3.0", "2.0.0"],
  "results_by_version": {
    "1.2.3": {
      "answer": "...",
      "source_count": 3,
      "sources": [...]
    },
    "1.3.0": {...},
    "2.0.0": {...}
  }
}
```

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

Get query history.

**Query Parameters:**
- `limit` (optional): Number of entries (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "history": [
    {
      "id": 1,
      "query": "How does UserService work?",
      "timestamp": "2025-01-27T10:00:00",
      "version": "1.2.3",
      "response_time": 2.5,
      "source_count": 3
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

#### `GET /history/search?q=<term>`

Search query history.

**Query Parameters:**
- `q` (required): Search term
- `limit` (optional): Maximum results (default: 20)

#### `GET /history/export?format=json|csv`

Export query history.

**Query Parameters:**
- `format`: Export format - 'json' or 'csv' (default: 'json')

#### `GET /favorites`

Get list of favorite queries.

**Response:**
```json
{
  "favorites": [
    "How does UserService work?",
    "What methods are available in UserService?"
  ]
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

#### `DELETE /favorites`

Remove a query from favorites.

**Authentication:** Required if `AUTH_REQUIRED_FOR=write` or `all`

**Request Body:**
```json
{
  "query": "How does UserService work?"
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

#### `GET /auth/status`

Get authentication configuration status.

**Response:**
```json
{
  "enabled": true,
  "required_for": "write",
  "api_key_configured": true,
  "header_name": "X-API-Key"
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
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (invalid API key)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (Ollama not available)

---

## Rate Limiting

Currently no rate limiting is implemented. For production deployments, consider:
- Implementing rate limiting middleware
- Using reverse proxy (nginx) for rate limiting
- Monitoring query patterns via `/stats` endpoint

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
# Generate API key first
./scripts/generate-api-key.sh

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

