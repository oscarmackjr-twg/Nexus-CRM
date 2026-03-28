# Phase 5: DealCounterparty & DealFunding — Research

**Researched:** 2026-03-27
**Domain:** FastAPI nested sub-entity CRUD + SQLAlchemy aliased multi-join + React inline grid editing with date pickers
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Tab order: Profile | Counterparties | Funding | Activity | Tasks | AI Insights
- **D-02:** Counterparties as horizontally scrollable data table; company column sticky left; no column hiding
- **D-03:** Grid column order: Company (sticky), Tier, Investor Type, NDA Sent, NDA Signed, NRL, Materials, VDR, Feedback, Next Steps, Actions
- **D-04:** Stage date cells show abbreviated date ("Mar 15"); clicking any cell (set or unset) opens a date picker — always date picker, no click-to-stamp
- **D-05:** Stage dates editable directly from grid row — no modal required for date editing
- **D-06:** Add Counterparty modal fields: Company (required), Tier, Investor Type, Primary Contact Name, Check Size (amount+currency), Next Steps
- **D-07:** Edit modal exposes all fields including AUM, Primary Contact Email/Phone, Notes, all 6 stage dates as date inputs
- **D-08:** Empty state: "No counterparties tracked yet. Add the first investor to start tracking stage progression." + "+ Add Counterparty" button
- **D-09:** Funding table: Provider, Status, Projected Commitment, Actual Commitment, Commitment Date, Terms preview, Actions
- **D-10:** Add Funding modal: Capital Provider (company select), Status (RefSelect deal_funding_status), Projected Commitment, Actual Commitment, Commitment Date, Terms, Comments/Next Steps
- **D-11:** Edit funding uses same modal as add; no inline editing on funding table rows
- **D-12:** Funding empty state: "No funding commitments recorded. Add a capital provider to track commitments." + "+ Add Funding" button
- **D-13:** Both tables use REFDATA-15 FK pattern: `ForeignKey('ref_data.id', ondelete='SET NULL')`
- **D-14:** `company_id` on deal_counterparties: `ForeignKey('companies.id', ondelete='SET NULL')`
- **D-15:** `capital_provider_id` on deal_funding: `ForeignKey('companies.id', ondelete='SET NULL')`
- **D-16:** List endpoints resolve company name and all ref_data labels in a single JOIN query — no N+1; default page size 50
- **D-17:** Both tables have `deal_id FK cascade delete`
- **D-18:** `deal_counterparties` has `UniqueConstraint(deal_id, company_id)`
- **D-19:** Counterparties query key: `['deal-counterparties', dealId]`
- **D-20:** Funding query key: `['deal-funding', dealId]`
- **D-21:** Deactivated ref_data label renders as `"---"` — no broken display

### Claude's Discretion

- Exact column widths for stage date columns in the grid
- Whether date picker in grid appears as a popover anchored to cell or floating dialog
- Alembic migration numbering — pick next available numbers
- Whether `position` column is used for drag-to-reorder (probably not this phase)

### Deferred Ideas (OUT OF SCOPE)

- Per-counterparty interaction log (calls, meetings, emails) — v2 (INTLOG-01/02)
- Drag-to-reorder counterparties — not this phase
- Aggregate counterparty funnel view across all deals — v2 analytics (ANALYTICS-02)
- Investor relationship history — v2 (ANALYTICS-03)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CPARTY-01 | deal_counterparties table with id, org_id, deal_id FK cascade, company_id FK set null, primary_contact_name/email/phone, position | Migration 0010; ORM model DealCounterparty |
| CPARTY-02 | Stage date columns: nda_sent_at, nda_signed_at, nrl_signed_at, intro_materials_sent_at, vdr_access_granted_at, feedback_received_at (Date, nullable) | All 6 columns as `mapped_column(Date, nullable=True)` |
| CPARTY-03 | tier_id FK, investor_type_id FK, next_steps Text, notes Text | REFDATA-15 pattern; `ForeignKey('ref_data.id', ondelete='SET NULL')` |
| CPARTY-04 | check_size_amount/currency, aum_amount/currency | Numeric(18,2) + String(3) pairs — same as deal financials |
| CPARTY-05 | GET list resolves company name, stage dates, tier label, investor_type label — single query, no N+1 | aliased(RefData) pattern from DealService; aliased(Company) for company name |
| CPARTY-06 | POST /deals/{deal_id}/counterparties creates counterparty | Nested router attached to deals router |
| CPARTY-07 | PATCH /deals/{deal_id}/counterparties/{id} — updates including individual stage date columns | Pydantic Update schema with all Optional fields |
| CPARTY-08 | DELETE /deals/{deal_id}/counterparties/{id} | 204 No Content response |
| CPARTY-09 | Counterparties tab grid: Company, Tier, Investor Type, 6 stage date columns, Next Steps | Horizontally scrollable table with sticky first column |
| CPARTY-10 | Add counterparty from tab | Dialog with minimal fields (D-06) |
| CPARTY-11 | Edit counterparty inline (stage dates) and via modal (all fields) | Date picker on cell click; full edit Dialog via Actions button |
| CPARTY-12 | Remove counterparty from tab | DELETE mutation + invalidateQueries |
| FUNDING-01 | deal_funding table: id, org_id, deal_id FK cascade, capital_provider_id FK set null, status_id FK ref_data | Migration 0011; ORM model DealFunding |
| FUNDING-02 | projected_commitment_amount/currency, actual_commitment_amount/currency, actual_commitment_date | Numeric(18,2) + String(3) pairs + Date |
| FUNDING-03 | terms Text, comments_next_steps Text | Standard Text columns |
| FUNDING-04 | GET /deals/{deal_id}/funding resolves capital provider company name | aliased(Company) join |
| FUNDING-05 | POST /deals/{deal_id}/funding creates entry | Nested router |
| FUNDING-06 | PATCH /deals/{deal_id}/funding/{id} updates entry | Pydantic Update schema all Optional |
| FUNDING-07 | DELETE /deals/{deal_id}/funding/{id} | 204 No Content |
| FUNDING-08 | Funding tab: Provider, Status, Projected Commitment, Actual Commitment, Commitment Date, Terms | Standard table (no horizontal scroll) |
| FUNDING-09 | Add, edit, remove funding entries | Dialog for add/edit; DELETE mutation for remove |
</phase_requirements>

