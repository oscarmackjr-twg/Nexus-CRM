# Technology Stack — PE Data Model Expansion

**Project:** Nexus CRM — PE Blueprint data model expansion
**Researched:** 2026-03-26
**Scope:** Patterns for adding admin-configurable reference data, JSONB vs dedicated columns for sparse PE fields, and Alembic migration strategy for existing tables.

---

## Existing Stack Constraints (from codebase analysis)

The codebase is well-established. These facts constrain every recommendation:

| Fact | Implication |
|------|-------------|
| SQLAlchemy 2.0 async (`create_async_engine`, `async_sessionmaker`) | All new models follow `Mapped[T]` / `mapped_column()` typed-column style |
| Alembic env uses `psycopg` (sync) for migration, `asyncpg` for app | No changes needed to env.py; new migrations write explicit DDL |
| `0001_initial` used `metadata.create_all(bind)` (full schema dump) | All subsequent migrations MUST use explicit `op.add_column` / `op.create_table`, NOT autogenerate alone |
| `JSONVariant = JSON().with_variant(JSONB, "postgresql")` already defined | Reuse this alias for any new JSONB columns; do not re-declare |
| `custom_fields: Mapped[Optional[dict]]` on Contact, Company, Deal | Existing escape hatch — PE-specific sparse fields can go here or get dedicated columns depending on query needs |
| Multi-tenant via `org_id` FK on every entity | Reference/lookup tables MUST include `org_id` and be scoped per-org |
| Pydantic v2 schemas in `backend/schemas/` mirroring service layer | New entities need schema files; FK-resolved display names (e.g. `sector_name`) are computed in service layer, not ORM |

---

## Decision 1: Admin-Configurable Reference Data

### Recommendation: Dedicated `ref_data` table with a `category` discriminator column

**Use this pattern:**

