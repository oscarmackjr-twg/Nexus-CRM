# Feature Landscape: PE CRM — Counterparty Pipeline & Deal Management

**Domain:** Private Equity deal advisory / capital raises (equity, credit, preferred equity)
**Researched:** 2026-03-26
**Confidence note:** Web search and WebFetch were unavailable. Analysis draws on (a) TWG Asia's own existing DealCloud/PE Blueprint schema as captured in PROJECT.md — HIGH confidence primary source, (b) training knowledge of DealCloud, Navatar, Salesforce FSC, Altvia, and 4Degrees through August 2025 — MEDIUM confidence where corroborated by multiple products, LOW confidence where product-specific.

---

## Table Stakes

Features PE teams consider non-negotiable. Missing = product feels incomplete or requires parallel spreadsheets.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Per-deal counterparty pipeline | Every deal has a distinct investor list at different stages — one shared pipeline is useless | Medium | Core differentiator from generic CRMs; TWG already tracks this in spreadsheets |
| Named pipeline stages (NDA → NRL → Materials → VDR → Feedback) | Every PE advisory firm has a standard process for moving investors through a capital raise | Low | Stages should be configurable; TWG's specific stages are NDA Signed, NRL Signed, Intro Materials Sent, VDR Access Granted, Feedback Received |
| Stage date capture per counterparty | Compliance and deal management require knowing when each investor reached each stage | Low | Not just current stage — date stamps matter for reporting and LP communication |
| Free-text next-steps field per counterparty | Deal teams track next actions against each investor informally; this replaces the spreadsheet "Notes" column | Low | Critical for daily use — without it teams default back to Excel |
| Investor type classification | LPs, SWFs, pension funds, family offices, and corporates behave differently in a process; teams sort/filter by type | Low | Standard values: LP, SWF, Pension Fund, Family Office, Corporate Strategic, Fund of Funds, DFI, Co-investor |
| Tier/priority classification per counterparty | Not all investors are equal; tier 1/2/3 signals priority for follow-up | Low | Must be deal-specific — an investor can be tier 1 on one deal and tier 3 on another |
| Check size / commitment size tracking | Fundamental to capital raise math — sum of targeted commitments vs. deal size | Low | Separate fields for target check size and actual commitment |
| Deal financial metrics (EV, Revenue, EBITDA, Equity Investment) | Required for deal memos, investor materials, and portfolio reporting | Low | All standard in PE deal tracking; sourced from PE Blueprint schema |
| Transaction type (Equity, Credit, Preferred Equity, Mezzanine, Growth Equity) | Determines deal process, investor universe, and documentation | Low | Admin-configurable; different types have different pipeline stages |
| Deal date milestones (CIM, IOI, LOI, management presentation, live diligence, close) | Milestone tracking is how PE teams measure process velocity and report to deal committees | Low | All six milestones standard per PE Blueprint schema |
| Company AUM field | Required for LP/investor records — AUM is how PE contacts are sized and tiered | Low | Applies to company record, not just counterparty |
| Contact coverage person assignment | PE teams have coverage relationships — deal team member responsible for each investor contact | Low | Both company-level and contact-level coverage persons |
| Deal source tracking | Attribution to origination channel (proprietary, intermediary, network, auction) matters for strategy analysis | Low | Standard in all PE CRMs |
| Passed/dead reason codes | Required for pipeline reporting and deal team retrospectives | Low | Admin-configurable; not a free-text field — must be queryable |
| Fund association on deal | Multi-fund firms must associate each deal with the deploying fund | Low | Single field; not complex fund-of-fund accounting |
| Platform vs. add-on flag | Core PE concept — add-ons to existing portfolio companies have different processes | Low | Boolean or enum |

---

## Differentiators