---

## Summary

Phase 5 adds two sub-entity CRUD systems (DealCounterparty and DealFunding) anchored to the existing Deal model. The backend is straightforward: two new Alembic migrations (0010 and 0011 — migration 0009 is already taken by `deal_team_members`), two ORM models following the Fund/DealTeamMember patterns established in Phase 4, two service classes using the aliased multi-join pattern from DealService, and two new route files registered as nested routers under `/deals/{deal_id}/...`. A new `deal_funding_status` ref_data category must be seeded in migration 0010 or 0011.

The frontend complexity is concentrated in Plan 05-04. DealDetailPage already uses TanStack Query, `Dialog`, `RefSelect`, and the `Tabs` component — all reusable directly. The Counterparties tab requires a horizontally scrollable grid with a sticky company column and per-cell date picker inline editing (click on any date cell opens a date picker popover without opening the full edit modal). The Funding tab is a simpler standard table with modal-only editing.

**Primary recommendation:** Follow the FundService aliased-join pattern for both new services. Use `overflowX: scroll` + `position: sticky; left: 0` CSS for the counterparty grid. Use a native `<input type="date">` or a lightweight popover for inline stage date editing — no heavy date library needed given existing patterns.

---

## Standard Stack

### Core (all already in project — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy 2.0 | Existing | ORM models + async queries | Project standard |
| Alembic | Existing | Migration files 0010, 0011 | Project standard |
| FastAPI | Existing | Nested APIRouter for sub-entity routes | Project standard |
| Pydantic v2 | Existing | Create/Update/Response schemas | Project standard |
| TanStack Query | Existing | useQuery + useMutation in frontend | Project standard |
| React | Existing | DealDetailPage JSX | Project standard |
| Tailwind CSS | Existing | Styling for grid, sticky column | Project standard |

### No New Dependencies

Phase 5 introduces no new packages. All required libraries are already installed:
- Date formatting: use existing `formatDate` from `@/lib/utils` for display; native `<input type="date">` for editing
- Table scrolling: pure CSS (`overflow-x: auto`, `position: sticky`)
- Modals: existing `Dialog` from `@/components/ui/dialog`
- Ref dropdowns: existing `RefSelect` component
- Toast notifications: existing `sonner`

---

## Architecture Patterns

### Migration Numbering (CRITICAL)

The ROADMAP stubs say "0009_deal_counterparties.py" but **migration 0009 is already taken** by `deal_team_members`. The correct numbers are:

- **0010_deal_counterparties.py** — creates `deal_counterparties` table + seeds `deal_funding_status` ref_data
- **0011_deal_funding.py** — creates `deal_funding` table

Revision chain: `0009_deal_team_members` → `0010_deal_counterparties` → `0011_deal_funding`

### ORM Model Pattern (from Fund + DealTeamMember in models.py)

New ORM classes go in `backend/models.py` in dependency order — after `Deal` class (line ~329), before `DealActivity` class (line ~421):

```python
class DealCounterparty(Base):
    __tablename__ = "deal_counterparties"
    __table_args__ = (
        UniqueConstraint("deal_id", "company_id", name="uq_deal_counterparty_deal_company"),
        Index("ix_deal_counterparties_deal_id", "deal_id"),
        Index("ix_deal_counterparties_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    deal_id: Mapped[UUID] = mapped_column(Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    primary_contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    primary_contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    primary_contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nda_sent_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nda_signed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nrl_signed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    intro_materials_sent_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    vdr_access_granted_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    feedback_received_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    tier_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    investor_type_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    check_size_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    check_size_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    aum_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    aum_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    deal: Mapped["Deal"] = relationship(back_populates="counterparties", lazy="raise")
    company: Mapped[Optional["Company"]] = relationship(lazy="raise")
    tier: Mapped[Optional["RefData"]] = relationship(foreign_keys=[tier_id], lazy="raise")
    investor_type: Mapped[Optional["RefData"]] = relationship(foreign_keys=[investor_type_id], lazy="raise")
```

