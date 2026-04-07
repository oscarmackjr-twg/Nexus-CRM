# Requirements: Nexus CRM — All Milestones

---

## v1.1 UI Professionalism (Phases 7-12)

**Defined:** 2026-03-28 | **Status:** In Progress

### Branding & Theme

- [x] **BRAND-01**: TWG `#1a3868` navy replaces indigo/purple as the primary brand color throughout (CSS variables and Tailwind config updated)
- [x] **BRAND-02**: Gotham font applied as body font with system-ui fallback via CSS `@font-face` or font-family declaration
- [x] **BRAND-03**: CSS variables consolidated to match POC pattern: `--color-brand`, `--color-brand-hover`, `--color-page-bg`, `--color-content-bg`, `--color-text`

### Login Page

- [x] **LOGIN-01**: TWG logo (`twg-logo.png`) displayed centered above the login form
- [x] **LOGIN-02**: Staging banner displayed on login page when `VITE_APP_ENV !== 'production'` (amber-400, sticky top)
- [x] **LOGIN-03**: Backend health status indicator shown on login page ("Backend connected" / "Backend unreachable")
- [x] **LOGIN-04**: Login page button and focus rings use `#1a3868` navy primary color

### Staging Banner

- [x] **BANNER-01**: Amber-400 staging banner appears at top of every authenticated page when not in production (sticky, z-50)

### Navigation & Sidebar

- [x] **NAV-01**: Sidebar background is white with a right-side border separator
- [x] **NAV-02**: Active nav item shows navy `border-l-4` left indicator, navy text, and `bg-gray-50` highlight
- [x] **NAV-03**: Nav section group labels (DEALS, ADMIN) in uppercase muted tracking-widest text
- [x] **NAV-04**: Sidebar header displays TWG logo
- [x] **NAV-05**: Sidebar footer displays current user name, role, and Sign Out button in muted style

### Data Grids

- [x] **GRID-01**: Contacts list view uses compact row density (`py-2`, `text-sm`)
- [x] **GRID-02**: Companies list view uses compact row density (`py-2`, `text-sm`)
- [x] **GRID-03**: Deals list view uses compact row density (`py-2`, `text-sm`)
- [x] **GRID-04**: Column headers are uppercase, `text-xs`, `text-gray-500`, `tracking-wide`, with bottom border and sort indicators
- [x] **GRID-05**: Row hover highlights with `bg-gray-50`; row action buttons visible on hover only
- [x] **GRID-06**: Pagination bar shows page count, prev/next buttons, records-per-page selector in TWG style

### Detail Page Polish

- [x] **DETAIL-01**: Every section card header has `font-semibold` title, optional Edit button, and `border-b` separator
- [x] **DETAIL-02**: Field label/value pairs use two-column grid — muted `text-xs uppercase` label, normal value, consistent vertical spacing
- [x] **DETAIL-03**: Null/empty field values display `—` (em dash) instead of blank
- [x] **DETAIL-04**: Detail page tab bar uses navy underline for active tab with clean bottom border

### Contact & Company Data Completeness

- [ ] **CONTACT-08**: Contact detail Profile tab shows all 20+ PE Blueprint fields with per-card editing
- [ ] **CONTACT-09**: Contacts list view shows resolved label text for ref_data columns (e.g. "LP" not UUID)
- [ ] **CONTACT-10**: Contact API returns resolved label fields in both list and detail endpoints
- [ ] **COMPANY-10**: Company detail page shows all 33 PE Blueprint fields with per-card editing
- [ ] **COMPANY-11**: Companies list view shows resolved label text for company_type, tier, and sector
- [ ] **COMPANY-12**: Company API returns resolved label fields in both list and detail endpoints

### Deal & Fund Data Completeness

- [ ] **DEAL-11**: Deal detail Profile tab shows all 30+ PE expansion fields with per-card editing
- [ ] **DEAL-12**: Deal edit form includes all PE expansion fields with currency selectors and date pickers
- [ ] **FUND-05**: Fund dropdown is functional on the Deal edit form — user can assign or change a fund

---

## v1.2 Cloud Deployment (Phases 13-16)

**Defined:** 2026-03-29 | **Status:** Active

### AWS Infrastructure

