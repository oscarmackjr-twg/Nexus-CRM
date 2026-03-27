# Phase 3: Contact & Company Model Expansion — Research

**Researched:** 2026-03-27
**Domain:** SQLAlchemy migrations, FastAPI schema expansion, React tabbed forms with ref_data integration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Add a dedicated **"Profile" tab** to both ContactDetailPage and CompanyDetailPage, placed first in tab order before Activities/Tasks/LinkedIn/AI. All new PE fields live in this tab.
- **D-02:** Contact Profile tab uses three card sections: **Identity** (contact_type, primary_contact, phones, address, linkedin_url), **Investment Preferences** (sectors, sub_sectors, contact_frequency), **Internal Coverage** (coverage_persons, legacy_id).
- **D-03:** Company Profile tab uses three card sections: **Identity** (company_type, sub_types, tier, sector, sub_sector, phone, address, parent_company), **Investment Profile** (AUM, EBITDA range, bite size, co_invest, transaction_types, sector_preferences, sub_sector_preferences, preference_notes), **Internal** (watchlist, coverage_person, contact_frequency, legacy_id).
- **D-04:** All multi-select JSONB fields (sector_preferences, sub_sector_preferences, coverage_persons, transaction_types, company_sub_type_ids) use a **chips + RefSelect add** pattern: current values display as removable badge chips; a RefSelect dropdown appends additional values. No separate popover or repeated selects.
- **D-05:** Coverage persons (M2M to users) use the same chip pattern but source from the `/users` endpoint (not ref_data). Each chip shows the user's display name with an ×.
- **D-06:** `previous_employment` and `board_memberships` use a **row UI with add/remove**: each entry is one row with input fields. previous_employment columns: Company, Title, From (year), To (year or blank for current). board_memberships columns: Company, Title. An "+ Add" button appends a new empty row; × removes a row. Both shown in standalone cards in the Profile tab.
- **D-07:** Financial fields in CompanyDetailPage are grouped in a dedicated **"Investment Profile"** card. Amount and currency code fields are rendered side-by-side (amount input + 3-char currency input `w-16`).
- **D-08:** Contact-level activity logging is **in scope for Phase 3**. Activities can be logged on a contact without requiring a deal association.
- **D-09:** Activity fields: activity_type (call / meeting / email / note), occurred_at (date), notes (text). No dealId required.
- **D-10:** Make `deal_id` nullable on the existing activities table (migration), update ActivityService/routes to allow deal_id=null when contact_id is provided, update the log-activity form on ContactDetailPage to remove the required deal selector.
- **D-11:** All ref_data FK columns use `ForeignKey('ref_data.id', ondelete='SET NULL')` — Phase 2 REFDATA-15 pattern.
- **D-12:** All dropdown fields use `<RefSelect category="...">` with queryKey `['ref', category]` and staleTime 5min — Phase 2 canonical pattern.
- **D-13:** JSONB columns use the existing `JSONVariant` type alias (JSON with JSONB variant for PostgreSQL).
- **D-14:** All new columns in migrations are nullable (no breaking changes to existing records).

### Claude's Discretion

- Exact section header styling (font size, divider style) — match existing Phase 1 conventions.
- Ordering of fields within each section — group logically, no specific order mandated.
- Whether Employment History and Board Memberships each get their own card or share one — Claude decides based on field count. *(UI-SPEC resolves: each gets its own standalone Card.)*
- Currency input width and formatting (3-char input vs select) — Claude decides; 3-char text input `w-16` is fine.

### Deferred Ideas (OUT OF SCOPE)

