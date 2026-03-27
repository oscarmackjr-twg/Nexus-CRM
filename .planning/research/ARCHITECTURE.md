# Architecture Patterns: PE Data Model Expansion

**Domain:** Private Equity CRM — deal counterparty pipeline, reference data, model expansion
**Researched:** 2026-03-26
**Overall confidence:** HIGH (grounded in existing codebase; SQLAlchemy 2.0 / Pydantic v2 / Alembic patterns verified from live source files)

---

## Context: What Already Exists

The codebase uses a consistent set of conventions throughout. All new work must follow these patterns exactly — diverging creates maintenance burden and breaks the service layer's helpers.

**Established conventions to preserve:**
- All PKs are UUIDs with `default=uuid4`
- All org-owned models carry `org_id: Mapped[UUID]` with `ForeignKey("organizations.id", ondelete="CASCADE")`
- Nullable FKs to other entities use `ondelete="SET NULL"`
- Required FKs use `ondelete="RESTRICT"` (prevents orphan records without cascading deletes)
- Monetary values use `Numeric(14, 2)` stored as `Decimal`
- `JSONVariant` alias (`JSON` falling back to `JSONB` on PostgreSQL) used for unstructured fields
- `StringList` alias (`MutableList` wrapping `JSON`/`ARRAY(Text)`) used for tag arrays
- `created_at` / `updated_at` with `server_default=func.now()` and `onupdate=func.now()`
- Services receive `(db: AsyncSession, current_user: User)` in constructor; routes are thin
- All queries filter by `org_id == current_user.org_id` — multi-tenancy at the query layer
- Response objects are built by explicit field mapping in a `_*_response(row)` static method, not via `from_attributes` on ORM objects returned directly from complex joins
- The `_crm.py` shared helpers (`clamp_pagination`, `count_rows`, `merge_custom_fields`, `ensure_*_in_org`, `user_name_expr`) are used by every service

The initial Alembic migration (`0001_initial.py`) uses `Base.metadata.create_all(bind)` — a shortcut that works once. New migrations must use explicit `op.create_table` / `op.add_column` calls. See the Migration Ordering section.

---

## Question 1: DealCounterparty Stage Progression

### The Three Options Evaluated

**Option A: Boolean date columns per stage**
```
nda_sent_at: Date | None
nda_signed_at: Date | None
nrl_signed_at: Date | None
intro_materials_sent_at: Date | None
vdr_access_granted_at: Date | None
```

**Option B: Single enum status column**
```
stage: str  # "nda_sent" | "nda_signed" | "vdr_access" | ...
```

**Option C: Separate counterparty-stage junction table**
```
deal_counterparty_stages (counterparty_id, stage_name, reached_at)
```

### Recommendation: Option A — Boolean Date Columns

**Use boolean date columns (nullable `Date` per milestone).**

Rationale grounded in the domain:

1. **PE counterparty pipeline is non-linear.** A counterparty can have NDA signed but intro materials not yet sent. VDR access can be granted before formal NRL. Option B (enum) enforces sequential stages that the workflow does not guarantee. Option A captures which milestones have been hit and when, without imposing an order.

2. **The TWG Deal Tracker spreadsheet confirms this.** The source spreadsheet has per-counterparty columns: NDA Signed, NRL Signed, Intro Materials Sent, VDR Access, Feedback Received. These are independent boolean states with dates, not a linear funnel.

3. **Querying is trivial.** "Show all counterparties who have VDR access but no feedback" is `vdr_access_granted_at IS NOT NULL AND feedback_received_at IS NULL` — a single-table index scan. Option C requires a join to the stage table plus two correlated subqueries. Option B cannot represent this state at all.

4. **Option C over-engineers.** A separate stage table is appropriate when stages are user-configurable (like `PipelineStage` for `Pipeline`). The PE counterparty stages are fixed domain concepts defined by TWG's workflow; they do not need user configuration.

