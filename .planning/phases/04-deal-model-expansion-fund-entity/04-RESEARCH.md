# Phase 4: Deal Model Expansion & Fund Entity — Research

**Researched:** 2026-03-27
**Domain:** SQLAlchemy 2.0 migrations, FastAPI service layer, React TanStack Query, Radix UI tabs — within an established project codebase with locked patterns from Phases 2 and 3
**Confidence:** HIGH — all findings come directly from the live codebase, existing migration files, and Phase 2/3 summaries; no external library uncertainty

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Deal Detail Screen Layout**
- D-01: DealDetailPage gets a tabbed layout with four tabs: Profile, Activity, AI Insights, Tasks (in that order). Profile tab is first and holds all PE fields. The existing 3-column grid is replaced — existing content (activity log, AI score card, tasks) moves into their respective tabs.
- D-02: Profile tab uses five section cards in order: Deal Identity, Financials, Process Milestones, Source & Team, Passed / Dead. All five cards are always visible regardless of deal status.
- D-03: Editing uses per-card Edit/Save buttons — same pattern as Phase 3 Contact/Company Profile cards. Only one card in edit mode at a time.

**Deal Identity Card**
- D-04: Deal Identity card fields: transaction_type_id (RefSelect), fund_id (dropdown + `+ New fund` inline create), platform_or_addon (select: Platform / Add-on / Neither), platform_company_id (company link, shown only when add-on selected), description (textarea), legacy_id (text input).

**Financials Card**
- D-05: Financials card fields grouped in two sub-sections:
  - Deal Metrics: revenue (amount + currency), EBITDA (amount + currency), enterprise_value (amount + currency), equity_investment (amount + currency)
  - Bid Amounts: ioi_bid (amount + currency), loi_bid (amount + currency)
  - Amount and currency pairs rendered side-by-side (3-char currency input) — same pattern as Phase 3 D-07.

**Process Milestones Card**
- D-06: Milestones displayed as a 2-column date grid: label on left, date value on right, two columns side by side. `new_deal_date` appears first. Remaining 8 milestones follow in process order: CIM Received, IOI Due, IOI Submitted, Management Presentation, LOI Due, LOI Submitted, Live Diligence, Portfolio Company. Null dates display as `—`. In edit mode, date picker inputs.

**Source & Team Card**
- D-07: Source & Team card fields: deal_team (M2M users — chip pattern same as Phase 3 coverage_persons D-05), originator_id (user select), source_type_id (RefSelect, category=deal_source_type), source_company_id (company link/select), source_individual_id (contact link/select).

**Passed / Dead Card**
- D-08: Passed / Dead card is always visible in the Profile tab. Fields: passed_dead_date (date picker), passed_dead_reasons (multi-select chips using RefSelect, category=passed_dead_reason), passed_dead_commentary (textarea).

**Fund Entity**
- D-09: Fund entity is created via an inline quick-create modal triggered by `+ New fund` in the Deal Identity card (edit mode). Modal fields: fund_name (text, required), fundraise_status_id (RefSelect, category=fund_status), target_fund_size_amount + target_fund_size_currency (amount + currency pair), vintage_year (number). On create, fund is selected automatically in the dropdown.
- D-10: The fund_status ref_data category needs to be added: seed values = `Fundraising`, `Closed`, `Deployed`, `Returning Capital`. New category not in Phase 2 seed list.
- D-11: Fund CRUD routes: `GET /funds` (list for org), `POST /funds` (create), `PATCH /funds/{id}` (update). No delete.

**Patterns Carried Forward from Phase 3**
- D-12: All ref_data FK columns use `ForeignKey('ref_data.id', ondelete='SET NULL')`.
- D-13: All new migration columns are nullable.
- D-14: JSONB columns (passed_dead_reasons) use the existing `JSONVariant` type alias.
- D-15: `<RefSelect category="...">` with queryKey `['ref', category]` and staleTime 5min.
- D-16: All ref_data FK fields in API responses return resolved labels alongside UUIDs.
- D-17: Deal team field returns display names for all assigned users.

