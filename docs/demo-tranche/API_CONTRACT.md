# Demo Tranche API Contract

## Existing creates

- `POST /api/v1/contacts` creates a contact from first and last name plus optional relationship fields; returns `201` and the record.
- `POST /api/v1/companies` creates a company from name plus optional attributes; returns `201` and the record.
- `POST /api/v1/deals` creates a deal from name, pipeline, and stage plus optional value and relationships; returns `201` and the record.

## Pipeline discovery

`GET /api/v1/pipelines` returns non-archived pipelines in the authenticated caller’s organization, ordered with the default first. Each pipeline includes ordered stages. It is additive, authenticated, read-only, and returns `200`; invalid credentials return the repository-standard `401` response.

## Evolution

The API is path-versioned at `/api/v1`; additions are backward compatible. The list is intentionally bounded by organization scope and has no mutable behavior.
