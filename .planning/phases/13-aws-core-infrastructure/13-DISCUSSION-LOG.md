# Phase 13: AWS Core Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 13-aws-core-infrastructure
**Areas discussed:** Terraform structure

---

## Terraform Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Refactor to environments/ dirs | Move to environments/staging/ and environments/prod/ — each has its own main.tf, backend config, and tfvars. Shared logic in terraform/modules/. Matches requirements exactly. | ✓ |
| Keep flat + use tfvars | Keep terraform/ flat, use -var-file=staging.tfvars vs prod.tfvars. Simpler but doesn't match DEPLOY-04. | |
| Root module + symlinks | One root main.tf symlinked from environment dirs containing only backend configs and tfvars. | |

**User's choice:** Refactor to environments/ dirs

---

| Option | Description | Selected |
|--------|-------------|----------|
| terraform/modules/ (stay put) | environments/staging/main.tf calls module "vpc" { source = "../../modules/networking" }. Modules don't move. | ✓ |
| Move modules up to root | Root-level modules/ directory at same level as environments/. | |

**User's choice:** terraform/modules/ stays put — no relocation

---

| Option | Description | Selected |
|--------|-------------|----------|
| Replace with environments/ | Delete flat root wiring files once environments/ are in place. Clean break. | ✓ |
| Keep as reference | Leave old flat files as fallback. Risk: two competing entry points. | |

**User's choice:** Replace (delete) the flat files once environments/ structure is live

---

## Claude's Discretion

- State backend bootstrap approach
- Secret values strategy (shell resources vs storing in tfstate)
- Module approach (extend custom modules vs community modules)
- Provider/Terraform version upgrade
- entrypoint.sh Alembic removal

## Deferred Ideas

None.
