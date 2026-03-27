---
phase: 2
slug: reference-data-system
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio 0.23.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest backend/tests/test_ref_data.py -x` |
| **Full suite command** | `pytest backend/tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest backend/tests/test_ref_data.py -x`
- **After every plan wave:** Run `pytest backend/tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | REFDATA-01 | integration | `pytest backend/tests/test_ref_data.py::test_ref_data_table_exists -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | REFDATA-02 | integration | `pytest backend/tests/test_ref_data.py::test_all_categories_seeded -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | REFDATA-03–10 | integration | `pytest backend/tests/test_ref_data.py::test_seed_values -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | REFDATA-11 | integration | `pytest backend/tests/test_ref_data.py::test_get_ref_data_by_category -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | REFDATA-12 | integration | `pytest backend/tests/test_ref_data.py::test_create_ref_data_auth -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | REFDATA-13 | integration | `pytest backend/tests/test_ref_data.py::test_patch_ref_data -x` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 2 | REFDATA-14 | integration | `pytest backend/tests/test_ref_data.py::test_soft_delete_hides_item -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 3 | REFDATA-15 | — | N/A this phase | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_ref_data.py` — covers REFDATA-01 through REFDATA-14 (stubs for all test cases above)
- [ ] `seed_ref_data` fixture in `backend/tests/conftest.py` — injects seed rows for tests that require active ref data (migration-independent)
- [ ] `frontend/src/__tests__/RefSelect.test.jsx` — tests `<RefSelect>` renders options from mocked `useRefData`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| REFDATA-15: FK ondelete="SET NULL" behavior | REFDATA-15 | FK constraint validated when Phase 3–5 tables are created | Verified in Phase 3–5 migration tests |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
