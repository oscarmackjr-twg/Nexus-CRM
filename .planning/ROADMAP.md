# Roadmap: Nexus CRM — PE Deal Management Platform

## Milestones

- ✅ **v1.0 PE CRM Foundation** — Phases 1-6 (shipped 2026-03-28) — [archive](.planning/milestones/v1.0-ROADMAP.md)
- 📋 **v1.1 UI Professionalism** — Phases 7-12 (in progress)
- 📋 **v1.2 Cloud Deployment** — Phases 13-16 (planned)

---

## Phases

<details>
<summary>✅ v1.0 PE CRM Foundation (Phases 1-6) — SHIPPED 2026-03-28</summary>

- [x] Phase 1: UI Polish (3/3 plans) — completed 2026-03-27
- [x] Phase 2: Reference Data System (3/3 plans) — completed 2026-03-27
- [x] Phase 3: Contact & Company Model Expansion (6/6 plans) — completed 2026-03-28
- [x] Phase 4: Deal Model Expansion & Fund Entity (4/4 plans) — completed 2026-03-28
- [x] Phase 5: DealCounterparty & DealFunding (4/4 plans) — completed 2026-03-28
- [x] Phase 6: Admin Reference Data UI (3/3 plans) — completed 2026-03-28

</details>

### v1.1 UI Professionalism

- [x] **Phase 7: Brand Foundation** — TWG color palette, Gotham font, CSS variable consolidation (completed 2026-03-29)
- [x] **Phase 8: Login, Banner & Sidebar** — branded login page, staging banner, white sidebar redesign (completed 2026-03-29)
- [ ] **Phase 9: Data Grids** — compact Salesforce-style list views for Contacts, Companies, Deals
- [ ] **Phase 10: Detail Page Polish** — section card headers, field layout, empty values, tab bar
- [ ] **Phase 11: Contact & Company Data Completeness** — API label resolution + detail/list UI for Contact and Company PE fields
- [ ] **Phase 12: Deal & Fund Data Completeness** — Deal detail/edit UI for all PE expansion fields, Fund selector on Deal form

### v1.2 Cloud Deployment

- [x] **Phase 13: AWS Core Infrastructure** — Terraform bootstrap, VPC, RDS, RDS Proxy, ElastiCache, ECR, Secrets Manager, IAM OIDC (completed 2026-03-30)
- [ ] **Phase 14: AWS Compute, CDN & HTTPS** — ECS Fargate cluster + task definitions, ALB, CloudFront + S3 frontend, ACM cert, Route 53 DNS
- [ ] **Phase 15: CI/CD Pipeline** — GitHub Actions build → migration → deploy pipeline, multi-environment support, entrypoint cleanup
- [ ] **Phase 16: Azure Warm Failover** — Azure PostgreSQL, ACR, ACI standby containers, pg_dump schedule, failover runbook

---

## Phase Details

### Phase 7: Brand Foundation
**Goal**: The TWG color palette and Montserrat font are live globally — all subsequent UI work builds on this baseline
**Depends on**: Nothing (first phase of v1.1)
**Requirements**: BRAND-01, BRAND-02, BRAND-03
**Success Criteria** (what must be TRUE):
  1. Every button, active indicator, and focus ring in the app shows `#1a3868` navy instead of indigo or purple
  2. Body text renders in Montserrat with system-ui fallback on all pages
  3. CSS variables `--color-brand`, `--color-brand-hover`, `--color-page-bg`, `--color-content-bg`, `--color-text` are defined and consumed throughout — no inline hex or one-off Tailwind color overrides
**Plans:** 1/1 plans complete
Plans:
- [x] 07-01-PLAN.md — Navy CSS variables + Montserrat font + POC tokens + indigo sweep
**UI hint**: yes

