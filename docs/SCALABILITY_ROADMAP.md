# RAGU Scalability Roadmap

## Overview

This document outlines the scalability improvements needed to support 10-100 concurrent users in RAGU. The implementation is divided into four phases, starting with Docker containerization (Phase 0), followed by three scalability phases.

## Prerequisites

- Docker and Docker Compose installed
- For Phase 0: Docker 20.10+ and Docker Compose 2.0+
- For Phase 1-3: Phase 0 must be completed first

---

## Phase 0: Docker Compose Setup (Priority: Foundation)

**Timeline**: 1 week  
**Target**: Containerize entire application stack for consistent deployment

### Overview

Phase 0 containerizes the RAGU application using Docker Compose, providing a foundation for all subsequent scalability improvements. This phase ensures consistent environments across development and production.

### 0.1 Docker Configuration Files

**Files created:**
- `Dockerfile` - Backend API container
- `web-ui/Dockerfile` - Frontend container (multi-stage)
- `docker-compose.yml` - Base orchestration
- `docker-compose.dev.yml` - Development overrides
- `docker-compose.prod.yml` - Production overrides
- `.dockerignore` - Backend exclusions
- `web-ui/.dockerignore` - Frontend exclusions
- `web-ui/nginx.conf` - Production frontend server

**Implementation:**
- Backend: Python 3.11-slim base, supports dev/prod modes
- Frontend: Multi-stage build (Node.js build + Nginx serve)
- Services: backend, redis, celery-worker, frontend-dev, frontend-prod, ollama (optional)

### 0.2 Environment Configuration

**Files created:**
- `.env.docker` - Docker-specific environment template

**Configuration:**
- Redis URL: `redis://redis:6379/0`
- Ollama URL: Configurable (container or external)
- Volume mounts for persistent data

### 0.3 Helper Scripts

**Files created:**
- `scripts/docker-start.sh` - Start services
- `scripts/docker-stop.sh` - Stop services
- `scripts/docker-logs.sh` - View logs
- `scripts/docker-reset.sh` - Reset volumes

### 0.4 Documentation Updates

**Files modified:**
- `docs/SCALABILITY_ROADMAP.md` - Add Phase 0
- `README.md` - Docker instructions
- `QUICKSTART.md` - Docker quick start
- `docs/DOCKER_GUIDE.md` - Detailed Docker guide

### Benefits

1. **Simplified Setup**: Single command to start entire stack
2. **Environment Consistency**: Same environment for all developers
3. **Isolation**: Services run in isolated containers
4. **Scalability Foundation**: Ready for Phase 1-3 implementations
5. **Easy Testing**: Spin up/down environments quickly
6. **Production Parity**: Dev and prod environments closely match

### Usage

**Development:**
```bash
./scripts/docker-start.sh dev
```

**Production:**
```bash
./scripts/docker-start.sh prod
```

**With containerized Ollama:**
```bash
./scripts/docker-start.sh dev container
```

---

## Current Architecture Issues

1. **Flask Development Server**: Single-threaded, not production-ready
2. **ChromaDB Connection Management**: New connection per request, no pooling
3. **Synchronous Blocking Operations**: All I/O operations block request threads
4. **Web Scraping**: Synchronous with `time.sleep()`, blocks threads for minutes
5. **No Rate Limiting**: No protection against resource exhaustion
6. **No Connection Pooling**: External API calls create new connections each time

---

## Phase 1: Support 10 Concurrent Users (Priority: Critical)

**Timeline**: 1-2 weeks  
**Target**: Handle 10 concurrent users with acceptable performance

**GitHub Issue**: Create issue titled "Phase 1: Support 10 Concurrent Users" with labels `enhancement`, `scalability`, `phase1`

### 1.1 Production WSGI Server Setup

**GitHub Subtask**: "1.1: Setup Production WSGI Server (Gunicorn)"

**Files to modify:**
- [ ] `requirements.txt` - Add Gunicorn
- [ ] `scripts/start-rag-server.sh` - Update startup script
- [ ] `README.md` - Update deployment instructions