### Claude's Discretion
- Exact tab label abbreviations if needed for narrow viewports.
- Whether platform_company_id shows as a read-only link or a live search select in edit mode.
- Column ordering within the 2-column milestones grid.
- Fund dropdown query key: `['funds']` or similar.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. No DealCounterparty or DealFunding sub-entities this phase. No Admin UI this phase.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEAL-01 | Deal model: description (Text), new_deal_date (Date), transaction_type_id (FK ref_data) | Alembic ADD COLUMN pattern from 0003/0005; REFDATA-15 FK pattern |
| DEAL-02 | deal_team M2M association table to users (deal_team_members) | contact_coverage_persons M2M pattern from 0004 |
| DEAL-03 | fund_id (FK to Fund), platform_or_addon (String), platform_company_id (FK to companies) | Fund table must exist before this migration; FK to companies established |
| DEAL-04 | source_type_id (FK ref_data), source_company_id (FK companies), source_individual_id (FK contacts), originator_id (FK users) | All FK targets exist; SET NULL pattern for ref_data, companies, contacts |
| DEAL-05 | Financial fields: revenue, ebitda, enterprise_value, equity_investment — all Numeric(18,2) + currency String(3) | Numeric(18,2) pattern from Company model; 4 amount+currency pairs |
| DEAL-06 | Bid fields: loi_bid, ioi_bid — Numeric(18,2) + currency String(3) | Same pattern as DEAL-05 |
| DEAL-07 | Date milestone fields (8): cim_received, ioi_due, ioi_submitted, management_presentation, loi_due, loi_submitted, live_diligence, portfolio_company — all Date, nullable | Date column type from existing Deal model (expected_close_date) |
| DEAL-08 | Passed/dead fields: passed_dead_date (Date), passed_dead_reasons (JSONB), passed_dead_commentary (Text) | JSONVariant pattern from Contact/Company models |
| DEAL-09 | legacy_id (String, org-scoped unique index) | UniqueConstraint pattern from contacts/companies |
| DEAL-10 | API responses: resolved labels for all FK ref_data fields + deal_team display names | aliased(RefData) join pattern from 03-02; deal_team loaded separately like coverage_persons |
| DEAL-11 | Deal detail screen: all new PE fields grouped in 5 section cards | Tabs + per-card edit pattern from ContactDetailPage (Phase 3) |
| DEAL-12 | Deal detail edit form: all new fields with correct input types | RefSelect, chips, amount+currency pairs — all from Phase 3 |
| FUND-01 | funds table: id, org_id, fund_name, fundraise_status_id (FK ref_data), target_fund_size_amount (Numeric 18,2), target_fund_size_currency (String 3), vintage_year (Integer) | New table following ORM conventions |
| FUND-02 | GET /funds — list all funds for org | Standard DealService-style list pattern |
| FUND-03 | POST /funds — create fund | Standard create pattern |
| FUND-04 | PATCH /funds/{id} — update fund | model_dump(exclude_unset=True) partial update pattern |
| FUND-05 | Fund dropdown on Deal edit form | useQuery(['funds'], getFunds); inline + New fund modal |
</phase_requirements>

---

## Summary

Phase 4 is a data-model expansion and UI overhaul with no novel technical territory — every pattern needed has already been established in Phases 2 and 3. The backend work involves three Alembic migrations (Fund table, Deal PE columns, deal_team_members M2M), one new service/route module (funds), and expansion of the existing DealService and DealResponse to carry ~30 new fields plus resolved labels. The frontend work involves replacing the DealDetailPage 3-column grid with a 4-tab layout and adding a Profile tab with five section cards that mirror the ContactDetailPage structure established in Phase 3.

The most complex backend change is the DealService `_base_stmt` expansion: it must join against multiple aliased RefData instances (transaction_type, source_type — two separate joins) plus deal_team users (loaded separately via a secondary query, same as coverage_persons in 03-02). The most complex frontend change is the fund_id inline quick-create modal: POST /funds, auto-select the created fund in the Deal Identity dropdown, invalidate `['funds']` query.

The migration ordering constraint is critical: the Fund table migration (0007) must precede the Deal PE fields migration (0008) because deal.fund_id is an FK to funds.id. The deal_team_members M2M table (0009) can follow independently. All three must downgrade cleanly with explicit downgrade() functions.

