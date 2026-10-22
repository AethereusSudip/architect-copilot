# Starter project structure: licensing portal (modular monolith)

Implements ADR-001: one deployable web application with internal modules, a managed relational database,
object storage for documents, scheduled jobs for nightly integrations and a payment adapter.

```text
licensing-portal/
├── src/
│   ├── app/
│   │   ├── main.py              # Web app entry point; mounts each module's routes
│   │   └── config.py            # Reads settings from environment variables only
│   ├── modules/                 # ADR: enforce module boundaries; modules talk through service interfaces
│   │   ├── applications/        # Forms, save-and-resume, e-signature hand-off, status tracking
│   │   ├── documents/           # Upload, per-type checklist, object storage client
│   │   ├── workflow/            # Reviewer work queue, approvals, correspondence templates
│   │   └── payments/            # Adapter for the real-time payment provider (no card data stored)
│   └── shared/
│       ├── auth.py              # OIDC sign-in via the existing identity provider
│       ├── audit.py             # Audit log events (REVIEW: audit scope is an open question)
│       ├── db.py                # Database session; connection string from secret store
│       └── telemetry.py         # Structured logs, traces and metrics to the monitoring workspace
├── jobs/
│   ├── finance_export.py        # Nightly export to the finance system
│   └── student_data_sync.py     # Nightly import from the student data system
├── migration/
│   └── README.md                # Plan for 20 years of records and scanned files (ASSUMPTION: under 5 TB)
├── api/openapi.yaml             # API contract (02_openapi.yaml)
├── infra/terraform/             # IaC starter (03_main.tf), split into main/variables/outputs
├── docs/
│   ├── adr/ADR-001.md           # The approved ADR this code implements
│   └── diagrams/architecture.mmd
├── tests/                       # Unit tests per module + contract tests against openapi.yaml
├── .env.example                 # Keys only, no values
└── README.md
```

## .env.example keys (names only, values come from the secret store or pipeline variables)

```text
APP_ENV=<ENVIRONMENT>
OIDC_ISSUER_URL=<IDP_ISSUER_URL>
OIDC_CLIENT_ID=<CLIENT_ID>
DB_CONNECTION_SECRET_NAME=<KEY_VAULT_SECRET_NAME>
DOCUMENT_CONTAINER=<STORAGE_CONTAINER>
PAYMENT_PROVIDER_BASE_URL=<PAYMENT_PROVIDER_URL>
APPLICATIONINSIGHTS_CONNECTION_STRING=${APPINSIGHTS_CONNECTION_STRING}
```

ASSUMPTION: Python with a standard web framework; swap for the team's approved stack.
REVIEW: confirm module list against the functional requirements before creating repositories.
