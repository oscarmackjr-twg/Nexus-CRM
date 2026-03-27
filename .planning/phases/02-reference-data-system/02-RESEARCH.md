# Phase 2: Reference Data System - Research

**Researched:** 2026-03-26
**Domain:** Alembic migrations with seeding, FastAPI service/route patterns, TanStack Query hooks + shadcn/ui Select
**Confidence:** HIGH — all findings are verified directly against the project codebase

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** `sub_sector` is pre-seeded at migration time — not left empty. Claude selects a sensible PE-relevant sub-sector list covering the 10 seeded parent sectors. Values can be edited via Admin UI in Phase 6.

**D-02:** All other categories use the values already specified in REQUIREMENTS.md (REFDATA-03 through REFDATA-10). No additional values beyond what's listed.

**D-03:** `GET /admin/ref-data?category=<category>` is accessible to all authenticated users — no `require_role` guard on the GET endpoint. Only POST and PATCH require `org_admin` role.

**D-04:** GET endpoint returns a union of system defaults (org_id=NULL) + org-specific items — no deduplication. Both appear if labels match. Org admins can deactivate the system default via PATCH if they want to replace it.

**D-05:** `<RefSelect>` uses shadcn/ui `Select` component (simple dropdown, no search input). No Combobox/type-to-filter for this phase.

**D-06:** Component interface: `<RefSelect category="sector" value={value} onChange={onChange} placeholder="Select sector" />`. Caller controls value/onChange — uncontrolled form integration is out of scope this phase.

### Claude's Discretion

- Exact sub-sector seed values: Claude selects a PE-appropriate list (~3–5 sub-sectors per parent sector). Example: Technology → Software & SaaS, Fintech, Healthtech, Hardware & Semiconductors.
- Migration file structure: Add `RefData` model to `backend/models.py` (for ORM use in the service layer) + write explicit `op.create_table` DDL in `0002_pe_ref_data.py` migration (not the `metadata.create_all` shortcut from 0001). Seed via `op.bulk_insert`.
- `position` default: Start all system seed values at position=0 (sorted by label as tiebreaker). Org-added items get position=0 by default.
- `value` field: Use lowercase snake_case slugs (e.g., `financial_services`, `technology`). `label` is the display string.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REFDATA-01 | `ref_data` table with columns: id, org_id (nullable), category, value, label, position, is_active, created_at | SQLAlchemy 2.x Mapped/mapped_column pattern; nullable org_id for system defaults |
| REFDATA-02 | 10 categories pre-seeded at migration time: sector, sub_sector, transaction_type, tier, contact_type, company_type, company_sub_type, deal_source_type, passed_dead_reason, investor_type | `op.bulk_insert` in Alembic upgrade — no separate seed step |
| REFDATA-03 | sector seeded with 10 TWG values | Explicit seed list in migration |
| REFDATA-04 | transaction_type seeded with 8 values | Explicit seed list in migration |
| REFDATA-05 | tier seeded with 3 values | Explicit seed list in migration |
| REFDATA-06 | contact_type seeded with 7 values | Explicit seed list in migration |
| REFDATA-07 | company_type seeded with 8 values | Explicit seed list in migration |
| REFDATA-08 | deal_source_type seeded with 6 values | Explicit seed list in migration |
| REFDATA-09 | passed_dead_reason seeded with 8 values | Explicit seed list in migration |
| REFDATA-10 | investor_type seeded with 7 values | Explicit seed list in migration |
| REFDATA-11 | `GET /admin/ref-data?category=<category>` returns active items ordered by position then label | SQLAlchemy `or_` for NULL org_id + current org; `order_by(position, label)` |
| REFDATA-12 | `POST /admin/ref-data` creates new reference item, org_admin only | `require_role("org_admin", "super_admin")` Depends on route |
| REFDATA-13 | `PATCH /admin/ref-data/{id}` updates label, position, or is_active, org_admin only | Partial update pattern — same as existing Update schemas |
| REFDATA-14 | Soft-delete via PATCH is_active=false; row stays; item disappears from dropdowns | GET filter `where(RefData.is_active == True)` |
| REFDATA-15 | All entity FK columns to ref_data use `ondelete="SET NULL"` | ForeignKey declaration pattern; Phase 3–5 responsibility — this phase establishes the table |
</phase_requirements>