Features that distinguish a purpose-built PE advisory CRM from a generic CRM or basic spreadsheet.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Counterparty pipeline as deal sub-view | Seeing all investors on one deal in a grid — sorted by stage — is the primary daily workflow | Medium | Not a separate CRM pipeline; nested within deal detail. The TWG Deal Tracker spreadsheet is exactly this view |
| DealFunding entity (capital provider commitments) | Tracks projected vs. actual commitments from capital providers, separate from investor pipeline; feeds fund reporting | Medium | Distinct from counterparty pipeline — DealFunding is about who is actually committing capital and on what terms |
| Bite size range on company/investor records | PE-standard qualifier — "min $50M, max $200M" — used to filter investor universe before outreach | Low | Stored as min/max pair or range string; sourced from PE Blueprint company schema |
| Investment preference fields (sector focus, geography, stage) | Used to match investors to deals — without this, investor matching is manual | Medium | Sector preferences on contact record are common in DealCloud; avoid making it a complex tagging system |
| Co-invest flag on company | Identifies investors willing to co-invest alongside the lead — a key criterion for large-cap deals | Low | Boolean; company-level |
| Watchlist flag on company | Enables a curated "hot list" of prioritized targets without polluting search results | Low | Boolean; org-scoped |
| Previous employment / board memberships on contact | PE relationship intelligence — knowing a contact's prior firms surfaces warm intro paths | Low | Array of strings; sourced from PE Blueprint contact schema |
| Legacy ID / external system ID on all entities | Enables future data migration from DealCloud without losing cross-references | Low | Critical for TWG's eventual import; just a nullable string field |
| Admin-configurable reference data | Sectors, tiers, transaction types, contact types change as the firm evolves — hardcoded values create support burden | Medium | Must support: create, rename, reorder, soft-delete (items in use cannot be hard-deleted) |
| Interaction log against counterparty | Not just deal-level activities — specific investor-level notes (call, meeting, email) | Medium | DealCloud/Altvia both have this; generic CRM activity log is insufficient |

---

## Anti-Features

Features to explicitly NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full LP portal / document distribution | Out of scope for a deal advisory CRM; this is fund administration software (iLevel, Allvue) | Reference VDR access as a stage flag; link to external VDR (Intralinks, Datasite) |
| Complex multi-currency FX conversion | Adds significant backend complexity; PE deal teams use a single reporting currency per deal | Store amount + currency code; display "as entered"; defer FX conversion |
| Automated email parsing to populate counterparty stages | High complexity, high error rate; PE teams need manual confirmation of each stage change | Manual stage updates with keyboard-efficient UI; auto-suggestions deferred |
| Fund-level waterfall / carry calculations | This is fund accounting, not CRM | Flag the fund on the deal; all waterfall logic stays in the portfolio management system |
| Investor portal with login access | Increases security surface area and compliance scope dramatically | Track investor status internally; distribute materials via existing VDR tools |
| Cap table management | Complex legal/corporate governance feature; separate tooling (Carta, Visible) owns this | Record equity investment amount; leave ownership structure to dedicated tools |
| Duplicate investor deduplication AI | High complexity; PE firms have small, known investor universes (hundreds, not millions) | Standard search + manual merge; deduplication AI not justified at this scale |
| Mobile-native deal management | Polish pass only this milestone; mobile is a separate surface | Web-first; mobile can read but not be the primary workflow tool |

---

## Feature Dependencies

```
Admin reference data (sectors, types, tiers) → DealCounterparty (uses tier, investor type)
Admin reference data → Deal expanded fields (uses transaction type, source type, passed/dead reason)
Admin reference data → Company expanded fields (uses sector, sub-sector, type, sub-type)
Admin reference data → Contact expanded fields (uses contact type)

Company expanded fields (AUM, bite sizes, investment prefs) → DealCounterparty (pre-populate AUM, check size on add)
Contact expanded fields (coverage person) → DealCounterparty (pre-populate contact reference)

Deal expanded fields (fund, transaction type, financial metrics, milestones) → DealFunding (fund context)
DealCounterparty → DealFunding (capital provider in DealFunding may also be a DealCounterparty)

Deal → DealCounterparty (one deal, many counterparties)
Deal → DealFunding (one deal, many funding commitments)
```