5. **Column count is bounded and known.** There are 5-6 milestones. Adding 6 nullable date columns is not "sparse" at this scale.

### Concrete Schema

```python
class DealCounterparty(Base):
    __tablename__ = "deal_counterparties"
    __table_args__ = (
        UniqueConstraint("deal_id", "company_id", name="uq_deal_counterparty"),
        Index("ix_deal_counterparties_deal", "deal_id"),
        Index("ix_deal_counterparties_company", "company_id"),
        Index("ix_deal_counterparties_org", "org_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    deal_id: Mapped[UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False
    )
    # The investor / counterparty firm (optional link — firm may not yet be in CRM)
    company_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    # Free-text name for counterparties not yet in Companies table
    counterparty_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Primary contact at the counterparty (optional link)
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # Classification
    investor_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Financial profile
    check_size_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    check_size_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    aum: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")

    # Pipeline milestone dates — nullable = not yet reached
    nda_sent_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nda_signed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nrl_signed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    intro_materials_sent_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    vdr_access_granted_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    feedback_received_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Qualitative tracking
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    passed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    pass_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    deal: Mapped[Deal] = relationship(back_populates="counterparties")
    company: Mapped[Optional[Company]] = relationship(foreign_keys=[company_id])
    contact: Mapped[Optional[Contact]] = relationship(foreign_keys=[contact_id])
    org: Mapped[Organization] = relationship()
```

**Add to `Deal`:**
```python
counterparties: Mapped[list[DealCounterparty]] = relationship(
    back_populates="deal", cascade="all, delete-orphan"
)
```

**Add to `Organization`:**
```python
deal_counterparties: Mapped[list[DealCounterparty]] = relationship(
    back_populates="org", cascade="all, delete-orphan"
)
```

**UniqueConstraint explanation:** `UNIQUE(deal_id, company_id)` prevents duplicating a firm on the same deal. This is a partial uniqueness constraint — it does not block `company_id=NULL` rows (counterparties not yet in the CRM), which is intentional. PostgreSQL treats `NULL != NULL` in unique constraints.

**Derived "current stage" for UI:** Compute this in the service, not the DB, based on which milestone dates are populated. The display order is: `intro_materials_sent_at` → `nda_sent_at` → `nda_signed_at` → `nrl_signed_at` → `vdr_access_granted_at` → `feedback_received_at`. The service returns the name of the furthest reached milestone as a `current_stage: str` computed field in the Pydantic response.

---

## Question 2: DealFunding Schema

DealFunding tracks committed capital per deal from specific capital providers.

```python
class DealFunding(Base):
    __tablename__ = "deal_fundings"
    __table_args__ = (
        Index("ix_deal_fundings_deal", "deal_id"),
        Index("ix_deal_fundings_org", "org_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    deal_id: Mapped[UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False
    )
    # Capital provider — FK to company (preferred) or free text
    company_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    provider_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Commitment tracking
    projected_commitment: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    actual_commitment: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")

    # Terms and notes
    instrument_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    deal: Mapped[Deal] = relationship(back_populates="fundings")
    company: Mapped[Optional[Company]] = relationship(foreign_keys=[company_id])
    org: Mapped[Organization] = relationship()
```

**Add to `Deal`:**
```python
fundings: Mapped[list[DealFunding]] = relationship(
    back_populates="deal", cascade="all, delete-orphan"
)
```

---

## Question 3: Reference Data Tables

### The Three Options Evaluated

**Option A: Single polymorphic `ref_data` table**
```
ref_data (id, org_id, category, value, label, sort_order, is_active)
```

**Option B: Per-type tables**
```
sectors, sub_sectors, transaction_types, tiers, contact_types, ...
```

**Option C: Org `settings` JSONB blob**
```
Organization.settings["sectors"] = ["PE", "VC", ...]
```

### Recommendation: Option A — Single Polymorphic Reference Table

**Use a single `ref_data` table with a `category` discriminator column.**

