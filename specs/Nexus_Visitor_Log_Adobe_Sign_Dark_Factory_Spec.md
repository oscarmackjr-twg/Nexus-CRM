# Nexus Visitor Log with Adobe Acrobat Sign

## Dark Factory Functional, Security, Integration, and Test Specification

**Document ID:** `NEXUS-VISITOR-DF-SPEC-001`  
**Version:** `0.9.0-candidate`  
**Status:** `CANDIDATE_FOR_HUMAN_REVIEW`  
**Prepared:** 2026-09-03  
**Target platform:** Nexus CRM  
**Target organization:** Sister company configured as a separate Nexus organization  
**Signature provider:** Adobe Acrobat Sign REST API v6  
**Signature assurance:** Standard Adobe electronic signature  
**Visitor journeys:** Scheduled and walk-in visitors

---

## 1. Executive summary

The Visitor Log function will allow a sister company to preregister scheduled visitors or register walk-in visitors, require an NDA when policy dictates, present the NDA on the visitor's mobile device through a short-lived QR-code journey, obtain a standard electronic signature through Adobe Acrobat Sign, and archive the completed NDA and audit trail in Nexus.

The sister company is isolated as its own Nexus organization. Every visitor, visit, NDA template, Adobe agreement reference, QR session, archive object, administrative action, and audit event is organization-bound. Nexus is the operational system of record for the visit and archive index; Adobe Acrobat Sign is the authority for the signing ceremony, agreement status, signed PDF, and Adobe audit trail.

The function must fail closed. A visitor whose required NDA is not confirmed complete may not be checked in. A redirect from the signing page is not proof of signature. Only a verified Adobe API status or authenticated webhook followed by server-side reconciliation may satisfy the NDA gate.

---

## 2. Dark Factory operating principles

Delivery must follow this sequence:

1. Authority and policy decisions
2. Domain and state-machine specification
3. API and integration contracts
4. Security and privacy controls
5. Test contracts and fixtures
6. Tests-first implementation
7. Minimal production code
8. Reproducible validation and evidence
9. Human acceptance and production authorization

No UI demonstration, successful Adobe redirect, manually downloaded PDF, or passing happy-path test is sufficient by itself. Completion requires traceability from every requirement to implementation and automated evidence.

---

## 3. Authority and precedence

When sources conflict, use this precedence:

1. Approved version of this specification
2. Approved sister-company visitor, NDA, privacy, retention, and records policies
3. Current Nexus security, tenancy, authentication, and audit contracts
4. Adobe Acrobat Sign REST API v6 and account configuration
5. Existing implementation behavior

An unresolved conflict is a stop condition. Codex must not invent legal language, retention duration, signer assurance, tenant-sharing rules, or check-in authorization.

### 3.1 Human decisions required before production activation

| Decision ID | Required decision | Candidate behavior | Production gate |
|---|---|---|---|
| `VIS-GOV-001` | Approved NDA legal text and template owner | Versioned Adobe library document controlled by Legal/Admin | Mandatory |
| `VIS-GOV-002` | NDA applicability policy | Required by default, with documented policy-based exemption | Mandatory |
| `VIS-GOV-003` | Visitor and signed-NDA retention periods | Organization-configurable; no destructive purge until approved | Mandatory |
| `VIS-GOV-004` | Authorized archive viewers | Security/Legal/Admin plus explicitly authorized reception roles | Mandatory |
| `VIS-GOV-005` | Host notification channels | In-app initially; email/SMS integrations remain out of scope unless approved | Before notification activation |
| `VIS-GOV-006` | Whether visitor photographs, government IDs, or badge-system integration are allowed | Not collected in the initial release | Required before scope expansion |

---

## 4. Scope

### 4.1 Included

- Separate-organization configuration for the sister company.
- Scheduled visitor preregistration.
- Walk-in visitor registration by authorized reception staff.
- Visitor lookup and repeat-visitor assistance within the same organization.
- Host selection from active organization users.
- Visit purpose, company, arrival, check-in, check-out, and disposition tracking.
- Organization-controlled NDA applicability.
- Versioned NDA template selection.
- Visitor-specific, expiring QR session.
- Mobile NDA review and Adobe standard electronic signature.
- Adobe agreement lifecycle synchronization through webhooks plus reconciliation.
- Check-in gate based on verified NDA state.
- Retrieval and archival of the signed PDF and Adobe audit trail.
- Authorized archive search, view, and download.
- Operational and security audit events.
- Configurable retention metadata and policy-ready purge workflow.
- Accessibility, mobile usability, resilience, and observability requirements.

### 4.2 Excluded from the first release

- SMS, knowledge-based, government-ID, biometric, or enhanced Adobe identity verification.
- Visitor photographs or identity-document capture.
- Physical access-control, turnstile, printer, or badge-system integration.
- Facial recognition.
- Background checks or sanctions screening.
- Email/calendar synchronization.
- SMS messaging.
- Legal drafting or automated modification of NDA text.
- Visitor self-service creation without a scheduled invitation or reception-created walk-in record.
- Cross-organization visitor or document search.
- Public or permanent links to signed NDAs.
- Adobe credentials stored in frontend code, QR codes, logs, or browser storage.
- Production deployment or historical-data migration under this specification alone.

---

## 5. Actors and permissions

| Actor | Capabilities | Prohibited behavior |
|---|---|---|
| Visitor | Open assigned mobile session, review NDA, enter/confirm permitted fields, sign in Adobe, view completion result | Search Nexus, view other visitors, reuse another visit's token, download archive unless separately authorized |
| Host | Preregister visitors, view visits where they are the host, see readiness/check-in status | View unrelated NDA contents by default, override a required NDA, administer templates |
| Reception | Create scheduled/walk-in visits, issue/reissue QR sessions, verify status, check in/out, correct permitted visit data | Mark an NDA signed manually, access other organizations, change legal templates |
| Visitor Administrator | Configure locations, visitor types, applicability rules, reception permissions, operational reports | Edit signed documents or Adobe audit evidence |
| Legal/Records Administrator | Activate approved NDA versions, view/download archives, place legal holds, administer retention when authorized | Alter a completed signed PDF or audit trail |
| Nexus Organization Administrator | Manage organization users and roles and integration configuration | Bypass tenant isolation or silently weaken legal/security controls |
| Integration Service | Call Adobe, receive webhooks, reconcile status, retrieve final artifacts | Act without an organization-bound service identity and scoped secret |
| Auditor | Read authorized visit and evidence records and export governed evidence | Modify operational or archive records |

