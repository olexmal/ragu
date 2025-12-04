# Java Backend Cutover Runbook

This document captures the agreed plan for rolling the Quarkus backend into all environments and decommissioning the legacy Python stack.

## 1. Preconditions

1. ✅ Feature branch `feature/java-migration-execution` merged into `main`.
2. ✅ Phase 6 completed (Python services removed from Docker Compose / docs).
3. ✅ Phase 7 test suite (`PhaseSevenIntegrationTest`) green in CI.
4. ✅ Observability endpoints online (`/q/metrics`, `/q/health`, JSON console logs).

## 2. Staged Rollout

| Stage | Actions | Success Criteria |
| --- | --- | --- |
| **Dev** | Deploy Quarkus backend + Redis only. Run automated suite (`./mvnw test`). | All tests pass, health endpoint ready. |
| **Staging** | Enable optional monitoring profile (Prometheus/Loki) and replay representative traffic. | Metrics show <1.5s P95 `/query`, scrape tasks finish <5s. |
| **Canary (Prod 10%)** | Scale backend to 2 pods/containers. Route 10% of `/api` traffic through new stack (e.g., load balancer weight). | Error rate <0.5%, no elevated latency, Prometheus scrape stable. |
| **Full Production** | Increase traffic weighting to 100%, tear down Python workers. | 24h steady-state with no Sev2+ incidents. |

## 3. Monitoring Checklist

- `http://<host>/q/metrics` → `ragu_query_requests`, `ragu_embedding_requests`, `ragu_scrape_tasks`.
- `http://<host>/q/health/ready` for readiness probes.
- Loki/central log aggregation: filter on `service="ragu-backend"` to watch WARN/ERROR.
- Frontend smoke tests (embed + query) after each stage.

## 4. Rollback Plan

1. Keep the previous Python deployment manifest (from `main` history) tagged.
2. If metrics breach SLOs or sustained errors occur:
   - Re-route traffic back to Python services (flip load balancer weight).
   - Redeploy the Python containers using the last known good compose file.
   - Capture logs/metrics, create incident report.
3. File follow-up issues before reattempting cutover.

## 5. Communication

- Announce each stage in #ragu-release with links to dashboards/logs.
- Document start/end times and SLO results in the release notes.
- Flag blockers immediately; do not proceed to next stage without sign-off from QA + platform teams.