Rationale:

1. **Reference categories are structurally identical.** Every category needs the same columns: `value` (machine key), `label` (display text), `sort_order` (display ordering), `is_active` (soft delete), `is_system` (seeded values that cannot be deleted), `org_id` (org-scoped). There is no category that needs additional columns at this time.

2. **Admin CRUD is one service, one route module.** With per-type tables (Option B), you write 10+ identical services and route handlers. With a single table, one `RefDataService` handles all categories via a `category` filter parameter.

3. **Seeding is straightforward.** One Alembic migration seeds all categories in a single `op.bulk_insert` call. New categories are added as new seed rows, not schema changes.

4. **Option C (JSONB blob) is wrong for structured reference data.** You cannot FK-reference a value inside a JSONB array from `deals.sector_id`. You cannot enforce uniqueness. You cannot query efficiently. Reserve JSONB for truly unstructured config.

5. **The pattern already exists in the codebase.** `PipelineStage.stage_type` stores `"open" | "won" | "lost"` as discriminated string values in a common table. Reference data is the admin-managed equivalent.

### Concrete Schema

```python
class RefData(Base):
    __tablename__ = "ref_data"
    __table_args__ = (
        UniqueConstraint("org_id", "category", "value", name="uq_ref_data_org_category_value"),
        Index("ix_ref_data_org_category", "org_id", "category"),
        Index("ix_ref_data_org_category_active", "org_id", "category", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # category values: "sector" | "sub_sector" | "transaction_type" | "tier"
    #                  "contact_type" | "company_type" | "company_sub_type"
    #                  "currency" | "deal_source_type" | "pass_dead_reason"

    value: Mapped[str] = mapped_column(String(100), nullable=False)   # machine key, e.g. "financial_services"
    label: Mapped[str] = mapped_column(String(255), nullable=False)   # display text, e.g. "Financial Services"
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    # is_system=True: seeded by migration, cannot be deleted via admin UI — only deactivated
    parent_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # parent_value: used for sub_sector → sector hierarchy. e.g. sub_sector.parent_value = "technology"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    org: Mapped[Organization] = relationship()
```

**`parent_value` for hierarchical categories:** Sub-sectors belong to sectors. Store the parent sector's `value` string in `sub_sector.parent_value`. This is a denormalized reference (not a FK) intentionally — it avoids a self-join and the parent is always within the same table/org/category. Query: `WHERE category='sub_sector' AND parent_value='technology' AND is_active=true`.

**Seeded values in migration:** System seed rows are inserted with `is_system=True`. Admin UI must call `PATCH /ref-data/{id}` which sets `is_active=False` rather than allowing `DELETE` for system rows. `DELETE` is permitted for non-system rows only.

**Linking ref_data to domain models:** Domain models (Deal, Contact, Company) store the `value` string as a plain `String` column, not a UUID FK to `ref_data`. This is intentional:
- Avoids a FK constraint that would break if a ref_data row is deactivated
- Keeps the deals/contacts tables readable without joining ref_data for every query
- Ref data values are validated at write time in the service layer (check that the value exists and is active before persisting)

Example on `Deal`:
```python
sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
# Validated on write: assert ref_data WHERE category='sector' AND value=sector AND is_active=true EXISTS
```

**Add to `Organization`:**
```python
ref_data: Mapped[list[RefData]] = relationship(back_populates="org", cascade="all, delete-orphan")
```

---

## Question 4: Expanding Existing Models with Many New Fields

### Strategy: Direct Column Expansion, All Nullable

**Add all new PE fields as nullable `mapped_column` entries directly on the existing models.** Do not use extension tables, JSON catch-all columns, or EAV patterns.

Rationale:

1. **The fields are not sparse enough to justify EAV.** 20-40 new fields sounds like a lot, but these are first-class PE data points that will be queried, sorted, and filtered. EAV (entity-attribute-value) makes every filter a join. Direct columns keep the query plan flat.