None deferred — the Calls & Notes capability was folded into Phase 3 scope (D-08 through D-10).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONTACT-01 | Contact model has business_phone, mobile_phone, assistant_name, assistant_email, assistant_phone | Migration 0003: add columns via op.add_column, all nullable String |
| CONTACT-02 | Contact model has address fields: address, city, state, postal_code, country | Migration 0003: add 5 nullable String columns |
| CONTACT-03 | Contact model has contact_type_id (FK ref_data), primary_contact (Bool), contact_frequency (Int) | Migration 0003: FK via op.add_column + op.create_foreign_key, REFDATA-15 ondelete=SET NULL |
| CONTACT-04 | Contact model has coverage_persons M2M association table to users | Migration 0004: CREATE TABLE contact_coverage_persons (contact_id, user_id, PK composite), explicit downgrade |
| CONTACT-05 | Contact model has sector (JSONB array of ref_data IDs), sub_sector (JSONB array) | Migration 0003: JSONVariant columns, nullable |
| CONTACT-06 | Contact model has previous_employment (JSONB array of objects), board_memberships (JSONB array of objects) | Migration 0003: JSONVariant columns, nullable |
| CONTACT-07 | Contact model has linkedin_url (Text), legacy_id (String, org-scoped unique index) | Migration 0003: Text + String with UniqueConstraint(org_id, legacy_id) |
| CONTACT-08 | API responses include resolved labels for contact_type_id and coverage_persons display names | Service: join to ref_data for label, subquery for coverage_persons list |
| CONTACT-09 | Contact detail screen shows all new PE fields grouped by section | UI: Profile tab with 3 cards + 2 standalone cards (Employment, Board) |
| CONTACT-10 | Contact detail edit form supports all new fields with correct input types | UI: per-card editing toggle, RefSelect for FKs, chips for JSONB multi |
| COMPANY-01 | Company model has company_type_id (FK), company_sub_type_ids (JSONB), description (Text) | Migration 0005: FK + JSONVariant + Text columns |
| COMPANY-02 | Company model has main_phone (String), parent_company_id (self-ref FK to companies) | Migration 0005: self-ref FK ForeignKey('companies.id', ondelete='SET NULL') |
| COMPANY-03 | Company model has address fields: address, city, state, postal_code (existing country retained) | Migration 0005: 4 nullable String columns (country exists already — verify) |
| COMPANY-04 | Company model has tier_id, sector_id, sub_sector_id FKs to ref_data | Migration 0005: 3 FK columns, REFDATA-15 pattern each |
| COMPANY-05 | Company model has sector_preferences (JSONB), sub_sector_preferences (JSONB), preference_notes (Text) | Migration 0005: JSONVariant + Text |
| COMPANY-06 | Company model has aum_amount (Numeric 18,2), aum_currency (String 3), ebitda_amount, ebitda_currency | Migration 0005: Numeric(18,2) + String(3) pairs |
| COMPANY-07 | Company model has bite_size fields, co_invest (Bool), target_deal_size_id (FK ref_data) | Migration 0005: Numeric pairs + Bool + FK |
| COMPANY-08 | Company model has transaction_types (JSONB), min_ebitda, max_ebitda, ebitda_range_currency | Migration 0005: JSONVariant + Numeric pair + String(3) |
| COMPANY-09 | Company model has watchlist (Bool), coverage_person_id (FK users), contact_frequency (Int), legacy_id | Migration 0005: Bool + FK to users (ondelete=SET NULL) + Int + String with UniqueConstraint |
| COMPANY-10 | Company API responses include resolved labels for all FK ref_data fields and coverage person name | Service: extended _base_stmt with outerjoin to ref_data ×3 + users for coverage person |
| COMPANY-11 | Company detail screen shows all new PE fields grouped by section | UI: Profile tab with 3 cards (Identity, Investment Profile, Internal) |
| COMPANY-12 | Company detail edit form supports all new fields with correct input types | UI: per-card edit, RefSelect, chips, amount+currency pairs, Switch |
</phase_requirements>

---

## Summary

Phase 3 adds a large set of PE Blueprint fields to the Contact and Company models through three Alembic migrations, extended Pydantic schemas, updated service query methods, and new Profile tab UIs. The codebase patterns are all established: SQLAlchemy 2.0 `Mapped[T]` column declarations, async service classes, REFDATA-15 FK pattern, RefSelect component, and TanStack Query invalidation. There is no new technology to introduce — Phase 3 is an expansion of existing patterns.

The activity logging scope extension (D-08 to D-10) requires one targeted migration: making `deal_id` nullable on `deal_activities`. The existing `ContactService.get_contact_activities` method only returns deal-joined activities; it must be extended to also return contact-level (deal_id=null) activities. The frontend `logActivity` currently calls `POST /deals/{deal_id}/activities` — a new or updated route is needed that accepts an optional deal_id, or a separate `POST /contacts/{id}/activities` route.

The most complex individual piece is the Company service's `_base_stmt` and `_company_response` — it will need outerjoin to ref_data three times (for tier, sector, sub_sector labels) and once more to users (for coverage_person name). Multi-label aliases must be unique. The pattern is well understood from the Phase 2 ref_data service union query.

**Primary recommendation:** Execute in plan order (03-01 → 03-02 → 03-03 → 03-04 → 03-05). Never write a service method that touches columns that don't yet exist. Run `pytest` after each migration plan before proceeding to the service plan.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| alembic | ~1.13 (installed) | Database migrations | Project standard; 0001/0002 already use it |
| sqlalchemy | ~2.0 (installed) | ORM + query building | Project uses 2.0 Mapped[] API throughout |
| pydantic | ~2.x (installed) | Request/response schemas | Project standard; `ConfigDict(from_attributes=True)` pattern |
| fastapi | ~0.110 (installed) | API routes | Project standard |
| React + TanStack Query | 18 + v5 (installed) | Frontend state + data fetching | Project standard |
| react-hook-form + zod | installed | Form validation | Project standard |
| RefSelect | Phase 2 (in codebase) | ref_data FK dropdowns | Canonical Phase 2 component |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | installed | Icons (Edit3, ExternalLink, X) | Per UI-SPEC icon choices |
| sonner | installed | Toast notifications | onSuccess/onError mutations |
| Radix Select / Switch / Tabs | installed via ui/ | Boolean toggle, tab navigation | Profile tab, boolean fields |

