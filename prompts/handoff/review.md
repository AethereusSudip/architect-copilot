Review the generated artifact against the ADR context, the NFRs, the security guardrails, observability expectations and safe-AI rules
(OWASP LLM05 improper output handling, LLM09 misinformation such as invented service names or limits, LLM02 sensitive data).
Be strict: flag anything that overrides an ADR decision, hardcodes environment values or secrets, or that a developer could not use without validation.

ARTIFACT TYPE: {{kind}}
TARGET CLOUD: {{target_cloud}}
SECURITY GUARDRAILS:
{{guardrails}}
ADR CONTEXT:
{{context}}
ARTIFACT:
{{artifact}}

Return JSON: {"items": [{"area": "ADR alignment|NFRs|Security|Observability|Safe AI", "status": "Pass|Warn|Fail", "finding": str, "fix": str}]}