---

## Counterparty Pipeline Stages — Standard PE Capital Raise

Based on TWG Asia's Deal Tracker and corroborated by standard PE advisory practice across DealCloud, Navatar, and Altvia implementations. Confidence: HIGH (from primary source PROJECT.md).

### Stage Sequence

```
1. NDA Sent          → Investor targeted; NDA circulated
2. NDA Signed        → NDA executed; investor is now a confirmed counterparty
3. NRL Signed        → Non-Reliance Letter signed (common in credit/structured deals)
4. Intro Materials Sent → Teaser or CIM distributed
5. VDR Access Granted → Data room credentials issued; active diligence begins
6. Feedback Received  → Investor has responded with interest level or passed
7. Term Sheet / IOI   → Indication of Interest submitted
8. LOI / Exclusivity  → Letter of Intent executed
9. Closed / Committed → Commitment confirmed
```

Notes on stage design:
- TWG's current tracker uses: NDA, NRL, Materials, VDR, Feedback, Next Steps. This is the minimum viable set.
- NRL is specific to credit/structured products — for straight equity deals it is often skipped. The stage should be optional.
- "Feedback" in TWG's workflow is a text field, not a stage — model it as both: a stage flag ("feedback received: yes/no") and a free-text feedback notes field.
- Stages should be stored as boolean checkboxes with date stamps, not as a single enum. An investor can have NDA Signed = true and VDR Access = false simultaneously; they don't progress linearly in all cases.

### Per-Counterparty Fields (Essential — Used Daily)

Sourced from PE Blueprint/DealCloud schema and TWG Deal Tracker. Confidence: HIGH.

| Field | Type | Usage Frequency | Notes |
|-------|------|-----------------|-------|
| Investor name (company link) | FK to Company | Every row | Core identity |
| Primary contact (contact link) | FK to Contact | Every row | Who to call |
| TWG owner (user link) | FK to User | Every row | Accountability |
| Investor type | Enum (admin-configured) | Every row | LP, SWF, Pension, Family Office, Corporate, FoF, DFI |
| Tier | Enum (admin-configured) | Every row | 1 / 2 / 3 or A / B / C |
| NDA sent date | Date | High | |
| NDA signed date | Date | High | |
| NRL signed date | Date | Medium | Credit deals primarily |
| Intro materials sent date | Date | High | |
| VDR access granted date | Date | High | |
| Feedback received date | Date | High | |
| Feedback notes | Text | High | What they said — critical for internal reporting |
| Next steps | Text | Every row | Primary action field; the TWG tracker "next steps" column |
| Target check size | Decimal + currency | High | What we're asking this investor for |
| AUM | Decimal + currency | Medium | Pulled from company record, can be overridden per deal |
| Status | Enum: Active / Passed / On Hold / Committed | Every row | Quick filter for deal team |
| Passed reason | Text / enum | Medium | Why they declined |
| Last contacted date | Date | High | Derived from interaction log or manually set |
| Comments / notes | Text | High | General notes field |

### Per-Counterparty Fields (Supplemental — Useful but Not Daily)

| Field | Type | Notes |
|-------|------|-------|
| Relationship source | Text | How we know them — referral, conference, prior deal |
| GP interest (co-invest flag) | Boolean | Will they participate as co-investor |
| Legal counsel | Text | Investor's counsel for NDA/LOI execution |
| Side letter requirements | Text | Institutional investors often require side letters |
| Previous investment in company | Boolean | Have they backed this company before |

---

## Deal-Level Fields — Essential for PE Advisory

Sourced directly from PE Blueprint schema (Intapp DealCloud export template). Confidence: HIGH.

