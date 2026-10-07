"""Turn the pipeline state into Markdown files the architect can review."""
import datetime
import pathlib

BANNER = "> **AI-generated draft. Architect review and approval required.**\n\n"


def comparison_md(state):
    matrix = state["tradeoff"]
    opts = {o["id"]: o["name"] for o in state["options"]["options"]}
    crit = matrix["criteria"]
    lines = ["| Criterion | " + " | ".join(opts.values()) + " |",
             "|---|" + "---|" * len(opts)]
    for c in crit:
        row = [f"{matrix['scores'][oid][c]['score']}/5 - {matrix['scores'][oid][c]['note']}"
               for oid in opts]
        lines.append(f"| {c} | " + " | ".join(row) + " |")
    return "\n".join(lines)


def requirements_md(state):
    data = state["intake"]
    out = ["# Extracted requirements\n"]
    for key in ("functional", "nfrs", "constraints", "assumptions", "unknowns"):
        out.append(f"## {key.title()}")
        out += [f"- {item}" for item in data.get(key, [])]
        out.append("")
    return "\n".join(out)


def risk_md(state):
    out = ["# OWASP LLM Top 10 and safe-use review\n", "| ID | Risk | Status | Finding | Control |", "|---|---|---|---|---|"]
    for r in state["risk"]["items"]:
        out.append(f"| {r['id']} | {r['name']} | {r['status']} | {r['finding']} | {r['control']} |")
    return "\n".join(out)


def summary_md(state):
    out = ["# Client summary (slide outline)\n"]
    for i, s in enumerate(state["summary"]["slides"], 1):
        out.append(f"## Slide {i}: {s['title']}")
        out += [f"- {b}" for b in s["bullets"]]
        out.append("")
    return "\n".join(out)


def export(state, base="outputs"):
    folder = pathlib.Path(base) / datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)
    rec = state["recommendation"]
    files = {
        "01_requirements.md": requirements_md(state),
        "02_option_comparison.md": comparison_md(state),
        "03_recommendation.md": f"# Recommendation\n\n{rec['rationale']}\n\n**Confidence:** {rec['confidence']}\n\n"
                               + "\n".join(f"- Risk: {r}" for r in rec["risks"])
                               + "\n\n**Review notes:** " + rec["review_notes"],
        "04_adr.md": state["adr"]["markdown"],
        "05_diagram.mmd": state["diagram"]["mermaid"],
        "05_diagram_prompt.md": state["diagram"]["prompt"],
        "06_risk_checklist.md": risk_md(state),
        "07_client_summary.md": summary_md(state),
    }
    for name, body in files.items():
        (folder / name).write_text(BANNER + body if name.endswith(".md") else body, encoding="utf-8")
    return folder