### Alternatives Considered

None — all decisions are locked. No new libraries introduced.

**Installation:** No new packages required. All dependencies are already installed.

---

## Architecture Patterns

### Backend Migration Pattern (established from 0002)

Each migration uses explicit `op.add_column` / `op.create_table` DDL — NOT `metadata.create_all` (reserved for 0001 only). Every migration has an explicit `downgrade()` with the reverse operations.

```python
# Source: alembic/versions/0002_pe_ref_data.py pattern + CONVENTIONS.md

revision = "0003_contact_pe_fields"
down_revision = "0002_pe_ref_data"

def upgrade() -> None:
    # Add nullable column — D-14: all new columns nullable
    op.add_column("contacts", sa.Column(
        "contact_type_id",
        sa.String(36),
        sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
        nullable=True,
    ))
    # Add UniqueConstraint for legacy_id (org-scoped)
    op.create_unique_constraint(
        "uq_contacts_org_legacy_id", "contacts", ["org_id", "legacy_id"]
    )

def downgrade() -> None:
    op.drop_constraint("uq_contacts_org_legacy_id", "contacts", type_="unique")
    op.drop_column("contacts", "contact_type_id")
```

### Association Table Migration Pattern (for contact_coverage_persons)

```python
# Migration 0004 — standalone association table
def upgrade() -> None:
    op.create_table(
        "contact_coverage_persons",
        sa.Column("contact_id", sa.String(36),
                  sa.ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("contact_id", "user_id",
                                name="pk_contact_coverage_persons"),
    )

def downgrade() -> None:
    op.drop_table("contact_coverage_persons")
```

### ORM Model Column Addition Pattern

New columns are added to the existing `Contact` and `Company` class bodies in `backend/models.py`. All use `Mapped[Optional[T]]` + `mapped_column(..., nullable=True)`. JSONB via `JSONVariant`. Numeric(18,2) for financial amounts.

```python
# backend/models.py — Contact additions (D-11, D-13, D-14)
from backend.models import JSONVariant  # existing alias

# FK column
contact_type_id: Mapped[Optional[str]] = mapped_column(
    String(36), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True, index=True
)
# JSONB multi-ref
sector: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
# JSONB structured array
previous_employment: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
# String with unique constraint declared in __table_args__
legacy_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
```

**Important:** The `legacy_id` UniqueConstraint(org_id, legacy_id) is added to `__table_args__` on the model class AND created via `op.create_unique_constraint` in the migration. Keep them in sync.

### Association Table ORM Model

A new `ContactCoveragePerson` association table model (or Table object) is added to `backend/models.py`. The `Contact` model gains a `coverage_persons` relationship.

```python
class ContactCoveragePerson(Base):
    __tablename__ = "contact_coverage_persons"
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

# On Contact model:
coverage_persons: Mapped[list[User]] = relationship(
    "User",
    secondary="contact_coverage_persons",
    back_populates=None,  # no back_populates since User doesn't know about this
    lazy="selectin",  # or loaded explicitly in service
)
```

**Note:** Loading coverage_persons for a list query would cause N+1 if using ORM relationships with lazy loading. The preferred approach for the detail view is a separate scalar subquery or `selectinload`. For list views, coverage_persons are not needed.

### Service Pattern: Resolved Labels in Response

The existing `ContactService._base_stmt()` outerjoin pattern is extended to join ref_data for label resolution. Multiple ref_data joins need aliased table references.

```python
# backend/services/contacts.py
from sqlalchemy.orm import aliased
from backend.models import RefData  # new import

ContactTypeRef = aliased(RefData)

def _base_stmt(self):
    return (
        select(
            Contact,
            Company.name.label("company_name"),
            user_name_expr().label("owner_name"),
            ContactTypeRef.label.label("contact_type_label"),
        )
        .outerjoin(Company, Company.id == Contact.company_id)
        .outerjoin(User, User.id == Contact.owner_id)
        .outerjoin(ContactTypeRef, ContactTypeRef.id == Contact.contact_type_id)
        .where(Contact.org_id == self.current_user.org_id)
    )
```

Coverage persons (M2M) cannot be resolved in the same join without row duplication. The pattern is a separate scalar subquery or a post-load step in `get_contact`:

```python
# Fetch coverage person display names separately in get_contact / _contact_response
from sqlalchemy import select
coverage_stmt = (
    select(User.id, User.full_name)
    .join(ContactCoveragePerson, ContactCoveragePerson.user_id == User.id)
    .where(ContactCoveragePerson.contact_id == contact_id)
)
coverage_rows = (await self.db.execute(coverage_stmt)).all()
coverage_persons = [{"id": str(r.id), "name": r.full_name} for r in coverage_rows]
```