**Primary recommendation:** Follow the Phase 3 Contact/Company expansion blueprint exactly — same migration → service/schema → UI plan split; same aliased RefData join pattern; same chips + RefSelect pattern for M2M fields; same per-card edit/save state management.

---

## Standard Stack

### Core (already installed — no new dependencies needed)

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| SQLAlchemy | 2.0 (async) | ORM + migrations | Mapped columns, async session |
| Alembic | current | DB migrations | op.add_column, op.create_table patterns |
| FastAPI | current | API routes | APIRouter, Depends, HTTPException |
| Pydantic | v2 | Request/response schemas | ConfigDict(from_attributes=True) |
| TanStack Query | v5 | Server state, mutations | queryKey arrays, invalidateQueries |
| React | 18 | UI | Hooks, useState |
| Radix UI / shadcn | current | UI primitives | Tabs, Dialog, Select, Card |
| react-hook-form + zod | current | Form validation | zodResolver pattern |

### No New Packages Required

All required primitives (Tabs, Dialog) are already in `frontend/src/components/ui/`. The `tabs.jsx` component exists. The `dialog.jsx` component exists (used in ContactDetailPage). No pip or npm installs needed.

**Installation:** None required.

---

## Architecture Patterns

### Recommended Module Layout for Phase 4

```
backend/
├── models.py                    — add Fund class, DealTeamMember class, Deal PE columns
├── schemas/
│   ├── deals.py                 — expand DealCreate/Update/Response; add ~30 new fields
│   └── funds.py                 — new: FundCreate, FundUpdate, FundResponse
├── services/
│   ├── deals.py                 — expand _base_stmt with ref_data joins; add _load_deal_team
│   └── funds.py                 — new: FundService (list, create, update)
├── api/routes/
│   ├── deals.py                 — existing PATCH route accepts new fields
│   └── funds.py                 — new: GET /funds, POST /funds, PATCH /funds/{id}

alembic/versions/
├── 0007_fund.py                 — CREATE TABLE funds; down_revision=0006
├── 0008_deal_pe_fields.py       — ADD COLUMN to deals + UniqueConstraint legacy_id
│                                   down_revision=0007 (fund_id FK requires funds to exist)
└── 0009_deal_team_members.py    — CREATE TABLE deal_team_members; down_revision=0008

frontend/src/
├── api/funds.js                 — new: getFunds, createFund, updateFund
├── pages/DealDetailPage.jsx     — full rewrite: 4-tab layout + 5 Profile cards
```

### Pattern 1: Alembic Migration Chain for Phase 4

**What:** Three sequential migrations, strictly ordered so FK dependencies are satisfied.
**When to use:** Any time a new table is referenced as a FK target before it exists.

```python
# 0007_fund.py — must run first
revision = "0007_fund"
down_revision = "0006_activity_deal_id_nullable"

def upgrade() -> None:
    op.create_table(
        "funds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fund_name", sa.String(255), nullable=False),
        sa.Column("fundraise_status_id", sa.String(36), sa.ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_fund_size_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("target_fund_size_currency", sa.String(3), nullable=True),
        sa.Column("vintage_year", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_funds_org_id", "funds", ["org_id"])

def downgrade() -> None:
    op.drop_index("ix_funds_org_id", table_name="funds")
    op.drop_table("funds")
```

```python
# 0008_deal_pe_fields.py — requires funds table to exist for fund_id FK
revision = "0008_deal_pe_fields"
down_revision = "0007_fund"
```

```python
# 0009_deal_team_members.py
revision = "0009_deal_team_members"
down_revision = "0008_deal_pe_fields"
```

### Pattern 2: ORM Model for Fund and DealTeamMember

**What:** New standalone Fund entity + association table for deal_team M2M.

```python
# In backend/models.py — Fund placed before Deal class (forward-ref avoidance)
class Fund(Base):
    __tablename__ = "funds"
    __table_args__ = (
        Index("ix_funds_org_id", "org_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    fund_name: Mapped[str] = mapped_column(String(255), nullable=False)
    fundraise_status_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True
    )
    target_fund_size_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    target_fund_size_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    vintage_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Organization] = relationship(back_populates="funds")
    deals: Mapped[list["Deal"]] = relationship(back_populates="fund")


class DealTeamMember(Base):
    __tablename__ = "deal_team_members"
    deal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
```