**Note:** `lazy="raise"` on ALL relationships — service layer uses explicit JOINs, never relationship traversal.

**Deal model also needs back-ref:**
```python
# Add to Deal class relationships:
counterparties: Mapped[list["DealCounterparty"]] = relationship(cascade="all, delete-orphan", lazy="raise")
funding: Mapped[list["DealFunding"]] = relationship(cascade="all, delete-orphan", lazy="raise")
```

**Organization model also needs back-refs** (to maintain cascade chain):
```python
deal_counterparties: Mapped[list["DealCounterparty"]] = relationship(back_populates="org", cascade="all, delete-orphan")
deal_funding: Mapped[list["DealFunding"]] = relationship(back_populates="org", cascade="all, delete-orphan")
```

Wait — DealCounterparty.org_id has `ondelete="CASCADE"` on the FK to organizations, so the DB handles it; the ORM relationship on Organization is optional but recommended for ORM-level cascade awareness. Check whether Fund/DealActivity follow this — Fund has `org: Mapped[Organization] = relationship(back_populates="funds")` and Organization has `funds` listed. Follow the same pattern.

### Service Layer Pattern (from DealService / FundService)

```python
# Source: backend/services/deals.py — established aliased multi-join pattern
from sqlalchemy.orm import aliased

TierRef = aliased(RefData)
InvestorTypeRef = aliased(RefData)
CpartyCompany = aliased(Company)

class DealCounterpartyService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    async def list_for_deal(self, deal_id: UUID, page: int = 1, size: int = 50) -> DealCounterpartyListResponse:
        # Verify deal belongs to org first (404 if not)
        # Single JOIN query — resolves company_name, tier_label, investor_type_label
        stmt = (
            select(
                DealCounterparty,
                CpartyCompany.name.label("company_name"),
                TierRef.label.label("tier_label"),
                InvestorTypeRef.label.label("investor_type_label"),
            )
            .outerjoin(CpartyCompany, CpartyCompany.id == DealCounterparty.company_id)
            .outerjoin(TierRef, TierRef.id == DealCounterparty.tier_id)
            .outerjoin(InvestorTypeRef, InvestorTypeRef.id == DealCounterparty.investor_type_id)
            .where(
                DealCounterparty.deal_id == deal_id,
                DealCounterparty.org_id == self.current_user.org_id,
            )
            .order_by(DealCounterparty.position.nullslast(), DealCounterparty.created_at)
        )
        # Apply page/size clamp (max 50 per D-16)
```

**Key insight from Phase 4 STATE.md note:** "FundService aliased(RefData) label-join pattern established — reuse for DealCounterparty and DealFunding services in Phase 5." This is the canonical pattern.

**Null label handling (D-21):**
```python
# In _counterparty_response():
tier_label = row.tier_label or "---"
investor_type_label = row.investor_type_label or "---"
```

### Route Registration Pattern (from main.py)

Two new route files, each registered in `main.py`:

```python
# backend/api/routes/counterparties.py
router = APIRouter(prefix="/deals/{deal_id}/counterparties", tags=["counterparties"])

# backend/api/routes/funding.py
router = APIRouter(prefix="/deals/{deal_id}/funding", tags=["funding"])
```

In `main.py`, add both to the import and the router loop:
```python
from backend.api.routes import ... counterparties, funding ...
# then add counterparties.router and funding.router to the loop
```

### Pydantic Schema Pattern

```python
# backend/schemas/counterparties.py
from __future__ import annotations
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class DealCounterpartyCreate(BaseModel):
    company_id: UUID | None = None          # required by business logic but nullable FK
    tier_id: UUID | None = None
    investor_type_id: UUID | None = None
    primary_contact_name: str | None = None
    check_size_amount: Decimal | None = None
    check_size_currency: str | None = None
    next_steps: str | None = None

class DealCounterpartyUpdate(BaseModel):
    company_id: UUID | None = None
    tier_id: UUID | None = None
    investor_type_id: UUID | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    primary_contact_phone: str | None = None
    nda_sent_at: date | None = None
    nda_signed_at: date | None = None
    nrl_signed_at: date | None = None
    intro_materials_sent_at: date | None = None
    vdr_access_granted_at: date | None = None
    feedback_received_at: date | None = None
    check_size_amount: Decimal | None = None
    check_size_currency: str | None = None
    aum_amount: Decimal | None = None
    aum_currency: str | None = None
    next_steps: str | None = None
    notes: str | None = None

class DealCounterpartyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    org_id: UUID
    deal_id: UUID
    company_id: UUID | None
    company_name: str | None       # resolved from JOIN
    tier_id: UUID | None
    tier_label: str | None         # resolved, "---" if deactivated
    investor_type_id: UUID | None
    investor_type_label: str | None
    primary_contact_name: str | None
    primary_contact_email: str | None
    primary_contact_phone: str | None
    nda_sent_at: date | None
    nda_signed_at: date | None
    nrl_signed_at: date | None
    intro_materials_sent_at: date | None
    vdr_access_granted_at: date | None
    feedback_received_at: date | None
    check_size_amount: Decimal | None
    check_size_currency: str | None
    aum_amount: Decimal | None
    aum_currency: str | None
    next_steps: str | None
    notes: str | None
    position: int | None
    created_at: datetime
```