### Service Pattern: Company Multi-FK Labels

Company needs multiple ref_data joins. Use `aliased` for each:

```python
TierRef = aliased(RefData)
SectorRef = aliased(RefData)
SubSectorRef = aliased(RefData)
CompanyTypeRef = aliased(RefData)
CoveragePersonUser = aliased(User)

def _base_stmt(self):
    return (
        select(
            Company,
            user_name_expr().label("owner_name"),
            TierRef.label.label("tier_label"),
            SectorRef.label.label("sector_label"),
            SubSectorRef.label.label("sub_sector_label"),
            CompanyTypeRef.label.label("company_type_label"),
            CoveragePersonUser.full_name.label("coverage_person_name"),
        )
        .outerjoin(User, User.id == Company.owner_id)
        .outerjoin(TierRef, TierRef.id == Company.tier_id)
        .outerjoin(SectorRef, SectorRef.id == Company.sector_id)
        .outerjoin(SubSectorRef, SubSectorRef.id == Company.sub_sector_id)
        .outerjoin(CompanyTypeRef, CompanyTypeRef.id == Company.company_type_id)
        .outerjoin(CoveragePersonUser, CoveragePersonUser.id == Company.coverage_person_id)
        .where(Company.org_id == self.current_user.org_id)
    )
```

### Activity Logging Extension Pattern (D-08 to D-10)

Migration makes `deal_id` nullable on `deal_activities`. The existing `DealActivity` model requires `deal_id: Mapped[UUID]` (non-nullable) — this must become `Mapped[Optional[UUID]]`. The migration adds a `contact_id` column (FK to contacts) so contact-level activities can be queried by contact.

```python
# Migration 0006 (activity nullable deal_id)
def upgrade() -> None:
    # Make deal_id nullable
    op.alter_column("deal_activities", "deal_id", nullable=True)
    # Add contact_id FK for contact-level activities
    op.add_column("deal_activities", sa.Column(
        "contact_id", sa.String(36),
        sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    ))

def downgrade() -> None:
    op.drop_column("deal_activities", "contact_id")
    op.alter_column("deal_activities", "deal_id", nullable=False)
```

**New route:** `POST /contacts/{contact_id}/activities` accepts `contact_id` in path, optional `deal_id` in body.

### UI Pattern: Per-Card Edit Toggle

ContactDetailPage currently has a single `editing` boolean. Phase 3 changes this to per-card state. Each of the 3 Profile tab cards (Identity, Investment Preferences, Internal Coverage) has its own `useState` edit toggle.

```jsx
// Per-card editing state
const [editingIdentity, setEditingIdentity] = useState(false);
const [editingPreferences, setEditingPreferences] = useState(false);
const [editingCoverage, setEditingCoverage] = useState(false);
```

Each card form calls `updateContact(id, partialPayload)` — the backend PATCH already supports partial updates via `model_dump(exclude_unset=True)`.

**Note:** The existing route uses PUT not PATCH. The `update_contact` service uses field-by-field `if value is not None` checks which mimics PATCH behavior. This is fine — no route change needed, just ensure the frontend sends only the card's fields.

### UI Pattern: Chips + RefSelect

```jsx
// Multi-JSONB field with chips
const [sectors, setSectors] = useState(contact?.sector || []);
// chips render
{sectors.map(id => {
  const label = refDataMap[id]?.label || id;
  return (
    <Badge key={id} className="flex items-center gap-1">
      {label}
      <Button
        variant="ghost" size="icon"
        aria-label={`Remove ${label}`}
        onClick={() => setSectors(s => s.filter(x => x !== id))}
      ><X className="h-3 w-3" /></Button>
    </Badge>
  );
})}
// append via RefSelect
<RefSelect
  category="sector"
  value=""
  onChange={(selectedId) => {
    if (selectedId && !sectors.includes(selectedId))
      setSectors(s => [...s, selectedId]);
  }}
  placeholder="Add sector..."
/>
```

### UI Pattern: Employment History Rows

```jsx
const [employment, setEmployment] = useState(contact?.previous_employment || []);

// Row rendering
{employment.map((entry, i) => (
  <div key={i} className="flex gap-3 items-center">
    <Input className="flex-1" value={entry.company} onChange={...} placeholder="Company" />
    <Input className="flex-1" value={entry.title} onChange={...} placeholder="Title" />
    <Input className="w-20" value={entry.from} onChange={...} placeholder="From" />
    <Input className="w-20" value={entry.to} onChange={...} placeholder="To" />
    <Button variant="ghost" size="icon" aria-label="Remove position"
      onClick={() => setEmployment(e => e.filter((_, j) => j !== i))}>
      <X className="h-4 w-4" />
    </Button>
  </div>
))}
<Button variant="outline" size="sm"
  onClick={() => setEmployment(e => [...e, { company: '', title: '', from: '', to: '' }])}>
  + Add position
</Button>
```

