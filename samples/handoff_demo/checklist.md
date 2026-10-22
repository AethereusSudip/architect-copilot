# Architecture compliance checklist: licensing portal handoff

Tick an item only after you have checked it yourself. Each item traces to ADR-001 or a security guardrail.

## ADR alignment
- [ ] Single deployable web application; no separately deployed services per module (ADR decision)
- [ ] Module boundaries enforced: modules call each other only through service interfaces (ADR consequence)
- [ ] Nightly integrations implemented as scheduled jobs, payment as a real-time adapter (ADR decision)
- [ ] Cloud services used are only the candidates named in the ADR, and the platform choice has been validated
- [ ] Any deviation from ADR-001 is recorded as an ADR change, not made silently in code

## NFRs
- [ ] All resources deploy to US regions only (Terraform `location` validation in place)
- [ ] Scale-out rule and load test cover the two-week filing window peak
- [ ] WCAG 2.1 AA checks are part of the UI definition of done
- [ ] Availability, RTO/RPO and retention targets agreed and reflected in SKUs and replication (open in ADR)

## Security
- [ ] No secrets, keys or passwords in code, Terraform or config files; all secrets in Key Vault
- [ ] App reads secrets through a managed identity and Key Vault references
- [ ] Sign-in only via the existing identity provider (OIDC); reviewer endpoints require the reviewer role
- [ ] TLS 1.2+ enforced on the web app, database and storage; storage containers are private
- [ ] No card data stored; payment uses the provider's redirect flow

## Observability
- [ ] Application Insights connected for the web app and the nightly jobs
- [ ] Audit events written for submissions, document uploads and approval decisions (scope to confirm)
- [ ] Alerts defined for failed nightly jobs, payment errors and peak-window latency

## Safe AI usage
- [ ] Every generated file carries the AI-generated draft label until reviewed
- [ ] Service names, SKUs and limits checked against official documentation (no invented values)
- [ ] `terraform validate` / `plan` run in a sandbox and the OpenAPI file linted before use
- [ ] No client names, personal data, private URLs or production values in any artifact