### Frontend Pattern: Horizontally Scrollable Grid with Sticky Column

The standard approach using Tailwind — confirmed by examining DealDetailPage.jsx which already uses overflow patterns:

```jsx
{/* Counterparties Tab */}
<div className="overflow-x-auto">
  <table className="min-w-full text-sm">
    <thead>
      <tr>
        <th className="sticky left-0 z-10 bg-white px-3 py-2 text-left font-medium">Company</th>
        <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Tier</th>
        {/* ... more columns ... */}
      </tr>
    </thead>
    <tbody>
      {counterparties.map((cp) => (
        <CounterpartyRow key={cp.id} cp={cp} dealId={id} onEdit={...} onDelete={...} />
      ))}
    </tbody>
  </table>
</div>
```

**Sticky column implementation:** `sticky left-0 z-10 bg-white` on both `<th>` and `<td>` for the company column. `bg-white` is critical — without it the sticky cell shows content behind it when scrolling.

### Frontend Pattern: Inline Stage Date Editing (D-04, D-05)

Click on any date cell opens a date picker directly in the grid without opening the edit modal. Implementation options:

**Option A — Native HTML input type="date" revealed on click (recommended):**
```jsx
function StageDateCell({ value, field, counterpartyId, dealId }) {
  const [editing, setEditing] = useState(false);
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (newDate) => patchCounterparty(dealId, counterpartyId, { [field]: newDate || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-counterparties', dealId] });
      setEditing(false);
    },
  });

  if (editing) {
    return (
      <input
        type="date"
        autoFocus
        defaultValue={value || ''}
        onBlur={(e) => mutation.mutate(e.target.value || null)}
        onKeyDown={(e) => e.key === 'Escape' && setEditing(false)}
        className="w-28 border rounded px-1 py-0.5 text-xs"
      />
    );
  }
  return (
    <button
      onClick={() => setEditing(true)}
      className="text-left text-xs hover:underline text-muted-foreground w-full"
    >
      {value ? formatAbbrevDate(value) : <span className="text-muted-foreground/40">—</span>}
    </button>
  );
}
```

**Option B — Popover with date picker:** More complex, uses Radix UI Popover (already in project as shadcn). Overkill for this use case.

**Recommendation: Option A.** Native `input[type=date]` is universally supported, requires no new libraries, and fits the "no click-to-stamp, always date picker" requirement from D-04. The `autoFocus` + `onBlur` pattern auto-saves when focus leaves.

**Abbreviated date display helper:**
```js
// Add to @/lib/utils.js or inline in component
export function formatAbbrevDate(isoStr) {
  if (!isoStr) return '';
  const [year, month, day] = isoStr.split('-');
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${months[parseInt(month, 10) - 1]} ${parseInt(day, 10)}`;
}
// Example: "2026-03-15" → "Mar 15"
```

### Frontend Pattern: Add/Edit Modal

Reuse `Dialog` pattern from DealDetailPage (fund modal, lines ~208-218):

```jsx
// Add Counterparty modal
const [addOpen, setAddOpen] = useState(false);
const [addForm, setAddForm] = useState({ company_id: '', tier_id: '', investor_type_id: '', primary_contact_name: '', check_size_amount: '', check_size_currency: 'USD', next_steps: '' });

const createMutation = useMutation({
  mutationFn: (data) => createCounterparty(id, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['deal-counterparties', id] });
    setAddOpen(false);
    toast.success('Counterparty added');
  },
  onError: () => toast.error('Failed to add counterparty'),
});
```

### Frontend API Module Pattern (from funds.js)

```js
// frontend/src/api/counterparties.js
import client from './client';

export const getCounterparties = async (dealId) =>
  (await client.get(`/deals/${dealId}/counterparties`)).data;
export const createCounterparty = async (dealId, data) =>
  (await client.post(`/deals/${dealId}/counterparties`, data)).data;
export const updateCounterparty = async (dealId, id, data) =>
  (await client.patch(`/deals/${dealId}/counterparties/${id}`, data)).data;
export const deleteCounterparty = async (dealId, id) =>
  client.delete(`/deals/${dealId}/counterparties/${id}`);

// frontend/src/api/funding.js
import client from './client';

export const getFunding = async (dealId) =>
  (await client.get(`/deals/${dealId}/funding`)).data;
export const createFunding = async (dealId, data) =>
  (await client.post(`/deals/${dealId}/funding`, data)).data;