### Core Deal Identity
| Field | Why |
|-------|-----|
| Transaction type | Equity / Credit / Preferred Equity / Mezzanine — drives investor universe and process |
| Fund | Which fund is deploying; multi-fund firms need this for attribution |
| Platform vs. add-on | Different diligence processes and investor expectations |
| Deal source type | Proprietary / intermediary / auction / network — strategy attribution |
| Deal team members | Who internally is responsible; multi-person |
| Sector / sub-sector | Industry classification for reporting and investor matching |

### Financial Metrics (Deal-Level)
| Field | Why |
|-------|-----|
| Revenue | Standard deal memo metric |
| EBITDA | Primary PE valuation driver |
| Enterprise value (EV) | Deal size indicator |
| Equity investment | Actual check size being raised |
| Deal currency | USD / HKD / SGD / etc. — store code, no conversion |

### Date Milestones
| Field | Why |
|-------|-----|
| CIM date | When the Confidential Information Memorandum was distributed |
| IOI date | Indication of Interest deadline |
| LOI date | Letter of Intent executed |
| Management presentation date | MP scheduled — a key process milestone |
| Live diligence date | Diligence period opened |
| Portfolio company date | When company entered portfolio (for buy-side deals) |
| Expected close date | Standard pipeline field |
| Actual close date | For closed deal reporting |

### Deal Outcome Tracking
| Field | Why |
|-------|-----|
| Passed/Dead reason | Valuation, process, no fit, market — required for deal team retrospectives |
| Win/Loss | Binary outcome for pipeline velocity metrics |

---

## Investor/Company Fields — Essential for PE Contact Management

Sourced from PE Blueprint company and contact schemas. Confidence: HIGH.

### Company Fields (LP/Investor Records)
| Field | Notes |
|-------|-------|
| Company type | PE Fund, LP, SWF, Corporate, Family Office, Lender, Advisor |
| Company sub-type | More granular — e.g., under LP: Pension, Endowment, Insurance |
| AUM | Assets under management — primary size metric for investors |
| Min bite size | Minimum investment per deal |
| Max bite size | Maximum investment per deal |
| Investment sector preferences | Which industries they invest in |
| Investment stage preferences | Growth / buyout / credit / special situations |
| Geography focus | Regional preferences |
| Co-invest appetite | Boolean |
| Watchlist flag | Firm-internal prioritization |
| Coverage person | Primary TWG team member covering this firm |
| Tier | Relationship tier (1/2/3) |
| Legacy ID / DealCloud ID | For future migration |

### Contact Fields (LP/GP Contact Records)
| Field | Notes |
|-------|-------|
| Contact type | LP, GP, Advisor, Management Team, Lender |
| Direct phone | Not just "phone" — direct line matters in PE |
| Mobile phone | Distinct from direct line |
| Assistant name + phone | Senior PE contacts are often reached via assistant |
| LinkedIn URL | Standard enrichment field |
| Coverage persons | Which TWG team members cover this contact (can be multiple) |
| Sector preferences | Individual preferences may differ from firm's |
| Previous employment | Array — prior firms, useful for relationship mapping |
| Board memberships | Array — what companies they sit on |
| Legacy ID / DealCloud ID | For future migration |

---

## DealFunding Fields — Capital Provider Commitments

For tracking actual capital commitments per deal, separate from the counterparty pipeline.

| Field | Why |
|-------|-----|
| Capital provider | FK to Company |
| Provider contact | FK to Contact |
| Projected commitment | What we expect them to commit |
| Actual commitment | What was confirmed |
| Commitment currency | |
| Terms summary | Brief description of instrument terms |
| Status | Soft circle / Hard circle / Signed / Funded |
| Comments / next steps | Free text |
| Date committed | |
| Notes | General |

---

## Reporting & Visibility Requirements

What PE deal teams need to see — informs dashboard and list view design.

### Deal-Level Views (Daily Use)
- Counterparty grid: all investors on a deal, sorted by tier, with stage status at a glance
- Stage summary: how many investors at each stage (e.g., "12 NDAs sent, 8 signed, 4 in VDR")
- Next steps feed: all open next-steps actions across all counterparties on a deal, sorted by date
- Capital raise progress: total targeted commitments vs. deal equity investment amount

