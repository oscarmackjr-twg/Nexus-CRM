---
phase: 13-aws-core-infrastructure
plan: 02
subsystem: infra
tags: [terraform, aws, networking, rds, elasticache, secrets, iac]

# Dependency graph
requires: ["13-01"]
provides:
  - "terraform/modules/networking/ with RDS Proxy SG and configurable NAT gateway count"
  - "terraform/modules/rds/ with PostgreSQL 17 and custom parameter group (logical replication)"
  - "terraform/modules/elasticache/ with Redis replication group with encryption"
  - "terraform/modules/secrets/ with shell-resource pattern at /nexus/{env}/ paths"
affects: [13-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RDS Proxy SG pattern: proxy SG mediates between ECS SGs and RDS SG (no direct ECS→RDS connectivity)"
    - "NAT gateway modulo: count.index % var.nat_gateway_count allows 2 subnets with 1 NAT gateway"
    - "Shell-resource pattern: Secrets Manager secrets created without values — populated out-of-band via CLI"
    - "ElastiCache replication group: required for Redis HA, encryption, and multi-AZ"

key-files:
  created: []
  modified:
    - terraform/modules/networking/main.tf
    - terraform/modules/networking/variables.tf
    - terraform/modules/networking/outputs.tf
    - terraform/modules/rds/main.tf
    - terraform/modules/rds/outputs.tf
    - terraform/modules/elasticache/main.tf
    - terraform/modules/elasticache/variables.tf
    - terraform/modules/elasticache/outputs.tf
    - terraform/modules/secrets/main.tf
    - terraform/modules/secrets/variables.tf
    - terraform/modules/secrets/outputs.tf

key-decisions:
  - "RDS SG ingress from rds_proxy SG only (not directly from api/worker) — enforces all DB connections go through RDS Proxy"
  - "NAT gateway modulo pattern: count.index % nat_gateway_count — staging uses 1 NAT, prod uses 2 NATs, private route tables always have 2 entries"
  - "ElastiCache engine_version 7.1 (not 7.0) with parameter_group_name default.redis7 — matches replication group API requirements"
  - "Secrets shell-resource pattern: no aws_secretsmanager_secret_version resources — secret values populated via aws CLI post-apply"
  - "Secret paths changed from /${app_name}/${env}/ to /nexus/${env}/ — shorter canonical path used by ECS task definitions and RDS Proxy"

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 13 Plan 02: Fix Terraform Modules Summary

**Four Terraform modules updated with RDS Proxy SG, configurable NAT count, PG17 parameter group, ElastiCache replication group with encryption, and secrets shell-resource pattern at /nexus/{env}/ paths**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-30T02:10:24Z
- **Completed:** 2026-03-30T02:13:00Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Networking module gains RDS Proxy security group (ingress 5432 from api+worker, egress 5432 to rds) and configurable `nat_gateway_count` variable with modulo routing for 2 subnets across N NATs
- RDS SG ingress now accepts only from rds_proxy SG — no direct ECS-to-RDS connectivity
- RDS module upgraded to PostgreSQL 17 with custom parameter group enabling logical replication (required for read replicas and DMS)
- ElastiCache module migrated from `aws_elasticache_cluster` to `aws_elasticache_replication_group` with at-rest and in-transit encryption, engine 7.1
- Secrets module migrated from full-resource (stores plaintext in state) to shell-resource pattern — values populated out-of-band
- Secret paths corrected from `/${app_name}/${env}/` to `/nexus/${env}/`
- Individual ARN outputs added: `db_password_secret_arn`, `jwt_secret_arn`, `redis_url_secret_arn`, `database_url_secret_arn`

## Task Commits

1. **Task 1: Fix networking and RDS modules** - `3e26c47` (feat)
2. **Task 2: Fix ElastiCache and Secrets modules** - `0ee16c4` (feat)

## Files Modified

- `terraform/modules/networking/main.tf` - Add rds_proxy SG, update RDS SG ingress, configurable NAT count with modulo route tables
- `terraform/modules/networking/variables.tf` - Add nat_gateway_count variable (default 2)
- `terraform/modules/networking/outputs.tf` - Add rds_proxy_security_group_id output
- `terraform/modules/rds/main.tf` - Add aws_db_parameter_group (postgres17 family), upgrade engine_version to 17, add parameter_group_name
- `terraform/modules/rds/outputs.tf` - Add db_instance_identifier output
- `terraform/modules/elasticache/main.tf` - Replace aws_elasticache_cluster with aws_elasticache_replication_group (encryption, engine 7.1, lifecycle)
- `terraform/modules/elasticache/variables.tf` - Add num_cache_clusters variable (default 1)
- `terraform/modules/elasticache/outputs.tf` - Switch to primary_endpoint_address, add replication_group_id
- `terraform/modules/secrets/main.tf` - Shell-resource pattern, /nexus/{env}/ paths, no aws_secretsmanager_secret_version
- `terraform/modules/secrets/variables.tf` - Remove all sensitive value variables, keep only app_name, environment, recovery_window_in_days
- `terraform/modules/secrets/outputs.tf` - Add secret_arns map and individual ARN outputs

## Decisions Made

- RDS SG now accepts traffic from rds_proxy SG only — forces all application DB traffic through RDS Proxy for connection pooling and failover
- NAT count modulo pattern: 2 private subnets always get route tables, but each route table's NAT gateway wraps via `count.index % var.nat_gateway_count` — allows staging with 1 NAT and prod with 2 NATs without changing subnet count
- ElastiCache `engine_version = "7.1"` with `parameter_group_name = "default.redis7"` — required by the replication group API
- `automatic_failover_enabled` and `multi_az_enabled` are computed as `var.num_cache_clusters >= 2` — single node staging doesn't need failover, multi-node prod does
- Secret paths use `/nexus/` prefix (not `/nexus-crm/` or `/${var.app_name}/`) per plan specification — shorter canonical path

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all module files are complete and ready for wiring in environment main.tf (Plan 03).

## Self-Check: PASSED

Files exist:
- terraform/modules/networking/main.tf: FOUND
- terraform/modules/rds/main.tf: FOUND
- terraform/modules/elasticache/main.tf: FOUND
- terraform/modules/secrets/main.tf: FOUND

Commits exist:
- 3e26c47: FOUND
- 0ee16c4: FOUND
