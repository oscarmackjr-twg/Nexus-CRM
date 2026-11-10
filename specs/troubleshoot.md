# Nexus CRM — Demo Tranche Troubleshooting Status

**Status:** `PAUSED — BASELINE DEBUGGING ACTIVE`  
**Updated:** 2026-09-02T13:06:05-04:00  
**Paused workstream:** `NEXUS_CRM_DARK_FACTORY_DEMO_TRANCHE_001`

## Pause point

The demo-tranche workstream stopped at Gate 0 (repository and authority verification), before any tranche implementation, tests, migrations, seed-data changes, or demo-tranche contract documents were created.

The checkout is the intended repository and exactly matches the reviewed baseline:

```text
REPOSITORY_IDENTITY=oscarmackjr-twg/Nexus-CRM
START_BRANCH=main
START_HEAD=3d1090d09fb0ff43760f2a95a5a778570c44ccaa
BASELINE_DRIFT_STATUS=NONE
```

## Fixed implementation decisions

- `specs/` is the authoritative location of the three controlling documents.
- CSV export row cap: 10,000.
- Inactive owners remain selectable/filterable.
- Contact search includes partial company-name matching.
- A signed-in admin may never deactivate themself.
- Group reactivation only makes a group available for future assignment; it does not restore memberships.
- CSV exports omit financial fields by default.
- Local development/test seed data may be updated.
- Password reset is deferred pending separate security approval.

## Baseline evidence

### Frontend

The native frontend baseline ran before any scoped change and failed:

```text
Test Files  3 failed | 5 passed (8)
Tests  6 failed | 39 passed (45)
```

Failing suites:

- `frontend/src/__tests__/LoginPage.test.jsx` — 3 failures caused by stale expectations for the login label (`Email` versus the rendered `Username`) and backend-status text (`Backend: Connected` versus `Backend connected`).
- `frontend/src/__tests__/RefSelect.test.jsx` — 2 failures because the test expects a visible native `combobox`, while the current Radix select renders an `aria-hidden` native select for form behavior.
- `frontend/src/__tests__/Layout.test.jsx` — 1 failure caused by a stale expectation for raw role text (`admin`) while the UI renders the friendly label.

### Backend / Docker

Docker Desktop became available on 2026-09-02. The prescribed backend test command started successfully and reached pytest collection:

```text
collected 73 items
```

It reported the first 15 tests passing, then remained in the running/unhealthy `deploy-backend-run-*` container state rather than completing during the observed interval. The active container must be checked before any retry; do not assume it failed or passed without its final logs and exit status.

## Blocking constraints

1. The controlling prompt requires a passing, attributable baseline before demo-tranche implementation. The six frontend failures are pre-existing and outside the tranche.
2. The backend baseline must finish or yield a reproducible failure before it can establish backend baseline status.

## Current debugging scope

Diagnose the stale frontend test expectations and the backend test-container stall. Do not modify demo-tranche production code while this status is unresolved.

## Resume order

1. Capture final backend-container logs and exit status.
2. Reproduce and diagnose each frontend baseline failure against the current rendered component contracts.
3. Obtain approval to implement narrowly scoped baseline-test/code repairs, if needed.
4. Re-run full backend and frontend baselines to green.
5. Resume `NEXUS_CRM_DARK_FACTORY_DEMO_TRANCHE_001` at Gate 0.

## Worktree preservation

Pre-existing modified/untracked `.claude/`, `.planning/`, and `specs/` content is user-owned and must remain untouched. This file is the only file created while pausing the demo tranche.

## Debugging update

The backend test process did not stall. Its Compose health status is `unhealthy` because the inherited healthcheck probes Uvicorn at `http://localhost:8000/health`, while this container runs `pytest`; that signal is not applicable to test execution. The live pytest process was consuming CPU and advanced through 98% of the suite.

The observed backend failure is `backend/tests/test_ref_data.py::test_all_categories_seeded`. Its expected category set retains the original ten categories, but `backend/tests/conftest.py::seed_ref_data` now includes `fund_status` entries used by the Fund feature. This is a stale test expectation.

The frontend findings are refined as follows:

- `RefSelect` is a component defect, not merely a stale test. It imports Radix `SelectPrimitive.Root` but supplies native `<option>` children and no Radix trigger/content/items. That produces inaccessible loading/error output; the failed `combobox` assertion exposes the mismatch.
- The login test is stale in its backend-status wording, but the accessible login label should be aligned with the email-facing placeholder and validation message rather than renamed in the test.
- The Layout test is stale: the friendly `Admin` role label is intentional and should be asserted instead of the raw `admin` role value.

Recommended baseline-repair scope, pending implementation authorization:

1. Make `RefSelect` internally consistent (native select or complete Radix composition) and verify its loading/error accessibility.
2. Align the LoginPage accessible username label with `Email`, and update the status assertion to the current intended copy.
3. Update the Layout role assertion to `Admin`.
4. Update the reference-data category expectation to include `fund_status` (or use a required-category subset assertion if extensibility is intended).
5. Wait for the backend process to emit its final test/coverage result, then rerun both baselines after any approved repair.

## Repair execution update

Approved baseline repairs applied:

- `RefSelect` now uses a native `<select>` consistently with its existing option and change-event contract.
- LoginPage exposes its username field as `Email`; its status test matches the rendered copy.
- The Layout test asserts the intentional friendly role label.
- The reference-data required-category assertion now allows additive categories such as `fund_status`.
- `package-lock.json` was brought into sync with the declared `recharts` dependency, which was absent from the installed tree and blocked the production build.

Verification completed: focused frontend tests passed 17/17 and the full frontend suite passed 45/45. Docker-backed backend verification and the frontend build were still running when this update was written; record their final output before resuming the demo tranche.
