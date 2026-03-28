---
phase: 05-deal-counterparty-deal-funding
verified: 2026-03-28T00:00:00Z
status: human_needed
score: 20/20 must-haves verified (automated); 2 items need human confirmation
human_verification:
  - test: "Counterparties tab — full CRUD flow"
    expected: "Add counterparty with company, tier, investor type; grid appears; click blank stage date cell to activate inline date input; abbreviated date displays after selection; edit modal shows all fields; delete removes row"
    why_human: "Inline date editing requires browser interaction; visual grid layout (sticky column, horizontal scroll) cannot be verified by grep"
  - test: "Funding tab — full CRUD flow"
    expected: "Add funding entry with provider, status (deal_funding_status dropdown), amounts, date, terms; row appears; edit pre-populates modal; delete removes row; null status renders as '---'"
    why_human: "Modal form population and RefSelect dropdown rendering require browser interaction"
---

# Phase 5: DealCounterparty & DealFunding Verification Report

**Phase Goal:** Deal detail has two new sub-entity tabs — Counterparties for tracking investor stage progression (NDA, NRL, materials, VDR, feedback) and Funding for tracking capital commitments — both with full inline management from the deal detail screen.
**Verified:** 2026-03-28
**Status:** human_needed — all automated checks pass; 2 visual/interactive items need human confirmation
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Counterparties tab loads with company name, tier, investor type, all 6 stage dates, check size, next steps in single query (no N+1) | ✓ VERIFIED | `_base_stmt` uses 3 aliased outerjoin in single SELECT; `DealCounterpartyService` list_for_deal default size=50 |
| 2 | Deal team member can add counterparty, set all 6 stage dates inline, update next steps, remove — without leaving deal detail | ? HUMAN | Code present and wired; full CRUD mutations implemented with invalidateQueries; requires browser verification |
| 3 | Deal team member can add capital provider with projected/actual amounts, status, terms to Funding tab | ? HUMAN | Code present and wired; FundingTab modal has all fields; requires browser verification |
| 4 | Counterparty and funding list endpoints enforce 50-row default page size | ✓ VERIFIED | `list_for_deal(... size: int = 50)` in both services; route defaults `size: int = 50` |
| 5 | Deactivated ref_data used by counterparty renders as "---" gracefully | ✓ VERIFIED | Line 227: `row.tier_label \|\| '---'`; line 228: `row.investor_type_label \|\| '---'`; line 645 funding: `entry.status_label \|\| '---'` |

**Score:** 3/5 truths fully verified automatically; 2 require human confirmation (visual/interactive)

---

### Required Artifacts

#### Plan 05-01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `alembic/versions/0010_deal_counterparties.py` | deal_counterparties table DDL + indexes | ✓ VERIFIED | Contains `op.create_table("deal_counterparties"`, all 22 columns, UniqueConstraint, 2 indexes, downgrade |
| `backend/models.py` — DealCounterparty class | ORM class with all columns | ✓ VERIFIED | Lines 329-367: class exists, all 6 stage dates, 2 ref_data FKs, financial fields, lazy="raise" |

#### Plan 05-02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/schemas/counterparties.py` | DealCounterpartyCreate/Update/Response/ListResponse | ✓ VERIFIED | All 4 classes present; company_name/tier_label/investor_type_label in Response |
| `backend/services/counterparties.py` | DealCounterpartyService with list/create/update/delete | ✓ VERIFIED | All 4 methods present; aliased joins present |
| `backend/api/routes/counterparties.py` | 4 CRUD routes under /deals/{deal_id}/counterparties | ✓ VERIFIED | GET/POST/PATCH/DELETE all present; registered in main.py |