### UI Pattern: Amount + Currency Side-by-Side

```jsx
// Per UI-SPEC: amount flex-1, currency w-16
<div className="flex gap-2">
  <Input type="number" className="flex-1" placeholder="Amount"
    {...register('aum_amount')} />
  <Input className="w-16" maxLength={3} placeholder="USD"
    {...register('aum_currency')} />
</div>
```

### Recommended File Touch List

```
backend/
├── models.py                    — Add Contact/Company columns + ContactCoveragePerson table
├── schemas/
│   ├── contacts.py              — ContactCreate/Update/Response expansion
│   └── companies.py             — CompanyCreate/Update/Response expansion
├── services/
│   ├── contacts.py              — _base_stmt + _contact_response + coverage_persons loading
│   └── companies.py             — _base_stmt + _company_response multi-alias
├── api/routes/
│   └── contacts.py              — POST /{contact_id}/activities route
alembic/versions/
├── 0003_contact_pe_fields.py    — Contact column additions
├── 0004_contact_coverage_persons.py — M2M table
├── 0005_company_pe_fields.py    — Company column additions
└── 0006_activity_deal_id_nullable.py — DealActivity deal_id optional + contact_id FK
frontend/src/
├── pages/
│   ├── ContactDetailPage.jsx    — Profile tab, per-card edit, activity dialog update
│   └── CompanyDetailPage.jsx    — Profile tab, per-card edit, Tabs layout
└── api/
    └── contacts.js              — Add logContactActivity function
```

### Anti-Patterns to Avoid

- **Using `metadata.create_all` in migrations:** Only 0001_initial uses it. All subsequent migrations must use explicit `op.add_column`, `op.create_table`, etc.
- **Single edit state for all cards:** The existing single `editing` boolean in ContactDetailPage must be split into per-card state for D-01 design. Saving one card must not reset another card's edit state.
- **Row-multiplying JOINs for M2M:** Joining `contact_coverage_persons` in `_base_stmt` for list queries will multiply rows. Load coverage persons separately in `get_contact` detail only.
- **Sending full contact payload from each card:** Only send the fields that belong to the card being saved. The backend update method treats `None` as "no change" — but explicit `None` in a JSON body WILL overwrite. Use per-card partial payloads.
- **Accessing `row.contact_type_label` without alias in result row:** When multiple ref_data tables are joined with aliases, the labeled columns appear on the result row tuple at named positions. Access via `row.contact_type_label` (label name), not `row.ContactTypeRef.label`.
- **`op.alter_column` for SQLite:** `op.alter_column` for nullable change works on PostgreSQL but requires a workaround for SQLite (tests use SQLite). Use `batch_alter_table` context manager for the activity migration, or skip SQLite compat and rely on the SQLite test db being recreated from scratch.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ref_data dropdown with loading/error states | Custom select with fetch logic | `<RefSelect category="..." />` | Already built in Phase 2 with all 4 states |
| Multi-value chip display | Inline badge loop | `<Badge>` + × Button pattern (D-04) | Consistent removal UX across all multi fields |
| Resolved FK labels in API | Load ORM relationship on response | `aliased(RefData)` outerjoin in `_base_stmt` | Single query; no ORM lazy load N+1 |
| Currency validation | Regex or enum | 3-char `<Input maxLength={3} />` + browser native | Out-of-scope per requirements (display only, no FX conversion) |
| User dropdown for coverage persons | Custom user fetch hook | `getUsers()` from existing `/users` endpoint | Endpoint exists in `backend/api/routes/auth.py` |

**Key insight:** Every data-display and form-input problem in Phase 3 has a pattern already established in Phases 1 and 2. The work is composition and expansion, not new primitives.

---

## Common Pitfalls

### Pitfall 1: `op.alter_column` nullable change breaks SQLite tests

**What goes wrong:** Migration 0006 makes `deal_id` nullable. `op.alter_column(..., nullable=True)` is not natively supported by SQLite. When tests run (SQLite), the migration will fail or be silently skipped.

**Why it happens:** SQLite has very limited ALTER TABLE support. Alembic's SQLite backend emulates ALTER via table recreation when using `batch_alter_table`.

**How to avoid:** Wrap nullable alter in `with op.batch_alter_table("deal_activities") as batch_op: batch_op.alter_column("deal_id", nullable=True)`. This works for both PostgreSQL and SQLite.

**Warning signs:** `alembic upgrade head` succeeds in prod but `pytest` throws `OperationalError: near "ALTER": syntax error`.

### Pitfall 2: Row duplication when joining M2M in a list query

**What goes wrong:** If `contact_coverage_persons` is joined in `_base_stmt`, a contact with 3 coverage persons returns 3 rows per contact. `count_rows()` returns inflated numbers.