**Implementation:**
- [ ] Add `gunicorn>=21.2.0` to `requirements.txt`
- [ ] Create `gunicorn_config.py` with 4 workers configuration
- [ ] Update startup script to use Gunicorn instead of `app.run()`
- [ ] Configure worker timeout (30s) and keepalive settings

**Configuration:**
```python
# gunicorn_config.py
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
bind = "0.0.0.0:8080"
```

### 1.2 ChromaDB Connection Pooling

**GitHub Subtask**: "1.2: Implement ChromaDB Connection Pooling"

**Files to modify:**
- [ ] `src/get_vector_db.py` - Implement connection caching
- [ ] `src/embed.py` - Update to use pooled connections
- [ ] `src/query.py` - Update to use pooled connections

**Implementation:**
- [ ] Create singleton pattern for ChromaDB connections per collection
- [ ] Cache `Chroma` instances in a dictionary keyed by `(collection_name, version)`
- [ ] Add thread-safe locking for connection creation
- [ ] Implement connection cleanup on application shutdown

**Key changes:**
```python
# src/get_vector_db.py
_chroma_cache = {}
_cache_lock = threading.Lock()

def get_vector_db(collection_name=None, version=None):
    cache_key = (collection_name or COLLECTION_NAME, version)
    if cache_key not in _chroma_cache:
        with _cache_lock:
            if cache_key not in _chroma_cache:
                _chroma_cache[cache_key] = Chroma(...)
    return _chroma_cache[cache_key]
```

### 1.3 Background Job Queue for Web Scraping

**GitHub Subtask**: "1.3: Implement Background Job Queue (Celery) for Web Scraping"

**Files to modify:**
- [ ] `requirements.txt` - Add Celery and Redis
- [ ] `src/app.py` - Add async endpoint for web scraping
- [ ] `src/embed.py` - Create Celery task for `embed_url`
- [ ] `web-ui/src/app/core/services/embed.service.ts` - Update to poll job status
- [ ] `web-ui/src/app/features/admin/import/import.component.ts` - Update UI for async jobs

**New files:**
- [ ] `src/celery_app.py` - Celery configuration
- [ ] `src/tasks.py` - Background task definitions

**Implementation:**
- [ ] Install `celery>=5.3.0` and `redis>=5.0.0`
- [ ] Create Celery app with Redis broker
- [ ] Move `embed_url()` to Celery task
- [ ] Add `/embed-url/status/<task_id>` endpoint for job status
- [ ] Update frontend to poll for job completion

### 1.4 Basic Rate Limiting

**GitHub Subtask**: "1.4: Implement Basic Rate Limiting"

**Files to modify:**
- [ ] `requirements.txt` - Add Flask-Limiter
- [ ] `src/app.py` - Add rate limiting middleware

**Implementation:**
- [ ] Install `Flask-Limiter>=3.5.0`
- [ ] Configure rate limits per endpoint:
  - [ ] `/query`: 30 requests/minute per IP
  - [ ] `/embed`: 10 requests/minute per IP
  - [ ] `/embed-url`: 2 requests/minute per IP
- [ ] Use Redis for distributed rate limiting (if multiple workers)

### 1.5 Request Timeouts

**GitHub Subtask**: "1.5: Add Request Timeouts"

**Files to modify:**
- [ ] `src/app.py` - Add timeout decorator
- [ ] `src/query.py` - Add timeout to LLM calls
- [ ] `src/embed.py` - Add timeout to embedding operations

**Implementation:**
- [ ] Use `signal.alarm()` or `concurrent.futures.TimeoutError` for long operations
- [ ] Set 30s timeout for queries
- [ ] Set 60s timeout for embeddings
- [ ] Return appropriate error messages on timeout

---

## Phase 2: Support 50 Concurrent Users (Priority: High)

**Timeline**: 2-4 weeks  
**Target**: Handle 50 concurrent users with good performance