#### Plan 05-03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `alembic/versions/0011_deal_funding.py` | deal_funding table DDL + deal_funding_status seed | ✓ VERIFIED | Table with 13 columns; 5 seeds: Soft Circle, Hard Circle, Committed, Funded, Declined |
| `backend/models.py` — DealFunding class | ORM class with all columns | ✓ VERIFIED | Lines 370-394: class exists, all financial fields, actual_commitment_date, terms, lazy="raise" |
| `backend/schemas/funding.py` | DealFundingCreate/Update/Response/ListResponse | ✓ VERIFIED | All 4 classes present; capital_provider_name/status_label in Response |
| `backend/services/funding.py` | DealFundingService with list/create/update/delete | ✓ VERIFIED | All 4 methods present; StatusRef/ProviderCompany aliased joins |
| `backend/api/routes/funding.py` | 4 CRUD routes under /deals/{deal_id}/funding | ✓ VERIFIED | GET/POST/PATCH/DELETE all present; registered in main.py |

#### Plan 05-04 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/api/counterparties.js` | getCounterparties/createCounterparty/updateCounterparty/deleteCounterparty | ✓ VERIFIED | All 4 exports present, correct URL patterns |
| `frontend/src/api/funding.js` | getFunding/createFunding/updateFunding/deleteFunding | ✓ VERIFIED | All 4 exports present, correct URL patterns |
| `frontend/src/pages/DealDetailPage.jsx` | 6-tab strip + CounterpartiesTab + FundingTab | ✓ VERIFIED | 6 tabs in correct order; both components present at module level |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/models.py` | `0010_deal_counterparties.py` | DealCounterparty ORM matches migration columns | ✓ WIRED | All 22 columns match between migration and ORM class |
| `backend/models.py` | `0011_deal_funding.py` | DealFunding ORM matches migration columns | ✓ WIRED | All 13 columns match between migration and ORM class |
| `backend/services/counterparties.py` | `backend/models.py` | `aliased(RefData)` multi-join | ✓ WIRED | TierRef/InvestorTypeRef/CpartyCompany all aliased; used in _base_stmt |
| `backend/api/routes/counterparties.py` | `backend/services/counterparties.py` | `DealCounterpartyService(db, current_user)` | ✓ WIRED | All 4 route handlers instantiate and call service |
| `backend/api/main.py` | `backend/api/routes/counterparties.py` | `counterparties.router` | ✓ WIRED | Line 19 import; line 86 router registration |
| `backend/services/funding.py` | `backend/models.py` | `aliased(RefData)` join | ✓ WIRED | StatusRef/ProviderCompany aliased; used in _base_stmt |
| `backend/api/main.py` | `backend/api/routes/funding.py` | `funding.router` | ✓ WIRED | Line 19 import; line 88 router registration |
| `DealDetailPage.jsx` | `/api/v1/deals/{deal_id}/counterparties` | `queryKey: ['deal-counterparties', dealId]` | ✓ WIRED | Line 101: queryKey present; getCounterparties imported and called |
| `DealDetailPage.jsx` | `/api/v1/deals/{deal_id}/funding` | `queryKey: ['deal-funding', dealId]` | ✓ WIRED | Line 515: queryKey present; getFunding imported and called |
| `DealDetailPage.jsx` | `CounterpartiesTab` and `FundingTab` | `<TabsContent value="counterparties">` and `<TabsContent value="funding">` | ✓ WIRED | Lines 1612-1621: both wired with dealId and companies props |
| `0011_deal_funding.py` | `ref_data table` | `op.bulk_insert` for deal_funding_status | ✓ WIRED | 5 seeds inserted with category="deal_funding_status" |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `CounterpartiesTab` | `cpartiesQuery.data?.items` | `getCounterparties(dealId)` → `DealCounterpartyService.list_for_deal` → aliased JOIN query against `deal_counterparties` table | Yes — SELECT with outerjoin from real DB table | ✓ FLOWING |
| `FundingTab` | `fundingQuery.data?.items` | `getFunding(dealId)` → `DealFundingService.list_for_deal` → aliased JOIN query against `deal_funding` table | Yes — SELECT with outerjoin from real DB table | ✓ FLOWING |
| `DealCounterpartyResponse.tier_label` | `row.tier_label` | `TierRef.label.label("tier_label")` outerjoin on `ref_data` table | Yes — DB join resolves label | ✓ FLOWING |
| `DealFundingResponse.status_label` | `row.status_label` | `StatusRef.label.label("status_label")` outerjoin on `ref_data` table | Yes — DB join resolves label from seeded deal_funding_status | ✓ FLOWING |

---

### Behavioral Spot-Checks

Step 7b: SKIPPED for server-dependent endpoints — requires running backend. The Vite build check would verify frontend compilation but was not run in this verification pass. Code-level wiring verified instead.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CPARTY-01 | 05-01 | deal_counterparties table with id, org_id, deal_id FK cascade, company_id FK set null, contact fields, position | ✓ SATISFIED | migration 0010 + ORM class verified |
| CPARTY-02 | 05-01 | 6 stage date columns: nda_sent_at, nda_signed_at, nrl_signed_at, intro_materials_sent_at, vdr_access_granted_at, feedback_received_at | ✓ SATISFIED | All 6 columns in migration and ORM at lines 345-350 |
| CPARTY-03 | 05-01 | tier_id FK ref_data, investor_type_id FK ref_data, next_steps, notes | ✓ SATISFIED | Lines 352-360 in models.py; SET NULL cascade on both |
| CPARTY-04 | 05-01 | check_size_amount/currency, aum_amount/currency (Numeric 18,2) | ✓ SATISFIED | Lines 355-358 in models.py |
| CPARTY-05 | 05-02 | GET /deals/{deal_id}/counterparties with company name, stage dates, tier label, investor type label — single query no N+1 | ✓ SATISFIED | _base_stmt with 3 aliased outerjoin; list_for_deal default size=50 |
| CPARTY-06 | 05-02 | POST /deals/{deal_id}/counterparties creates counterparty | ✓ SATISFIED | POST route with 201 status; create() verifies deal ownership |
| CPARTY-07 | 05-02 | PATCH /deals/{deal_id}/counterparties/{id} updates including individual stage dates | ✓ SATISFIED | PATCH route; update() uses model_dump(exclude_unset=True) + setattr |
| CPARTY-08 | 05-02 | DELETE /deals/{deal_id}/counterparties/{id} removes counterparty | ✓ SATISFIED | DELETE route with 204 status |
| CPARTY-09 | 05-04 | Counterparties tab grid with Company, Tier, Investor Type, 6 stage dates, Next Steps columns | ? HUMAN | Code implements all columns; visual verification required |
| CPARTY-10 | 05-04 | Add counterparty from Counterparties tab | ? HUMAN | Add dialog wired with all required fields; visual verification required |
| CPARTY-11 | 05-04 | Edit counterparty inline or via modal including stage dates and next steps | ? HUMAN | editingCell inline date + edit dialog both present; visual verification required |
| CPARTY-12 | 05-04 | Remove counterparty from Counterparties tab | ? HUMAN | deleteMutation wired; visual verification required |
| FUNDING-01 | 05-03 | deal_funding table with id, org_id, deal_id FK cascade, capital_provider_id FK set null, status_id FK ref_data | ✓ SATISFIED | migration 0011 verified; ORM class lines 370-394 |
| FUNDING-02 | 05-03 | projected/actual commitment amount+currency, actual_commitment_date | ✓ SATISFIED | All 5 columns present in migration and ORM |
| FUNDING-03 | 05-03 | terms, comments_next_steps | ✓ SATISFIED | Both columns in migration and ORM |
| FUNDING-04 | 05-03 | GET /deals/{deal_id}/funding returns entries with capital provider company name resolved | ✓ SATISFIED | _base_stmt joins ProviderCompany; capital_provider_name in response |
| FUNDING-05 | 05-03 | POST /deals/{deal_id}/funding creates funding entry | ✓ SATISFIED | POST route with 201; create() verifies deal ownership |
| FUNDING-06 | 05-03 | PATCH /deals/{deal_id}/funding/{id} updates entry | ✓ SATISFIED | PATCH route; update() uses setattr loop |
| FUNDING-07 | 05-03 | DELETE /deals/{deal_id}/funding/{id} removes entry | ✓ SATISFIED | DELETE route with 204 |
| FUNDING-08 | 05-04 | Funding tab with Provider, Status, Projected Commitment, Actual Commitment, Date, Terms columns | ? HUMAN | FundingTab renders all columns; visual verification required |
| FUNDING-09 | 05-04 | Add, edit, remove funding entries from Funding tab | ? HUMAN | All 3 mutations wired; visual verification required |

**Note on REQUIREMENTS.md traceability table:** CPARTY-01 through CPARTY-08 and FUNDING-01 through FUNDING-07 are still marked "Pending" in the traceability matrix at the bottom of REQUIREMENTS.md. The code satisfies all these requirements but the documentation was not updated to reflect completion. This is a documentation gap only — no code gap.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/services/funding.py` | 165 | `await self.db.flush()` in `delete()` with no `commit()` | ℹ️ Info | Intentional — route handler owns `db.commit()`. Consistent with funds.py pattern. No functional gap. |
| `backend/services/counterparties.py` | 127, 153, 173 | `await self.db.commit()` inside service methods | ℹ️ Info | Inconsistent with funding service pattern (service owns commit here, route does not). Works correctly; minor pattern inconsistency. |