2. **The existing `custom_fields: JSONVariant` already absorbs truly sparse one-off data.** New PE Blueprint fields are structured and known — they belong as typed columns. Unstructured data continues to go into `custom_fields`.

3. **Extension tables add join complexity for no benefit here.** Extension tables (1-to-1 joined tables) are warranted when you have optional modules where most rows have no data at all (e.g., only 5% of contacts have the PE extension data). At TWG, all contacts and companies will have PE context — the data is the core use case, not an extension.

4. **Nullable columns with `server_default=None` are backward compatible.** Existing API consumers receive `null` for new fields. This matches the Pydantic pattern in use (`str | None = None`).

### Deal New Fields

```python
# Transaction classification
transaction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
fund: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
is_platform: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
# is_platform=False means add-on deal

# Deal team (stored as list of user IDs or free-text names)
deal_team_members: Mapped[list[str]] = mapped_column(StringList, nullable=False, default=list)

# Source tracking
deal_source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
deal_source_detail: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

# Financial metrics
revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
enterprise_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
equity_investment: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

# Date milestones
cim_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
ioi_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
loi_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
management_presentation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
live_diligence_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
portfolio_company_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

# Outcome
pass_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
dead_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

# Reference
legacy_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
```

### Contact New Fields

```python
phone_mobile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
phone_direct: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
assistant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
assistant_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
contact_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ref_data: contact_type
sector_preferences: Mapped[list[str]] = mapped_column(StringList, nullable=False, default=list)
coverage_person_id: Mapped[Optional[UUID]] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
previous_employment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
board_memberships: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
legacy_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
```

**Note on `coverage_person_id`:** Adds a second FK from `Contact` to `User`. The existing `owner_id` FK already exists. SQLAlchemy handles multiple FKs to the same table correctly, but the relationship definition on `User` needs `foreign_keys=` specified explicitly (the same pattern used for `Task.assignee_id` / `Task.created_by` already in the codebase).

### Company New Fields

```python
company_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # ref_data: company_type
company_sub_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ref_data: company_sub_type
aum: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
bite_size_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
bite_size_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
investment_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)   # ref_data: tier
sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ref_data: sector
sub_sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ref_data: sub_sector
co_invest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
watchlist: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
coverage_person_id: Mapped[Optional[UUID]] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
legacy_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
```

---

## API Backward Compatibility

### Rule: Additive Only, No Breaking Changes

All new fields on existing models are `Optional` (nullable) with a default of `None`. This means:

1. **Existing `POST /deals` requests continue to work.** The new fields are absent from the request body — Pydantic treats absent optional fields as `None`.
2. **Existing `GET /deals` responses include new fields with `null` values.** Frontend consumers that do not know about the new fields ignore unknown keys (standard JSON behavior; TanStack Query does not break on extra keys).
3. **No URL versioning required.** The change is additive. URL versioning (`/api/v2/deals`) is only needed when a breaking change is unavoidable — removing a required field, changing a field's type, or restructuring the response envelope. None of those apply here.

### Pydantic v2 Schema Extension Pattern

The codebase uses `BaseModel` with `ConfigDict(from_attributes=True)` on response schemas. The correct extension pattern is field addition with `Optional[T] = None` default — not schema inheritance or `model_config` changes.

**For `DealCreate` / `DealUpdate` (input schemas):** Add optional fields with defaults.

```python
class DealCreate(BaseModel):
    # ... existing fields unchanged ...
    transaction_type: str | None = None
    fund: str | None = None
    is_platform: bool = False
    revenue: float | None = None
    ebitda: float | None = None
    enterprise_value: float | None = None
    equity_investment: float | None = None
    cim_date: date | None = None
    ioi_date: date | None = None
    loi_date: date | None = None
    # ... etc
```

