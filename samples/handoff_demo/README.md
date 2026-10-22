# Licensing portal: developer handoff

This starter implements **ADR-001: Application architecture for the licensing portal** (simulated client "Agency X").

## Architecture intent
- One deployable web application (modular monolith) with internal modules: applications, documents, workflow, payments.
- Managed relational database, object storage for documents, scheduled jobs for the nightly finance and student data integrations, and a small adapter for the real-time payment provider.
- Sign-in through the existing identity provider (OIDC). Data stays in US regions. WCAG 2.1 AA for every user-facing page.
- Candidate platform for this pack: **Azure** (App Service, Azure SQL, Blob Storage, Key Vault, Application Insights). The ADR leaves Azure vs AWS open, so this choice must be validated.

## What is in the pack
| File | Purpose |
|---|---|
| 01_scaffold.md | Folder structure mapped to ADR modules |
| 02_openapi.yaml | API contract for the portal |
| 03_main.tf | Terraform starter for the Azure resources |
| 04_diagram.mmd | Mermaid diagram of the deployed components |
| 06_compliance_checklist.md | What a reviewer checks before use |

## Assumptions
- ASSUMPTION: peak concurrency stays below 500 users during the filing window.
- ASSUMPTION: scanned files total under 5 TB.
- ASSUMPTION: Python web stack; replace with the team's approved stack if different.

## Local setup
1. Copy `.env.example` to `.env` and fill values from your secret store or pipeline variables. Never commit `.env`.
2. Set `OIDC_ISSUER_URL=<IDP_ISSUER_URL>` and `OIDC_CLIENT_ID=<CLIENT_ID>` for a non-production identity provider tenant.
3. Run the app locally against a local database container, then open http://localhost:8000.
4. Run contract tests against `api/openapi.yaml`.

## Deploying the infrastructure (sandbox only)
```bash
cd infra/terraform
terraform init
terraform plan -var="subscription_id=<SUBSCRIPTION_ID>" -var="environment=dev" -var="location=eastus2"
```
REVIEW: do not apply to any shared or production subscription until the checklist is complete.

## Open questions carried from the ADR
- Availability target and RTO/RPO (drives storage replication and database tier)
- Records retention period and audit logging scope
- Expected file volume growth
- Final cloud platform (Azure or AWS)

## Review notes
All files in this pack are AI-generated drafts. Each one must be reviewed against ADR-001 and the compliance checklist before use.
