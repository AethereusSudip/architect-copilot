"""Headless run of the whole pipeline (auto-approves; for testing only)."""
import sys

from pipeline import render, safety, stages

mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
brief = open("samples/brief.md", encoding="utf-8").read()
assert not safety.sanitize_check(brief), "brief failed sanitization"
state = {"brief": brief, "approved_assumptions": True}
state["intake"] = stages.intake(mode, brief)
state["clarify"] = stages.clarify(mode, state["intake"])
state["options"] = stages.options(mode, state["intake"], {})
state["tradeoff"] = stages.tradeoff(mode, state["options"])
state["recommendation"] = stages.recommend(mode, state["options"], state["tradeoff"])
sel = state["recommendation"]["recommended_id"]
state["approved_option"] = sel
state["adr"] = stages.adr(mode, state["intake"], state["options"], state["recommendation"], sel)
state["diagram"] = stages.diagram(mode, state["options"], sel)
state["summary"] = stages.summary(mode, state["recommendation"], sel)
state["risk"] = safety.owasp_review(mode, state)
state["approved_adr"] = True
print("Exported to", render.export(state))
print("Guardrails:", safety.static_checks(state))