**For `DealResponse` (output schema):** Add optional fields with `None` default. Because the service builds `DealResponse` via explicit constructor call (not `model_validate(orm_obj)`), each new field must also be added to the `_deal_response()` static method in `DealService`.

```python
class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ... existing fields unchanged ...
    transaction_type: str | None = None
    fund: str | None = None
    is_platform: bool = False
    revenue: float | None = None
    # ... etc
    counterparties: list[DealCounterpartyResponse] | None = None  # optional sideload
```

**Pydantic v2 caveat on `from_attributes`:** The `_deal_response()` method in `DealService` constructs `DealResponse` by passing individual keyword arguments (not `model_validate(row[0])`). This means adding a field to `DealResponse` does NOT automatically populate it — you must also add the field to the explicit constructor call in `_deal_response()`. This is a subtle trap. The pattern is correct and safe; just remember both files must be updated together.

### New Sub-Entities: Nested vs Separate Routes

DealCounterparty and DealFunding are sub-resources of Deal. Use nested routes:

```
GET    /deals/{deal_id}/counterparties
POST   /deals/{deal_id}/counterparties
GET    /deals/{deal_id}/counterparties/{counterparty_id}
PUT    /deals/{deal_id}/counterparties/{counterparty_id}
DELETE /deals/{deal_id}/counterparties/{counterparty_id}

GET    /deals/{deal_id}/fundings
POST   /deals/{deal_id}/fundings
GET    /deals/{deal_id}/fundings/{funding_id}
PUT    /deals/{deal_id}/fundings/{funding_id}
DELETE /deals/{deal_id}/fundings/{funding_id}
```

**Why nested:** The existing `/{deal_id}/activities` and `/{deal_id}/move-stage` routes in `deals.py` establish this pattern. Sub-resources of a deal live under the deal's URL path.

**Service pattern:** Create `DealCounterpartyService(db, current_user)` and `DealFundingService(db, current_user)` following the exact constructor signature of `DealService`. Register the new routes either in `deals.py` (if the team prefers a single file for deal-related resources) or in new files `deal_counterparties.py` and `deal_fundings.py` mounted to the same `/deals` prefix. The separate files approach is preferred for maintainability.

### Reference Data Routes

```
GET    /ref-data?category=sector          # list values for a category
POST   /ref-data                          # admin: create a custom value
PATCH  /ref-data/{id}                     # admin: update label/sort_order/is_active
DELETE /ref-data/{id}                     # admin: delete (non-system rows only)
GET    /ref-data/categories               # list all known categories
```

Authorization: `GET` is available to all authenticated users in the org. `POST`/`PATCH`/`DELETE` requires `require_role("org_admin", "super_admin")` using the existing `require_role` dependency.

---

## Alembic Migration Ordering

The initial migration (`0001_initial.py`) uses `Base.metadata.create_all(bind)` which is a one-shot schema creation. All subsequent migrations must use explicit DDL operations. The migration chain must respect foreign key dependencies.

### Migration Dependency Graph

```
0001_initial.py  (organizations, teams, users, contacts, companies, deals, ...)
  └── 0002_ref_data.py
        Creates: ref_data table + org_id FK to organizations
        Seeds: all TWG system values (is_system=True)

  └── 0003_expand_contacts.py
        ALTER contacts: ADD COLUMN phone_mobile, phone_direct, assistant_name,
                        assistant_email, contact_type, sector_preferences,
                        coverage_person_id, previous_employment, board_memberships, legacy_id

  └── 0004_expand_companies.py
        ALTER companies: ADD COLUMN company_type, company_sub_type, aum, ebitda,
                         bite_size_min, bite_size_max, investment_preferences, tier,
                         sector, sub_sector, co_invest, watchlist, coverage_person_id,
                         country, currency, legacy_id

  └── 0005_expand_deals.py
        ALTER deals: ADD COLUMN transaction_type, fund, is_platform, deal_team_members,
                     deal_source_type, deal_source_detail, revenue, ebitda,
                     enterprise_value, equity_investment, cim_date, ioi_date, loi_date,
                     management_presentation_date, live_diligence_date,
                     portfolio_company_date, pass_reason, dead_reason, legacy_id

  └── 0006_deal_counterparties.py
        Creates: deal_counterparties table
        FKs: organizations.id, deals.id, companies.id, contacts.id
        Depends on: 0001 (organizations, deals, companies, contacts)

  └── 0007_deal_fundings.py
        Creates: deal_fundings table
        FKs: organizations.id, deals.id, companies.id
        Depends on: 0001 (organizations, deals, companies)
```