```python
class RefData(Base):
    __tablename__ = "ref_data"
    __table_args__ = (
        UniqueConstraint("org_id", "category", "value", name="uq_ref_data_org_category_value"),
        Index("ix_ref_data_org_category", "org_id", "category"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

`category` values: `"sector"`, `"sub_sector"`, `"transaction_type"`, `"tier"`, `"contact_type"`, `"company_type"`, `"company_sub_type"`, `"currency"`, `"deal_source_type"`, `"passed_dead_reason"`.

**Why this pattern over the alternatives:**

| Alternative | Why Rejected |
|-------------|-------------|
| Separate table per category (e.g. `sectors`, `tiers`) | 10+ migrations to add tables; JOIN fan-out in queries; no benefit for a domain with ~10 small lists |
| Python Enum / hardcoded string literals | Cannot be edited by admin at runtime; changing values requires a deployment |
| JSONB blob on Organization.settings | No FK referential integrity; cannot do `WHERE ref_data_id = X` joins; hard to paginate or sort by |
| One table per entity with JSONB array of allowed values | Mixes config with data; no per-value metadata (position, active flag) |

**Why single table works here:**
- All categories are small lists (< 100 values each in practice)
- The `(org_id, category)` compound index makes per-category lookups O(1)
- Pre-populated TWG values are seeded once in a migration data step — admin can add/edit/deactivate values at runtime without schema changes
- The `is_active` flag lets admins soft-delete values that are in use on existing records (hard delete would break FK integrity)
- Single CRUD API surface: `GET /admin/ref-data?category=sector`, `POST /admin/ref-data`, `PATCH /admin/ref-data/{id}`

**Seeding TWG values:**

Seed data belongs in the migration that creates the table, not in `seed.py`, because it is schema-level configuration that must exist in production. Use Alembic's `op.bulk_insert()`:

```python
def upgrade() -> None:
    op.create_table("ref_data", ...)
    ref_data_table = sa.table("ref_data",
        sa.column("id", sa.String),
        sa.column("org_id", sa.String),  # NULL for system defaults — see note below
        sa.column("category", sa.String),
        sa.column("value", sa.String),
        sa.column("label", sa.String),
        sa.column("position", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(ref_data_table, [
        {"id": str(uuid4()), "org_id": None, "category": "sector", "value": "financial_services", "label": "Financial Services", "position": 1, "is_active": True},
        # ... etc
    ])
```

**System defaults vs org-specific values:**

Use `org_id = NULL` to represent system-level defaults shipped with the product. The query to populate a dropdown is then:

```sql
SELECT * FROM ref_data
WHERE category = 'sector'
  AND (org_id = :org_id OR org_id IS NULL)
  AND is_active = TRUE
ORDER BY position, label;
```

This lets each org add their own values on top of the defaults without copying every row, and lets an org deactivate a system default by adding a shadow row with `is_active = FALSE` and the same `value`. **If this org-override logic adds complexity, simplify to org-only rows and copy defaults during org creation.** The copy-on-create approach is simpler and more explicit — recommended for this project's scale.

**FK strategy on parent tables:**

Store the `ref_data.id` UUID as a nullable FK on the deal/contact/company table:

```python
sector_id: Mapped[Optional[UUID]] = mapped_column(
    ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True, index=True
)
```

`ondelete="SET NULL"` is correct: if an admin deletes a ref value, existing records become `NULL` rather than raising an FK violation. This is preferable to `RESTRICT` (blocks admin deletion) or `CASCADE` (silently nulls many records without admin awareness — accept this tradeoff given the domain).

Do NOT store only the string value in the parent table (e.g. `sector: str = "Technology"`). That approach loses the FK relationship, makes renaming a value a bulk UPDATE across all rows, and cannot enforce valid values at the DB level.

**Confidence:** HIGH — this is the standard Django/SQLAlchemy pattern for admin-managed lookup tables. The single-table-with-category discriminator is well-established for small enumerable domains.

---

## Decision 2: JSONB vs Dedicated Columns for PE-Specific Fields

### Recommendation: Dedicated columns for all named PE fields; JSONB only for genuinely unknown future fields

The existing `custom_fields` JSONB column is already the generic escape hatch. The PE Blueprint fields are fully enumerated in the PROJECT.md requirements. Putting known fields into JSONB would throw away PostgreSQL's ability to:

- Index on individual field values (e.g. filter deals by `transaction_type`)
- Enforce NOT NULL, type, and FK constraints
- Write readable SQLAlchemy queries (`Deal.revenue_usd > 1_000_000` vs `Deal.custom_fields["revenue_usd"].astext.cast(Numeric) > 1_000_000`)
- Generate sensible Alembic diffs going forward

**Rule of thumb for this codebase:**
- Field appears in the PROJECT.md requirements list → dedicated column
- Field is a reference to a lookup list → dedicated FK column (`sector_id UUID REFERENCES ref_data(id)`)
- Field is a financial metric (revenue, EBITDA, EV, equity investment) → `Numeric(18, 2)` column + companion `_currency` String(3) if multi-currency
- Field is a date milestone (CIM, IOI, LOI, etc.) → `Date` column, nullable
- Field is a multi-value list (e.g. coverage persons = multiple users, deal team = multiple users) → association table, not JSONB array
- Field is truly ad-hoc, user-defined, unpredictable shape → stays in `custom_fields` JSONB

**JSONB is appropriate for:**
- `custom_fields` (already exists): keeps catch-all for one-off fields no schema anticipates
- `DealCounterparty.next_steps` / `DealCounterparty.feedback` if these are long-form text blobs with evolving sub-structure — though plain `Text` columns are simpler
- Do NOT add a second JSONB blob alongside `custom_fields`. One JSONB catch-all per entity is the ceiling.

**Sparse columns are fine in PostgreSQL:**

PostgreSQL stores NULL columns with zero storage cost per row (NULL bitmap). A contact with 30 PE fields where 20 are NULL does not waste meaningful storage. The "use JSONB for sparse fields" argument applies to key-value stores and wide-column NoSQL, not PostgreSQL.

**Confidence:** HIGH — PostgreSQL documentation explicitly confirms NULL column storage is 1 bit in the heap tuple header, not per-column storage.

---

## Decision 3: Alembic Migration Strategy for Adding Many Columns

### Context: the existing initial migration is a metadata dump

`0001_initial` calls `models.Base.metadata.create_all(bind)`. This means Alembic's autogenerate (`--autogenerate`) will see a diff between the live schema and models.py any time models change. **Do not rely on autogenerate alone** — it will attempt to regenerate the whole schema.

### Recommended approach: hand-write explicit DDL migrations

For this milestone, write one migration file per logical unit:

```
0002_pe_ref_data.py          # CREATE TABLE ref_data + seed TWG defaults
0003_contact_pe_fields.py    # ALTER TABLE contacts ADD COLUMN ...
0004_company_pe_fields.py    # ALTER TABLE companies ADD COLUMN ...
0005_deal_pe_fields.py       # ALTER TABLE deals ADD COLUMN ...
0006_deal_counterparty.py    # CREATE TABLE deal_counterparties
0007_deal_funding.py         # CREATE TABLE deal_funding
```

Split by entity so that a failed migration can be rolled back without undoing unrelated changes. Alembic's `downgrade()` for each file should be the exact reverse (drop columns / drop tables).

**Pattern for adding nullable columns to an existing table:**

```python
def upgrade() -> None:
    # All PE fields are nullable — no default needed for existing rows
    op.add_column("deals", sa.Column("transaction_type_id", sa.UUID(), sa.ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True))
    op.add_column("deals", sa.Column("revenue_usd", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("ebitda_usd", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("ev_usd", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("equity_investment_usd", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("date_cim", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("date_ioi", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("date_loi", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("date_mgmt_presentation", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("date_live_diligence", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("date_portfolio_company", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("is_platform", sa.Boolean(), server_default="0", nullable=False))
    op.add_column("deals", sa.Column("fund", sa.String(100), nullable=True))
    op.add_column("deals", sa.Column("legacy_id", sa.String(100), nullable=True))
    op.add_column("deals", sa.Column("passed_reason_id", sa.UUID(), sa.ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True))
    op.add_column("deals", sa.Column("source_type_id", sa.UUID(), sa.ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_deals_transaction_type", "deals", ["transaction_type_id"])
    op.create_index("ix_deals_legacy_id", "deals", ["legacy_id"])

def downgrade() -> None:
    op.drop_index("ix_deals_transaction_type", "deals")
    op.drop_index("ix_deals_legacy_id", "deals")
    op.drop_column("deals", "transaction_type_id")
    # ... reverse all add_column calls
```

**Key rules:**
1. All new PE columns are `nullable=True` (or use `server_default` for booleans). Existing rows require no backfill.
2. Add FK indexes explicitly with `op.create_index`. Alembic does not create FK indexes automatically — and `(org_id, transaction_type_id)` compound indexes improve filter queries.
3. `op.add_column` on PostgreSQL is an instant metadata change for nullable columns (no table rewrite). Adding many columns to a live table is safe.
4. Do not call `metadata.create_all()` or `metadata.drop_all()` in any migration after `0001`. It bypasses Alembic's revision tracking and will corrupt the migration graph if applied out of order.

**Avoiding the `op.get_bind()` deprecation:**

The existing `0001_initial` uses `op.get_bind()` which is deprecated in Alembic 1.12+. New migrations should use `op.get_context().bind` or preferably avoid imperative DDL entirely by using `op.add_column`, `op.create_table`, etc. directly (which is what the pattern above does).

**Confidence:** HIGH — based on Alembic 1.13 documentation patterns and SQLAlchemy 2.0 migration guides.

---

## Decision 4: Multi-Value Association Fields

Some PE fields are inherently many-to-many:

- `deal.deal_team` — multiple users assigned to a deal
- `contact.coverage_persons` — multiple internal users covering a contact
- `contact.previous_employment` — multiple company entries
- `contact.board_memberships` — multiple company entries

**Recommendation: Association tables for user arrays; JSONB for employment/board history**

For user assignments (deal team, coverage persons), use association tables:

```python
class DealTeamMember(Base):
    __tablename__ = "deal_team_members"
    __table_args__ = (UniqueConstraint("deal_id", "user_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    deal_id: Mapped[UUID] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g. "lead", "analyst"
```

This allows querying "all deals where user X is a team member" with a proper index rather than a JSONB containment query (`@>` operator), and surfaces correctly in Pydantic response schemas without raw UUID arrays.

For `previous_employment` and `board_memberships` on contacts, these are historical data with free-form metadata (company name, title, date range) that will not be queried individually. Store as JSONB:

```python
previous_employment: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
# Structure: [{"company": "Blackstone", "title": "VP", "from": "2018", "to": "2022"}]
```

This is the correct use of JSONB: variable-length arrays of structured-but-not-queried data.

**Confidence:** MEDIUM — association table vs JSONB array tradeoff is context-dependent. The decision above is based on query patterns described in PROJECT.md requirements.

---

## Decision 5: DealCounterparty and DealFunding as First-Class Tables

Both are explicitly listed in PROJECT.md as new entities. Both have structured fields that will be displayed in list views, filtered, and sorted. Neither should be a JSONB blob on `deals`.

**DealCounterparty schema shape:**

```python
class DealCounterparty(Base):
    __tablename__ = "deal_counterparties"
    __table_args__ = (
        Index("ix_deal_counterparties_deal", "deal_id"),
        Index("ix_deal_counterparties_company", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    deal_id: Mapped[UUID] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    contact_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    # Pipeline stage tracking
    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="prospect")  # or ref_data FK
    nda_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    nda_signed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nrl_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    intro_materials_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    vdr_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tier_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    check_size_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    check_size_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    aum: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    investor_type_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

**DealFunding schema shape:**

```python
class DealFunding(Base):
    __tablename__ = "deal_funding"
    __table_args__ = (
        Index("ix_deal_funding_deal", "deal_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    deal_id: Mapped[UUID] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    capital_provider_company_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    capital_provider_contact_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    projected_commitment: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    actual_commitment: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

**Confidence:** HIGH — structure derived directly from PE Blueprint requirements in PROJECT.md.

---

## Decision 6: Pydantic v2 Schema Strategy for New Entities

The existing pattern (from `deals.py` schema):
- `*Create` — fields accepted on POST; FKs as UUIDs
- `*Update` — all fields optional; FKs as UUID | None
- `*Response` — `model_config = ConfigDict(from_attributes=True)`; computed display names (e.g. `sector_name: str | None`) populated by the service layer from a JOIN or eager-load

**For ref_data FK columns, the Response schema should carry both the ID and the resolved label:**

```python
class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ...
    transaction_type_id: UUID | None = None
    transaction_type_label: str | None = None   # resolved in service layer
    sector_id: UUID | None = None
    sector_label: str | None = None
```

The service layer resolves these in a single JOIN to `ref_data` rather than N+1 lookups. The frontend receives both the UUID (for form pre-population) and the label (for display), matching the existing pattern for `pipeline_name`, `stage_name`, `owner_name` in `DealResponse`.

**Frontend dropdown pattern with TanStack Query:**

```typescript
// Fetch all ref data once per category, cache for 10 minutes
const { data: sectors } = useQuery({
  queryKey: ['ref-data', 'sector'],
  queryFn: () => api.get('/admin/ref-data?category=sector'),
  staleTime: 10 * 60 * 1000,
})
```

Ref data is low-volatility (changes rarely). Aggressive caching (10-minute staleTime) prevents redundant network calls across forms. Invalidate on admin save.

**Confidence:** HIGH — consistent with existing codebase patterns.

---

## What to Avoid

### Avoid: Storing ref data values as plain strings on parent tables

Bad: `deal.sector = "Technology"` (String column, no FK)

Why: Admin rename of "Technology" to "Tech & Software" requires a bulk `UPDATE deals SET sector = 'Tech & Software' WHERE sector = 'Technology'` across potentially thousands of rows. FK to ref_data makes rename a single row UPDATE.

### Avoid: Python Enum for admin-configurable values

Bad: `class Sector(str, Enum): technology = "Technology"`

Why: Adding a new sector requires a code deploy. The whole point of admin-configurable reference data is runtime configurability.

### Avoid: Autogenerate-only Alembic workflow

Bad: Editing `models.py` then running `alembic revision --autogenerate`

Why: The initial migration (`0001_initial`) used `create_all`, so autogenerate will produce incorrect diffs on a fresh database (it sees no schema to diff against). Always write explicit DDL in migration `upgrade()` / `downgrade()` bodies.

### Avoid: Single monolithic migration for all PE fields

Bad: One `0002_pe_all_fields.py` adding all new tables and columns

Why: If the migration fails mid-way (e.g. FK to a table not yet created), the partial rollback is painful. Separate migrations per entity allow targeted downgrade.

### Avoid: Multiple JSONB catch-all columns

Bad: Adding `pe_fields: JSONB` alongside the existing `custom_fields: JSONB`

Why: Splits the catch-all surface, creates ambiguity about where to put new fields. The existing `custom_fields` is the single JSONB escape hatch — add to it if truly needed, or create a dedicated column.

### Avoid: `op.get_bind()` in new migrations

Bad: The pattern in `0001_initial` calling `models.Base.metadata.create_all(bind=op.get_bind())`

Why: `op.get_bind()` is deprecated in Alembic 1.12+ and will raise a warning. New migrations use the imperative DDL API (`op.add_column`, `op.create_table`) directly.

---

## Supporting Libraries (No New Dependencies Required)

All patterns above use only what is already installed:

| Need | Library | Already in stack |
|------|---------|-----------------|
| JSONB column type | `sqlalchemy.dialects.postgresql.JSONB` | Yes — `JSONVariant` alias in `models.py` |
| Numeric financial fields | `sqlalchemy.Numeric` | Yes — used on `Deal.value`, `Company.annual_revenue` |
| UUID primary keys | `uuid.uuid4` + `sqlalchemy.UUID` | Yes — universal across all models |
| Alembic bulk_insert for seed | `alembic.op.bulk_insert` | Yes — Alembic 1.13 |
| Pydantic v2 response schemas | `pydantic.BaseModel`, `ConfigDict` | Yes — Pydantic 2.6 |
| TanStack Query caching | `useQuery`, `staleTime` | Yes — TanStack Query 5.64 |

No new Python or npm packages are needed for this milestone.

---

## Migration Checklist Summary

- [ ] `0002_pe_ref_data.py` — CREATE TABLE ref_data with (org_id, category, value) unique constraint; seed TWG defaults via `op.bulk_insert`
- [ ] `0003_contact_pe_fields.py` — ADD COLUMN on contacts: phones (JSONB array), assistant (Text), contact_type_id (FK ref_data), sector_pref_ids (JSONB array of UUIDs), previous_employment (JSONB), board_memberships (JSONB), linkedin_url (Text), legacy_id (String)
- [ ] `0004_company_pe_fields.py` — ADD COLUMN on companies: company_type_id, company_sub_type_id, aum, ebitda, bite_size_min, bite_size_max, sector_id, sub_sector_id, tier_id, co_invest_ok (Boolean), is_watchlist (Boolean), coverage_user_id (FK users), legacy_id
- [ ] `0005_deal_pe_fields.py` — ADD COLUMN on deals: transaction_type_id, fund, is_platform, is_add_on, source_type_id, revenue_usd, ebitda_usd, ev_usd, equity_investment_usd, date_cim, date_ioi, date_loi, date_mgmt_presentation, date_live_diligence, date_portfolio_company, passed_reason_id, legacy_id
- [ ] `0006_deal_team_members.py` — CREATE TABLE deal_team_members (deal_id, user_id, role)
- [ ] `0007_deal_counterparties.py` — CREATE TABLE deal_counterparties
- [ ] `0008_deal_funding.py` — CREATE TABLE deal_funding

---

## Sources

- Codebase analysis: `/Users/oscarmack/OpenClaw/nexus-crm/backend/models.py` (HIGH confidence — direct inspection)
- Codebase analysis: `/Users/oscarmack/OpenClaw/nexus-crm/alembic/versions/0001_initial.py` (HIGH confidence — direct inspection)
- Codebase analysis: `/Users/oscarmack/OpenClaw/nexus-crm/backend/services/_crm.py` (HIGH confidence — direct inspection)
- SQLAlchemy 2.0 docs: `Mapped` typed column syntax, `DeclarativeBase`, async patterns (HIGH confidence — training knowledge consistent with observed codebase usage)
- Alembic 1.13 docs: `op.add_column`, `op.create_table`, `op.bulk_insert`, deprecation of `op.get_bind()` (HIGH confidence — training knowledge, consistent with Alembic 1.13 changelog)
- PostgreSQL NULL storage: NULL bitmap in heap tuple header, zero per-column overhead (HIGH confidence — PostgreSQL documentation, widely verified)