No blockers. No stubs. No placeholder content found.

---

### Human Verification Required

#### 1. Counterparties Tab — Full Interaction Verification

**Test:** Run `make dev`, log in with admin@demo.local / password123, navigate to any deal detail page
**Expected:**
- Tab strip shows 6 tabs in order: Profile | Counterparties | Funding | Activity | Tasks | AI Insights
- Counterparties tab shows empty state "No counterparties tracked yet..." with Add button
- Add Counterparty modal opens with Company (required select), Tier (RefSelect), Investor Type (RefSelect), Primary Contact Name, Check Size fields, Next Steps
- After adding: row appears in horizontally scrollable grid with sticky Company column
- Grid columns visible: Company (sticky left), Tier, Investor Type, NDA Sent, NDA Signed, NRL, Materials, VDR, Feedback, Next Steps, Actions
- Clicking a blank stage date cell activates an inline date input; selecting a date persists it and shows abbreviated format (e.g. "Mar 15")
- Edit button opens full edit modal with all fields including AUM, email, phone, notes, all 6 stage dates
- Delete button removes the row
- Deactivated tier/investor_type labels show "---" (not error)
**Why human:** Inline date editing via click-to-activate requires browser interaction. Sticky column behavior, horizontal scroll, abbreviated date format, and modal population require visual confirmation.

