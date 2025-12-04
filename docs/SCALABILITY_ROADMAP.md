# Scalability Roadmap

> Updated for the Java/Quarkus architecture. Python-specific notes now live in `docs/archive/`.

## Phase 0 – Baseline (✅)
- Docker Compose orchestrates the Quarkus backend, Redis, optional Qdrant, and the Angular frontend.
- Auth and rate limiting use Redis; configuration lives in `.env`.
- Kafka is currently simulated inside `ScrapeTaskService` to support `/embed-url` progress streams.

## Phase 1 – Hardening & Reliability (WIP)
- [ ] Harden `java-backend/src/main/docker/Dockerfile.jvm` (non-root user, health checks, read-only filesystem).
- [ ] Document every `AUTH_*`, `RATE_LIMIT_*`, `VECTOR_*`, `SCRAPE_*` variable in `README.md` and `docs/DOCKER_GUIDE.md`.
- [ ] Add retry/backoff logic for Redis, Kafka, and Qdrant clients so brief outages don’t crash requests.
- [ ] Enforce CI jobs that run `./mvnw test` and Angular lint/tests for every pull request.

## Phase 2 – Throughput & Parallelism
- [ ] Replace the simulated Kafka publisher with a real Kafka cluster and durable topics.
- [ ] Deploy dedicated embedding workers that consume Kafka topics so API pods remain thin/stateless.
- [ ] Point vector operations to managed Qdrant/Pinecone and enable replication + sharding for millions of vectors.
- [ ] Split cache tiers (Redis/Dragonfly) for rate limiting vs embedding cache workloads.

## Phase 3 – Horizontal Scale
- [ ] Package the backend for Kubernetes/OpenShift with HPAs driven by CPU and Kafka lag metrics.
- [ ] Add an ingress/load balancer (NGINX, Traefik, or cloud LB) with sticky sessions for SSE.
- [ ] Persist SSE progress checkpoints in Redis/Kafka so any replica can resume a stream.
- [ ] Move secrets/API keys to Vault or cloud secret managers; remove plaintext `.env` files from CI runners.

## Phase 4 – Observability & Automation
- [ ] Integrate Micrometer + Prometheus exporters (request latency, cache hit rate, Kafka lag, embedding throughput).
- [ ] Enable OpenTelemetry tracing across API → services → vector store/Kafka.
- [ ] Publish Grafana dashboards + alert rules (rate-limit exhaustion, task backlog, error spikes).
- [ ] Automate ingestion/test workflows via GitHub Actions and Testcontainers-based smoke tests.

## Phase 5 – Multi-Region & DR
- [ ] Evaluate Qdrant distributed mode or replicate vectors to a secondary region.
- [ ] Deploy Redis with Sentinel/Cluster or managed Redis Enterprise for HA + failover.
- [ ] Document failover/runbook procedures, including feature flags for gradual cutovers.

## Success Metrics
- Phase 1: 99% availability, `/query` P95 < 1.5 s at 5 RPS.
- Phase 2: sustain 20 RPS ingestion with embedding workers; vector writes P95 < 500 ms.
- Phase 3: zero-downtime deploys with ≥3 backend pods and auto-scaling.
- Phase 4: full metrics/tracing coverage, alert MTTR < 15 min.
- Phase 5: regional failover < 10 min with no data loss.

## References
- `docker-compose.yml` – Local baseline stack.
- `java-backend/src/main/docker/` – Dockerfiles targeted in Phase 1.
- `docs/ARCHITECTURE_JAVA.md` – Architectural context.
- `docs/DOCKER_GUIDE.md` – Operational instructions aligned with this roadmap.

_Last updated: 2025-12-04_