**Rule:** Tables that have FKs into other tables must be created after those tables. The `ref_data` table only depends on `organizations`, so it can be migration 0002. `deal_counterparties` depends on `deals`, `companies`, `contacts`, and `organizations` — all in `0001`, so it is safe as 0006.

**ALTER TABLE ordering:** Alembic `op.add_column` is safe on a running PostgreSQL database when adding nullable columns or columns with defaults — no table lock is acquired for the data rewrite (PostgreSQL 11+). All new columns here are either nullable or have `server_default` values. Do not combine dozens of `ADD COLUMN` calls in one `op.execute(ALTER TABLE...)` string; use individual `op.add_column()` calls so Alembic can correctly generate downgrade operations.

**Downgrade operations:** Always implement `downgrade()` using `op.drop_column` / `op.drop_table`. The initial migration's `metadata.drop_all` approach is acceptable only for the initial schema — later migrations must be individually reversible for safe rollbacks in production.

### Migration File Template for ALTER

```python
"""expand deals with PE fields"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005_expand_deals"
down_revision = "0004_expand_companies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deals", sa.Column("transaction_type", sa.String(50), nullable=True))
    op.add_column("deals", sa.Column("fund", sa.String(100), nullable=True))
    op.add_column("deals", sa.Column("is_platform", sa.Boolean(), nullable=False,
                                     server_default="0"))
    op.add_column("deals", sa.Column("revenue", sa.Numeric(14, 2), nullable=True))
    # ... etc
    op.create_index("ix_deals_legacy_id", "deals", ["legacy_id"])


def downgrade() -> None:
    op.drop_index("ix_deals_legacy_id", table_name="deals")
    op.drop_column("deals", "revenue")
    op.drop_column("deals", "is_platform")
    op.drop_column("deals", "fund")
    op.drop_column("deals", "transaction_type")
    # ... etc
```

---

## SQLAlchemy 2.0 Relationship Patterns for New Entities

### Multiple FKs to the Same Table

`Contact` and `Company` will have both `owner_id` and `coverage_person_id` pointing to `users`. The existing codebase already demonstrates the required pattern in `Task` (two FKs to `users`: `assignee_id` and `created_by`):

```python
# In Contact model:
owner: Mapped[Optional[User]] = relationship(
    back_populates="owned_contacts", foreign_keys=[owner_id]
)
coverage_person: Mapped[Optional[User]] = relationship(
    foreign_keys=[coverage_person_id]
    # No back_populates needed unless User needs to list all contacts it covers
)
```

Do NOT add `back_populates` on `User` for `coverage_person` unless the frontend needs to query "which contacts does this user cover." If needed, add:
```python
# In User model:
covered_contacts: Mapped[list[Contact]] = relationship(
    back_populates="coverage_person", foreign_keys="Contact.coverage_person_id"
)
```

### Async Lazy Loading is Disabled

SQLAlchemy 2.0 async sessions do not support implicit lazy loading. Any `relationship()` attribute access outside of a `select()` with `joinedload()` or explicit `selectinload()` will raise `MissingGreenlet`.

The codebase correctly avoids this: `DealService._deal_response()` builds response objects from explicit join queries (the `_base_deal_stmt` method joins User, Pipeline, PipelineStage, Contact, Company). New services must follow the same pattern — build a `SELECT` with all needed joins, then map columns to the response schema explicitly.