#### 2. Funding Tab — Full Interaction Verification

**Test:** Navigate to the Funding tab on the same deal detail page
**Expected:**
- Funding tab shows empty state "No funding commitments recorded..." with Add button
- Add Funding modal opens with Capital Provider (company select), Status (RefSelect showing: Soft Circle, Hard Circle, Committed, Funded, Declined), Projected Commitment amount+currency, Actual Commitment amount+currency, Commitment Date, Terms, Comments/Next Steps
- After adding: row appears in table with columns: Provider, Status, Projected, Actual, Date, Terms (truncated), Actions
- Edit button pre-populates modal with existing values
- Delete button removes the row
- Null status renders as "---" not blank or error
**Why human:** RefSelect dropdown population from seeded deal_funding_status requires browser verification. Modal pre-population requires interactive test.

---

## Gaps Summary

No automated gaps found. All 20 must-have artifacts exist, are substantive, and are wired end-to-end with real data flowing from database through service to frontend.

The only outstanding items are human-verification tasks (CPARTY-09 through CPARTY-12 and FUNDING-08 through FUNDING-09) which require browser interaction. The SUMMARY for plan 05-04 records that visual verification was already approved by the user on 2026-03-28 at the Task 2 checkpoint. If that approval is accepted as satisfying the human verification requirement, status can be upgraded to **passed**.

**Documentation note:** The traceability matrix in `.planning/REQUIREMENTS.md` still shows CPARTY-01 through CPARTY-08 and FUNDING-01 through FUNDING-07 as "Pending". These should be updated to "Complete" to match the actual state of the codebase.

---

_Verified: 2026-03-28_
_Verifier: Claude (gsd-verifier)_