**Critical:** `Fund` and `DealTeamMember` must be placed in models.py BEFORE the `Deal` class to avoid forward-reference issues (same pattern as `ContactCoveragePerson` before `Contact`). Add `funds: Mapped[list["Fund"]]` relationship to `Organization`.

### Pattern 3: Multiple aliased RefData Joins in DealService._base_stmt

**What:** The deal response needs labels for multiple ref_data FK columns (transaction_type, source_type). Use aliased(RefData) for each, following the pattern established in 03-02 for ContactService.

```python
from sqlalchemy.orm import aliased
from backend.models import RefData  # already imported via models

TxnType = aliased(RefData)
SourceType = aliased(RefData)
FundStatusRef = aliased(RefData)  # only needed in FundService, not DealService

stmt = (
    select(
        Deal,
        Pipeline.name.label("pipeline_name"),
        PipelineStage.name.label("stage_name"),
        owner_name,
        contact_name,
        Company.name.label("company_name"),
        days_in_stage.label("days_in_stage"),
        is_rotting.label("is_rotting"),
        TxnType.label.label("transaction_type_label"),
        SourceType.label.label("source_type_label"),
        # source_company_name, source_individual_name via separate outerjoin aliases
    )
    .outerjoin(TxnType, TxnType.id == Deal.transaction_type_id)
    .outerjoin(SourceType, SourceType.id == Deal.source_type_id)
    # ... existing joins
)
```

### Pattern 4: deal_team Loaded Separately (Not in Base Stmt)

**What:** Same pattern as coverage_persons in ContactService (03-02). Load deal_team members on get_deal only, pass empty list on list_deals.

```python
async def _load_deal_team(self, deal_id: UUID) -> list[dict]:
    stmt = (
        select(User.id, User.full_name, User.email)
        .join(DealTeamMember, DealTeamMember.user_id == User.id)
        .where(DealTeamMember.deal_id == str(deal_id))
    )
    rows = (await self.db.execute(stmt)).all()
    return [{"id": str(row.id), "name": row.full_name or row.email} for row in rows]
```

**DealTeamMember update pattern** (same as coverage_persons delete+re-insert):
```python
async def _set_deal_team(self, deal_id: UUID, user_ids: list[UUID]) -> None:
    await self.db.execute(
        delete(DealTeamMember).where(DealTeamMember.deal_id == str(deal_id))
    )
    for uid in user_ids:
        self.db.add(DealTeamMember(deal_id=str(deal_id), user_id=str(uid)))
    await self.db.flush()
```

### Pattern 5: FundService (New Module)

**What:** Minimal service following the same constructor and pattern as existing services.

```python
class FundService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    async def list_funds(self) -> list[FundResponse]:
        stmt = select(Fund).where(Fund.org_id == self.current_user.org_id).order_by(Fund.fund_name)
        rows = (await self.db.execute(stmt)).scalars().all()
        return [FundResponse.model_validate(r) for r in rows]

    async def create_fund(self, payload: FundCreate) -> FundResponse:
        fund = Fund(org_id=self.current_user.org_id, **payload.model_dump())
        self.db.add(fund)
        await self.db.flush()
        await self.db.refresh(fund)
        return FundResponse.model_validate(fund)

    async def update_fund(self, fund_id: UUID, payload: FundUpdate) -> FundResponse:
        fund = await self.db.scalar(
            select(Fund).where(Fund.id == fund_id, Fund.org_id == self.current_user.org_id)
        )
        if fund is None:
            raise HTTPException(status_code=404, detail="Fund not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(fund, k, v)
        await self.db.flush()
        await self.db.refresh(fund)
        return FundResponse.model_validate(fund)
```

### Pattern 6: DealDetailPage Tab Layout

**What:** Replace existing 3-column grid with 4-tab layout. Existing `tabs.jsx` Radix component is already in `frontend/src/components/ui/`.

