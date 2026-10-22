Revise the artifact below according to the architect's instruction, keeping it grounded in the ADR context.
If the instruction contradicts an ADR decision or a security guardrail, keep the ADR/guardrail, explain it under "conflicts", and apply the rest.
Keep placeholders instead of secrets or environment-specific values. Keep "ASSUMPTION:" and "REVIEW:" comments up to date.

ARTIFACT TYPE: {{kind}}
INSTRUCTION: {{instruction}}
TARGET CLOUD: {{target_cloud}}
SECURITY GUARDRAILS:
{{guardrails}}
ADR CONTEXT:
{{context}}
CURRENT ARTIFACT:
{{artifact}}

Return JSON: {"content": str (the full revised artifact), "assumptions": [str], "conflicts": [str], "review_notes": str (what changed and what to verify)}