**Why it happens:** SQL JOIN on a one-to-many relationship multiplies rows.

**How to avoid:** Never join `contact_coverage_persons` in `_base_stmt`. Load coverage persons only in `get_contact` (detail view) via a separate query. For `list_contacts`, coverage_persons are not needed.

**Warning signs:** Contact list pagination returns wrong `total` count.

### Pitfall 3: Pydantic `None` vs `exclude_unset` — overwriting with null

**What goes wrong:** The frontend sends a partial card payload like `{ "contact_type_id": null }` which Pydantic parses as `None`. The service's `if value is not None` guard then skips setting the field — but the intent was to clear it.

**Why it happens:** `None` is ambiguous between "not sent" and "intentionally cleared". The `ContactUpdate` schema uses `| None = None` for all fields.

**How to avoid:** For FK fields that can be intentionally cleared, consider a sentinel approach or use `model_dump(exclude_unset=True)` in the service. The existing service uses field-by-field `if value is not None` checks — this means FK fields cannot be cleared to NULL via the API without additional handling. For Phase 3, this is acceptable: add a note in service comments. Clearing FKs is a future UX enhancement.

**Warning signs:** User removes a sector from the chip list, saves, but the sector FK remains because None was filtered out.

### Pitfall 4: Multiple aliased ref_data joins — wrong label for wrong field

**What goes wrong:** If `TierRef`, `SectorRef`, and `CompanyTypeRef` are all aliased to `RefData`, but the join conditions are accidentally swapped, the company response returns wrong labels.

**Why it happens:** Aliased joins require every alias to have its own distinct join condition. Copy-paste errors swap the `company.tier_id` / `company.sector_id` conditions.

**How to avoid:** Name aliases clearly and keep join definition and outerjoin in the same code block. Verify with a quick test that `tier_label` matches `tier_id`.

### Pitfall 5: Contact `country` field — Company already has it

**What goes wrong:** `COMPANY-03` says "existing country field retained". The existing `Company` model does NOT have a `country` column. The `REQUIREMENTS.md` also does not list `country` among company fields for COMPANY-03 — but the requirements do say "existing country field retained". Checking the model: Company has no `country` column currently.

**Why it happens:** REQUIREMENTS.md references a field that may not exist yet.

**How to avoid:** Before writing migration 0005, re-verify the Company model columns. `country` should be added for both Contact and Company in their respective migrations since neither currently has it. The phrase "existing country field retained" in COMPANY-03 likely refers to not removing it if it existed — since it does not exist, it must be added.

**Warning signs:** Migration fails because `alter_column` can't find a column that doesn't exist.

### Pitfall 6: `/users` endpoint is admin-only

**What goes wrong:** `GET /users` in `backend/api/routes/auth.py` uses `Depends(require_org_admin)` — only org admins can call it. The UI-SPEC says coverage persons are sourced from `/users`. Regular reps cannot fetch users, so the coverage persons picker will return 403.

**Why it happens:** The users list was gated as an admin feature.

**How to avoid:** Either: (a) open `GET /users` to all authenticated users for the org (change to `Depends(get_current_user)`), or (b) add a lightweight `GET /users/team-members` endpoint for coverage person selection that is scoped to all authenticated users. Recommend option (a) since internal user listing within an org is not sensitive — all users can see who their colleagues are.

**Warning signs:** Coverage persons card shows empty list for non-admin users; console shows 403 from `/users`.

---

## Code Examples

### Alembic: Numeric(18,2) + String(3) Column Pair

```python
# Source: SQLAlchemy Alembic docs pattern
op.add_column("companies", sa.Column("aum_amount", sa.Numeric(18, 2), nullable=True))
op.add_column("companies", sa.Column("aum_currency", sa.String(3), nullable=True))
```

### Pydantic: JSONB Array Field in Schema

```python
# Source: CONVENTIONS.md — Field(default_factory=list) for mutable defaults
class ContactUpdate(BaseModel):
    sector: list[str] | None = None           # JSONB array of ref_data UUIDs
    previous_employment: list[dict] | None = None  # JSONB array of {company, title, from, to}
    coverage_persons: list[str] | None = None  # list of user UUIDs

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sector: list[str] = Field(default_factory=list)
    sector_labels: list[str] = Field(default_factory=list)  # resolved in service
    coverage_persons: list[dict] = Field(default_factory=list)  # [{id, name}]
    contact_type_id: str | None = None
    contact_type_label: str | None = None
```

### Service: Updating JSONB Array Correctly

```python
# Direct assignment replaces the array (correct for JSONB overwrite)
if data.sector is not None:
    contact.sector = data.sector  # full replacement, not merge

# For coverage_persons M2M, delete + insert:
if data.coverage_persons is not None:
    await self.db.execute(
        delete(ContactCoveragePerson).where(
            ContactCoveragePerson.contact_id == str(contact.id)
        )
    )
    for user_id in data.coverage_persons:
        self.db.add(ContactCoveragePerson(
            contact_id=str(contact.id), user_id=str(user_id)
        ))
```

