# Architect Co-pilot: Architecture Decision & Risk Review Agent

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

## Run
```bash
pip install -r requirements.txt
streamlit run app.py          # sidebar: Demo (cached, no key) or Live
python cli.py demo            # headless smoke test
```
Live mode: copy `.env.example`, set `ANTHROPIC_API_KEY`, export it, pick **Live** in the sidebar.

## Layout
```
app.py            Streamlit UI with the three approval gates
cli.py            headless run
pipeline/         llm.py (demo/live), stages.py, safety.py, render.py
prompts/          one prompt template per stage
knowledge/        cloud_patterns.json, owasp_llm_top10.json
samples/          brief.md (simulated), demo_run.json (cached run)
```

## Guardrails (PoC constraints)
- Simulated or sanitized input only; emails, phones, IDs and secrets are blocked before analysis
- Every output shows assumptions, confidence and review notes under an "AI-generated draft" banner
- Cloud services are framed as candidates to validate
- No auto-finalization: exports are blocked until all three approvals are given