For `DealCounterparty`, the base statement:
```python
stmt = (
    select(
        DealCounterparty,
        Company.name.label("company_name"),
        Contact.first_name.label("contact_first_name"),
        Contact.last_name.label("contact_last_name"),
    )
    .outerjoin(Company, Company.id == DealCounterparty.company_id)
    .outerjoin(Contact, Contact.id == DealCounterparty.contact_id)
    .where(
        DealCounterparty.deal_id == deal_id,
        DealCounterparty.org_id == current_user.org_id,
    )
)
```

### cascade="all, delete-orphan" for Sub-Entities

`DealCounterparty` and `DealFunding` are owned by `Deal`. Use `cascade="all, delete-orphan"` on the `Deal.counterparties` and `Deal.fundings` relationships (already shown in the schema above). This ensures that deleting a `Deal` cascades to its counterparties and fundings at the SQLAlchemy ORM level, in addition to the `ON DELETE CASCADE` at the DB level.

Both constraints are needed: the FK cascade handles direct SQL deletes (e.g., Alembic running `DELETE FROM deals`); the ORM cascade handles `session.delete(deal)` calls in service code.

---

## Component Boundaries

| Component | Responsibility | New Work |
|-----------|---------------|----------|
| `backend/models.py` | All ORM model definitions | Add `DealCounterparty`, `DealFunding`, `RefData`; extend `Deal`, `Contact`, `Company` |
| `backend/schemas/deal_counterparties.py` | Pydantic I/O schemas for counterparties | New file |
| `backend/schemas/deal_fundings.py` | Pydantic I/O schemas for fundings | New file |
| `backend/schemas/ref_data.py` | Pydantic I/O schemas for reference data | New file |
| `backend/schemas/deals.py` | Extend `DealCreate`, `DealUpdate`, `DealResponse` | Additive field additions |
| `backend/schemas/contacts.py` | Extend `ContactCreate`, `ContactUpdate`, `ContactResponse` | Additive field additions |
| `backend/schemas/companies.py` | Extend `CompanyCreate`, `CompanyUpdate`, `CompanyResponse` | Additive field additions |
| `backend/services/deal_counterparties.py` | CRUD for `DealCounterparty` | New service |
| `backend/services/deal_fundings.py` | CRUD for `DealFunding` | New service |
| `backend/services/ref_data.py` | CRUD + seeding for `RefData` | New service |
| `backend/api/routes/deal_counterparties.py` | HTTP endpoints for counterparties | New route module |
| `backend/api/routes/deal_fundings.py` | HTTP endpoints for fundings | New route module |
| `backend/api/routes/ref_data.py` | HTTP endpoints for reference data | New route module |
| `backend/api/main.py` | Router registration | Add 3 new router includes |
| `alembic/versions/` | Schema migrations | 6 new migrations (0002–0007) |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Using `custom_fields` for PE Blueprint Fields

**What:** Storing `transaction_type`, `ebitda`, `sector` etc. inside the existing `custom_fields: JSONB` column on Deal/Contact/Company instead of adding typed columns.

**Why bad:** JSONB fields cannot be indexed for range queries (`ebitda > 10000000`), cannot have type enforcement, cannot be validated by Pydantic at model level, and require `->` / `->>` extraction operators in every query. The PE Blueprint fields are the core data model, not custom data.

**Instead:** Typed nullable columns as described above.

### Anti-Pattern 2: Enum Types for Counterparty Stage

**What:** Using PostgreSQL `ENUM` type or a Python `enum.Enum` for `DealCounterparty` stage.

**Why bad:** PostgreSQL ENUM types require `ALTER TYPE` to add values — a DDL operation that cannot be rolled back and requires exclusive lock. Python `Enum` in SQLAlchemy with `native_enum=True` has the same problem. The PE workflow may add new milestone types (e.g., "management presentation scheduled").