### Frontend: Per-Card Save with Partial Payload

```jsx
// ContactDetailPage — Identity card save
const saveIdentity = editForm.handleSubmit(async (values) => {
  // Only send Identity card fields — not preference or coverage fields
  await updateContact(id, {
    contact_type_id: values.contact_type_id || null,
    primary_contact: values.primary_contact,
    business_phone: values.business_phone || null,
    mobile_phone: values.mobile_phone || null,
    linkedin_url: values.linkedin_url || null,
    address: values.address || null,
    city: values.city || null,
    state: values.state || null,
    postal_code: values.postal_code || null,
    country: values.country || null,
  });
  queryClient.invalidateQueries({ queryKey: ['contact', id] });
  setEditingIdentity(false);
  toast.success('Contact updated');
});
```

### Frontend: Log Activity Without Required Deal

```jsx
// Updated activitySchema — dealId optional
const activitySchema = z.object({
  dealId: z.string().optional(),
  activity_type: z.string().min(1),
  notes: z.string().optional(),
  occurred_at: z.string().min(1),
});

// New API call: POST /contacts/{id}/activities
export const logContactActivity = async (contactId, data) =>
  (await client.post(`/contacts/${contactId}/activities`, data)).data;
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Single `editing` state for contact card | Per-card editing state (3 cards) | Users can edit one section without losing another section's unsaved changes |
| `deal_id` required on activity | `deal_id` optional, `contact_id` provides context | Activities logged at contact level without needing a deal |
| Company detail — no tab structure | Profile tab added first | Scales to accommodate full PE data model |

**Deprecated/outdated patterns to avoid:**
- `session.query()` — project uses `select()` + `session.execute()`
- `Optional[X]` from typing — project uses `X | None` union syntax
- `Column(...)` without `mapped_column` — project uses `Mapped[T]` + `mapped_column`

---

## Open Questions

1. **`/users` auth gate for coverage persons picker**
   - What we know: `GET /users` requires `require_org_admin`. Non-admins will get 403 when loading coverage persons.
   - What's unclear: Whether the intent was always to restrict user listing to admins, or if it was incidental.
   - Recommendation: In plan 03-02, open `GET /users` to all authenticated users (`get_current_user`). Coverage persons picker is essential functionality for all deal team members. Document the change.

2. **`alter_column` nullable for SQLite test compatibility**
   - What we know: SQLite does not support `ALTER COLUMN`. Tests use SQLite.
   - What's unclear: Whether the test suite drops and recreates the schema from models (bypassing migration history) or runs migrations.
   - What we found: `0001_initial.py` uses `models.Base.metadata.create_all(bind)` — so the initial schema is created from ORM models, not migration DDL. Tests likely use a fresh SQLite DB created from models. If tests don't run migrations, the `batch_alter_table` concern in 0006 may be moot for testing.
   - Recommendation: In plan 03-02, verify the test setup. If tests use model-based DB creation, the `alter_column` issue is production-only and safe on PostgreSQL. If tests run migrations, use `batch_alter_table`.

3. **`target_deal_size_id` category for COMPANY-07**
   - What we know: REQUIREMENTS.md specifies `target_deal_size_id (FK to ref_data)` but does not specify the ref_data category.
   - What's unclear: Which category this FK should reference. No "deal_size" category is seeded in 0002.
   - Recommendation: Use category `transaction_type` as a placeholder (it's the closest existing category), OR treat this as a FK to a future "deal_size" category. For Phase 3, make it a nullable FK to ref_data with no category filter in the dropdown — or omit it from the UI and leave it as a backend-only field until the category is defined.

---

## Environment Availability

Step 2.6: Audited — this phase is pure code/config changes (migrations, backend Python, frontend React). No new external services, CLIs, or runtimes are required beyond what is already running for development.

| Dependency | Required By | Available | Notes |
|------------|------------|-----------|-------|
| Python 3.11+ | Backend | ✓ | Project uses `X \| Y` union syntax requiring 3.10+ |
| Node.js | Frontend | ✓ | frontend/node_modules/ present |
| Alembic | Migrations | ✓ | 0002 already executed |
| PostgreSQL (prod) / SQLite (tests) | Database | ✓ | test_nexus.db present |

---

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json` — validation section included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest with pytest-asyncio (`asyncio_mode = auto`) |
| Config file | `backend/tests/pytest.ini` |
| Quick run command | `cd /Users/oscarmack/OpenClaw/nexus-crm && pytest backend/tests/test_crm_core.py -x -q` |
| Full suite command | `cd /Users/oscarmack/OpenClaw/nexus-crm && pytest backend/tests/ -q` |