- [x] **INFRA-01**: VPC provisioned via Terraform with public/private subnets, NAT gateway, and security groups for all services
- [x] **INFRA-02**: RDS PostgreSQL (Flexible / Multi-AZ capable) provisioned with parameter group configured for logical replication readiness
- [x] **INFRA-03**: RDS Proxy provisioned alongside RDS for connection pooling — ECS services connect via Proxy endpoint, not RDS directly
- [x] **INFRA-04**: ECR repositories created with immutable tags and lifecycle policies (one repo per service: api and worker (frontend is served from S3+CloudFront, not a container))
- [ ] **INFRA-05**: ALB with HTTPS listener, ACM certificate (DNS validation), and Route 53 A-record alias pointing to ALB
- [ ] **INFRA-06**: CloudFront distribution backed by S3 bucket serving the Vite-built React frontend; `/api/*` path behavior routes to ALB
- [x] **INFRA-07**: AWS Secrets Manager secrets created for all runtime secrets (DB password, JWT secret, Redis URL) with staging/prod path separation (`/nexus/staging/` vs `/nexus/prod/`)
- [ ] **INFRA-08**: ECS Fargate cluster with task definitions for API service, Celery worker service, and one-shot migration runner task; all secrets injected via `secrets[]` block (not `environment[]`)
- [x] **INFRA-09**: ElastiCache Redis provisioned cluster (not Serverless) — required broker for Celery worker
- [x] **INFRA-10**: IAM OIDC provider and GitHub Actions deployment role with least-privilege ECS/ECR/Secrets permissions; `lifecycle { ignore_changes = [task_definition] }` on ECS services

### CI/CD Pipeline

- [ ] **DEPLOY-01**: GitHub Actions workflow builds Docker images on merge to `main`, tags with commit SHA, pushes to ECR
- [ ] **DEPLOY-02**: Pipeline runs Alembic migration as one-shot ECS task (`run-task` with command override); polls `aws ecs wait tasks-stopped` and asserts `exitCode == 0` before proceeding
- [ ] **DEPLOY-03**: ECS services updated via rolling deployment (zero-downtime) after successful migration step
- [ ] **DEPLOY-04**: Multi-environment support — staging and prod have separate Terraform state files, separate ECS clusters, and separate Secrets Manager paths; prod deploy requires manual approval gate
- [ ] **DEPLOY-05**: `entrypoint.sh` Alembic call removed — app containers must not run migrations at startup (migration is pipeline-only)

### Azure Warm Failover

- [ ] **FAILOVER-01**: Azure PostgreSQL Flexible Server provisioned via Terraform; `pg_failover_slots` extension enabled before replication begins
- [ ] **FAILOVER-02**: Azure Container Registry provisioned; GitHub Actions pipeline mirrors ECR images to ACR on every build
- [ ] **FAILOVER-03**: Azure Container Instances (API + worker) pre-deployed via Terraform in stopped state — containers exist but receive zero traffic
- [ ] **FAILOVER-04**: Scheduled pg_dump job runs on AWS (Lambda or ECS task), ships dump to Azure Blob Storage, and restores to Azure PostgreSQL on a 4-hour schedule (4h RPO)
- [ ] **FAILOVER-05**: Failover runbook documented — step-by-step operator procedure: stop AWS writes → confirm restore current → start ACI containers → update DNS to Azure ALB

---

## Future Requirements