**GitHub Issue**: Create issue titled "Phase 2: Support 50 Concurrent Users" with labels `enhancement`, `scalability`, `phase2`

### 2.1 Async Framework Migration

**GitHub Subtask**: "2.1: Migrate to Async Framework (FastAPI or Flask async)"

**Files to modify:**
- [ ] `requirements.txt` - Add FastAPI and uvicorn (or Flask async support)
- [ ] `src/app.py` - Migrate to FastAPI (or Flask async)
- [ ] All route handlers - Convert to async functions
- [ ] `src/query.py` - Make async-compatible
- [ ] `src/embed.py` - Make async-compatible

**Decision Point**: FastAPI vs Flask async
- **Option A**: FastAPI (recommended) - Better async support, automatic docs
- **Option B**: Flask 2.0+ with async routes - Less migration effort

**Implementation:**
- [ ] Migrate all routes to async handlers
- [ ] Use `httpx` for async HTTP requests to external APIs
- [ ] Use `asyncio.gather()` for parallel operations
- [ ] Update all service calls to be async-compatible

### 2.2 Redis Caching Layer

**GitHub Subtask**: "2.2: Implement Redis Caching Layer"

**Files to modify:**
- [ ] `src/cache.py` - Enhance with Redis backend
- [ ] `src/query.py` - Use Redis for query result caching
- [ ] `src/embed.py` - Cache embedding results

**Implementation:**
- [ ] Replace in-memory cache with Redis
- [ ] Cache query results with TTL (1 hour)
- [ ] Cache embedding function results
- [ ] Cache ChromaDB collection metadata
- [ ] Use Redis for session storage

### 2.3 Connection Pooling for External APIs

**GitHub Subtask**: "2.3: Implement Connection Pooling for External APIs"

**Files to modify:**
- [ ] `src/llm_providers.py` - Add connection pooling
- [ ] `src/query.py` - Reuse LLM connections
- [ ] `src/embed.py` - Reuse embedding connections

**Implementation:**
- [ ] Create connection pool for OpenAI/OpenRouter APIs
- [ ] Reuse HTTP sessions for external API calls
- [ ] Implement retry logic with exponential backoff
- [ ] Add connection timeout configuration

### 2.4 Enhanced Error Handling and Retries

**GitHub Subtask**: "2.4: Add Enhanced Error Handling and Retries"

**Files to modify:**
- [ ] `requirements.txt` - Add tenacity library
- [ ] `src/app.py` - Add global error handlers
- [ ] `src/llm_providers.py` - Add retry logic
- [ ] `src/query.py` - Add retry for failed queries

**Implementation:**
- [ ] Use `tenacity` library for retry logic
- [ ] Implement exponential backoff for API failures
- [ ] Add circuit breaker pattern for external services
- [ ] Log errors with context for debugging

### 2.5 Monitoring and Metrics

**GitHub Subtask**: "2.5: Add Monitoring and Metrics"

**Files to modify:**
- [ ] `requirements.txt` - Add Prometheus client
- [ ] `src/app.py` - Add metrics endpoints
- [ ] `src/monitoring.py` - Enhance with metrics

**Implementation:**
- [ ] Add Prometheus metrics for:
  - [ ] Request count and latency
  - [ ] Active connections
  - [ ] Cache hit rates
  - [ ] Error rates
- [ ] Create `/metrics` endpoint
- [ ] Add health check improvements

---

## Phase 3: Support 100 Concurrent Users (Priority: Medium)

**Timeline**: 4-8 weeks  
**Target**: Handle 100 concurrent users with excellent performance

**GitHub Issue**: Create issue titled "Phase 3: Support 100 Concurrent Users" with labels `enhancement`, `scalability`, `phase3`

### 3.1 Load Balancing Setup

**GitHub Subtask**: "3.1: Setup Load Balancing with Nginx"

**Files to modify:**
- [ ] `nginx.conf` - New file for reverse proxy
- [ ] `docker-compose.yml` - Update for multiple app instances
- [ ] `README.md` - Add load balancing documentation