### Pipeline Views (Weekly Use)
- Deal pipeline by stage (existing kanban — still valid)
- Deals by transaction type
- Deals by sector
- Deals by TWG owner
- Stage velocity: average days from CIM to IOI, IOI to LOI, LOI to close

### Investor Views (Ad Hoc)
- All deals a specific investor has participated in
- Investor activity across deals (investor relationship history)
- Tier 1 investors with no contact in last 30/60/90 days

### Anti-Patterns in Reporting
- Do NOT try to aggregate counterparty stage across deals into a single global pipeline — investors appear on multiple deals at different stages simultaneously; a global view is misleading
- Do NOT show deal financial metrics on list views by default — sensitive information; keep on detail view only

---

## Admin Reference Data — Required Values

These must be pre-populated with TWG Asia's actual values and user-editable by org admins.

| Reference Set | Minimum Required Values |
|---------------|------------------------|
| Sectors | Financial Services, Technology, Healthcare, Real Estate, Infrastructure, Consumer, Industrials, Energy |
| Sub-Sectors | Varies per sector; start with free-text or a flat list |
| Transaction Types | Equity, Credit, Preferred Equity, Mezzanine, Growth Equity |
| Tiers | Tier 1, Tier 2, Tier 3 |
| Investor / Contact Types | LP, GP, SWF, Pension Fund, Family Office, Corporate Strategic, Fund of Funds, DFI, Lender, Advisor, Management |
| Company Types | PE Fund, LP, SWF, Corporate, Family Office, Lender, Financial Institution, Advisor |
| Company Sub-Types | Varies per type |
| Deal Source Types | Proprietary, Intermediary, Auction, Network Referral, Repeat |
| Passed / Dead Reasons | Valuation, No Fit, Process Timing, Market Conditions, Relationship, Other |
| Currencies | USD, HKD, SGD, EUR, GBP, CNY, JPY — at minimum |

---

## MVP Recommendation for This Milestone

The milestone scope in PROJECT.md is well-calibrated. Priority order within the milestone:

1. **Admin reference data first** — all other entities depend on it for foreign keys to reference tables; build and populate before expanding entity schemas
2. **Deal expanded fields** — extends existing Deal model; lowest risk, high immediate value for TWG's daily reporting
3. **Company and Contact expanded fields** — expands existing records; needed before DealCounterparty can pre-populate investor data
4. **DealCounterparty entity** — the primary net-new feature; core daily workflow for TWG; build after Company/Contact fields are in place so auto-population works from day one
5. **DealFunding entity** — simpler than DealCounterparty; fewer fields, no stage workflow; can be built in parallel with or after DealCounterparty
6. **UI surface** — all expanded fields on detail screens; DealCounterparty as a grid/table sub-view within deal detail (not a separate page)

**Defer within this milestone (if time-constrained):**
- Interaction log per counterparty (call/meeting/email) — valuable but not in the original scope; use the deal-level activity log as a proxy for now
- Pipeline velocity analytics using new date milestones — the math exists in backend already; populate the endpoints after the data model is stable

---

## Sources

- PRIMARY: `/Users/oscarmack/OpenClaw/nexus-crm/.planning/PROJECT.md` — TWG Asia workflow description, PE Blueprint/DealCloud schema fields, TWG Deal Tracker structure (HIGH confidence — first-party source data)
- TRAINING KNOWLEDGE: Intapp DealCloud feature set as of ~2024-2025 (MEDIUM confidence — corroborated across multiple fields described in PE Blueprint schema)
- TRAINING KNOWLEDGE: Navatar, Salesforce FSC Financial Services Cloud, Altvia, 4Degrees feature sets (MEDIUM confidence for table-stakes features shared across products; LOW confidence for product-specific differentiators)
- Note: Web search, WebFetch, and all MCP search tools were unavailable in this research session. All claims about competitor products are based on training data through August 2025 and should be validated if product-specific accuracy is required.