```jsx
// ContactDetailPage (Phase 3) is the canonical reference for this pattern
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Per-card edit state
const [editingIdentity, setEditingIdentity] = useState(false);
const [editingFinancials, setEditingFinancials] = useState(false);
const [editingMilestones, setEditingMilestones] = useState(false);
const [editingSourceTeam, setEditingSourceTeam] = useState(false);
const [editingPassedDead, setEditingPassedDead] = useState(false);

// Fund query for the dropdown
const { data: funds } = useQuery({ queryKey: ['funds'], queryFn: getFunds });

// Inline create modal state
const [fundModalOpen, setFundModalOpen] = useState(false);
```

### Pattern 7: Fund Inline Quick-Create

**What:** The `+ New fund` button opens a Dialog, POSTs to `/funds`, then sets the newly created fund as the selected value in the deal_id dropdown — all without losing the in-progress edit state.

```jsx
const createFundMutation = useMutation({
  mutationFn: createFund,
  onSuccess: (newFund) => {
    queryClient.invalidateQueries({ queryKey: ['funds'] });
    setIdentityForm(prev => ({ ...prev, fund_id: newFund.id }));
    setFundModalOpen(false);
    toast.success('Fund created');
  }
});
```

### Anti-Patterns to Avoid

- **Loading deal_team inside _base_stmt via join:** Causes N+1 on list views. Load separately for detail only, pass empty array for list.
- **Running 0008_deal_pe_fields before 0007_fund:** fund_id FK will fail because funds table doesn't exist yet. Migration chain must be 0007 → 0008 → 0009.
- **Using bare `[]` defaults in Pydantic Response models:** Use `Field(default_factory=list)` per conventions.
- **Importing ORM models inside migration files:** Always use inline `sa.table()` for `op.bulk_insert` calls.
- **fund_status in existing seed migration:** Do NOT modify 0002_pe_ref_data.py. Add fund_status seed values in 0007_fund.py upgrade() using op.bulk_insert against an inline sa.table() for ref_data.
- **platform_or_addon as an enum type:** Use plain String column — SQLite (test environment) doesn't support native PostgreSQL enums; store "platform" / "addon" / null as string values.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ref data label resolution | Custom dict lookup in Python | aliased(RefData) outerjoin in SQLAlchemy stmt | Already established in 03-02; server-side join is one query |
| Dropdown options for fund_status | Hardcoded array | `<RefSelect category="fund_status" />` | fund_status is seeded in ref_data; RefSelect handles loading/error/empty states |
| Multi-user chip input for deal_team | Custom multi-select | Chips + `/users` fetch pattern (same as coverage_persons in ContactDetailPage) | Pattern already implemented; just copy and adapt |
| Amount + currency side-by-side layout | New component | Inline flex pattern from Phase 3 CompanyDetailPage Financials card | Pattern already established, no new component needed |
| Fund list fetch + cache | Manual fetch | `useQuery({ queryKey: ['funds'], queryFn: getFunds })` | Standard TanStack Query; invalidate on fund creation |
| Passed/dead multi-reason chips | Custom multi-select | Chips + RefSelect (category=passed_dead_reason) pattern | Identical to passed_dead_reasons pattern from Phase 3 company_sub_type_ids |

**Key insight:** Phase 4 has no novel patterns — every technical problem has a direct analog in Phase 3. The planner should reference Phase 3 implementation files, not prototype new approaches.

---

## Common Pitfalls

### Pitfall 1: Migration Order Violation (fund_id FK before funds table)

**What goes wrong:** 0008_deal_pe_fields.py adds `fund_id` as a FK to `funds.id`. If 0008 runs before 0007, the FK constraint fails immediately on PostgreSQL (and silently creates an unvalidated constraint on some setups).
**Why it happens:** Migrations default to the previous head unless explicitly chained.
**How to avoid:** Explicitly set `down_revision = "0007_fund"` in 0008. Verify the chain with `alembic history --verbose` before running.
**Warning signs:** `alembic upgrade head` raises `ForeignKeyViolation` or `NoReferencedTableError`.

### Pitfall 2: fund_status Seeds Not in ref_data

**What goes wrong:** The Fund entity's `fundraise_status_id` dropdown (`<RefSelect category="fund_status">`) returns empty because `fund_status` was not seeded. The Phase 2 migration (0002) only seeds 10 categories; `fund_status` is new (D-10).
**Why it happens:** Easy to forget that `fund_status` is a brand-new category absent from Phase 2.
**How to avoid:** Add `op.bulk_insert` for fund_status seed rows inside 0007_fund.py's upgrade() function. Use the same ad-hoc `sa.table("ref_data", ...)` inline table pattern from 0002_pe_ref_data.py.
**Warning signs:** Fund status dropdown shows "No options available" or "Loading..." indefinitely.