Frontend tests use Vitest (`npm test` in `frontend/`).

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONTACT-01 | business_phone, mobile_phone columns persisted | integration | `pytest backend/tests/test_crm_core.py -k "contact" -x` | ✅ (test_crm_core.py) |
| CONTACT-02 | Address fields persisted and returned | integration | same | ✅ |
| CONTACT-03 | contact_type_id FK stored; primary_contact bool | integration | same | ✅ |
| CONTACT-04 | coverage_persons M2M stored and returned | integration | `pytest backend/tests/test_crm_core.py -k "coverage" -x` | ❌ Wave 0 |
| CONTACT-05 | sector/sub_sector JSONB arrays round-trip | integration | `pytest backend/tests/test_crm_core.py -k "contact" -x` | ✅ |
| CONTACT-06 | previous_employment / board_memberships JSONB | integration | same | ✅ |
| CONTACT-07 | linkedin_url, legacy_id with unique constraint | integration | same | ✅ |
| CONTACT-08 | contact_type_label in response; coverage_persons list | integration | `pytest backend/tests/test_crm_core.py -k "label" -x` | ❌ Wave 0 |
| CONTACT-09 | Profile tab renders (smoke) | manual-only | N/A — UI not tested | — |
| CONTACT-10 | Edit form saves all new fields (smoke) | manual-only | N/A | — |
| COMPANY-01 | company_type_id, company_sub_type_ids, description | integration | `pytest backend/tests/test_crm_core.py -k "company" -x` | ✅ |
| COMPANY-02 | main_phone, parent_company_id self-ref FK | integration | same | ✅ |
| COMPANY-03 | Address fields persisted | integration | same | ✅ |
| COMPANY-04 | tier_id, sector_id, sub_sector_id FKs | integration | same | ✅ |
| COMPANY-05 | sector_preferences, preference_notes JSONB | integration | same | ✅ |
| COMPANY-06 | aum_amount/currency, ebitda fields Numeric | integration | same | ✅ |
| COMPANY-07 | bite_size fields, co_invest, target_deal_size_id | integration | same | ✅ |
| COMPANY-08 | transaction_types, ebitda range, currency | integration | same | ✅ |
| COMPANY-09 | watchlist, coverage_person_id, legacy_id | integration | same | ✅ |
| COMPANY-10 | Resolved labels for all FK fields in response | integration | `pytest backend/tests/test_crm_core.py -k "label" -x` | ❌ Wave 0 |
| COMPANY-11 | Company Profile tab renders (smoke) | manual-only | N/A | — |
| COMPANY-12 | Company edit form saves all new fields (smoke) | manual-only | N/A | — |

### Sampling Rate

- **Per task commit:** `pytest backend/tests/test_crm_core.py -x -q`
- **Per wave merge:** `pytest backend/tests/ -q && cd frontend && npm test -- --run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_crm_core.py` — add `test_contact_pe_fields_round_trip` covering CONTACT-01 through CONTACT-08 (save + fetch, verify new fields + labels)
- [ ] `backend/tests/test_crm_core.py` — add `test_contact_coverage_persons` covering CONTACT-04 (M2M add/remove/list)
- [ ] `backend/tests/test_crm_core.py` — add `test_company_pe_fields_round_trip` covering COMPANY-01 through COMPANY-10
- [ ] `backend/tests/test_crm_core.py` — add `test_contact_activity_no_deal` covering D-08/D-09/D-10 (log activity without deal_id)

---

## Sources

### Primary (HIGH confidence)

- Codebase: `backend/models.py` (lines 105–165) — existing Contact and Company ORM models, column inventory
- Codebase: `backend/services/contacts.py` — existing `_base_stmt`, `_contact_response`, `update_contact` patterns
- Codebase: `backend/services/companies.py` — existing `_base_stmt`, `_company_response` patterns
- Codebase: `backend/schemas/contacts.py`, `backend/schemas/companies.py` — current schema fields
- Codebase: `alembic/versions/0002_pe_ref_data.py` — explicit DDL migration pattern
- Codebase: `.planning/codebase/CONVENTIONS.md` — SQLAlchemy 2.0, Pydantic, async patterns
- Codebase: `.planning/phases/02-reference-data-system/02-03-SUMMARY.md` — RefSelect API, queryKey convention
- Codebase: `.planning/phases/03-contact-company-model-expansion/03-UI-SPEC.md` — UI component choices, spacing, layout decisions

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — CONTACT-01 through CONTACT-10, COMPANY-01 through COMPANY-12 definitions
- `.planning/phases/03-contact-company-model-expansion/03-CONTEXT.md` — D-01 through D-14 locked decisions

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are already installed and in active use
- Architecture: HIGH — all patterns are established in the codebase; research confirmed from source files
- Pitfalls: HIGH — SQLite ALTER TABLE issue is well-known; M2M join multiplication verified from query patterns; auth gate issue confirmed from reading auth.py line 267

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable stack — 30 day window)