---

## Summary

Phase 2 builds a foundational lookup table that all downstream entity fields (Phases 3–5) will reference. The work falls into three sub-tasks: a database migration that creates and seeds the table, a backend service and API, and a frontend query hook plus reusable dropdown component.

All patterns needed already exist in the codebase. The Alembic migration must use explicit `op.create_table` DDL and `op.bulk_insert` (not the `metadata.create_all` shortcut used in `0001_initial.py`). The service follows the `RefDataService(db, current_user)` constructor pattern from `ContactService`. The frontend hook is a thin `useQuery` wrapper identical to `useContacts`, and `<RefSelect>` wraps the existing `select.jsx` shadcn/ui primitive.

The critical design constraint is that system defaults use `org_id=NULL` and org-specific items carry the org's UUID. The GET query must union both via `or_(RefData.org_id == current_user.org_id, RefData.org_id.is_(None))` filtered by `is_active=True`, ordered by `position` then `label`.

**Primary recommendation:** Follow the contacts service/schema/route/hook stack exactly — no novel patterns are needed for this phase.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy (async) | 2.0.x (pinned `>=2.0,<3.0`) | ORM + query builder for `ref_data` model | Used throughout the codebase; `Mapped`/`mapped_column` pattern required |
| Alembic | 1.13.x (pinned `>=1.13,<2.0`) | Migration + seed in one step | Project standard; `env.py` already configured |
| FastAPI | 0.110.x (pinned `>=0.110,<1.0`) | Route handler for `/admin/ref-data` | Project backend framework |
| Pydantic v2 | 2.6.x (pinned `>=2.6,<3.0`) | `RefDataCreate`/`RefDataUpdate`/`RefDataResponse` schemas | Project schema layer |
| TanStack Query | v5 (in `frontend/node_modules`) | `useRefData` hook with 5-min `staleTime` | Project server-state manager |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn/ui `Select` | already installed (`frontend/src/components/ui/select.jsx`) | `<RefSelect>` wrapper renders native `<select>` | Phase 2 `<RefSelect>` component |
| pytest-asyncio | `>=0.23,<1.0` | Async test fixtures | All backend tests; `asyncio_mode = "auto"` in pyproject.toml |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `op.bulk_insert` in migration | Separate seed script | `bulk_insert` runs atomically with schema creation; no extra step needed |
| Single table with nullable `org_id` | Separate `system_ref_data` + `org_ref_data` tables | Single-table approach is simpler; union query is a single filter |
| Native `<select>` via shadcn wrapper | Radix UI `Select` (combobox) | D-05 locks simple dropdown; 5–10 items per category doesn't need search |

**No additional installation required.** All libraries are already in `pyproject.toml` and `frontend/package.json`.

---

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── models.py                        # Add RefData class here (end of file)
├── schemas/
│   └── ref_data.py                  # RefDataCreate, RefDataUpdate, RefDataResponse
├── services/
│   └── ref_data.py                  # RefDataService(db, current_user)
└── api/routes/
    └── admin.py                     # GET/POST/PATCH /admin/ref-data

alembic/versions/
└── 0002_pe_ref_data.py              # CREATE TABLE + op.bulk_insert for all 10 categories

frontend/src/
├── api/
│   └── refData.js                   # getRefData, createRefData, updateRefData
├── hooks/
│   └── useRefData.js                # useRefData(category) — thin useQuery wrapper
└── components/
    └── RefSelect.jsx                # <RefSelect category="..." value onChange placeholder />
