Generate one implementation handoff artifact grounded ONLY in the extracted ADR context below.
Rules:
- Follow every approved decision. If the request or comments would contradict the ADR, do not silently comply: keep the ADR decision and list the conflict under "conflicts".
- Never include real secrets, client names, private URLs, IPs or production values. Use variables, configuration keys and <PLACEHOLDER> values.
- Mark assumptions inline with comments starting "ASSUMPTION:" and things to verify with "REVIEW:".
- Target cloud: {{target_cloud}}. Use the naming given.
- Do not add a draft banner; the tool adds one.

ARTIFACT TO GENERATE: {{kind}}
WHAT IT MUST CONTAIN:
{{kind_instructions}}

ARCHITECT GUIDANCE COMMENTS (structured comments to turn into code/template blocks; may be empty):
{{comments}}

NAMING: {{names}}
SECURITY GUARDRAILS:
{{guardrails}}
ADR CONTEXT:
{{context}}

Return JSON: {"content": str (the full artifact text), "assumptions": [str], "conflicts": [str], "review_notes": str}
