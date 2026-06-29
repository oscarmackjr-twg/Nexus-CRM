---
phase: 18
slug: access-enforcement
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-29
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | backend (pytest via conftest.py — `seeded_org` fixture) |
| **Quick run command** | `pytest backend/tests -k access -q` |
| **Full suite command** | `pytest backend/tests -q` |
| **Estimated runtime** | ~TBD seconds (confirm in Wave 0) |

---

## Sampling Rate

- **After every task commit:** Run `pytest backend/tests -k access -q`
- **After every plan wave:** Run `pytest backend/tests -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** TBD seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| {N}-01-01 | 01 | 0/1 | ACCESS-01..07 | — | Role × action matrix enforced; 403 (not 404) on out-of-scope records | unit/integration | `pytest backend/tests -k access -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Planner: populate one row per task from the role × action matrix in 18-RESEARCH.md (## Validation Architecture).*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_access_enforcement.py` (or equivalent) — stubs for ACCESS-01..ACCESS-07 role × action matrix
- [ ] `backend/tests/conftest.py` — add a `principal` user to the `seeded_org` fixture (gap found in research — required for ACCESS-05 coverage)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Frontend distinguishes 403 ("no access") from 404 ("not found") in deal detail error UI | ACCESS-07 | Visual/UX behavior in `DealDetailPage.jsx` | Load a deal id outside the user's scope; confirm "no access" message, not "removed" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < TBDs
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