- ElastiCache Serverless (currently broken with Celery 5.3+ — revisit when fixed upstream)
- Near-real-time pglogical replication if RPO < 4h is required
- Automated Route 53 failover routing (health-check-based DNS failover to Azure)
- Blue/green ECS deployments (AWS native blue/green GA'd July 2025 — upgrade path when needed)
- Azure VPN / private connectivity between AWS and Azure (required if public RDS endpoint is not acceptable)

## Out of Scope (v1.2)

- Kubernetes (EKS/AKS) — ACI + ECS Fargate is the right tier for this app size
- DMS continuous replication — pg_dump at 4h RPO is the chosen approach
- Automated failover — warm failover is manual cutover per operator runbook
- Multi-region AWS — single region primary with cross-cloud failover is the architecture
- Monitoring / alerting stack (CloudWatch alarms, PagerDuty) — deferred to v1.3

---

## Traceability

| REQ-ID | Phase | Plan |
|--------|-------|------|
| BRAND-01 to BRAND-03 | Phase 7 | 07-01 |
| LOGIN-01 to LOGIN-04 | Phase 8 | 08-01 |
| BANNER-01 | Phase 8 | 08-01 |
| NAV-01 to NAV-05 | Phase 8 | 08-02 |
| GRID-01 to GRID-06 | Phase 9 | 09-01, 09-02, 09-03 |
| DETAIL-01 to DETAIL-04 | Phase 10 | TBD |
| CONTACT-08 to CONTACT-10 | Phase 11 | TBD |
| COMPANY-10 to COMPANY-12 | Phase 11 | TBD |
| DEAL-11 to DEAL-12 | Phase 12 | TBD |
| FUND-05 | Phase 12 | TBD |
| INFRA-01 | Phase 13 | 13-01, 13-02 |
| INFRA-02 | Phase 13 | 13-01, 13-02 |
| INFRA-03 | Phase 13 | 13-03 |
| INFRA-04 | Phase 13 | 13-03 |
| INFRA-07 | Phase 13 | 13-02 |
| INFRA-09 | Phase 13 | 13-02 |
| INFRA-10 | Phase 13 | 13-03 |
| INFRA-05 | Phase 14 | TBD |
| INFRA-06 | Phase 14 | TBD |
| INFRA-08 | Phase 14 | TBD |
| DEPLOY-01 | Phase 15 | TBD |
| DEPLOY-02 | Phase 15 | TBD |
| DEPLOY-03 | Phase 15 | TBD |
| DEPLOY-04 | Phase 15 | TBD |
| DEPLOY-05 | Phase 13 (precondition), Phase 15 | 13-03 (entrypoint fix) |
| FAILOVER-01 | Phase 16 | TBD |
| FAILOVER-02 | Phase 16 | TBD |
| FAILOVER-03 | Phase 16 | TBD |
| FAILOVER-04 | Phase 16 | TBD |
| FAILOVER-05 | Phase 16 | TBD |

---

## v1.3 Access Control & Audit Trails

**Defined:** 2026-04-06 | **Status:** In Progress

### Groups & Role Model

- [ ] **GROUP-01**: Admin can create, rename, and deactivate groups
- [ ] **GROUP-02**: Admin can assign any user to exactly one group (moving a user to a new group removes them from their current group)
- [ ] **GROUP-03**: Admin can grant a user the Supervisor role within their group
- [ ] **GROUP-04**: Admin can grant a user the Principal role (cross-group visibility and reports access)
- [ ] **GROUP-05**: Admin can grant a user the Admin role (user & group management capability)
- [ ] **GROUP-06**: A user's effective role (Regular User / Supervisor / Principal / Admin) is visible in their profile and in the admin user list

### Access Control

- [ ] **ACCESS-01**: Contacts and Companies are readable by all authenticated users regardless of group
- [ ] **ACCESS-02**: Calls, Notes, and Deals are readable only by members of the same group, Supervisors of that group, Principals, and Admins
- [ ] **ACCESS-03**: A Regular User can create, edit, and delete their own Calls, Notes, and Deals
- [ ] **ACCESS-04**: A Supervisor can read and edit (but not delete) any Call, Note, or Deal belonging to members of their group
- [ ] **ACCESS-05**: A Principal can read all Calls, Notes, and Deals across all groups
- [ ] **ACCESS-06**: An Admin has full CRUD access to all objects across all groups
- [ ] **ACCESS-07**: API endpoints enforce group-scoping — requests for out-of-scope records return 403, not 404

### Call Entity

- [ ] **CALL-01**: User can create a Call record linked to a Contact and/or Company, with date, duration, direction (inbound/outbound), and notes fields
- [ ] **CALL-02**: User can edit and delete their own Call records
- [ ] **CALL-03**: Calls list view shows all calls visible to the current user (group-scoped), sortable by date
- [ ] **CALL-04**: Call detail view shows all fields including created_by, created_at, updated_by, updated_at

### Note Entity

- [ ] **NOTE-01**: User can create a Note linked to a Contact, Company, and/or Deal, with a title and body
- [ ] **NOTE-02**: User can edit and delete their own Note records
- [ ] **NOTE-03**: Notes list view shows all notes visible to the current user (group-scoped), sortable by date
- [ ] **NOTE-04**: Note detail view shows all fields including created_by, created_at, updated_by, updated_at

### Authorship Tracking

- [ ] **AUDIT-01**: All objects (Contact, Company, Deal, Call, Note, Fund, DealCounterparty, DealFunding) store `created_by` (user FK) and `created_at` (timestamp) — set on insert, never updated
- [ ] **AUDIT-02**: All objects store `updated_by` (user FK) and `updated_at` (timestamp) — updated on every write
- [ ] **AUDIT-03**: Detail views for all objects display created by / created date and last modified by / modified date

### Modification History

- [ ] **HIST-01**: Every write to a major entity (Contact, Company, Deal, Call, Note) appends a snapshot row to a corresponding `_history` table capturing the full object state, user, and timestamp
- [ ] **HIST-02**: Admin can view the change history for any individual record — who changed it, when, and what the previous values were
- [ ] **HIST-03**: Admin can restore a record to any prior version from the history view
- [ ] **HIST-04**: History entries are immutable — no user can delete or alter them

### Principal Reports

- [ ] **REPORT-01**: Principal can view an Activity by Group report — count of Calls and Notes logged per group over a selected date range, with drill-down to individual records
- [ ] **REPORT-02**: Principal can view a Deal Pipeline by Group report — deal count by stage, total deal value, and win/loss counts per group
- [ ] **REPORT-03**: Principal can view a User Activity report — per-user count of Calls logged, Notes written, and Deals touched over a selected date range

### Admin UI

- [ ] **ADMIN-10**: Admin has a User Management screen: list all users, see their group and role, add new users, edit role/group assignment
- [ ] **ADMIN-11**: Admin has a Group Management screen: list all groups with member count, create group, rename group, view and change members

## Out of Scope (v1.3)

- Row-level security at database layer (PostgreSQL RLS) — access enforced in application service layer
- Field-level encryption for audit history — data stored plaintext in history tables
- Real-time notifications for permission changes — applied on next request
- Audit log for Contacts and Companies (group-scoped entities only get history; global entities get authorship fields but not full history by default)
- Fine-grained field-level permissions — role-based object-level access only
