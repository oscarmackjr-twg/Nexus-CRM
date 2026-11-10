# Nexus CRM — Demo Functionality Priorities

**Repository reviewed:** [oscarmackjr-twg/Nexus-CRM](https://github.com/oscarmackjr-twg/Nexus-CRM)  
**Reviewed source:** `main` at commit `3d1090d09fb0ff43760f2a95a5a778570c44ccaa`  
**Review date:** 2026-09-02  
**Purpose:** Prioritize low-effort, high-visibility functionality expected by basic CRM users and administrators before a proof-of-concept demo.

## Executive recommendation

Nexus CRM already has a strong PE-specific foundation: contacts, companies, deals, funds, deal counterparties, funding commitments, role-aware administration, configurable reference data, and polished detail pages. The best pre-demo investment is not another major entity. It is closing the small interaction gaps that make the current application feel unfinished.

The recommended demo tranche is:

1. Add visible **New Contact**, **New Company**, and **New Deal** actions.
2. Add **search and useful filters** to the three primary list pages.
3. Replace the unfinished AI command palette with a usable **global record search** or hide it for the demo.
4. Add **CSV export of the current view**.
5. Complete two small admin lifecycle gaps: **reactivate users/groups** and **admin password reset**.

These changes produce a complete demo loop: find or create a relationship, update it, progress a deal, export the result, and administer access.

## Priority definitions

| Priority | Meaning | Demo guidance |
|---|---|---|
| **P0** | Must address before demo | Visible in the main demo path or likely to invite an immediate question |
| **P1** | Strong pre-demo enhancement | Adds credibility and daily usefulness without expanding the product boundary |
| **P2** | Expected next capability | Valuable, but larger or less visible than the P0/P1 work |
| **P3** | Defer | Significant implementation, security, or workflow complexity |

## P0 — Demo-critical low-hanging fruit

| Rank | User | Function | Why it matters | Minimum useful scope | Relative effort |
|---:|---|---|---|---|---|
| 1 | Basic | **Create Contact, Company, and Deal from list pages** | The list pages currently have no visible Add action. A CRM demo feels incomplete if a presenter cannot create its three core records from their natural entry points. | Add a primary button beside each page title; open a focused create dialog or route; validate required fields; save and navigate to the new detail record. | Small–Medium |
| 2 | Basic | **Search and filter core lists** | Contacts and Companies have no visible filters; Deals only filter by status. Users expect to locate a person, firm, or deal immediately. | Debounced search by name; Contacts: company/owner/stage; Companies: type/tier/sector/owner; Deals: stage/status/owner. Preserve filter state in the URL if practical. | Small–Medium |
| 3 | Basic | **Make Cmd/Ctrl+K useful—or hide it** | The layout opens an AI modal whose only result is “AI query coming in Phase 14+.” Discovering this during a demo undermines confidence. | Preferred: use the existing command palette as global search across contacts, companies, and deals, with keyboard navigation. Minimum fallback: remove the shortcut/modal until it is functional. | Small for hide; Medium for search |
| 4 | Basic | **Demo-safe empty, error, and retry states** | The grids have loading/empty support, but a failed API call should not look like an empty database. This is cheap insurance for a live demo. | Distinguish loading, no results, and service failure; provide Retry; retain current filters after retry; show a clear save error without discarding form data. | Small |
| 5 | Admin | **Reactivate users and groups** | Admins can deactivate users/groups, but the current user screen does not expose inactive-user recovery and the group dialog warns deactivation cannot be undone in the UI. Reversible administration is expected. | “Show inactive” toggle for users; Reactivate action for users and groups; confirmation and success toast; preserve prior group when safe or require reassignment. | Small |

## P1 — High-value pre-demo enhancements

| Rank | User | Function | Why it matters | Minimum useful scope | Relative effort |
|---:|---|---|---|---|---|
| 6 | Basic | **CSV export of the filtered list** | CRM users routinely take a working list into Excel or send it to stakeholders. It also creates a strong, simple demo moment. | Export the current filtered result for Contacts, Companies, and Deals; use friendly labels rather than UUIDs; include export timestamp and active filters in the filename or metadata. | Small |
| 7 | Basic | **My Work / follow-up panel** | The dashboard should answer “What do I need to do next?” Existing deal-counterparty next steps and dates can drive this without building a full notification system. | Dashboard card for overdue and upcoming next steps, ordered by due date; link each row to its source deal/contact; allow quick completion or date change only if already supported cleanly. | Medium |
| 8 | Basic | **Recent records and favorites/watchlist** | Demo navigation becomes faster and the CRM feels personalized. The company model already includes a watchlist concept. | Show five recently viewed records; allow company watchlist toggle; add a compact watched-companies dashboard card. | Small–Medium |
| 9 | Basic | **Clickable communication fields** | Basic users expect email addresses, phone numbers, websites, and LinkedIn URLs to act like links. | `mailto:`, `tel:`, external website, and LinkedIn links with safe URL handling and clear external-link behavior. | Small |
| 10 | Admin | **Reset a user password** | Creating a user without being able to help them regain access is an obvious administrative gap. | Admin-generated temporary password or reset link; force change at next login if the current auth model supports it; never reveal stored credentials. | Medium |
| 11 | Admin | **User search, filters, and clearer lifecycle status** | The user table is client-paginated and lacks practical filtering as the organization grows. | Search name/email; filter role/group/status; show last login if already recorded; prevent deactivating the current/last active admin. | Small–Medium |
| 12 | Admin | **Reference-data usage protection** | Reference data is already a strength. Showing where a value is used prevents confusing deactivation and demonstrates mature administration. | Display usage count; warn when deactivating an in-use value; keep historical records readable; allow reactivation. | Medium |

## P2 — Expected next capabilities

### Basic users

| Rank | Function | Recommendation |
|---:|---|---|
| 13 | **Duplicate detection and manual merge** | Warn on matching contact email and similar company name/domain during create. Defer full merge until ownership and relationship rules are defined. |
| 14 | **Saved views** | Let users save common filters such as “My open deals,” “Tier 1 investors,” or “No contact in 30 days.” |
| 15 | **Bulk edit / reassignment** | Start with owner and status reassignment for selected records; require confirmation and report partial failures. |
| 16 | **Import wizard** | CSV template, preview, validation errors, and dry run for contacts/companies. This is useful but not low-hanging because deduplication and rollback behavior must be defined. |
| 17 | **Visible activity timeline** | Consolidate calls, notes, emails, and changes on detail pages after the Call/Note and history roadmap phases are complete. |
| 18 | **Pipeline visual and stage aging** | Add a simple kanban or funnel backed by real data; do not demo analytics endpoints that remain stubs. |

### Administrators

| Rank | Function | Recommendation |
|---:|---|---|
| 19 | **Role/permission matrix** | Read-only page explaining what Regular User, Supervisor, Principal, and Admin can do; this is valuable even before editable permissions exist. |
| 20 | **Audit-history viewer and restore** | Continue the existing Phase 20 plan. Treat restore as a governed admin action with actor, timestamp, before/after view, and confirmation. |
| 21 | **Principal/admin reports** | Complete real pipeline-by-group and activity reports only after their underlying records and access enforcement are stable. |
| 22 | **Data retention and export controls** | Define organization export, retention, and deletion rules before production or external-client use. |

## P3 — Explicitly defer from the low-hanging-fruit demo tranche

- Full email/calendar synchronization.
- Real-time notifications and notification preferences.
- Automated email parsing or automatic counterparty-stage updates.
- AI-generated scoring or answers unless the output is backed by implemented endpoints and clearly labeled.
- Fine-grained field-level permissions.
- PostgreSQL row-level security migration.
- Multi-currency FX conversion.
- Investor portal, VDR/document distribution, cap table, waterfall, or fund-accounting functionality.

These may be valid roadmap items, but each materially expands integration, security, governance, or data-quality risk.

## Recommended pre-demo implementation cut

### Cut A — Minimum credible demo

- P0 items 1–5.
- Seed a coherent scenario with at least two user roles, several companies/contacts, and two deals at different stages.
- Verify all visible navigation destinations. Hide stub-only pages or mark them clearly as preview capabilities.
- Rehearse create → search → update → export → admin recovery as one end-to-end flow.

### Cut B — Stronger stakeholder demo

- Everything in Cut A.
- CSV export.
- My Work / next-step dashboard card.
- Clickable communication fields.
- Admin password reset if authentication behavior is stable enough to demonstrate safely.

## Suggested demo story

1. Sign in as a regular user and open **My Work**.
2. Search for an investor company and open its relationship record.
3. Create a new contact from the Contacts page and associate it with that company.
4. Open a live deal, update the investor’s next step or stage, and show the PE-specific counterparty workflow.
5. Filter the deal list to the presenter’s open deals and export the view.
6. Sign in as an administrator, add or update a user’s group/role, and demonstrate reversible deactivation.

This story emphasizes what differentiates Nexus—PE relationship and counterparty workflow—while demonstrating the basic completeness stakeholders expect from a CRM.

## Repository evidence behind the priorities

- The [README](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/README.md) documents the strong existing domain model and identifies unfinished analytics and v1.3 administration/history work.
- [ContactsPage.jsx](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/frontend/src/pages/ContactsPage.jsx), [CompaniesPage.jsx](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/frontend/src/pages/CompaniesPage.jsx), and [DealsPage.jsx](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/frontend/src/pages/DealsPage.jsx) confirm that the primary grids currently lack create controls, search, and export; Deals has only a status filter.
- [Layout.jsx](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/frontend/src/components/Layout.jsx) exposes Cmd/Ctrl+K, while [AIQueryBar.jsx](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/frontend/src/components/AIQueryBar.jsx) confirms that the visible AI interaction is still a placeholder.
- [AdminUsersPage.jsx](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/frontend/src/pages/AdminUsersPage.jsx) supports add, role/group edit, and deactivate, but not inactive-user discovery, reactivation, or password reset.
- [AdminGroupsPage.jsx](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/frontend/src/pages/AdminGroupsPage.jsx) supports create, rename, and deactivate; its confirmation text explicitly states that deactivation cannot be undone in the UI.
- The project’s [feature landscape](https://github.com/oscarmackjr-twg/Nexus-CRM/blob/main/.planning/research/FEATURES.md) correctly prioritizes the PE counterparty workflow and cautions against expanding into fund administration, VDR distribution, complex FX, and automated email parsing.

## Acceptance criteria for the demo tranche

- A basic user can create, find, open, and update each core record without using an API client or direct URL.
- Search/filter state produces consistent results across pagination and export.
- No visible control opens a placeholder-only experience during the rehearsed demo.
- Empty results, API failures, and validation failures are visibly distinct and recoverable.
- An admin can deactivate and reactivate a user/group and cannot accidentally remove the last active administrator.
- Role restrictions are enforced by the backend, not only hidden in the frontend.
- Seed data supports the complete rehearsed narrative without manual database edits.