### Pitfall 3: Organization model missing funds relationship

**What goes wrong:** SQLAlchemy emits a warning or back_populates mismatch error when Fund.org relationship references Organization.funds but the reverse is not declared.
**Why it happens:** All existing entity relationships (contacts, companies, deals, etc.) are declared on Organization. Fund is a new entity.
**How to avoid:** Add `funds: Mapped[list["Fund"]] = relationship(back_populates="org", cascade="all, delete-orphan")` to Organization class in models.py. Place it alongside the other entity relationships.

### Pitfall 4: DealResponse schema mismatch — new fields not marked Optional

**What goes wrong:** Any deal record created before Phase 4 migration returns `None` for all new fields. If the Pydantic schema doesn't mark them Optional with `= None` default, existing deal API responses fail validation.
**Why it happens:** `DealResponse` extends `BaseModel` with `from_attributes=True`; non-optional fields with no default raise ValidationError when the ORM attribute is None.
**How to avoid:** All new DealResponse fields must be `field_name: type | None = None`. Financial fields: `float | None = None`. Date fields: `date | None = None`. deal_team: `list[dict] = Field(default_factory=list)`.

### Pitfall 5: DealDetailPage — existing 3-column grid content must be preserved in tabs

**What goes wrong:** The rewrite replaces the grid with tabs. If the Activity, AI Insights, and Tasks content is not moved into their respective tab bodies, users lose access to existing functionality.
**Why it happens:** It's easy to focus on the new Profile tab and leave the other tabs as empty placeholders.
**How to avoid:** Move existing content: `activitiesQuery` + log form → Activity tab; `DealScoreCard` component → AI Insights tab; `tasksQuery` → Tasks tab. The Profile tab is additive; the other three tabs are migrations of existing content.

### Pitfall 6: source_company_id / source_individual_id — company and contact FK scope

**What goes wrong:** source_company_id is an FK to `companies.id` and source_individual_id is an FK to `contacts.id`. These are not ref_data FKs — they need company/contact name resolution via separate outerjoin aliases in `_base_stmt`, not RefData joins.
**Why it happens:** Confusion between ref_data FK fields (resolved via aliased RefData) and entity FK fields (resolved via direct table outerjoin).
**How to avoid:** Add `SourceCompany = aliased(Company)` and `SourceContact = aliased(Contact)` in the _base_stmt; outerjoin each with their respective FK column. Label: `SourceCompany.name.label("source_company_name")`, `SourceContact.first_name.label("source_contact_first_name")`.

### Pitfall 7: SQLite test compatibility for JSONB and Date columns

**What goes wrong:** Tests run against SQLite. `passed_dead_reasons` is `JSONVariant` (JSON/JSONB). Date columns are `Date`. Both work in SQLite but require correct type aliases.
**Why it happens:** If `JSONB` is used directly (not `JSONVariant`), SQLite tests fail.
**How to avoid:** Always use `JSONVariant` for JSONB fields (already in models.py). Use `sa.JSON` not `sa.JSONB` in migration DDL inline table definitions. Use `sa.Date` (not `sa.DateTime`) for date milestone columns.

---

## Code Examples

Verified patterns from the live codebase:

### Migration: Add Column Pattern (from 0003_contact_pe_fields.py analog)
```python
# Source: alembic/versions/0003_contact_pe_fields.py pattern
def upgrade() -> None:
    # Scalar columns
    op.add_column("deals", sa.Column("description", sa.Text, nullable=True))
    op.add_column("deals", sa.Column("new_deal_date", sa.Date, nullable=True))
    # FK column
    op.add_column("deals", sa.Column("transaction_type_id", sa.String(36), nullable=True))
    op.create_foreign_key("fk_deals_transaction_type_id", "deals", "ref_data", ["transaction_type_id"], ["id"], ondelete="SET NULL")
    # Numeric + currency pair
    op.add_column("deals", sa.Column("revenue_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("revenue_currency", sa.String(3), nullable=True))
    # UniqueConstraint for legacy_id
    op.create_unique_constraint("uq_deals_org_legacy_id", "deals", ["org_id", "legacy_id"])

def downgrade() -> None:
    op.drop_constraint("uq_deals_org_legacy_id", "deals", type_="unique")
    op.drop_constraint("fk_deals_transaction_type_id", "deals", type_="foreignkey")
    op.drop_column("deals", "transaction_type_id")
    # ... reverse all add_column calls
```