### Phase 8: Login, Banner & Sidebar
**Goal**: Users see a professional TWG-branded login screen and a white sidebar with navy indicators on every authenticated page
**Depends on**: Phase 7
**Requirements**: LOGIN-01, LOGIN-02, LOGIN-03, LOGIN-04, BANNER-01, NAV-01, NAV-02, NAV-03, NAV-04, NAV-05
**Success Criteria** (what must be TRUE):
  1. Login page shows TWG logo centered above the form, navy primary button, and the staging banner when not in production
  2. A backend health status indicator is visible on the login page ("Backend connected" or "Backend unreachable")
  3. The sidebar background is white with a right-border separator; the active nav item shows a navy `border-l-4` left bar, navy text, and `bg-gray-50` highlight
  4. Section group labels (DEALS, ADMIN) appear in uppercase muted tracking-widest text in the sidebar
  5. The sidebar footer shows the current user's name, role, and a Sign Out button in muted style
  6. The amber-400 staging banner appears at the top of every authenticated page (not just login) when not in production
**Plans:** 2/2 plans complete
Plans:
- [x] 08-01-PLAN.md — StagingBanner component, TWG logo asset, login page polish
- [x] 08-02-PLAN.md — White sidebar layout with nav groups, logo header, user footer
**UI hint**: yes

### Phase 9: Data Grids
**Goal**: Contacts, Companies, and Deals list views use compact Salesforce-style density with polished headers, hover states, and pagination
**Depends on**: Phase 7
**Requirements**: GRID-01, GRID-02, GRID-03, GRID-04, GRID-05, GRID-06
**Success Criteria** (what must be TRUE):
  1. All three list views (Contacts, Companies, Deals) use tight row padding (`py-2`) and `text-sm` throughout — visibly more compact than before
  2. Column headers are uppercase, `text-xs`, `text-gray-500`, `tracking-wide`, with a bottom border and sort indicator arrows
  3. Hovering a row highlights it with `bg-gray-50`; row action buttons (View/Edit) are only visible on hover
  4. The pagination bar shows page count, previous/next buttons, and a records-per-page selector in consistent TWG style
**Plans:** 2/3 plans executed
Plans:
- [x] 09-01-PLAN.md — Shared DataGrid + Pagination components + test infrastructure
- [x] 09-02-PLAN.md — ContactsPage + CompaniesPage list views + /contacts and /companies routes
- [ ] 09-03-PLAN.md — DealsPage list view + Deals sidebar nav link + /deals route
**UI hint**: yes

### Phase 10: Detail Page Polish
**Goal**: All detail pages have consistent section cards, field layout, empty value display, and navy tab indicators
**Depends on**: Phase 7
**Requirements**: DETAIL-01, DETAIL-02, DETAIL-03, DETAIL-04
**Success Criteria** (what must be TRUE):
  1. Every section card header across Contact, Company, and Deal detail pages shows a `font-semibold` title, optional right-aligned Edit button, and a `border-b` separator
  2. Field label/value pairs use a two-column grid — muted `text-xs uppercase` label on the left, normal value on the right, with consistent vertical spacing
  3. Fields with null or empty values display `—` (em dash) instead of blank space
  4. The tab bar on detail pages uses a navy underline for the active tab, with a clean bottom border
**Plans**: TBD
**UI hint**: yes

### Phase 11: Contact & Company Data Completeness
**Goal**: Contact and Company detail pages display all PE Blueprint fields with resolved label values in both list and detail views
**Depends on**: Phase 10
**Requirements**: CONTACT-08, CONTACT-09, CONTACT-10, COMPANY-10, COMPANY-11, COMPANY-12
**Success Criteria** (what must be TRUE):
  1. The Contact detail Profile tab shows all 20+ PE Blueprint fields (identity, employment, board memberships, investment preferences, internal coverage) with per-card editing
  2. The Contacts list view shows resolved label text (e.g., "LP" not a UUID) for contact_type and other ref_data columns
  3. The Company detail page displays all 33 PE Blueprint fields with per-card editing — financials, investment preferences, coverage person, and parent company all visible
  4. The Companies list view shows resolved label text for company_type, tier, and sector
  5. Both Contact and Company API responses include resolved label fields in list and detail endpoints (no raw UUIDs surfacing to the UI)
**Plans**: TBD
**UI hint**: yes

### Phase 12: Deal & Fund Data Completeness
**Goal**: The Deal detail page and edit form expose all PE expansion fields, and Fund can be selected when editing a deal
**Depends on**: Phase 11
**Requirements**: DEAL-11, DEAL-12, FUND-05
**Success Criteria** (what must be TRUE):
  1. The Deal detail Profile tab displays all 30+ PE expansion fields (financial metrics, date milestones, deal team, fund, source) with per-card editing
  2. The Deal edit form includes all PE expansion fields — financial metrics with currency selectors, all 8 date milestone pickers, deal team management
  3. The Fund dropdown is available and functional on the Deal edit form — a user can assign or change the fund associated with a deal
