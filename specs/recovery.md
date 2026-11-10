# Coverage Recovery Roadmap

Updated: 2026-09-03

## Current status

The backend coverage gate is cleared; functionality-prompt implementation may resume.

Latest authoritative gate:

```text
Container: nexus-full-coverage-direct-auth
Result: 97 passed, 4 XPASS, 1 warning
Coverage: 85.94%
Required: 85%
Exit code: 0
Runtime: 3m 37s
```

No backend test assertion failed.

Docker dependencies are currently healthy:

- `deploy-postgres-1`
- `deploy-redis-1`

## Work completed

- Expanded authentication, admin, CRM lifecycle/error/archive, seed-data, and health endpoint coverage.
- Added the focused test files:
  - `backend/tests/test_auth_coverage.py`
  - `backend/tests/test_core_crm_coverage.py`
  - `backend/tests/test_coverage_restoration.py`
  - `backend/tests/test_auth_admin_tranche.py`
- Fixed signed-in-admin self-deactivation through both user lifecycle paths.
- Fixed counterparty creation so unknown company IDs are handled before an FK insert failure.
- Latest auth/admin focused validation: `4 passed` in retained container `nexus-auth-admin-tranche`.
- Added mocked LinkedIn callback success coverage, refresh/logout rejection coverage,
  admin validation coverage, app lifespan/production-metrics coverage, and direct
  auth-handler coverage where decorator instrumentation did not attribute HTTP calls.
- Final complete gate: `97 passed, 4 XPASS`, 85.94% coverage, exit code 0.

## Recovery result

All focused slices were run in uniquely named retained Docker containers, followed
by the complete gate below. The gate exited 0 at 85.94%; the coverage prerequisite
for functionality-prompt work is satisfied.

## Required final verification

```powershell
docker-compose -f deploy/docker-compose.yml run --name nexus-full-coverage-next backend pytest backend/tests/ -v --cov=backend --cov-report=term-missing --cov-fail-under=85
```

## Retained-container policy

Keep existing named test containers and Compose orphans. They preserve diagnostic and verification evidence; do not remove them during recovery.
