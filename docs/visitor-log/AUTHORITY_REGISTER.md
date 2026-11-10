# Visitor Log and Adobe Acrobat Sign Authority Register

**Initiative:** Nexus Visitor Log with Adobe Acrobat Sign  
**Gate:** GATE-01 Authority  
**Status:** BLOCKED — decisions awaiting authorized approvers  
**Source specification:** NEXUS-VISITOR-DF-SPEC-001, version 0.9.0-candidate  
**Last reviewed:** 2026-09-03

## Purpose and reader

This register is for the product owner, Legal/Records, Privacy, Security, and the sister-company operations owner. Its post-read action is to make and record the approvals that allow the initiative to move from authority work to architecture work. It is not approval to configure Adobe Acrobat Sign, create agreements, collect visitor data, or begin implementation.

## Gate boundary

No production-oriented code, Adobe credentials, external Adobe agreement, webhook registration, visitor data collection, or retention purge may be created while any mandatory decision below remains unapproved. A missing or conflicting decision is a stop condition.

The order of authority is: the approved visitor-log specification; approved sister-company visitor, NDA, privacy, retention, and records policies; Nexus security, tenancy, authentication, and audit contracts; Adobe Acrobat Sign documentation and account configuration; then existing product behavior.

## Required decisions

| ID | Decision owner(s) | Decision to record | Current status | Required approval evidence |
|---|---|---|---|---|
| VIS-GOV-001 | Legal/Records owner; product owner | Approve the NDA legal text, the authoritative template version, and the accountable template owner. | PENDING | Legal approval reference; template identifier and version; named owner; effective date. |
| VIS-GOV-002 | Legal/Records owner; Privacy; sister-company operations owner | Define when an NDA is required and every permitted exemption, including who may grant each exemption. | PENDING | Approved policy reference; rule matrix by organization, location, visitor type, and visit context; exemption authority and audit requirement. |
| VIS-GOV-003 | Legal/Records owner; Privacy; Security | Set retention periods for visitor records, signed NDAs, audit trails, and operational/audit logs; define legal holds and destruction authorization. | PENDING | Approved retention schedule; legal-hold process; destruction authorization; archive recovery and access constraints. |
| VIS-GOV-004 | Security; Legal/Records owner; sister-company operations owner | Define which roles may search, view, download, export, or administer signed NDA archives. | PENDING | Approved role-to-action matrix; least-privilege rationale; access review cadence; export and audit requirements. |

The candidate behaviors in the source specification are prompts for the approvers, not decisions: versioned Adobe library documents, NDA required by default with policy-based exemptions, non-destructive retention until approved, and archive access limited to authorized roles.

## Approval record

For each decision, append one approval entry containing:

- Decision ID and final decision text.
- Approver name, role, and approving organization.
- Date and durable policy, ticket, or signed-record reference.
- Effective date, review date, and superseded decision reference when applicable.
- Any scope limits, exceptions, or required controls.

Do not record NDA contents, visitor PII, credentials, Adobe tokens, signing URLs, or signed-document bytes in this register.

## Gate completion criteria

GATE-01 is complete only when all four decisions are approved and their evidence is recorded above. The product owner and Security must confirm that the decisions do not conflict with Nexus organization isolation, authorization, audit, or privacy controls.

Once complete, the next permitted gate is GATE-02 Architecture: document the domain model, state machines, API boundaries, Adobe integration boundary, QR security controls, archive/retention design, and threat model. Adobe configuration and integration remain prohibited until their relevant contracts are reviewed and explicitly authorized.

## Decision log

No approvals have been recorded.
