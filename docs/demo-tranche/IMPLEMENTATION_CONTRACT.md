# Demo Tranche Implementation Contract

## Reader and outcome

This contract is for engineers extending the demo tranche. After reading it, they can add a scoped capability without weakening authorization or the demo flow.

## Scope

Tranche A delivers core-record creation, search/filtering, a resolved command-palette disposition, recoverable states, and reversible admin lifecycle. DF-FUNC-001 is implemented through list-page dialogs that create a record, invalidate its list, and open its detail page.

## Invariants

- Backend authorization remains the source of truth.
- Create requests use existing resource endpoints and schemas.
- Required values are validated in the form and again by the API.
- Failed saves retain entered form values; pending saves cannot be submitted twice.
- Deal creation uses authorized pipeline/stage choices, never identifiers typed by an end user.

## Delivery order

1. Core creation and its API discovery dependency.
2. Search, filters, and URL state.
3. Command palette implementation or documented removal.
4. Error/empty/loading states and admin lifecycle.
5. CSV export and integration verification.