**Plans**: TBD
**UI hint**: yes

### Phase 13: AWS Core Infrastructure
**Goal**: All foundational AWS networking, data stores, secrets, and access control are provisioned via Terraform — compute and pipeline have everything they need to reference
**Depends on**: Nothing (first phase of v1.2; Terraform bootstrap is a prerequisite manual step within this phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-07, INFRA-09, INFRA-10
**Success Criteria** (what must be TRUE):
  1. `terraform apply` in `environments/staging/` and `environments/prod/` completes without error; state is stored in a versioned, KMS-encrypted S3 bucket with native lockfile — no DynamoDB table required
  2. VPC exists with public and private subnets across two AZs, a NAT gateway, and security groups that allow ALB → ECS and ECS → RDS/Redis traffic only (no ECS task has a public IP)
  3. RDS PostgreSQL instance is reachable from the private subnet using a custom parameter group with `rds.logical_replication = 1`, `idle_in_transaction_session_timeout = 30000`, and `wal_sender_timeout = 0` set at initial creation
  4. ElastiCache provisioned Redis replication group (not Serverless) is reachable from the ECS security group; Celery can connect and queue tasks
  5. ECR repositories exist for `api` and `worker` with immutable image tags and lifecycle policies; a test push with a SHA-tagged image succeeds and is visible in the ECR console
  6. AWS Secrets Manager secrets exist at `/nexus/staging/` and `/nexus/prod/` paths for `db_password`, `jwt_secret`, and `redis_url`; the GitHub Actions OIDC role can read them and has least-privilege ECS/ECR permissions
**Plans:** 3/3 plans complete
Plans:
- [x] 13-01-PLAN.md — Bootstrap config, environment directory structure, provider upgrade, delete flat root
- [x] 13-02-PLAN.md — Fix networking, RDS, ElastiCache, and Secrets modules
- [x] 13-03-PLAN.md — RDS Proxy module, IAM OIDC fix, environment wiring, ECR inline, entrypoint cleanup

### Phase 14: AWS Compute, CDN & HTTPS
**Goal**: The application is reachable over HTTPS at the production domain — ECS tasks run in private subnets, the React frontend is served from CloudFront/S3, and the ALB is the only public ingress
**Depends on**: Phase 13
**Requirements**: INFRA-05, INFRA-06, INFRA-08
**Success Criteria** (what must be TRUE):
  1. ECS Fargate cluster has running task definitions for the API service, Celery worker service, and a one-shot migration runner; all secrets are injected via the `secrets[]` block (not `environment[]`) — no credentials appear in CloudWatch logs or the console
  2. `GET https://crm.oscarmackjr.com/api/v1/health` returns HTTP 200 with DB connectivity confirmed; ALB health checks and ECS container health checks both pass
  3. The React SPA loads from the CloudFront URL; `/api/*` requests route through to the ALB; direct S3 access is blocked (origin access control enforced)
  4. ACM certificate is issued and attached to both the ALB HTTPS listener and the CloudFront distribution; all HTTP traffic redirects to HTTPS
  5. Route 53 A alias record for `crm.oscarmackjr.com` resolves to the CloudFront distribution; no browser certificate warning appears
  6. `lifecycle { ignore_changes = [task_definition] }` is set on all ECS service resources in Terraform — a `terraform apply` with no image changes does not trigger a rolling restart
**Plans:** 3 plans
Plans:
- [ ] 14-01-PLAN.md — ACM module (dual-region) + ALB module + environment wiring (provider alias, Route 53 data source)
- [ ] 14-02-PLAN.md — ECS module (cluster, 3 task defs, 2 services, log groups) + environment wiring + Phase 15 outputs
- [ ] 14-03-PLAN.md — CloudFront module (S3 + OAC + distribution + Route 53 alias) + IAM update + Phase 15 outputs

### Phase 15: CI/CD Pipeline
**Goal**: Every merge to `main` automatically builds, migrates, and deploys to staging; production deploys require a manual approval gate; the app never runs Alembic at container startup
**Depends on**: Phase 14
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05
**Success Criteria** (what must be TRUE):
  1. `entrypoint.sh` no longer calls `alembic upgrade head` — app containers start without running any migration; this change is committed before the first ECS deploy
  2. Merging a PR to `main` triggers the GitHub Actions pipeline: Docker images are built for `linux/amd64`, tagged with the Git commit SHA, and pushed to ECR; ECR tag immutability prevents overwriting existing tags
  3. The pipeline runs the Alembic migration as a one-shot ECS task (`run-task` with command override), polls `aws ecs wait tasks-stopped`, and asserts `exitCode == 0` before any service update proceeds; a failed migration aborts the deploy
  4. After a successful migration, ECS services are updated via rolling deployment with `minimum_healthy_percent = 100` and `maximum_percent = 200`; deployment circuit breaker is enabled with auto-rollback on failure
  5. Staging deploys automatically on every merge to `main`; production deploy is gated by a GitHub Environment protection rule requiring manual approval; both environments use separate Terraform state files and separate Secrets Manager paths
**Plans**: TBD

### Phase 16: Azure Warm Failover
**Goal**: A warm Azure failover environment is pre-deployed and idle — Azure PostgreSQL has a current copy of the data, ACI containers exist but receive no traffic, and a tested runbook enables manual cutover within 30 minutes
**Depends on**: Phase 13 (RDS endpoint as replication source), Phase 15 (ECR image URIs to mirror via CI)
**Requirements**: FAILOVER-01, FAILOVER-02, FAILOVER-03, FAILOVER-04, FAILOVER-05
**Success Criteria** (what must be TRUE):
  1. Azure PostgreSQL Flexible Server is provisioned via Terraform with `pg_failover_slots` extension enabled and configured before any replication subscription is created; logical replication slot survives an Azure Flexible Server HA failover test
  2. GitHub Actions pipeline mirrors every ECR image push to ACR in the same workflow run; ACI container definitions reference ACR images and exist in stopped/idle state — no traffic reaches them during normal operation
  3. The Azure PostgreSQL schema matches RDS (applied via pg_dump --schema-only after each Alembic migration); scheduled pg_dump/restore job runs on a 4-hour cadence with confirmed successful restores, providing documented 4-hour RPO
  4. Azure Key Vault contains mirrored secrets including the identical JWT secret from AWS Secrets Manager; ACI containers can start and accept existing user sessions without requiring re-login
  5. Failover runbook is documented and has been executed once against the staging environment — an operator can follow it to stop AWS writes, confirm restore is current, start ACI containers, and update DNS to the Azure endpoint within 30 minutes
**Plans**: TBD

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. UI Polish | v1.0 | 3/3 | Complete | 2026-03-27 |
| 2. Reference Data System | v1.0 | 3/3 | Complete | 2026-03-27 |
| 3. Contact & Company Model Expansion | v1.0 | 6/6 | Complete | 2026-03-28 |
| 4. Deal Model Expansion & Fund Entity | v1.0 | 4/4 | Complete | 2026-03-28 |
| 5. DealCounterparty & DealFunding | v1.0 | 4/4 | Complete | 2026-03-28 |
| 6. Admin Reference Data UI | v1.0 | 3/3 | Complete | 2026-03-28 |
| 7. Brand Foundation | v1.1 | 1/1 | Complete   | 2026-03-29 |
| 8. Login, Banner & Sidebar | v1.1 | 2/2 | Complete   | 2026-03-29 |
| 9. Data Grids | v1.1 | 2/3 | In Progress|  |
| 10. Detail Page Polish | v1.1 | 0/? | Not started | - |
| 11. Contact & Company Data Completeness | v1.1 | 0/? | Not started | - |
| 12. Deal & Fund Data Completeness | v1.1 | 0/? | Not started | - |
| 13. AWS Core Infrastructure | v1.2 | 3/3 | Complete    | 2026-03-30 |
| 14. AWS Compute, CDN & HTTPS | v1.2 | 0/3 | Not started | - |
| 15. CI/CD Pipeline | v1.2 | 0/? | Not started | - |
| 16. Azure Warm Failover | v1.2 | 0/? | Not started | - |
