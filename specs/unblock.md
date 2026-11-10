# Unblocking the Demo-Tranche Baseline

**Status:** Recommended prerequisite work before resuming `NEXUS_CRM_DARK_FACTORY_DEMO_TRANCHE_001`  
**Evidence date:** 2026-09-02

## Current blocker

The full Docker-backed backend test suite completed without failing assertions:

```text
69 passed, 4 xpassed, 1 warning
```

However, its required coverage gate failed:

```text
TOTAL: 3,986 statements, 977 missed, 75.49% coverage
Required minimum: 85%
```

The controlling demo-tranche prompt requires the existing backend suite to be green and to meet the repository coverage gate before Gate 1 can begin. The current result therefore blocks implementation even though no test assertion failed.

## Recommendation

Do **not** lower the coverage threshold or exclude broad production directories merely to make the baseline pass. That would contradict both the repository's documented 85% gate and the demo-tranche specification.

Instead, complete a small, explicit **baseline coverage restoration** prerequisite, then rerun the full suite. The current suite needs approximately 379 additional currently-uncovered statements exercised to reach 85%, assuming the total statement count remains stable.

Prioritize tests by high uncovered surface area and direct relevance to the demo tranche:

1. **Contacts and Companies route/service coverage**
   - Cover list, get, create, update, invalid payload, not-found, org-scoped authorization, and list pagination.
   - These modules account for substantial uncovered route and service behavior and are directly needed for DF-FUNC-001, DF-FUNC-002, and DF-FUNC-006.

2. **Authentication route coverage**
   - Cover login success/failure, refresh, logout, `/auth/me`, and guarded user-management paths.
   - This is a large uncovered module and verifies the authentication boundary used by every demo flow.

3. **Shared CRM and Deal service paths**
   - Add normal and invalid-path tests for shared query/filter helpers and untested deal CRUD branches.
   - Reuse existing fixtures and public API calls rather than mocking service internals.

4. **Admin update/error paths**
   - Cover the existing untested branches in user/group update routes and reference-data mutation errors.
   - This supports the later user/group lifecycle work without changing role semantics.

5. **Narrow operational modules only where practical**
   - Add direct tests for health/readiness, telemetry fallback, structured logging, and graceful-shutdown behavior.
   - Do not pad coverage with tests of imports, generated models, or trivial statements that provide no behavior assurance.

## Execution rules

- Treat this as a separate prerequisite workstream; the demo-tranche feature scope remains paused.
- Use test-first vertical slices: one failing public-interface test, minimum repair/coverage addition, then focused verification.
- Do not count existing non-strict `XPASS` tests as evidence for new coverage requirements.
- Preserve the 85% repository-wide gate.
- Re-run the exact authoritative command after the final change:

```powershell
docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -v --cov=backend --cov-report=term-missing --cov-fail-under=85
```

## Alternative requiring explicit human authorization

If the 85% repository-wide threshold was never meant to apply to the full application, a human may redefine the coverage policy—for example, a documented changed-code threshold plus narrowly justified exclusions for seed scripts and unimplemented placeholder routes. This is a governance decision, not an implementation shortcut, and must be approved by the project owner before changing coverage configuration.

## Resume condition

Resume Gate 0 of `NEXUS_CRM_DARK_FACTORY_DEMO_TRANCHE_001` only after the full backend command exits `0` with coverage at or above 85%, and the frontend suite remains green.