All privileged permissions are enforced by backend policy. Hiding a UI control is not authorization.

---

## 6. Core invariants

1. Every record belongs to exactly one Nexus `organization_id`.
2. No query, count, export, webhook update, archive access, or background job may cross organizations.
3. Each visit has one immutable public `visit_reference` and internal UUID; neither grants access by itself.
4. Each QR session is visitor/visit-specific, opaque, short-lived, revocable, and stored only as a hash at rest.
5. QR content contains no PII, Adobe credential, Adobe agreement URL, signed-document URL, or durable object-store URL.
6. Each Adobe agreement is bound to exactly one organization, visit, visitor, NDA template version, and intended signer email.
7. A post-sign redirect is advisory only. It never sets `NDA_VERIFIED`.
8. Duplicate or out-of-order webhooks never duplicate archives or regress a terminal state.
9. Nexus verifies agreement identity and state server-side before check-in.
10. A completed NDA archive contains the exact signed PDF, Adobe audit trail, cryptographic hashes, retrieval timestamps, template version, agreement ID, and provenance metadata.
11. Completed artifacts are immutable. Corrections create new metadata/audit events, not modified evidence bytes.
12. A required NDA may be waived only by an authorized policy decision with reason, actor, and timestamp.
13. No visitor is marked `CHECKED_IN` while the effective NDA requirement is unsatisfied.
14. Standard Adobe electronic signature is accurately described; the system must not claim enhanced identity proofing.
15. Adobe access and refresh tokens never leave the backend secret boundary.

---

## 7. Domain model

### 7.1 Entity summary

| Entity | Purpose | Key relationships |
|---|---|---|
| `VisitorProfile` | Reusable organization-local visitor identity/contact information | Organization; many Visits |
| `Visit` | One planned or actual visit | Visitor, Host, Location, NDA Requirement |
| `Location` | Sister-company office/site | Organization; Visits; Policies |
| `VisitorType` | Vendor, candidate, client, guest, contractor, regulator, other | Organization; policy input |
| `NdaPolicy` | Determines whether and which NDA is required | Organization, Location, VisitorType |
| `NdaTemplateVersion` | Approved immutable template identity and metadata | Organization; Adobe library document; Agreements |
| `NdaAgreement` | Nexus projection of one Adobe agreement | Visit, Visitor, TemplateVersion |
| `QrSession` | Short-lived mobile bootstrap session | Visit; optional Agreement |
| `NdaArchive` | Immutable archive index and evidence metadata | Agreement; signed PDF; audit trail |
| `WebhookReceipt` | Durable idempotency and processing record | Organization; Adobe resource/event |
| `VisitAuditEvent` | Append-only business/security audit event | Organization; Visit; Actor |
| `LegalHold` | Prevents otherwise eligible archival deletion | Organization; Archive; Authorizing actor |

### 7.2 Required fields

#### VisitorProfile

- `id`
- `organization_id`
- `first_name`
- `last_name`
- `email`
- `phone` — optional
- `company_name` — optional
- `created_at`, `created_by`
- `updated_at`, `updated_by`
- `status` — `ACTIVE`, `RESTRICTED`, `INACTIVE`
- normalized lookup fields for organization-local duplicate assistance

The initial release must not automatically merge visitor profiles. It may warn reception about a likely match.

#### Visit

- `id`
- `organization_id`
- `visit_reference`
- `visitor_id`
- `host_user_id`
- `location_id`
- `visitor_type_id`
- `journey_type` — `SCHEDULED`, `WALK_IN`
- `purpose`
- `scheduled_start`, `scheduled_end` — required for scheduled visits
- `actual_arrival_at`, `checked_in_at`, `checked_out_at`
- `status`
- `nda_requirement_status`
- `nda_agreement_id` — nullable until created
- `created_at`, `created_by`, `updated_at`, `updated_by`
- `cancellation_reason` — optional
- `denial_reason` — optional, access controlled

#### NdaTemplateVersion

- `id`
- `organization_id`
- `logical_template_name`
- `version`
- `status` — `DRAFT_METADATA`, `APPROVED`, `ACTIVE`, `RETIRED`
- `adobe_library_document_id`
- `document_sha256` when retrievable and approved
- `effective_from`, `effective_to`
- `approved_by`, `approved_at`
- `legal_owner`
- `created_at`, `created_by`

An activated version is immutable. Retirement affects new agreements only.

#### NdaAgreement

- `id`
- `organization_id`
- `visit_id`
- `visitor_id`
- `nda_template_version_id`
- `signer_email`
- `adobe_agreement_id`
- `adobe_api_access_point_key` or environment reference, not a secret
- `external_id` containing a Nexus-generated correlation reference
- `status`
- `status_reason`
- `created_at`, `sent_at`, `viewed_at`, `signed_at`, `verified_at`
- `last_reconciled_at`
- `archive_id` — nullable until archived
- `idempotency_key`

#### QrSession

- `id`
- `organization_id`
- `visit_id`
- `token_hash`
- `purpose` — `NDA_SIGNING`
- `issued_at`, `expires_at`
- `issued_by`
- `first_opened_at`, `completed_at`, `revoked_at`
- `attempt_count`
- minimal risk telemetry such as truncated/derived network signal when policy permits

Raw QR tokens must never be persisted after issuance.

#### NdaArchive

- `id`
- `organization_id`
- `agreement_id`
- `visit_id`
- `visitor_id`
- `template_version_id`
- `signed_document_object_key`
- `signed_document_sha256`
- `audit_trail_object_key`
- `audit_trail_sha256`
- `adobe_agreement_status_at_retrieval`
- `retrieved_at`
- `retention_class`
- `retention_until` — nullable until policy decision
- `legal_hold_status`
- `archived_by_service_identity`
- `archive_status`

Object keys must be opaque and organization-prefixed. Direct object-store keys are never exposed as public authorization.

---

## 8. State machines

### 8.1 Visit state

```text
PLANNED | REGISTERED
  -> AWAITING_NDA (when required)
  -> READY_FOR_CHECK_IN (NDA verified or authorized exemption)
  -> CHECKED_IN
  -> CHECKED_OUT

Any pre-check-in state -> CANCELLED
AWAITING_NDA -> DENIED or EXPIRED
```

Rules:

- Scheduled visits begin `PLANNED`; walk-ins begin `REGISTERED`.
- `READY_FOR_CHECK_IN` is derived from effective policy and verified evidence.
- Only authorized reception can transition to `CHECKED_IN` or `CHECKED_OUT`.
- Check-in is rejected if required NDA state is not `VERIFIED_ARCHIVED` or an authorized exemption is not active.
- Terminal visit states do not silently reopen.

### 8.2 NDA agreement state

```text
NOT_REQUIRED
REQUIRED
CREATION_PENDING
IN_PROCESS
VIEWED
SIGNED_REPORTED
VERIFICATION_PENDING
VERIFIED
ARCHIVE_PENDING
VERIFIED_ARCHIVED

DECLINED | CANCELLED | EXPIRED | FAILED | RECONCILIATION_REQUIRED
```

Rules:

- `SIGNED_REPORTED` may originate from a webhook or browser redirect but is not sufficient for check-in.
- `VERIFIED` requires a server-side Adobe agreement retrieval matching organization binding, Adobe agreement ID, expected external correlation, signer, terminal/completed state, and template lineage.
- `VERIFIED_ARCHIVED` requires successful retrieval and hashing of both signed PDF and Adobe audit trail.
- A completed terminal Adobe agreement cannot return to `IN_PROCESS` because of a stale webhook.
- Declining the NDA prevents check-in unless an authorized exemption is separately created.

---

## 9. User journeys

### 9.1 Scheduled visitor

1. Host or reception creates the visit within the sister-company organization.
2. Nexus evaluates the effective NDA policy using organization, location, visitor type, and visit time.
3. If required, Nexus binds the currently active approved NDA template version.
4. Nexus creates an Adobe agreement for the visitor's email using `ESIGN` and records the returned agreement ID.
5. Nexus issues a visitor-specific QR session or makes it available to reception/host for display or printing.
6. Visitor scans the QR code on a mobile device.
7. Nexus validates token hash, purpose, expiry, revocation, visit state, organization binding, and signer context.
8. Nexus redirects to the authorized Adobe signing experience.
9. Adobe performs the standard electronic-signature ceremony.
10. Adobe webhook reports lifecycle events; Nexus acknowledges quickly, stores the receipt, and processes asynchronously.
11. Nexus retrieves authoritative agreement state.
12. When complete, Nexus retrieves the signed PDF and audit trail, hashes and archives both, and marks the NDA `VERIFIED_ARCHIVED`.
13. Reception sees `Ready for check-in` and checks the visitor in.
14. Reception checks the visitor out at departure.

### 9.2 Walk-in visitor

1. Reception creates or selects an organization-local visitor profile.
2. Reception captures the host, location, visitor type, purpose, and visitor email.
3. Nexus evaluates policy and creates the required Adobe agreement.
4. Nexus displays or prints a one-time QR code for that visit.
5. The remaining signing, verification, archival, check-in, and checkout flow matches the scheduled journey.

### 9.3 No personal mobile device or QR failure

- Reception may reissue the QR, invalidating prior active tokens.
- Reception may send/open an Adobe-supported signing invitation through an approved method if configured.
- A managed reception device may display the signing journey only if privacy/session-clearing controls are approved.
- Reception may never mark the agreement signed based on verbal confirmation or a screenshot.

---

## 10. QR security contract

- Generate at least 128 bits of cryptographically secure randomness.
- Encode only an opaque HTTPS URL token.
- Store only a slow or keyed cryptographic hash of the token.
- Default time-to-live: 15 minutes; organization policy may select a shorter value.
- Permit one active QR session per visit/purpose by default; reissue revokes the former session.
- Rate-limit token resolution by token and network risk signal.
- Use generic failure responses that do not disclose visitor identity or visit existence.
- Require TLS and prohibit referrer leakage of the QR token to Adobe or third-party resources.
- Exchange the QR token for a short-lived, secure, HTTP-only, SameSite session before leaving the Nexus page; remove the raw token from the browser URL.
- Mark the session completed after verified signing, and reject reuse.
- Do not render PII in the QR image or filename.
- Prevent caching of token-bearing pages with appropriate response headers.
- Record issuance, first open, expiration, revocation, reissue, abuse throttling, and completion as audit events.

---

## 11. Adobe Acrobat Sign integration contract

### 11.1 Authentication and endpoint selection

- Use OAuth 2.0 for the backend integration.
- Store client credentials and refresh tokens only in an approved secret manager.
- Request the minimum Acrobat Sign scopes needed for agreements, library documents, webhooks, and document retrieval.
- Resolve and cache the correct geographic API access point per Adobe account/environment; do not hard-code one regional hostname.
- Separate development/test Adobe accounts and credentials from production.
- Use `Authorization: Bearer <access-token>` for REST v6 requests.