**Instead:** `String` columns for all status/type fields (matching the codebase's convention: `Deal.status`, `PipelineStage.stage_type`, `User.role` are all `String`, not ENUM).

### Anti-Pattern 3: FK from ref_data Value Columns

**What:** Making `Deal.transaction_type` a UUID FK to `ref_data.id` rather than storing the `value` string directly.

**Why bad:** FK to a reference row that might be deactivated blocks deactivation or orphans the deal. UUID FK requires a JOIN in every deal query to resolve the display label. If the admin renames a ref_data label, deals that stored the UUID still display the old label through the join (the label is on the ref_data row, not the deal).

**Instead:** Store the `value` string on the domain model. Validate on write (ensure the value exists and is active). Display label is fetched as ref_data at render time in the frontend, not re-joined at query time in the backend.

### Anti-Pattern 4: Breaking the `_deal_response()` Explicit Mapping

**What:** Switching from the explicit `DealResponse(field=value, ...)` constructor to `DealResponse.model_validate(deal_orm_object)` to avoid adding new fields to both schema and service.

**Why bad:** The deal query returns a `Row` tuple (deal ORM object + computed column scalars like `pipeline_name`, `stage_name`, `owner_name`). Computed columns are not attributes of `Deal` — they live on the row object. `model_validate(deal)` would silently drop all computed fields. The explicit mapping is required.

**Instead:** When adding a new field to `DealResponse`, always add it to both `DealResponse` schema AND `DealService._deal_response()`. The same applies to `ContactService` and `CompanyService`.

### Anti-Pattern 5: Registering New Routes Under `/api/v2`

**What:** Creating a new `/api/v2` prefix for new endpoints.

**Why bad:** There is no breaking change — all new endpoints are net-new resources and all changes to existing endpoints are additive. API versioning creates frontend client complexity (two base URLs) for no benefit.

**Instead:** All new routes mount at `/api/v1` following the existing convention.

---

## Scalability Considerations

| Concern | At Current Scale (TWG, ~100 deals) | At 10K deals |
|---------|-------------------------------------|--------------|
| `deal_counterparties` table size | ~500-2000 rows — trivial | ~500K rows — index on `deal_id` covers all per-deal lookups |
| `ref_data` table | ~100-200 rows — fits in PG buffer pool | Static — grows only when admin adds values |
| `op.add_column` on contacts/companies/deals | Instant (PostgreSQL 11+ metadata-only ADD for nullable columns) | Instant — same |
| New joined fields in deal list query | 0 additional joins (new columns on `deals` table already in query) | 0 additional joins |
| `DealCounterparty` query joins | 2 outer joins (companies, contacts) — covered by index | Same — index handles it |

---

## Sources

- Codebase: `/Users/oscarmack/OpenClaw/nexus-crm/backend/models.py` — HIGH confidence (primary source)
- Codebase: `/Users/oscarmack/OpenClaw/nexus-crm/backend/services/deals.py` — HIGH confidence (primary source)
- Codebase: `/Users/oscarmack/OpenClaw/nexus-crm/backend/schemas/deals.py` — HIGH confidence (primary source)
- Codebase: `/Users/oscarmack/OpenClaw/nexus-crm/backend/services/_crm.py` — HIGH confidence (primary source)
- Codebase: `/Users/oscarmack/OpenClaw/nexus-crm/alembic/versions/0001_initial.py` — HIGH confidence (primary source)
- SQLAlchemy 2.0 async relationship patterns — HIGH confidence (established API, knowledge cutoff August 2025)
- Pydantic v2 `ConfigDict(from_attributes=True)` + optional field extension — HIGH confidence (established API)
- Alembic `op.add_column` behavior for nullable columns on PostgreSQL 11+ — HIGH confidence (established behavior)
- PostgreSQL `UNIQUE` constraint behavior with `NULL` values — HIGH confidence (SQL standard + PG docs)

*Architecture analysis: 2026-03-26*