```

### Pattern 1: SQLAlchemy Model with Nullable FK

The `org_id` on `RefData` is nullable because system defaults have no org. This differs from all other org-scoped models which have non-nullable `org_id`. Use `Mapped[UUID | None]` and `ForeignKey("organizations.id", ondelete="SET NULL")`.

```python
# Source: backend/models.py pattern (verified)
class RefData(Base):
    __tablename__ = "ref_data"
    __table_args__ = (
        UniqueConstraint("org_id", "category", "value", name="uq_ref_data_org_category_value"),
        Index("ix_ref_data_org_category", "org_id", "category"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

### Pattern 2: Alembic Migration with Explicit DDL + bulk_insert

The CONTEXT.md decision requires explicit `op.create_table` DDL (not `metadata.create_all`). The `0001_initial.py` is the anti-pattern here; `0002_pe_ref_data.py` must be written differently.

```python
# Source: Alembic docs pattern + project convention (verified by reading alembic/env.py)
from alembic import op
import sqlalchemy as sa
from uuid import uuid4
from datetime import datetime, timezone

revision = "0002_pe_ref_data"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

ref_data_table = sa.table(
    "ref_data",
    sa.column("id", sa.String),
    sa.column("org_id", sa.String),
    sa.column("category", sa.String),
    sa.column("value", sa.String),
    sa.column("label", sa.String),
    sa.column("position", sa.Integer),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime),
)

def upgrade() -> None:
    op.create_table(
        "ref_data",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("value", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "category", "value", name="uq_ref_data_org_category_value"),
    )
    op.create_index("ix_ref_data_org_category", "ref_data", ["org_id", "category"])

    now = datetime.now(timezone.utc).isoformat()
    rows = [
        # sector
        {"id": str(uuid4()), "org_id": None, "category": "sector", "value": "financial_services", "label": "Financial Services", "position": 0, "is_active": True, "created_at": now},
        # ... all 10 categories
    ]
    op.bulk_insert(ref_data_table, rows)


def downgrade() -> None:
    op.drop_index("ix_ref_data_org_category", table_name="ref_data")
    op.drop_table("ref_data")
```

**SQLite note:** SQLite does not enforce FK constraints by default. UUIDs are stored as String(36) in SQLite; PostgreSQL uses native UUID type. The existing codebase handles this via the `JSONVariant` / `StringList` type variants pattern. For `ref_data.id` the same approach applies — use `sa.String(36)` in the migration DDL (Alembic runs on the sync engine) and `mapped_column(primary_key=True, default=uuid4)` in the ORM model.

### Pattern 3: Service Layer — org-scoped union query

```python
# Source: backend/services/contacts.py pattern (verified)
from __future__ import annotations

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import RefData, User
from backend.schemas.ref_data import RefDataCreate, RefDataUpdate, RefDataResponse


class RefDataService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    async def list_by_category(self, category: str) -> list[RefDataResponse]:
        stmt = (
            select(RefData)
            .where(
                or_(
                    RefData.org_id == self.current_user.org_id,
                    RefData.org_id.is_(None),
                )
            )
            .where(RefData.category == category)
            .where(RefData.is_active.is_(True))
            .order_by(RefData.position, RefData.label)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return [RefDataResponse.model_validate(row) for row in rows]
```

### Pattern 4: Route Handler — split auth by method

D-03 requires GET to be accessible to all authenticated users (not just org_admin). Only POST and PATCH require `require_role`.

```python
# Source: backend/api/dependencies.py + contacts.py route pattern (verified)
from backend.api.dependencies import get_current_user, require_role, get_db

router = APIRouter(prefix="/admin/ref-data", tags=["admin"])

@router.get("/", response_model=list[RefDataResponse])
async def list_ref_data(
    category: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RefDataResponse]:
    return await RefDataService(db, current_user).list_by_category(category)


@router.post("/", response_model=RefDataResponse, status_code=status.HTTP_201_CREATED)
async def create_ref_data(
    payload: RefDataCreate,
    current_user: User = Depends(require_role("org_admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> RefDataResponse:
    return await RefDataService(db, current_user).create(payload)


@router.patch("/{item_id}", response_model=RefDataResponse)
async def update_ref_data(
    item_id: UUID,
    payload: RefDataUpdate,
    current_user: User = Depends(require_role("org_admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> RefDataResponse:
    return await RefDataService(db, current_user).update(item_id, payload)
```

### Pattern 5: Router registration in main.py

The new `admin.py` router must be imported and added to the loop in `backend/api/main.py`. The existing loop at line 77–94 iterates `[auth.router, orgs.router, ...]`. Add the new router to that list and to the import at line 19.

```python
# Source: backend/api/main.py lines 19 and 77-94 (verified)
from backend.api.routes import (
    ...,
    admin,   # add this
)

for router in [
    ...,
    admin.router,  # add this
]:
    app.include_router(router, prefix="/api/v1")
```

This means the full URL becomes `/api/v1/admin/ref-data` (prefix from main + prefix from router).

### Pattern 6: Frontend API module + hook

```javascript
// Source: frontend/src/api/contacts.js pattern (verified)
// frontend/src/api/refData.js
import client from './client';

export const getRefData = async (category) =>
  (await client.get('/admin/ref-data', { params: { category } })).data;

export const createRefData = async (data) =>
  (await client.post('/admin/ref-data', data)).data;

export const updateRefData = async (id, data) =>
  (await client.patch(`/admin/ref-data/${id}`, data)).data;
```

```javascript
// Source: frontend/src/hooks/useContacts.js pattern (verified)
// frontend/src/hooks/useRefData.js
import { useQuery } from '@tanstack/react-query';
import { getRefData } from '@/api/refData';

export function useRefData(category) {
  return useQuery({
    queryKey: ['ref', category],
    queryFn: () => getRefData(category),
    staleTime: 5 * 60 * 1000,  // 5 minutes — ref data changes rarely
  });
}
```

### Pattern 7: RefSelect component

```jsx
// Source: frontend/src/components/ui/select.jsx (verified) + D-05/D-06 decisions
// frontend/src/components/RefSelect.jsx
import { Select } from '@/components/ui/select';
import { useRefData } from '@/hooks/useRefData';

export function RefSelect({ category, value, onChange, placeholder }) {
  const { data: items = [], isLoading } = useRefData(category);

  return (
    <Select
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      disabled={isLoading}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {items.map((item) => (
        <option key={item.id} value={item.id}>
          {item.label}
        </option>
      ))}
    </Select>
  );
}
```

Note: The existing `select.jsx` is a native `<select>` wrapper (not Radix UI), so no additional primitives are needed. `onChange` receives the native event — the wrapper extracts `e.target.value` so the caller gets a plain string (the UUID of the selected ref_data row).

### Pattern 8: Query invalidation after admin mutations

```javascript
// Source: ARCHITECTURE.md TanStack Query patterns (verified)
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createRefData, updateRefData } from '@/api/refData';

const queryClient = useQueryClient();

const createMutation = useMutation({
  mutationFn: createRefData,
  onSuccess: () => {
    // Invalidate all ref data queries across all categories
    queryClient.invalidateQueries({ queryKey: ['ref'] });
  },
});
```

### Anti-Patterns to Avoid

- **Using `metadata.create_all` in 0002 migration:** The `0001_initial.py` uses this shortcut. The CONTEXT.md decision explicitly bans it for `0002` — use explicit `op.create_table` so downgrade can be a clean `op.drop_table`.
- **Putting `is_active` filter in the model:** The filter belongs in the service query, not on the model itself. This allows the PATCH soft-delete path to update the row without filter interference.
- **Guarding GET with `require_role`:** D-03 locks this — GET is authenticated-only (`get_current_user`), not admin-only. All roles need dropdown data.
- **Using `session.query()` style:** All queries must use `select(RefData)` + `await session.execute(stmt)`. `session.query()` is forbidden per CONVENTIONS.md.
- **Storing `value` as display label:** `value` is the snake_case slug (e.g., `financial_services`), `label` is the display string (e.g., `Financial Services`). FK references in downstream phases point at `id`, not `value`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dropdown caching | Custom in-memory store | TanStack Query `staleTime: 5min` | Cache invalidation, background refetch, loading state all handled |
| Role enforcement | Manual `if user.role != "org_admin"` | `require_role("org_admin", "super_admin")` Depends | Centralized; already handles super_admin elevation |
| Org scoping | Manual filter in every route | Service-layer `where(org_id == current_user.org_id)` | Consistent with all other services |
| Schema validation | Manual type checking in service | Pydantic `RefDataCreate`/`RefDataUpdate` | FastAPI validates before the route handler is called |

---

## Common Pitfalls

### Pitfall 1: UniqueConstraint with nullable org_id in SQLite

**What goes wrong:** SQLite treats NULL as distinct in unique constraints, so `(NULL, "sector", "financial_services")` and `(NULL, "sector", "financial_services")` do NOT violate the unique constraint in SQLite (because NULL != NULL). In PostgreSQL they are deduplicated correctly.

**Why it happens:** SQL standard difference in NULL handling for unique indexes.

**How to avoid:** The seed migration runs `op.bulk_insert` once per migration; it will never create true duplicates in the seed itself. The problem only surfaces on re-run. Since the migration has an explicit downgrade, re-running is clean. Ensure the test suite uses the `clean_db` autouse fixture (already in conftest.py) to drop/recreate tables between tests.

**Warning signs:** Duplicate rows in `ref_data` in test database after running tests multiple times.

### Pitfall 2: down_revision chain

**What goes wrong:** Setting `down_revision = None` in `0002_pe_ref_data.py` creates a branch head instead of a linear chain. `alembic upgrade head` would only run one of the two migrations.

**Why it happens:** Forgetting to wire `down_revision = "0001_initial"` in the new migration file.

**How to avoid:** Always set `down_revision = "0001_initial"` in the new file. Verify with `alembic history` after writing.

**Warning signs:** `alembic upgrade head` output shows "Running 1 migration" when 2 are expected.

### Pitfall 3: `op.bulk_insert` needs a `sa.table()` reference, not the ORM model

**What goes wrong:** Passing the ORM `RefData` class directly to `op.bulk_insert` fails because Alembic's `bulk_insert` operates on `sa.table()` constructs, not SQLAlchemy ORM models.

**Why it happens:** Assuming ORM model = table object.

**How to avoid:** Define a `ref_data_table = sa.table("ref_data", sa.column(...), ...)` at module level in the migration file and pass that to `op.bulk_insert(ref_data_table, rows)`.

### Pitfall 4: Route prefix collision — `/admin/ref-data` vs `/admin`

**What goes wrong:** If `main.py` uses prefix `/api/v1` and the router uses prefix `/admin/ref-data`, the full URL is `/api/v1/admin/ref-data`. A future Admin UI phase (6) may also register an `/admin` router. Names must not collide.

**Why it happens:** Multiple routers registered under the same path segment.

**How to avoid:** Use `prefix="/admin/ref-data"` on the `admin_ref_data` router. When Phase 6 adds an admin UI router, it should use a distinct prefix (e.g., `/admin`). The two do not conflict because prefix matching is path-prefix, not exact-match.

### Pitfall 5: `staleTime` unit is milliseconds, not seconds

**What goes wrong:** `staleTime: 5` caches for 5 milliseconds. The intent is 5 minutes.

**Why it happens:** TanStack Query `staleTime` is in milliseconds.

**How to avoid:** Use `staleTime: 5 * 60 * 1000` (300,000 ms = 5 minutes). Document the intent inline.

### Pitfall 6: `useRefData` called outside QueryClientProvider

**What goes wrong:** `<RefSelect>` internally calls `useRefData`, which calls `useQuery`. If `<RefSelect>` is rendered outside the `QueryClientProvider` boundary, it throws.

**Why it happens:** `QueryClientProvider` wraps all routes in `main.jsx` — this is safe for all pages. It only breaks in standalone Vitest tests that don't wrap with a provider.

**How to avoid:** Test wrapper in `frontend/src/test/setup.js` should include `QueryClientProvider`. Existing test files already do this (verify before writing new tests).

---

## Seed Data Reference

Complete seed values for all 10 categories. System defaults have `org_id=None`.

### sector (REFDATA-03)
| value | label |
|-------|-------|
| `financial_services` | Financial Services |
| `technology` | Technology |
| `healthcare` | Healthcare |
| `real_estate` | Real Estate |
| `infrastructure` | Infrastructure |
| `consumer` | Consumer |
| `industrials` | Industrials |
| `energy` | Energy |
| `media_telecom` | Media & Telecom |
| `business_services` | Business Services |

### sub_sector (D-01 — Claude's discretion, PE-appropriate)
| value | label | parent sector |
|-------|-------|--------------|
| `software_saas` | Software & SaaS | Technology |
| `fintech` | Fintech | Technology |
| `healthtech` | Healthtech | Technology |
| `hardware_semiconductors` | Hardware & Semiconductors | Technology |
| `healthcare_it` | Healthcare IT | Healthcare |
| `pharma_biotech` | Pharma & Biotech | Healthcare |
| `medical_devices` | Medical Devices | Healthcare |
| `asset_management` | Asset Management | Financial Services |
| `banking` | Banking | Financial Services |
| `insurance` | Insurance | Financial Services |
| `residential` | Residential | Real Estate |
| `commercial` | Commercial | Real Estate |
| `industrial_re` | Industrial | Real Estate |
| `energy_renewables_infra` | Energy & Renewables | Infrastructure |
| `transportation` | Transportation | Infrastructure |
| `utilities` | Utilities | Infrastructure |
| `retail` | Retail | Consumer |
| `food_beverage` | Food & Beverage | Consumer |
| `luxury` | Luxury | Consumer |
| `manufacturing` | Manufacturing | Industrials |
| `logistics` | Logistics | Industrials |
| `chemicals` | Chemicals | Industrials |
| `oil_gas` | Oil & Gas | Energy |
| `renewables` | Renewables | Energy |
| `power_generation` | Power Generation | Energy |
| `media` | Media | Media & Telecom |
| `telecom` | Telecom | Media & Telecom |
| `consulting` | Consulting | Business Services |
| `outsourcing` | Outsourcing | Business Services |
| `hr_staffing` | HR & Staffing | Business Services |

Note: `sub_sector` has no FK to `sector` in the `ref_data` table — they are separate category rows. The parent mapping above is documentation only. Downstream phases use both categories independently via JSONB arrays.

### transaction_type (REFDATA-04)
`equity`, `credit`, `preferred_equity`, `mezzanine`, `growth_equity`, `buyout`, `debt_advisory`, `ma_advisory`

### tier (REFDATA-05)
`tier_1`, `tier_2`, `tier_3`

### contact_type (REFDATA-06)
`lp`, `gp`, `advisor`, `management`, `lender`, `co_investor`, `strategic`

### company_type (REFDATA-07)
`financial_sponsor`, `strategic`, `family_office`, `sovereign_wealth_fund`, `pension_fund`, `insurance_company`, `bank`, `operating_company`

### deal_source_type (REFDATA-08)
`proprietary`, `bank`, `advisor`, `management`, `portfolio_company`, `existing_lp`

### passed_dead_reason (REFDATA-09)
`valuation`, `diligence`, `market_conditions`, `competitive`, `strategic_fit`, `timing`, `management`, `no_follow_up`

### investor_type (REFDATA-10)
`swf`, `pension_super`, `corporate`, `family_office`, `financial_sponsor`, `insurance`, `bank`

---

## Code Examples

### Full RefDataCreate/Update/Response schema

```python
# Source: backend/schemas/contacts.py pattern (verified)
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RefDataCreate(BaseModel):
    category: str
    value: str
    label: str
    position: int = 0


class RefDataUpdate(BaseModel):
    label: str | None = None
    position: int | None = None
    is_active: bool | None = None


class RefDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID | None = None
    category: str
    value: str
    label: str
    position: int
    is_active: bool
    created_at: datetime
```

### Service create and update methods

```python
# Source: ContactService pattern (verified)
async def create(self, payload: RefDataCreate) -> RefDataResponse:
    item = RefData(
        org_id=self.current_user.org_id,
        category=payload.category,
        value=payload.value,
        label=payload.label,
        position=payload.position,
    )
    self.db.add(item)
    await self.db.commit()
    await self.db.refresh(item)
    return RefDataResponse.model_validate(item)

async def update(self, item_id: UUID, payload: RefDataUpdate) -> RefDataResponse:
    stmt = select(RefData).where(
        RefData.id == item_id,
        or_(RefData.org_id == self.current_user.org_id, RefData.org_id.is_(None)),
    )
    item = (await self.db.execute(stmt)).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference item not found")
    if payload.label is not None:
        item.label = payload.label
    if payload.position is not None:
        item.position = payload.position
    if payload.is_active is not None:
        item.is_active = payload.is_active
    await self.db.commit()
    await self.db.refresh(item)
    return RefDataResponse.model_validate(item)
```

---

## Environment Availability

Step 2.6: All dependencies are code/config changes. No external services beyond the existing SQLite test DB and the running app are needed.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Backend | Assumed available (Phase 1 complete) | — | — |
| SQLite (aiosqlite) | Tests | Assumed available | — | — |
| Alembic | Migration | Pinned in pyproject.toml | 1.13.x | — |

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio 0.23.x |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest backend/tests/test_ref_data.py -x` |
| Full suite command | `pytest backend/tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REFDATA-01 | `ref_data` table created by migration | integration | `pytest backend/tests/test_ref_data.py::test_ref_data_table_exists -x` | ❌ Wave 0 |
| REFDATA-02 | All 10 categories present after upgrade | integration | `pytest backend/tests/test_ref_data.py::test_all_categories_seeded -x` | ❌ Wave 0 |
| REFDATA-03–10 | Seed row counts per category | integration | `pytest backend/tests/test_ref_data.py::test_seed_values -x` | ❌ Wave 0 |
| REFDATA-11 | GET returns active items ordered by position | integration | `pytest backend/tests/test_ref_data.py::test_get_ref_data_by_category -x` | ❌ Wave 0 |
| REFDATA-12 | POST creates item; non-admin gets 403 | integration | `pytest backend/tests/test_ref_data.py::test_create_ref_data_auth -x` | ❌ Wave 0 |
| REFDATA-13 | PATCH updates label/position/is_active | integration | `pytest backend/tests/test_ref_data.py::test_patch_ref_data -x` | ❌ Wave 0 |
| REFDATA-14 | Deactivated item absent from GET | integration | `pytest backend/tests/test_ref_data.py::test_soft_delete_hides_item -x` | ❌ Wave 0 |
| REFDATA-15 | FK ondelete="SET NULL" — verified in Phase 3–5 table creation | — | N/A this phase | N/A |

**Testing note on seeding:** Tests use `Base.metadata.create_all` (via `setup_db` fixture), not Alembic migrations. The `0002_pe_ref_data.py` migration seed runs only when Alembic runs. For tests, seed data must be inserted by the test fixture itself. One approach: a `seed_ref_data` pytest-asyncio fixture in `conftest.py` that bulk-inserts the same rows programmatically so tests are migration-independent.

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_ref_data.py -x`
- **Per wave merge:** `pytest backend/tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_ref_data.py` — covers REFDATA-01 through REFDATA-14
- [ ] `seed_ref_data` fixture in `backend/tests/conftest.py` — injects seed rows for tests that require them
- [ ] `frontend/src/__tests__/RefSelect.test.jsx` — tests `<RefSelect>` renders options from mocked `useRefData`

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `SQLAlchemy Column(...)` | `mapped_column(...)` with `Mapped[T]` | SQLAlchemy 2.0 | All new models must use `Mapped`/`mapped_column`; `Column` still works but is legacy |
| `Optional[X]` | `X \| None` | Python 3.10+ | Project uses union syntax throughout; new code must follow |
| `session.query()` | `select(Model)` + `session.execute()` | SQLAlchemy 2.0 | CONVENTIONS.md explicitly prohibits `session.query()` |
| TanStack Query v4 | TanStack Query v5 | 2023 | `useQuery` API unchanged for basic use; `onSuccess` callback removed in v5 — use `useEffect` or mutation `onSuccess` instead |

**Deprecated/outdated:**
- `from typing import Optional`: project uses `X | None` union syntax; new code must not import `Optional`
- Bare `[]` or `{}` as Pydantic field defaults: must use `Field(default_factory=list)` / `Field(default_factory=dict)`

---

## Open Questions

1. **UUID storage in SQLite migration DDL**
   - What we know: The ORM model uses `Mapped[UUID]` with `default=uuid4`. SQLite stores UUIDs as strings. The existing `0001_initial.py` uses `metadata.create_all` which lets SQLAlchemy handle the type mapping automatically.
   - What's unclear: Whether `op.create_table` with `sa.Column("id", sa.String(36))` correctly interoperates with the ORM's `Mapped[UUID]` in tests.
   - Recommendation: Use `sa.String(36)` in migration DDL for SQLite compat. The ORM's `mapped_column(primary_key=True, default=uuid4)` will handle UUID↔string conversion transparently via SQLAlchemy's type coercion. This is the same pattern used implicitly by `0001_initial.py`.

2. **`company_sub_type` category**
   - What we know: REFDATA-02 lists `company_sub_type` as a required category, but REQUIREMENTS.md has no REFDATA-XX entry listing its seed values (unlike all other categories which have REFDATA-03 through REFDATA-10 coverage).
   - What's unclear: Whether `company_sub_type` is intentionally left empty at seed time or was accidentally omitted from requirements.
   - Recommendation: Seed `company_sub_type` as an empty category (no rows) at migration time. Phase 6 Admin UI allows org admins to populate it. This is consistent with D-01 logic (sub_sector got values; other categories use REQUIREMENTS.md lists). Document the gap in the migration comment.

---

## Sources

### Primary (HIGH confidence)
- `backend/models.py` — SQLAlchemy 2.x model patterns, existing org-scoped table structure
- `alembic/versions/0001_initial.py` — migration file structure (anti-pattern reference for 0002)
- `alembic/env.py` — migration execution environment, `DATABASE_URL_SYNC` config
- `backend/services/contacts.py` — canonical `(db, current_user)` service constructor, `_base_stmt`, async query patterns
- `backend/schemas/contacts.py` — `ConfigDict(from_attributes=True)`, `Create`/`Update`/`Response` naming
- `backend/api/dependencies.py` — `get_current_user`, `require_role`, `get_db` Depends factories (verified full file)
- `backend/api/main.py` — router registration loop, import pattern
- `frontend/src/hooks/useContacts.js` — `useQuery` thin wrapper pattern
- `frontend/src/api/contacts.js` — Axios API module pattern
- `frontend/src/components/ui/select.jsx` — native `<select>` wrapper (not Radix UI)
- `backend/tests/conftest.py` — test fixture infrastructure, `setup_db`, `clean_db`, `seeded_org`
- `.planning/codebase/CONVENTIONS.md` — naming rules, async patterns, Pydantic rules
- `.planning/codebase/ARCHITECTURE.md` — request lifecycle, service layer, TanStack Query key patterns
- `pyproject.toml` — pytest config (`asyncio_mode = "auto"`, `testpaths`)

### Secondary (MEDIUM confidence)
- `.planning/phases/02-reference-data-system/02-CONTEXT.md` — locked decisions D-01 through D-06

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in pyproject.toml and node_modules
- Architecture: HIGH — all patterns verified directly from source files
- Pitfalls: HIGH (pitfalls 2–6) / MEDIUM (pitfall 1 — SQLite NULL in unique constraint is a known SQL behavior, not specifically tested in this codebase)
- Seed data: HIGH — REFDATA-03 through REFDATA-10 values are verbatim from REQUIREMENTS.md; sub_sector values are per D-01 (Claude's discretion)

**Research date:** 2026-03-26
**Valid until:** 2026-09-26 (stable stack — SQLAlchemy 2.x, FastAPI 0.11x, TanStack Query v5 are all stable)