**Implementation:**
- [ ] Configure Nginx as reverse proxy
- [ ] Set up multiple Gunicorn instances (2-3 servers, 4 workers each)
- [ ] Implement sticky sessions for ChromaDB consistency
- [ ] Add health check endpoints for load balancer

### 3.2 Database Optimization

**GitHub Subtask**: "3.2: Optimize Database Queries and Operations"

**Files to modify:**
- [ ] `src/get_vector_db.py` - Optimize ChromaDB queries
- [ ] `src/query.py` - Add query result pagination
- [ ] `src/embed.py` - Batch embedding operations

**Implementation:**
- [ ] Add indexes for common queries
- [ ] Implement query result pagination
- [ ] Batch embedding operations where possible
- [ ] Consider PostgreSQL for metadata (optional)

### 3.3 Advanced Caching Strategies

**GitHub Subtask**: "3.3: Implement Multi-Level Caching"

**Files to modify:**
- [ ] `src/cache.py` - Multi-level caching
- [ ] `src/query.py` - Cache at multiple levels

**Implementation:**
- [ ] L1: In-memory cache (fast, limited size)
- [ ] L2: Redis cache (medium speed, larger size)
- [ ] Cache embedding vectors
- [ ] Cache document chunks
- [ ] Implement cache warming strategies

### 3.4 Auto-scaling Configuration

**GitHub Subtask**: "3.4: Configure Auto-scaling"

**Files to modify:**
- [ ] `docker-compose.yml` - Add scaling configuration
- [ ] `kubernetes/` - New directory for K8s configs (optional)

**Implementation:**
- [ ] Configure horizontal pod autoscaling (if using K8s)
- [ ] Set up auto-scaling based on CPU/memory
- [ ] Configure minimum/maximum instance counts
- [ ] Add queue-based scaling for Celery workers

### 3.5 Performance Testing and Tuning

**GitHub Subtask**: "3.5: Performance Testing and Tuning"

**Files to create:**
- [ ] `tests/load_test.py` - Load testing scripts
- [ ] `docs/PERFORMANCE.md` - Performance benchmarks

**Implementation:**
- [ ] Use Locust or k6 for load testing
- [ ] Test with 10, 50, 100 concurrent users
- [ ] Identify and fix bottlenecks
- [ ] Document performance characteristics
- [ ] Set up continuous performance monitoring

---

## Implementation Dependencies

### Phase 0 Dependencies
- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] Ollama (external or containerized)

### Phase 1 Dependencies
- [ ] Phase 0 completed (recommended)
- [ ] Redis server (for Celery and rate limiting) - included in Docker
- [ ] Gunicorn installation - included in Docker
- [ ] No breaking changes to existing API

### Phase 2 Dependencies
- [ ] Phase 1 completed
- [ ] Redis server (already required) - included in Docker
- [ ] Async-compatible Python 3.8+

### Phase 3 Dependencies
- [ ] Phase 2 completed
- [ ] Nginx or similar load balancer - included in Docker
- [ ] Multiple server instances or container orchestration - Docker Compose supports scaling

---

## Risk Mitigation

1. **Breaking Changes**: Maintain backward compatibility during migration
2. **Data Loss**: Ensure ChromaDB connections are properly closed
3. **Performance Regression**: Benchmark before and after each phase
4. **External Dependencies**: Have fallback mechanisms for Redis/Celery

---

## Success Metrics

- **Phase 1**: 10 concurrent users, <2s average response time
- **Phase 2**: 50 concurrent users, <3s average response time, 80% cache hit rate
- **Phase 3**: 100 concurrent users, <3s average response time, 90% cache hit rate

---

## Files Summary

