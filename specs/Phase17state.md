# Phase 17 State — Coverage Restoration

Updated: 2026-09-03

## Status

Coverage restoration is in progress. The functionality-prompt implementation remains paused until the backend coverage gate reaches 85%.

The latest authoritative gate (`nexus-full-coverage-restoration`) completed with:

```text
85 passed, 4 xpassed
Total coverage: 83.04%
Required coverage: 85%
```

No assertion failed; the exit code was caused only by the coverage threshold. About 84 additional covered lines are needed.

## Completed restoration work

- Added broad API coverage for authentication, CRM lifecycle, activity, archive, and error paths.
- Added demo seed-data creation/idempotency coverage.
- Added health, readiness, liveness, metrics, and degraded-readiness coverage.
- Prevented signed-in admins from deactivating themselves through `PUT /api/v1/users/{id}` as well as the delete route.
- Validated counterparty company references before insert, preventing unhandled foreign-key errors.
- The preceding focused restoration slice passed: `6 passed` in `nexus-coverage-restoration-green`.

## Current auth/admin tranche

New test file: `backend/tests/test_auth_admin_tranche.py`.

It covers registration organization/team validation, user list filtering and lifecycle, non-admin mutation restrictions, and LinkedIn connect/callback error behavior.

The initial run was interrupted while Docker Desktop restarted, so it is not evidence and must be rerun.

## Resume sequence

1. Confirm Docker Desktop is healthy.
2. Run the focused tranche in a new retained container:

   ```powershell
   docker-compose -f deploy/docker-compose.yml run --name nexus-auth-admin-tranche-rerun backend pytest backend/tests/test_auth_admin_tranche.py -v
   ```

3. Fix any genuine failures and rerun it.
4. Run the authoritative full coverage gate:

   ```powershell
   docker-compose -f deploy/docker-compose.yml run --name nexus-full-coverage-auth-admin backend pytest backend/tests/ -v --cov=backend --cov-report=term-missing --cov-fail-under=85
   ```

5. Resume functionality implementation only after the full gate exits 0 at or above 85%.

## Retained-container policy

Do not remove existing named test containers or Compose orphans: they preserve diagnostic and verification evidence.