export const updateFunding = async (dealId, id, data) =>
  (await client.patch(`/deals/${dealId}/funding/${id}`, data)).data;
export const deleteFunding = async (dealId, id) =>
  client.delete(`/deals/${dealId}/funding/${id}`);
```

### ref_data Seed: deal_funding_status

Must be seeded in migration 0010 or 0011. Follow the `0007_fund.py` pattern (inline `sa.table` reference):

```python
# Values from CONTEXT.md code_context section
deal_funding_status_seeds = [
    {"label": "Soft Circle",  "value": "soft_circle",  "position": 1},
    {"label": "Hard Circle",  "value": "hard_circle",  "position": 2},
    {"label": "Committed",    "value": "committed",    "position": 3},
    {"label": "Funded",       "value": "funded",       "position": 4},
    {"label": "Declined",     "value": "declined",     "position": 5},
]
```

### Recommended Project Structure — New Files

```
backend/
├── models.py                          # Add DealCounterparty + DealFunding ORM classes
├── schemas/
│   ├── counterparties.py              # New: Create/Update/Response/ListResponse
│   └── funding.py                    # New: Create/Update/Response/ListResponse
├── services/
│   ├── counterparties.py              # New: DealCounterpartyService
│   └── funding.py                    # New: DealFundingService
├── api/
│   └── routes/
│       ├── counterparties.py          # New: nested router /deals/{deal_id}/counterparties
│       └── funding.py                # New: nested router /deals/{deal_id}/funding
└── api/main.py                        # Add counterparties + funding imports to router loop

alembic/versions/
├── 0010_deal_counterparties.py        # New: deal_counterparties table + deal_funding_status seed
└── 0011_deal_funding.py              # New: deal_funding table

frontend/src/
├── api/
│   ├── counterparties.js             # New: CRUD API calls
│   └── funding.js                   # New: CRUD API calls
└── pages/
    └── DealDetailPage.jsx            # Modify: add 2 tabs + queries + mutations
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-alias ref_data JOIN | Custom dict lookup after query | `aliased(RefData)` in single SELECT | N+1 avoided, single round-trip, established in DealService |
| Date formatting "Mar 15" | Custom date format function | Inline split/months array (3 lines) | No library needed; `formatDate` in utils already exists |
| Sticky column scrolling | JS scroll listener | CSS `sticky left-0 z-10 bg-white` | Native CSS handles this perfectly |
| Inline date editing | Calendar widget | `<input type="date">` with autoFocus + onBlur | Zero dependencies, consistent with browser date picker |
| Org scoping verification | Skip deal ownership check | Verify deal belongs to `current_user.org_id` before proceeding | Security requirement — same pattern in DealService |

---

## Common Pitfalls

### Pitfall 1: Stale Migration Number from ROADMAP
**What goes wrong:** ROADMAP stubs reference `0009_deal_counterparties.py` and `0010_deal_funding.py`, but `0009_deal_team_members.py` already exists. Writing a migration with `revision = "0009_deal_counterparties"` and `down_revision = "0008_deal_pe_fields"` creates a branched migration history — Alembic will error on `upgrade head` with "Multiple head revisions".
**Why it happens:** ROADMAP was written before Plan 04-02 created migration 0009.
**How to avoid:** Use `0010_deal_counterparties` (down_revision: `0009_deal_team_members`) and `0011_deal_funding` (down_revision: `0010_deal_counterparties`).
**Warning signs:** `alembic heads` returns more than one head after adding the migration.

### Pitfall 2: Missing lazy="raise" on ORM Relationships
**What goes wrong:** Without `lazy="raise"`, SQLAlchemy silently fires SELECT queries when relationship attributes are accessed — causing N+1 queries in the list endpoint.
**Why it happens:** SQLAlchemy default `lazy="select"` loads relationships lazily on attribute access.
**How to avoid:** Declare `lazy="raise"` on all relationships in DealCounterparty and DealFunding. Only explicit JOIN in the service query resolves data. Established pattern in codebase (CONVENTIONS.md line 95).
**Warning signs:** `sqlalchemy.exc.MissingGreenlet` errors with asyncio, or unexpectedly high query counts in logs.

### Pitfall 3: Multiple FKs to Same Table Without Aliases
**What goes wrong:** `deal_counterparties` has two FKs to `ref_data` (tier_id, investor_type_id) and one FK to `companies`. A naïve `outerjoin(RefData, RefData.id == DealCounterparty.tier_id)` then another `outerjoin(RefData, RefData.id == DealCounterparty.investor_type_id)` causes a SQLAlchemy error about ambiguous join conditions.
**Why it happens:** SQLAlchemy needs distinct table aliases to distinguish the two RefData joins.
**How to avoid:** `TierRef = aliased(RefData)` and `InvestorTypeRef = aliased(RefData)` — then `.outerjoin(TierRef, TierRef.id == DealCounterparty.tier_id)`. Established in DealService (lines 43-48).
**Warning signs:** `sqlalchemy.exc.InvalidRequestError: Can't determine join condition` at query execution time.