### aliased RefData Join Pattern (established in 03-02 ContactService)
```python
# Source: backend/services/contacts.py (03-02 pattern)
from sqlalchemy.orm import aliased
ContactTypeRef = aliased(RefData)
stmt = (
    select(Contact, ContactTypeRef.label.label("contact_type_label"), ...)
    .outerjoin(ContactTypeRef, ContactTypeRef.id == Contact.contact_type_id)
)
```

### Deal Schema Extension Pattern
```python
# Source: backend/schemas/deals.py — extend existing DealResponse
class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ... existing fields ...
    # New Phase 4 fields — all Optional with None default
    description: str | None = None
    new_deal_date: date | None = None
    transaction_type_id: str | None = None
    transaction_type_label: str | None = None
    fund_id: str | None = None
    fund_name: str | None = None
    platform_or_addon: str | None = None
    deal_team: list[dict] = Field(default_factory=list)
    # ... financials, milestones, source tracking, passed_dead fields
```

### Chips + User Selector (coverage_persons pattern — apply to deal_team)
```jsx
// Source: frontend/src/pages/ContactDetailPage.jsx (03-05 pattern)
// deal_team chip display
{dealTeam.map(u => (
  <Badge key={u.id} variant="secondary" className="gap-1">
    {u.name}
    {editingSourceTeam && (
      <button onClick={() => setDealTeam(prev => prev.filter(x => x.id !== u.id))}>
        <X className="h-3 w-3" />
      </button>
    )}
  </Badge>
))}
// Append user from select
<select onChange={(e) => {
  const user = users.find(u => u.id === e.target.value);
  if (user && !dealTeam.find(u => u.id === user.id)) {
    setDealTeam(prev => [...prev, { id: user.id, name: user.full_name || user.email }]);
  }
}}>...</select>
```

