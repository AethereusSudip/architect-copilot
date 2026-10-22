# Architect Co-pilot

Two capstone PoCs in one Streamlit app:
- **Use Case 1, Architecture Decision & Risk Review Agent** (main page `app`): requirement brief to an approved ADR.
- **Use Case 2, Architecture-to-Implementation Coding Assistant** (page **Coding Assistant**): approved ADR to a developer handoff package.

## Use Case 1: Architecture Decision & Risk Review Agent

A PoC agent that takes a sanitized requirement brief and walks a Solution Architect through
requirements → options → trade-offs → recommendation → ADR → diagram → client summary,
with OWASP LLM Top 10 checks. **The architect approves at three gates; the agent never finalizes anything.**

## Workflow
1. **Intake** – extract functional requirements, NFRs, constraints, assumptions, unknowns (input is PII-checked first)
2. **Clarify** – 3–5 high-value questions → *Gate 1: approve assumptions*
3. **Options** – 2+ architectures grounded in `knowledge/cloud_patterns.json`, scored on 7 criteria
4. **Recommend** – rationale, risks, confidence → *Gate 2: approve option*
5. **Artifacts** – ADR, Mermaid diagram + Eraser/draw.io prompt, client summary (3–5 slides), OWASP LLM review → *Gate 3: approve ADR*
6. **Export** – Markdown files in `outputs/run_<timestamp>/`

## Use Case 2: Architecture-to-Implementation Coding Assistant
Takes the ADR approved in Use Case 1 (or the sample, or a pasted ADR) plus a target cloud, naming and security guardrails, and produces a reviewable handoff package.

1. **Extract** – approved decisions, rejected alternatives, constraints, NFRs, components, integrations, deployment targets, open questions and conflicts; warns when the ADR is not yet approved
2. **Generate** – pick one artifact or all six; optional guidance comments are turned into code/template blocks
3. **Self-review** – every artifact gets a model review (ADR alignment, NFRs, security, observability, safe AI) *and* deterministic checks that do not depend on the model: hardcoded secrets, private hosts/IPs, hardcoded URLs, personal data, variables/placeholders, wrong cloud provider, reintroduced rejected alternatives
4. **Refine** – chat-style change requests per artifact; each one creates a new version and re-runs the review. Conflicts with the ADR are surfaced, not applied silently
5. **Package** – after the reviewer confirms, download a zip: `00_HANDOFF.md` (contents, open findings, review steps), the six artifacts with an *AI-generated draft* label in each file's own comment syntax, and `07_self_review.json`

| Artifact | File |
|---|---|
| Project scaffold | `01_scaffold.md` |
| API contract (OpenAPI 3) | `02_openapi.yaml` |
| IaC starter (Terraform) | `03_main.tf` |
| Diagram-as-code (Mermaid) | `04_diagram.mmd` |
| README | `05_README.md` |
| Compliance checklist | `06_compliance_checklist.md` |

**Demo story:** the cached run's first Terraform draft hardcodes the SQL admin password, so both reviews fail it. Apply the suggested change on the Terraform tab and v2 moves the secret to Key Vault with a managed identity, and the check passes. Both demo Terraform files pass `terraform validate`.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py          # both pages; sidebar: Demo (cached, no key) or Live
python cli.py demo            # headless smoke test, Use Case 1
python cli_handoff.py demo    # headless smoke test, Use Case 2
pip install pytest && python -m pytest -q
```
Live mode: copy `.env.example`, set `ANTHROPIC_API_KEY`, export it, pick **Live** in the sidebar.

## Layout
```
app.py                       Use Case 1 UI with the three approval gates
pages/2_Coding_Assistant.py  Use Case 2 UI
cli.py, cli_handoff.py       headless runs
pipeline/                    llm.py (demo/live), stages.py, safety.py, render.py,
                             handoff.py (Use Case 2 stages + packaging), handoff_checks.py (deterministic checks)
prompts/                     one prompt template per stage; prompts/handoff/ for Use Case 2
knowledge/                   cloud_patterns.json, owasp_llm_top10.json
samples/                     brief.md (simulated), demo_run.json (cached run), handoff_demo/ (cached Use Case 2 run)
tests/                       Use Case 2 checks and demo pipeline
```

## Guardrails (PoC constraints)
- Simulated or sanitized input only; emails, phones, IDs and secrets are blocked before analysis
- Every output shows assumptions, confidence and review notes under an "AI-generated draft" banner
- Cloud services are framed as candidates to validate
- No auto-finalization: exports are blocked until all three approvals are given
- Use Case 2: generated files use variables and `<PLACEHOLDER>` values, never secrets; every file is labelled as a draft; the package downloads only after the reviewer confirms; model-generated Mermaid is HTML-escaped before rendering