Adobe documents OAuth 2.0 for API authorization and recommends discovering the correct API base/access URI before resource calls. See [Managing OAuth Tokens](https://opensource.adobe.com/acrobat-sign/developer_guide/oauth.html) and [API Best Practices](https://opensource.adobe.com/acrobat-sign/developer_guide/best-practices.html).

### 11.2 Template and agreement creation

- Legal owns the NDA text; application code references an approved Adobe library document ID and immutable Nexus template version.
- Create a distinct Adobe agreement for each visit requiring a signature.
- Set the visitor email as the intended signer and use standard electronic signature (`ESIGN`).
- Include a Nexus correlation identifier in Adobe-supported external/reference metadata.
- Agreement names may include a non-sensitive visit reference but must avoid unnecessary PII.
- Use idempotency protection so retries do not create multiple active agreements for one visit/template/signer tuple.
- If agreement creation outcome is uncertain after a timeout, reconcile by correlation reference before retrying.
- Do not dynamically change approved legal text or fields without a new template version and approval.

Adobe REST v6 supports creating and managing agreements and reusable library documents. Adobe also documents transient documents, agreement creation, and resource views in its [API Usage guide](https://opensource.adobe.com/acrobat-sign/developer_guide/apiusage.html).

### 11.3 Mobile signing view

- Nexus may retrieve an authorized signing URL/view only after the agreement exists and the current Adobe account/participant state permits it.
- The signing URL must be treated as a secret bearer-like capability: short-lived in Nexus memory/session, never logged, never archived, and never directly encoded into the printed QR.
- Prefer redirecting the visitor from an organization-branded Nexus interstitial page that states the visitor is leaving Nexus for Adobe Acrobat Sign.
- On return, show `Signature submitted—verification in progress` until backend verification and archival complete.
- Do not treat a browser callback or redirect as authoritative completion.

Adobe's REST v6 materials describe retrieving signing URLs and agreement views, including `POST /agreements/{agreementId}/views`; availability depends on resource state and the caller's relationship to it. See [REST v6 release notes](https://opensource.adobe.com/acrobat-sign/releasenotes/v6releasenotes.html) and [REST API samples](https://opensource.adobe.com/acrobat-sign/developer_guide/samples.html).

### 11.4 Webhooks

- Use an HTTPS webhook endpoint dedicated to the Adobe integration.
- Complete Adobe's webhook endpoint verification/registration protocol exactly as documented.
- Subscribe only to needed agreement lifecycle events, including creation/in-process, action/view where useful, completion, rejection/decline, cancellation, expiration, and relevant failures.
- Persist a minimal webhook receipt before asynchronous processing.
- Derive an idempotency key from stable Adobe event/resource attributes.
- Validate the webhook's configured authentication mechanism and expected Adobe account/resource binding.
- Return success promptly after durable acceptance; perform Adobe reconciliation and archive downloads asynchronously.
- Treat webhook payloads as notifications, not complete authority. Retrieve current agreement state from Adobe before irreversible Nexus transitions.
- Handle duplicate, delayed, missing, and out-of-order delivery.
- Run a scheduled reconciliation job for nonterminal or archive-pending agreements.

Adobe describes webhooks as HTTPS push notifications for real-time workflow events and provides webhook registration and event documentation. See [Webhooks in Acrobat Sign](https://opensource.adobe.com/acrobat-sign/acrobat_sign_events/index.html), [Webhook APIs](https://opensource.adobe.com/acrobat-sign/developer_guide/webhookapis.html), and [Agreement Events](https://opensource.adobe.com/acrobat-sign/acrobat_sign_events/webhookeventsagreements.html).

### 11.5 Completion and archive retrieval

After authoritative completion:

1. Retrieve agreement metadata and participant information.
2. Confirm the Adobe agreement ID, Nexus correlation, signer email, template lineage, and completed status.
3. Retrieve the combined signed PDF or the approved final document set.
4. Retrieve the Adobe audit trail.
5. Stream each artifact through size/type limits and malware/content validation appropriate for trusted provider downloads.
6. Calculate SHA-256 before storage and verify after storage.
7. Store artifacts in encrypted private object storage under organization-scoped keys.
8. Persist archive metadata and hashes transactionally or through a recoverable saga.
9. Mark `VERIFIED_ARCHIVED` only after both required artifacts and metadata are durable.
10. Record a complete audit event.

Adobe identifies signed-document retrieval, audit-trail download, and archival as supported Sign API uses in its [API overview](https://opensource.adobe.com/acrobat-sign/developer_guide/).

---

## 12. Nexus functional requirements

### 12.1 Reception dashboard

The dashboard must provide:

- Today's scheduled visits.
- Walk-in registration action.
- Search by visitor name, company, host, visit reference, and status within the organization.
- Filters for location, host, journey type, NDA status, visit status, and date.
- Clear readiness states: `NDA required`, `Signing`, `Verification pending`, `Archive pending`, `Ready`, `Checked in`, `Checked out`, `Declined/Denied`, `Error`.
- QR issue/reissue action gated by permission and valid visit state.
- Check-in and check-out actions.
- Retry/reconcile action for authorized operators without permitting manual success override.
- Accessible loading, empty, no-match, error, and retry states.

### 12.2 Visitor detail

- Visitor and visit information.
- Host and location.
- Timeline of operational events.
- NDA requirement and template version.
- Adobe agreement status without exposing credentials or raw signing URLs.
- Archive availability to authorized users only.
- Check-in/out timestamps and actors.
- Correction workflow for permitted metadata with before/after audit trail.

### 12.3 Archive

- Search by visitor, company, host, date range, visit reference, Adobe agreement ID, NDA version, and archive status.
- Authorized inline view or time-limited download.
- Display artifact hashes, Adobe status, signed timestamp, retrieval timestamp, template version, retention class, and legal-hold state.
- Exports must be minimized, authorized, time-limited when generated, and audited.
- No public sharing links.
- No mutation of archived bytes.

### 12.4 Administration

- Locations and visitor types.
- NDA applicability rules with effective dates.
- Adobe connection health without token disclosure.
- Approved template-version activation/retirement.
- QR TTL and operational limits within security-approved bounds.
- Retention classes after `VIS-GOV-003` approval.
- Role assignments and access review report.
- Webhook and reconciliation health dashboard.

---

## 13. Candidate Nexus API surface

All routes are organization-scoped through authenticated context. Client-supplied `organization_id` must not override the caller's authorized organization.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/v1/visitor-log/visitors` | Create visitor profile |
| `GET` | `/api/v1/visitor-log/visitors` | Search organization-local visitors |
| `POST` | `/api/v1/visitor-log/visits` | Create scheduled or walk-in visit |
| `GET` | `/api/v1/visitor-log/visits` | Search/filter visits |
| `GET` | `/api/v1/visitor-log/visits/{visit_id}` | Retrieve authorized visit detail |
| `PATCH` | `/api/v1/visitor-log/visits/{visit_id}` | Update permitted pre-check-in metadata |
| `POST` | `/api/v1/visitor-log/visits/{visit_id}/nda-agreement` | Idempotently create/reconcile agreement |
| `POST` | `/api/v1/visitor-log/visits/{visit_id}/qr-sessions` | Issue/reissue QR session |
| `POST` | `/api/v1/visitor-log/mobile/session` | Exchange raw QR token for mobile session |
| `POST` | `/api/v1/visitor-log/mobile/signing-view` | Resolve authorized Adobe signing redirect |
| `GET` | `/api/v1/visitor-log/mobile/status` | Obtain privacy-minimized session status |
| `POST` | `/api/v1/visitor-log/visits/{visit_id}/reconcile` | Trigger authorized reconciliation |
| `POST` | `/api/v1/visitor-log/visits/{visit_id}/check-in` | Check in if gates pass |
| `POST` | `/api/v1/visitor-log/visits/{visit_id}/check-out` | Check out active visit |
| `POST` | `/api/v1/integrations/adobe-sign/webhooks` | Receive Adobe webhook |
| `GET` | `/api/v1/visitor-log/archives` | Search authorized archive metadata |
| `GET` | `/api/v1/visitor-log/archives/{archive_id}` | Retrieve archive metadata |
| `POST` | `/api/v1/visitor-log/archives/{archive_id}/download` | Issue audited, time-limited artifact access |

State-changing endpoints require CSRF protection where cookie authentication is used, idempotency keys where specified, optimistic concurrency or version checks, and structured audit events.

---

## 14. Privacy, security, and compliance requirements

### 14.1 Data minimization

- Collect only identity/contact, affiliation, visit, host, and NDA data required by approved policy.
- Do not collect sensitive identity documents, biometrics, or visitor photographs in v1.
- Do not put PII in QR codes, URLs, logs, metrics labels, object keys, or queue names.
- Redact signer URLs, OAuth tokens, webhook credentials, and document content from telemetry.

### 14.2 Tenant isolation

- Every table and object is organization-bound.
- Every service query includes authoritative organization scope.
- Adobe agreement correlation maps to exactly one organization.
- Webhooks resolving to zero or multiple organization mappings enter quarantine and never update a visit.
- Archive storage uses separate organization prefixes and least-privilege access policies.
- Cross-organization negative tests are release-blocking.

### 14.3 Encryption and secrets

- TLS in transit.
- Encryption at rest for database, object storage, backups, and queues containing sensitive metadata.
- OAuth client secret, refresh token, webhook secret/credential, and signing URLs are treated as secrets.
- Secrets are rotated and accessed by workload identity where available.
- No production secret in source, test fixture, CI output, or client bundle.

### 14.4 Audit

Append-only events must cover:

- Visitor/visit creation and permitted correction.
- Policy evaluation and template binding.
- Agreement create/retry/reconcile.
- QR issue, revoke, reissue, open, expire, throttle, and complete.
- Webhook receipt, validation, duplicate detection, quarantine, processing, and failure.
- Adobe status transitions.
- Artifact retrieval, hash, archive, view, download, hold, and disposition.
- Check-in, denied check-in, and check-out.
- Administrative policy, role, template, connection, and retention changes.

Events include organization, actor/service identity, action, target, timestamp, correlation ID, result, and reason. They exclude secrets and signed document content.

### 14.5 Retention and deletion

- Retention duration remains blocked pending `VIS-GOV-003`.
- Until approved, artifacts are retained and automated destructive purge is disabled.
- Once approved, implement policy-driven eligibility, legal hold, two-step authorization where required, deletion evidence, and backup-expiration alignment.
- Visitor profile deletion must not silently orphan required legal evidence.
- Privacy requests must be reviewed against legal retention obligations.

---

## 15. Reliability and recovery

- Agreement creation, webhook processing, archive retrieval, and check-in are idempotent.
- Use durable jobs with bounded retry and dead-letter/quarantine handling.
- Apply exponential backoff and respect Adobe rate limits and retry guidance.
- Circuit-break repeated Adobe failures while preserving reception visibility.
- Reconcile all nonterminal agreements periodically and archive-pending agreements more aggressively.
- Expose operational metrics for creation latency, signing latency, webhook delay, reconciliation backlog, archive failures, QR failures, and check-in denials.
- Alert on webhook silence, OAuth refresh failure, mapping quarantine, archive backlog, hash mismatch, and cross-tenant policy denial anomalies.
- Define recovery objectives before production authorization.
- A temporary Adobe outage must not permit a manual signed override; reception may wait, reschedule, or follow an approved offline procedure outside this specification.

---

## 16. Accessibility and mobile requirements

- Visitor pages target current mobile Safari and Chrome versions approved by the organization.
- Responsive layout at 320 CSS pixels and above.
- WCAG 2.2 AA target for Nexus-controlled pages.
- QR journey must have a non-QR accessible alternative.
- Touch targets, focus order, labels, contrast, error identification, and screen-reader announcements must be tested.
- Do not require installation of an app.
- Preserve no sensitive state in local storage.
- After handoff to Adobe, Nexus cannot guarantee Adobe UI behavior but must test the supported integration on target devices.

---

## 17. Test strategy

### 17.1 Test layers

| Layer | Purpose |
|---|---|
| Unit | Policy evaluation, state transitions, token hashing, mapping, normalization, authorization predicates |
| Contract | Nexus–Adobe request/response mapping using recorded synthetic schemas, not production payloads |
| API | Authenticated route behavior, validation, tenant isolation, idempotency, concurrency |
| Component | Reception, mobile, admin, and archive UI states |
| Integration | Database, queue, object storage, secret manager abstraction, Adobe sandbox/mock server |
| End-to-end | Scheduled and walk-in journeys on desktop reception plus mobile visitor device |
| Security | Token abuse, authorization, injection, secret leakage, webhook forgery/replay, cross-tenant access |
| Resilience | Timeouts, duplicates, out-of-order events, rate limits, queue retries, partial archive failure |
| Accessibility | Automated checks plus keyboard/screen-reader/manual mobile review |

No skipped, expected-failure, or unexecuted test counts as passing evidence.

### 17.2 Required synthetic fixtures

- Organizations `ORG_SISTER_A` and `ORG_OTHER_B`.
- Active/inactive hosts and reception/admin/auditor roles.
- Scheduled and walk-in visitors using reserved example domains.
- Active, retired, future-effective, and unapproved NDA template versions.
- Adobe sandbox/mock agreements in all relevant states.
- Duplicate, out-of-order, malformed, mismapped, and delayed webhook events.
- Signed PDF and audit-trail fixtures with known SHA-256 values.
- Object-store timeout, checksum mismatch, and partial-write simulations.
- Expired, revoked, reused, malformed, and cross-visit QR tokens.

---

## 18. Detailed test cases

### 18.1 Tenancy and authorization

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-TEN-001` | Reception in Sister A lists visits | Only Sister A visits returned; count and pagination exclude Other B |
| `VIS-TEN-002` | Sister A user requests Other B visit by UUID | `403` or policy-standard concealment response; no data leaked; audit event recorded |
| `VIS-TEN-003` | Sister A admin searches archives using Other B Adobe agreement ID | No result or authorized denial; no timing/detail leak beyond policy |
| `VIS-TEN-004` | Webhook agreement ID maps to Other B while correlation claims Sister A | Receipt quarantined; neither organization updated; security alert emitted |
| `VIS-TEN-005` | Background archive job is given mismatched organization and agreement IDs | Job fails closed; no object written; incident evidence recorded |
| `VIS-AUT-001` | Host creates a scheduled visitor for self | Allowed with organization-bound host |
| `VIS-AUT-002` | Host attempts walk-in check-in | Denied unless separately granted reception permission |
| `VIS-AUT-003` | Reception attempts to activate NDA template | Denied |
| `VIS-AUT-004` | Legal/Records Admin downloads authorized archive | Time-limited access issued and audited |
| `VIS-AUT-005` | Visitor attempts archive or list API access | Denied without revealing archive existence |

### 18.2 Scheduled and walk-in registration

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-REG-001` | Valid scheduled visit created | `PLANNED`; policy evaluated; actor/time recorded |
| `VIS-REG-002` | Valid walk-in created by reception | `REGISTERED`; arrival captured; policy evaluated |
| `VIS-REG-003` | Scheduled visit lacks start time | Validation error; no partial visit |
| `VIS-REG-004` | Walk-in lacks active host | Validation or controlled escalation; no check-in readiness |
| `VIS-REG-005` | Visitor email matches likely existing profile in same org | Duplicate warning; operator may select or create; no automatic merge |
| `VIS-REG-006` | Same email exists only in Other B | No cross-org match disclosed |
| `VIS-REG-007` | Inactive/restricted visitor profile selected | Policy-defined denial/escalation; audit event |
| `VIS-REG-008` | Concurrent duplicate create requests share idempotency key | One visit created; identical response semantics |

### 18.3 NDA policy and templates

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-POL-001` | Active rule requires NDA | Visit enters `AWAITING_NDA` and binds one active template version |
| `VIS-POL-002` | Approved policy says NDA not required | Visit readiness reflects `NOT_REQUIRED`; decision and rule version audited |
| `VIS-POL-003` | Two equal-precedence rules conflict | Fail closed; visit not ready; configuration error raised |
| `VIS-POL-004` | No active approved template exists for required NDA | Agreement not created; visit blocked; admin alert |
| `VIS-POL-005` | Template retired after agreement creation | Existing agreement retains bound version; new agreements use active version |
| `VIS-POL-006` | Operator tries to edit active template metadata affecting legal identity | Rejected; new version required |
| `VIS-POL-007` | Unauthorized NDA waiver attempted | Denied; NDA remains required |
| `VIS-POL-008` | Authorized exemption entered | Reason/actor/time/policy authority stored; visit may become ready |

### 18.4 QR token and mobile session

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-QR-001` | Valid unexpired token exchanged | Raw token removed from URL; secure short-lived session established |
| `VIS-QR-002` | Expired token used | Generic expired/assistance response; no visitor PII |
| `VIS-QR-003` | Revoked token used after reissue | Rejected; new token remains valid |
| `VIS-QR-004` | Token reused after completion | Rejected; no signing URL returned |
| `VIS-QR-005` | Random malformed tokens sprayed | Rate limited; generic responses; security telemetry without raw tokens |
| `VIS-QR-006` | Valid token supplied for a cancelled visit | Rejected; no Adobe redirect |
| `VIS-QR-007` | Token for Visit A manipulated with Visit B identifier | Binding mismatch rejected |
| `VIS-QR-008` | QR image inspected | Contains only opaque HTTPS token URL and no PII/Adobe credential |
| `VIS-QR-009` | Signing page loads third-party asset | Referrer does not disclose QR token |
| `VIS-QR-010` | Visitor uses non-QR alternative | Same identity, policy, session, and audit controls apply |

### 18.5 Adobe authentication and agreement creation

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-ADB-001` | OAuth refresh succeeds | Access token used server-side only; secret values absent from logs |
| `VIS-ADB-002` | OAuth refresh fails/revoked | Circuit/retry policy applied; visit remains blocked; alert emitted |
| `VIS-ADB-003` | Correct regional access point returned | Subsequent API calls use cached environment/account-specific base URI |
| `VIS-ADB-004` | Agreement created for required visit | Adobe ID and Nexus correlation stored; state becomes `IN_PROCESS` |
| `VIS-ADB-005` | Client retries same creation idempotency key | Existing agreement returned; no duplicate Adobe agreement |
| `VIS-ADB-006` | Timeout occurs after Adobe may have created agreement | Reconcile by correlation before retry; at most one active agreement accepted |
| `VIS-ADB-007` | Signer email differs from bound visitor email | Creation or verification rejected; operator correction required |
| `VIS-ADB-008` | Retired/unapproved template ID supplied | Request rejected before Adobe call |
| `VIS-ADB-009` | Signing URL appears in exception/log/telemetry path | Security test fails release; value must be redacted |
| `VIS-ADB-010` | Adobe reports agreement not signable/exposed | Friendly recoverable state; no readiness; reconciliation evidence retained |

### 18.6 Webhook processing

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-WHK-001` | Valid completion event received | Durable receipt acknowledged; asynchronous reconciliation starts |
| `VIS-WHK-002` | Exact duplicate event received | One effective transition/archive job; duplicate recorded harmlessly |
| `VIS-WHK-003` | Old `IN_PROCESS` arrives after completed event | Terminal state does not regress |
| `VIS-WHK-004` | Completion webhook never arrives | Scheduled reconciliation discovers completion and proceeds |
| `VIS-WHK-005` | Forged or unauthenticated request | Rejected/quarantined according to Adobe verification method; no state change |
| `VIS-WHK-006` | Malformed payload | Safe `4xx`/quarantine behavior; no secret or stack trace returned |
| `VIS-WHK-007` | Unknown agreement ID | Receipt quarantined; security/operations event; no visit updated |
| `VIS-WHK-008` | Webhook handler's downstream queue unavailable | Durable receipt retained; retry occurs; Adobe response remains bounded |
| `VIS-WHK-009` | Event delivery delayed beyond QR expiry | Agreement still reconciles; QR remains expired; archive/check-in status updates correctly |
| `VIS-WHK-010` | Declined/expired/cancelled event | Correct terminal state; check-in remains blocked |

### 18.7 Verification and archive

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-ARC-001` | Redirect claims success but Adobe state is in process | `VERIFICATION_PENDING`; check-in denied |
| `VIS-ARC-002` | Adobe confirms completion and bindings match | State becomes `VERIFIED`; archive retrieval begins |
| `VIS-ARC-003` | Adobe agreement signer/correlation/template mismatch | `RECONCILIATION_REQUIRED`; no archive-ready/check-in state; alert |
| `VIS-ARC-004` | Signed PDF and audit trail retrieved | Both hashed and stored; metadata persisted; `VERIFIED_ARCHIVED` |
| `VIS-ARC-005` | PDF succeeds but audit-trail retrieval fails | `ARCHIVE_PENDING`; retry only missing work; check-in policy follows strict required-artifact rule |
| `VIS-ARC-006` | Object-store write times out with unknown outcome | Verify object/hash before retry; no duplicate archive identity |
| `VIS-ARC-007` | Stored-object hash differs | Archive fails closed; object quarantined; alert; no readiness |
| `VIS-ARC-008` | Same completion processed concurrently | One archive record and one canonical object set |
| `VIS-ARC-009` | Authorized user views/downloads archive | Short-lived access; action audited; correct organization artifact |
| `VIS-ARC-010` | Unauthorized user guesses archive UUID | Denied; no signed document bytes or metadata leaked |
| `VIS-ARC-011` | Attempt to overwrite completed artifact | Rejected; immutable evidence retained |
| `VIS-ARC-012` | Legal hold active at retention eligibility | Purge skipped and evidence recorded |

### 18.8 Check-in and checkout

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-CHK-001` | Required NDA is `VERIFIED_ARCHIVED` | Authorized reception can check in once |
| `VIS-CHK-002` | Required NDA is `SIGNED_REPORTED` only | Check-in rejected |
| `VIS-CHK-003` | Required NDA is `ARCHIVE_PENDING` | Check-in rejected under strict default policy |
| `VIS-CHK-004` | NDA not required by approved policy | Check-in allowed when other gates pass |
| `VIS-CHK-005` | Valid authorized exemption exists | Check-in allowed and exemption shown in audit evidence |
| `VIS-CHK-006` | Two reception users check in concurrently | One transition succeeds; second is idempotent/conflict-safe |
| `VIS-CHK-007` | Checkout before check-in | Rejected |
| `VIS-CHK-008` | Valid checkout | Timestamp/actor recorded; state becomes `CHECKED_OUT` |
| `VIS-CHK-009` | Cancelled or denied visit checked in | Rejected |

### 18.9 UI, mobile, accessibility, and privacy

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-UI-001` | Reception dashboard loading/empty/no-match/error | Each state is distinct and recoverable |
| `VIS-UI-002` | Mobile viewport at 320 CSS px | No horizontal obstruction; primary actions usable |
| `VIS-UI-003` | Keyboard-only reception workflow | All actions reachable with visible focus |
| `VIS-UI-004` | Screen reader enters visitor mobile page | Purpose, NDA requirement, errors, and status announced meaningfully |
| `VIS-UI-005` | Adobe signing completes then redirects | Nexus says verification is pending until server evidence completes |
| `VIS-UI-006` | Browser back after token exchange | Raw QR token does not reappear or grant a second session |
| `VIS-UI-007` | Shared managed device flow ends | Session and sensitive browser state cleared according to approved procedure |
| `VIS-UI-008` | Analytics/error telemetry captured | No visitor PII, document content, tokens, or signing URLs present |

### 18.10 Retention, audit, resilience, and operations

| ID | Scenario | Expected result |
|---|---|---|
| `VIS-OPS-001` | Retention policy not approved | Destructive purge disabled; status visibly blocked |
| `VIS-OPS-002` | Approved record becomes eligible and has no hold | Governed deletion workflow runs and records evidence |
| `VIS-OPS-003` | Adobe rate limit returned | Backoff/retry honored; no request storm |
| `VIS-OPS-004` | Adobe unavailable during arrival | Clear operational state; no manual signature override |
| `VIS-OPS-005` | Archive backlog exceeds threshold | Alert with organization-safe metrics; no PII in labels |
| `VIS-OPS-006` | Webhook silence threshold exceeded | Health alert and reconciliation coverage activated |
| `VIS-OPS-007` | Audit event write fails during state change | State change fails or enters recoverable transaction state; no unaudited success |
| `VIS-OPS-008` | Backup restore test performed | Database/archive linkage and hashes reconcile in isolated recovery environment |
| `VIS-OPS-009` | Secret-scanning test runs on source/build artifacts | No Adobe or Nexus secrets detected |
| `VIS-OPS-010` | Dependency/provider contract changes | Contract suite detects incompatible Adobe response before production promotion |

---

## 19. Minimum end-to-end acceptance scenarios

### E2E-1 Scheduled visitor

Host preregisters visitor → policy requires NDA → correct template bound → agreement created → QR issued → mobile session opened → Adobe standard e-sign completed → webhook accepted → state reconciled → PDF and audit trail archived with hashes → reception checks in → reception checks out.

### E2E-2 Walk-in visitor

Reception registers walk-in → duplicate assistance remains organization-local → host/location selected → NDA created → QR scanned → signed and archived → check-in/out completed.

### E2E-3 Failure and recovery

Adobe completion webhook is missed → browser redirect remains non-authoritative → check-in initially blocked → scheduled reconciliation finds completion → archive retrieval partially fails → retry completes missing artifact → hashes pass → check-in becomes available.

### E2E-4 Tenant attack

Sister A user, visitor token, archive UUID, Adobe ID, and background job are each deliberately combined with Other B identifiers → every path fails closed → no Other B data or document bytes appear → security evidence is recorded.

### E2E-5 Declined NDA

Visitor declines NDA → Nexus reconciles `DECLINED` → QR cannot be reused → check-in remains blocked → reception sees safe next action without access to unrelated Adobe data.

---

## 20. Quality gates

| Gate | Required evidence |
|---|---|
| `GATE-01 Authority` | VIS-GOV decisions identified; approved decisions bound to versioned artifacts |
| `GATE-02 Architecture` | Tenant, state-machine, Adobe, QR, archive, and failure contracts reviewed |
| `GATE-03 Tests First` | Requirement-to-test traceability complete; expected red tests fail for missing behavior only |
| `GATE-04 Implementation` | Minimal scoped implementation satisfies contracts without prohibited expansion |
| `GATE-05 Security` | Threat model, cross-tenant, webhook, QR, secrets, authorization, and archive tests pass |
| `GATE-06 Validation` | Unit, API, frontend, integration, E2E, accessibility, migration, build, and smoke checks pass |
| `GATE-07 Adobe Sandbox` | Real sandbox agreement, mobile signing, webhook, reconciliation, document, and audit-trail flow verified |
| `GATE-08 Human Acceptance` | Reception, Legal/Records, Security, Privacy, and product owner approve |
| `GATE-09 Production Authorization` | Retention, support, monitoring, credentials, licensing, runbook, and rollback approved |

No gate may be inferred from a later gate. A successful E2E test does not replace security, retention, or legal approval.

---

## 21. Required implementation artifacts

Before production code:

- `docs/visitor-log/AUTHORITY_REGISTER.md`
- `docs/visitor-log/DOMAIN_MODEL.md`
- `docs/visitor-log/STATE_MACHINE.md`
- `docs/visitor-log/API_CONTRACT.md`
- `docs/visitor-log/ADOBE_SIGN_CONTRACT.md`
- `docs/visitor-log/QR_SECURITY_CONTRACT.md`
- `docs/visitor-log/ARCHIVE_AND_RETENTION_CONTRACT.md`
- `docs/visitor-log/THREAT_MODEL.md`
- `docs/visitor-log/TEST_MATRIX.md`
- `docs/visitor-log/TRACEABILITY_MATRIX.md`

Before human acceptance:

- Database migrations and downgrade evidence.
- Synthetic deterministic seed data.
- Automated test evidence.
- Adobe sandbox evidence with redacted identifiers.
- Accessibility and mobile-device report.
- Operational dashboards/alerts evidence.
- Incident, reconciliation, credential-rotation, and archive-recovery runbooks.
- `docs/visitor-log/IMPLEMENTATION_REPORT.md`.

---

## 22. Completion status schema

The implementation report must include:

```text
PHASE=NEXUS_VISITOR_LOG_ADOBE_SIGN_001
START_HEAD=
FINAL_HEAD=
AUTHORITY_STATUS=
TENANT_ISOLATION_STATUS=
SCHEDULED_VISITOR_STATUS=
WALK_IN_VISITOR_STATUS=
NDA_POLICY_STATUS=
QR_SECURITY_STATUS=
ADOBE_OAUTH_STATUS=
ADOBE_AGREEMENT_STATUS=
ADOBE_WEBHOOK_STATUS=
ADOBE_RECONCILIATION_STATUS=
SIGNED_PDF_ARCHIVE_STATUS=
AUDIT_TRAIL_ARCHIVE_STATUS=
CHECK_IN_GATE_STATUS=
RETENTION_STATUS=
UNIT_TEST_COUNTS=
API_TEST_COUNTS=
FRONTEND_TEST_COUNTS=
INTEGRATION_TEST_COUNTS=
E2E_TEST_COUNTS=
SECURITY_TEST_COUNTS=
ACCESSIBILITY_STATUS=
MIGRATION_STATUS=
BUILD_STATUS=
SMOKE_STATUS=
SKIPPED_TEST_COUNT=
XFAILED_TEST_COUNT=
UNRELATED_WORKTREE_PRESERVED=
PUSH_PERFORMED=NO
PR_CREATED=NO
MERGE_PERFORMED=NO
DEPLOYMENT_PERFORMED=NO
PRODUCTION_DATA_MUTATED=NO
OVERALL_STATUS=COMPLETE|PARTIAL|BLOCKED
NEXT_GATE=HUMAN_VISITOR_LOG_ACCEPTANCE
```

Every `PASS` requires cited, reproducible evidence. Every `BLOCKED` requires the exact missing authority, dependency, environment, or failed validation.

---

## 23. Stop conditions

Stop and report without guessing if:

- Approved NDA text or template authority is missing.
- Adobe licensing/account configuration does not permit the intended API or signing-view behavior.
- Adobe OAuth scopes or geographic access point cannot be verified.
- Retention or archive access decisions are required for production activation but absent.
- Current Nexus organization isolation cannot be proven for a new route, job, object, or webhook.
- A QR design would expose PII, a durable signing URL, credentials, or cross-visit access.
- The visitor's signer identity cannot be bound consistently to the Adobe agreement.
- Webhook authenticity/endpoint verification cannot be implemented according to the current Adobe contract.
- Signed PDF or audit trail cannot be retrieved and integrity-checked.
- Check-in would require a manual `signed=true` override.
- Real client, employee, visitor, or production document data would be used in tests.
- Existing unrelated worktree changes would be overwritten.
- Any action would push, merge, deploy, alter production, or create external agreements without explicit authorization.

---

## 24. Final acceptance criteria

The function is eligible for human acceptance only when:

1. Both scheduled and walk-in journeys pass end to end.
2. The sister company is demonstrably isolated as a separate Nexus organization.
3. QR sessions meet the token, expiry, revocation, privacy, and replay contracts.
4. Adobe standard electronic signatures are created and verified through server-side API evidence.
5. Duplicate, delayed, missing, and out-of-order webhooks are handled safely.
6. Signed PDFs and Adobe audit trails are archived immutably with verified SHA-256 hashes.
7. Required-NDA check-in fails closed until verification and archival succeed.
8. Archive access is least-privilege, time-limited where applicable, and audited.
9. Cross-tenant and authorization tests pass with zero data leakage.
10. Retention remains non-destructive until `VIS-GOV-003` is approved and implemented.
11. All required tests and quality gates pass without counting skips or expected failures.
12. Legal, Security, Privacy, Reception operations, and the product owner approve the release.

---

## 25. Adobe references

- [Acrobat Sign API overview](https://opensource.adobe.com/acrobat-sign/developer_guide/)
- [Managing OAuth Tokens](https://opensource.adobe.com/acrobat-sign/developer_guide/oauth.html)
- [API Best Practices](https://opensource.adobe.com/acrobat-sign/developer_guide/best-practices.html)
- [API Usage](https://opensource.adobe.com/acrobat-sign/developer_guide/apiusage.html)
- [REST API Samples](https://opensource.adobe.com/acrobat-sign/developer_guide/samples.html)
- [Webhook APIs](https://opensource.adobe.com/acrobat-sign/developer_guide/webhookapis.html)
- [Webhooks in Acrobat Sign](https://opensource.adobe.com/acrobat-sign/acrobat_sign_events/index.html)
- [Agreement Events](https://opensource.adobe.com/acrobat-sign/acrobat_sign_events/webhookeventsagreements.html)
- [REST v6 release notes](https://opensource.adobe.com/acrobat-sign/releasenotes/v6releasenotes.html)