### RefSelect Usage (canonical from 02-03)
```jsx
// Source: frontend/src/components/RefSelect.jsx
<RefSelect
  category="transaction_type"
  value={identityForm.transaction_type_id}
  onChange={(val) => setIdentityForm(prev => ({ ...prev, transaction_type_id: val }))}
  placeholder="Select transaction type"
/>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single flat deal detail with 3-column grid | Tabbed layout with Profile/Activity/AI Insights/Tasks | Phase 4 | DealDetailPage requires full rewrite, not incremental edit |
| Deal model — basic CRM fields only | Full PE transaction record (30+ fields) | Phase 4 | Existing `DealResponse` must be extended with all new fields |
| No Fund entity | Fund table with CRUD API | Phase 4 | New module: schemas/funds.py, services/funds.py, routes/funds.py |

**Deprecated/outdated for Phase 4:**
- The existing DealDetailPage 3-column grid layout: replaced by tabbed layout per D-01.
- The bare `DealUpdate` schema fields: must be extended to accept all new PE fields.

---

## Open Questions

1. **source_individual_id display name format**
   - What we know: source_individual_id is an FK to contacts.id; Contact has `first_name` + `last_name`.
   - What's unclear: Should the response field be `source_individual_name` (full name string) or separate first/last?
   - Recommendation: Use `source_individual_name` as a single joined string (`Contact.first_name || ' ' || Contact.last_name`) — consistent with existing `contact_name_expr()` helper in `_crm.py`.

2. **platform_company_id UI in edit mode**
   - What we know: CONTEXT.md leaves this as Claude's discretion.
   - What's unclear: Live search select (like company picker on deals list) or simple text input?
   - Recommendation: Use a simple select populated from a `useQuery(['companies'])` fetch restricted to org — same approach as existing company_id selector on deal create form. No typeahead needed.

3. **fund_status seeds: migration file vs. separate fixture**
   - What we know: 0002 adds all 10 original categories. fund_status is new.
   - What's unclear: Whether the test `seed_ref_data` fixture in conftest.py needs updating.
   - Recommendation: Add fund_status seed data to 0007_fund.py upgrade() directly. Also add `fund_status` entries to the `seed_ref_data` pytest fixture in `backend/tests/conftest.py` so fund-related tests can use them.

---

## Environment Availability

Step 2.6: SKIPPED (phase is code/config changes only — no new external services, databases, or CLI tools required beyond the existing project stack).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (asyncio_mode = auto) |
| Config file | `backend/tests/pytest.ini` |
| Quick run command | `pytest backend/tests/test_deals.py -x` |
| Full suite command | `pytest backend/tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FUND-01 | funds table created | unit/migration | `pytest backend/tests/test_funds.py::test_fund_table_exists -x` | Wave 0 |
| FUND-02 | GET /funds returns org funds | integration | `pytest backend/tests/test_funds.py::test_list_funds -x` | Wave 0 |
| FUND-03 | POST /funds creates fund | integration | `pytest backend/tests/test_funds.py::test_create_fund -x` | Wave 0 |
| FUND-04 | PATCH /funds/{id} updates fund | integration | `pytest backend/tests/test_funds.py::test_update_fund -x` | Wave 0 |
| DEAL-01 | Deal PE columns exist (description, new_deal_date, transaction_type_id) | unit | `pytest backend/tests/test_deals.py::test_deal_pe_columns -x` | Wave 0 |
| DEAL-02 | deal_team_members M2M table exists | unit | `pytest backend/tests/test_deals.py::test_deal_team_members_table -x` | Wave 0 |
| DEAL-05/06 | Financial columns persist and return correctly | integration | `pytest backend/tests/test_deals.py::test_deal_financials -x` | Wave 0 |
| DEAL-10 | API response includes resolved labels + deal_team names | integration | `pytest backend/tests/test_deals.py::test_deal_response_labels -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_deals.py backend/tests/test_funds.py -x`
- **Per wave merge:** `pytest backend/tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_funds.py` — FUND-01 through FUND-04 test stubs
- [ ] `backend/tests/test_deals.py` — extend with DEAL-01, DEAL-02, DEAL-05/06, DEAL-10 stubs
- [ ] `backend/tests/conftest.py` — add `fund_status` entries to `seed_ref_data` fixture; add `seed_fund` fixture

---

## Sources

### Primary (HIGH confidence)

- `backend/models.py` — existing Deal, Contact, Company, ContactCoveragePerson ORM models; all column patterns verified directly
- `alembic/versions/0003_contact_pe_fields.py` through `0006_activity_deal_id_nullable.py` — migration DDL patterns, revision chain
- `backend/services/deals.py` — existing `_base_stmt`, `_deal_response` patterns; verified aliased join extension points
- `backend/schemas/deals.py` — existing `DealCreate`, `DealUpdate`, `DealResponse` — exact fields to extend
- `frontend/src/pages/ContactDetailPage.jsx` — per-card edit pattern, chips+RefSelect, tabs layout — Phase 3 canonical reference
- `.planning/phases/03-contact-company-model-expansion/03-02-SUMMARY.md` — aliased(RefData) join pattern; delete+re-insert M2M; merge migration patterns
- `.planning/phases/02-reference-data-system/02-03-SUMMARY.md` — RefSelect API, useRefData hook, queryKey canonical convention
- `.planning/codebase/CONVENTIONS.md` — SQLAlchemy 2.0 patterns, Pydantic conventions, async service pattern, JSONVariant
- `frontend/src/components/ui/` — confirmed tabs.jsx, dialog.jsx, card.jsx, input.jsx, textarea.jsx all present

### Secondary (MEDIUM confidence)

- `.planning/phases/02-reference-data-system/02-02-SUMMARY.md` — REFDATA-15 FK pattern; service constructor pattern; model_dump(exclude_unset=True) partial update

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all patterns from live codebase
- Architecture: HIGH — all migration/service/UI patterns have direct Phase 3 analogs
- Pitfalls: HIGH — migration ordering and fund_status seeding confirmed by reading migration chain directly

**Research date:** 2026-03-27
**Valid until:** 2026-06-27 (stable codebase; patterns locked by previous phases)