### Phase 0 Files (Docker) - ✅ Completed
- [x] `Dockerfile` - Backend container
- [x] `web-ui/Dockerfile` - Frontend container (multi-stage)
- [x] `docker-compose.yml` - Base orchestration
- [x] `docker-compose.dev.yml` - Development overrides
- [x] `docker-compose.prod.yml` - Production overrides
- [x] `.dockerignore` - Backend exclusions
- [x] `web-ui/.dockerignore` - Frontend exclusions
- [x] `web-ui/nginx.conf` - Production frontend server
- [x] `ollama/Dockerfile` - Optional Ollama container
- [x] `ollama/entrypoint.sh` - Ollama entrypoint script
- [x] `.env.docker` - Docker environment template
- [x] `scripts/docker-start.sh` - Start helper script
- [x] `scripts/docker-stop.sh` - Stop helper script
- [x] `scripts/docker-logs.sh` - Logs helper script
- [x] `scripts/docker-reset.sh` - Reset helper script
- [x] `docs/DOCKER_GUIDE.md` - Docker documentation

### Phase 1-3 Files
- [x] `gunicorn_config.py` (already created)
- [x] `src/celery_app.py` (already created)
- [x] `src/tasks.py` (already created)
- [ ] `nginx.conf` (for load balancing in Phase 3)
- [ ] `tests/load_test.py`
- [ ] `docs/PERFORMANCE.md`

### Modified Files
- [x] `requirements.txt` (already updated)
- [ ] `src/app.py` (Phase 1-3)
- [ ] `src/get_vector_db.py` (Phase 1)
- [ ] `src/query.py` (Phase 1-3)
- [ ] `src/embed.py` (Phase 1-3)
- [ ] `src/llm_providers.py` (Phase 2)
- [ ] `src/cache.py` (Phase 2-3)
- [ ] `src/monitoring.py` (Phase 2)
- [ ] `scripts/start-rag-server.sh` (Phase 1)
- [x] `README.md` (Phase 0 - Docker instructions added)
- [x] `QUICKSTART.md` (Phase 0 - Docker quick start added)
- [x] `docs/SCALABILITY_ROADMAP.md` (Phase 0 added)
- [ ] `web-ui/src/app/core/services/embed.service.ts` (Phase 1)
- [ ] `web-ui/src/app/features/admin/import/import.component.ts` (Phase 1)

---

## GitHub Issues Creation Checklist

### Phase 0 Issues - ✅ Completed
- [x] Create main issue: "Phase 0: Docker Compose Setup" (Issue #22)

### Phase 1 Issues
- [ ] Create main issue: "Phase 1: Support 10 Concurrent Users"
- [ ] Create subtask: "1.1: Setup Production WSGI Server (Gunicorn)"
- [ ] Create subtask: "1.2: Implement ChromaDB Connection Pooling"
- [ ] Create subtask: "1.3: Implement Background Job Queue (Celery) for Web Scraping"
- [ ] Create subtask: "1.4: Implement Basic Rate Limiting"
- [ ] Create subtask: "1.5: Add Request Timeouts"

### Phase 2 Issues
- [ ] Create main issue: "Phase 2: Support 50 Concurrent Users"
- [ ] Create subtask: "2.1: Migrate to Async Framework (FastAPI or Flask async)"
- [ ] Create subtask: "2.2: Implement Redis Caching Layer"
- [ ] Create subtask: "2.3: Implement Connection Pooling for External APIs"
- [ ] Create subtask: "2.4: Add Enhanced Error Handling and Retries"
- [ ] Create subtask: "2.5: Add Monitoring and Metrics"

### Phase 3 Issues
- [ ] Create main issue: "Phase 3: Support 100 Concurrent Users"
- [ ] Create subtask: "3.1: Setup Load Balancing with Nginx"
- [ ] Create subtask: "3.2: Optimize Database Queries and Operations"
- [ ] Create subtask: "3.3: Implement Multi-Level Caching"
- [ ] Create subtask: "3.4: Configure Auto-scaling"
- [ ] Create subtask: "3.5: Performance Testing and Tuning"

---

**Last Updated**: 2025-01-27  
**Status**: Phase 0 Completed ✅  
**Next Step**: Begin Phase 1 implementation