### Pitfall 4: UniqueConstraint Violation on Company Re-Add
**What goes wrong:** A user tries to add a company to a deal's counterparties list a second time (after deleting and re-adding, or by mistake). The DB enforces `UniqueConstraint(deal_id, company_id)` and returns a DB integrity error that surfaces as a 500 unless caught.
**Why it happens:** The constraint correctly prevents duplicates but the service doesn't provide a friendly error message.
**How to avoid:** In `create()`, check for existing entry before insert:
```python
existing = await self.db.execute(select(DealCounterparty).where(
    DealCounterparty.deal_id == deal_id,
    DealCounterparty.company_id == payload.company_id,
))
if existing.scalar_one_or_none():
    raise HTTPException(status_code=400, detail="This company is already a counterparty on this deal")
```
**Warning signs:** `sqlalchemy.exc.IntegrityError: UNIQUE constraint failed` in server logs.

### Pitfall 5: Sticky Column Without Background Color
**What goes wrong:** The Company column is marked `sticky left-0` but when the user scrolls horizontally, table cell content from other columns bleeds through/under the sticky cell — looks broken.
**Why it happens:** Sticky positioning removes the element from the paint order unless it has an explicit background color.
**How to avoid:** Apply `bg-white` (or the card's background color) to both the `<th>` and every `<td>` in the sticky column. If the table has alternating row colors, the sticky cell background must match.
**Warning signs:** Visual "bleed-through" when scrolling the counterparties grid.

### Pitfall 6: deal_funding_status Not Seeded
**What goes wrong:** The Funding tab's Status dropdown (`<RefSelect category="deal_funding_status">`) returns zero items because the ref_data seed was not included in the migration.
**Why it happens:** The new category doesn't exist in the existing 0002 seed migration and requires explicit insertion.
**How to avoid:** Include the `deal_funding_status` seed rows in migration 0010 (using the same `sa.table` + `op.bulk_insert` pattern from `0007_fund.py`).
**Warning signs:** RefSelect shows "No options available" for the Status field on the Add Funding modal.

### Pitfall 7: Inline Date Edit Overwrites Unrelated Fields
**What goes wrong:** The PATCH endpoint updates only the fields present in the payload. If the frontend sends `{ nda_sent_at: "2026-03-15" }`, the service should update ONLY that field. If the service rebuilds the full object from the payload, other None fields wipe existing data.
**Why it happens:** Using `payload.model_dump()` (not `exclude_unset=True`) replaces all fields with defaults.
**How to avoid:** Use `payload.model_dump(exclude_unset=True)` in the update service method. Established pattern in Phase 3/4 services.
**Warning signs:** Setting one stage date clears other previously set stage dates.

---

## Code Examples

### Migration 0010 Structure

```python
"""deal_counterparties — create table and seed deal_funding_status

Revision ID: 0010_deal_counterparties
Revises: 0009_deal_team_members
Create Date: 2026-03-27
"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision: str = "0010_deal_counterparties"
down_revision: Union[str, Sequence[str]] = "0009_deal_team_members"
branch_labels = None
depends_on = None

ref_data_table = sa.table(
    "ref_data",
    sa.column("id", sa.Uuid),
    sa.column("org_id", sa.Uuid),
    sa.column("category", sa.String),
    sa.column("value", sa.String),
    sa.column("label", sa.String),
    sa.column("position", sa.Integer),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime),
)

def upgrade() -> None:
    op.create_table(
        "deal_counterparties",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deal_id", sa.Uuid(), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("primary_contact_name", sa.String(255), nullable=True),
        sa.Column("primary_contact_email", sa.String(255), nullable=True),
        sa.Column("primary_contact_phone", sa.String(50), nullable=True),
        sa.Column("nda_sent_at", sa.Date, nullable=True),
        sa.Column("nda_signed_at", sa.Date, nullable=True),
        sa.Column("nrl_signed_at", sa.Date, nullable=True),
        sa.Column("intro_materials_sent_at", sa.Date, nullable=True),
        sa.Column("vdr_access_granted_at", sa.Date, nullable=True),
        sa.Column("feedback_received_at", sa.Date, nullable=True),
        sa.Column("tier_id", sa.Uuid(), sa.ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True),
        sa.Column("investor_type_id", sa.Uuid(), sa.ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True),
        sa.Column("check_size_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("check_size_currency", sa.String(3), nullable=True),
        sa.Column("aum_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("aum_currency", sa.String(3), nullable=True),
        sa.Column("next_steps", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("position", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("deal_id", "company_id", name="uq_deal_counterparty_deal_company"),
    )
    op.create_index("ix_deal_counterparties_deal_id", "deal_counterparties", ["deal_id"])
    op.create_index("ix_deal_counterparties_company_id", "deal_counterparties", ["company_id"])

    # Seed deal_funding_status
    now = datetime.now(timezone.utc)
    op.bulk_insert(ref_data_table, [
        {"id": uuid4(), "org_id": None, "category": "deal_funding_status", "value": v, "label": l, "position": p, "is_active": True, "created_at": now}
        for v, l, p in [
            ("soft_circle", "Soft Circle", 1),
            ("hard_circle", "Hard Circle", 2),
            ("committed", "Committed", 3),
            ("funded", "Funded", 4),
            ("declined", "Declined", 5),
        ]
    ])

def downgrade() -> None:
    op.drop_index("ix_deal_counterparties_company_id", table_name="deal_counterparties")
    op.drop_index("ix_deal_counterparties_deal_id", table_name="deal_counterparties")
    op.drop_table("deal_counterparties")
    op.execute("DELETE FROM ref_data WHERE category = 'deal_funding_status' AND org_id IS NULL")
```

### Route Handler Pattern (verified from deals.py)

```python
# backend/api/routes/counterparties.py
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import User
from backend.schemas.counterparties import DealCounterpartyCreate, DealCounterpartyListResponse, DealCounterpartyResponse, DealCounterpartyUpdate
from backend.services.counterparties import DealCounterpartyService

router = APIRouter(prefix="/deals/{deal_id}/counterparties", tags=["counterparties"])

@router.get("/", response_model=DealCounterpartyListResponse)
async def list_counterparties(
    deal_id: UUID,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealCounterpartyListResponse:
    return await DealCounterpartyService(db, current_user).list_for_deal(deal_id, page=page, size=size)

@router.post("/", response_model=DealCounterpartyResponse, status_code=status.HTTP_201_CREATED)
async def create_counterparty(
    deal_id: UUID,
    payload: DealCounterpartyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealCounterpartyResponse:
    return await DealCounterpartyService(db, current_user).create(deal_id, payload)

@router.patch("/{counterparty_id}", response_model=DealCounterpartyResponse)
async def update_counterparty(
    deal_id: UUID,
    counterparty_id: UUID,
    payload: DealCounterpartyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealCounterpartyResponse:
    return await DealCounterpartyService(db, current_user).update(deal_id, counterparty_id, payload)

@router.delete("/{counterparty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_counterparty(
    deal_id: UUID,
    counterparty_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await DealCounterpartyService(db, current_user).delete(deal_id, counterparty_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### DealDetailPage Tab Addition Pattern (verified from DealDetailPage.jsx lines 275-281)

```jsx
// Existing tabs at line 275-281 — ADD two new triggers after "profile":
<TabsList>
  <TabsTrigger value="profile">Profile</TabsTrigger>
  <TabsTrigger value="counterparties">Counterparties</TabsTrigger>  {/* NEW */}
  <TabsTrigger value="funding">Funding</TabsTrigger>               {/* NEW */}
  <TabsTrigger value="activity">Activity</TabsTrigger>
  <TabsTrigger value="ai">AI Insights</TabsTrigger>
  <TabsTrigger value="tasks">Tasks</TabsTrigger>
</TabsList>

// Add two new queries at the top of DealDetailPage:
const counterpartiesQuery = useQuery({
  queryKey: ['deal-counterparties', id],
  queryFn: () => getCounterparties(id),
  enabled: Boolean(id),
});
const fundingQuery = useQuery({
  queryKey: ['deal-funding', id],
  queryFn: () => getFunding(id),
  enabled: Boolean(id),
});
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `session.query()` (SQLAlchemy 1.x) | `select()` + `session.execute()` (SQLAlchemy 2.0) | Phase 2+ | All queries use Core select() |
| `Optional[X]` | `X \| None` | Phase 2+ | New code uses union syntax |
| Eager `lazy="select"` on all relationships | `lazy="raise"` on sub-entities | Phase 4 | Prevents accidental N+1 |
| Separate seed step | Seeds embedded in migration | Phase 2 | No manual setup needed |

---

## Open Questions

1. **Should `deal_funding_status` seed go in 0010 or 0011?**
   - What we know: It's needed before the UI renders; logically it's referenced by `deal_funding` table.
   - What's unclear: Minor — either works since both run before UI is used.
   - Recommendation: Include in **0010** (counterparties migration) so it's available even if 0011 has an issue. Functionally identical.

2. **Company selector in Add Counterparty modal — search vs. full list?**
   - What we know: `DealDetailPage` already fetches companies with `size: 200` for the existing company selector. The counterparty modal can reuse this already-fetched list.
   - What's unclear: Whether 200 is enough for larger orgs (but this is consistent with existing pattern).
   - Recommendation: Reuse the existing `companiesQuery` (already fetched for DealDetailPage Profile tab) — no additional query needed.

3. **`position` column — include or omit?**
   - What we know: CONTEXT.md D-Claude's-Discretion says "insert order is fine for this phase."
   - Recommendation: Include the `position` column in the migration as `Integer, nullable=True` (zero cost, allows v2 drag-to-reorder without a migration). Do NOT build drag-to-reorder UI. Service orders by `position.nullslast(), created_at`.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 5 is code/config changes only. All dependencies (Python, Node.js, SQLite, existing packages) already verified operational in prior phases.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `backend/tests/pytest.ini` (`asyncio_mode = auto`) |
| Quick run command | `cd /Users/oscarmack/OpenClaw/nexus-crm && python -m pytest backend/tests/test_deal_sub_entities.py -x -q` |
| Full suite command | `cd /Users/oscarmack/OpenClaw/nexus-crm && python -m pytest backend/tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CPARTY-01 | deal_counterparties table created with correct columns | smoke | `pytest backend/tests/test_deal_sub_entities.py::test_counterparty_migration -x` | ❌ Wave 0 |
| CPARTY-05 | GET list returns single-query result with resolved labels | integration | `pytest backend/tests/test_deal_sub_entities.py::test_list_counterparties_resolves_labels -x` | ❌ Wave 0 |
| CPARTY-06 | POST creates counterparty with correct org_id scoping | integration | `pytest backend/tests/test_deal_sub_entities.py::test_create_counterparty -x` | ❌ Wave 0 |
| CPARTY-07 | PATCH updates individual stage date without overwriting others | integration | `pytest backend/tests/test_deal_sub_entities.py::test_patch_stage_date_partial_update -x` | ❌ Wave 0 |
| CPARTY-08 | DELETE removes counterparty, returns 204 | integration | `pytest backend/tests/test_deal_sub_entities.py::test_delete_counterparty -x` | ❌ Wave 0 |
| CPARTY-18 | UniqueConstraint: adding same company twice returns 400 | integration | `pytest backend/tests/test_deal_sub_entities.py::test_duplicate_counterparty_rejected -x` | ❌ Wave 0 |
| FUNDING-01 | deal_funding table created with correct columns | smoke | `pytest backend/tests/test_deal_sub_entities.py::test_funding_migration -x` | ❌ Wave 0 |
| FUNDING-04 | GET list resolves capital provider company name | integration | `pytest backend/tests/test_deal_sub_entities.py::test_list_funding_resolves_company -x` | ❌ Wave 0 |
| FUNDING-05 | POST creates funding entry | integration | `pytest backend/tests/test_deal_sub_entities.py::test_create_funding -x` | ❌ Wave 0 |
| FUNDING-06 | PATCH updates funding entry fields | integration | `pytest backend/tests/test_deal_sub_entities.py::test_patch_funding -x` | ❌ Wave 0 |
| CPARTY-09/11 | Counterparties tab grid + inline date editing | manual | — | Manual only |
| FUNDING-08/09 | Funding tab table + add/edit/delete modal | manual | — | Manual only |
| D-21 | Deactivated ref_data label renders as "---" | integration | `pytest backend/tests/test_deal_sub_entities.py::test_deactivated_ref_label_fallback -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest backend/tests/test_deal_sub_entities.py -x -q`
- **Per wave merge:** `python -m pytest backend/tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_deal_sub_entities.py` — covers CPARTY-01, CPARTY-05, CPARTY-06, CPARTY-07, CPARTY-08, FUNDING-01, FUNDING-04, FUNDING-05, FUNDING-06, D-21, and duplicate rejection

*(Existing `backend/tests/conftest.py` or fixtures in `test_crm_core.py` provide `db_session`, `crm_seed` — reuse in new test file.)*

---

## Sources

### Primary (HIGH confidence)
- `backend/models.py` — all existing ORM patterns; Deal, Fund, DealTeamMember class structure verified directly
- `backend/services/deals.py` — aliased multi-join pattern; `_deal_response` static method pattern
- `backend/api/routes/deals.py` — route handler signatures, Response pattern for 204
- `backend/api/main.py` — router registration loop
- `alembic/versions/` — confirmed 0009 is taken; 0010/0011 are correct next numbers
- `frontend/src/pages/DealDetailPage.jsx` — tab structure, query keys, mutation pattern, companiesQuery reuse
- `frontend/src/components/RefSelect.jsx` — component API (category, value, onChange, placeholder props)
- `frontend/src/api/funds.js` — API module pattern
- `.planning/phases/05-deal-counterparty-deal-funding/05-CONTEXT.md` — all locked decisions
- `.planning/REQUIREMENTS.md` — CPARTY-01 through CPARTY-12, FUNDING-01 through FUNDING-09
- `.planning/codebase/CONVENTIONS.md` — Python style, `from __future__ import annotations`, `X | None` syntax, `lazy="raise"` pattern

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` — "FundService aliased(RefData) label-join pattern established — reuse for Phase 5" (direct note from Phase 4 completion)
- `alembic/versions/0007_fund.py` — `deal_funding_status` seed pattern verified by direct file read

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project; verified by direct file inspection
- Migration numbering: HIGH — confirmed by listing alembic/versions/ directory
- Architecture patterns: HIGH — derived directly from Phase 4 code (DealService, FundService, DealDetailPage)
- Frontend inline date editing: MEDIUM-HIGH — native input[type=date] with autoFocus/onBlur is the established simple pattern; no external verification needed beyond browser compatibility (universal)
- Pitfalls: HIGH — migration conflict verified by directory listing; N+1/alias pitfalls verified from existing code patterns

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable stack — no fast-moving dependencies)
