"""Use Case 2: turn an approved ADR into a reviewable developer handoff package."""
import datetime
import io
import json
import pathlib
import zipfile

from . import handoff_checks
from .llm import ROOT, load_json, run_stage

DEMO_DIR = ROOT / "samples" / "handoff_demo"

ARTIFACTS = {
    "scaffold": {
        "label": "Project scaffold", "file": "01_scaffold.md", "lang": "markdown",
        "brief": "A starter folder structure as a fenced tree, one line per folder/file explaining its purpose, "
                 "mapped to the ADR components and integrations. Include .env.example keys (names only).",
    },
    "api": {
        "label": "API contract (OpenAPI)", "file": "02_openapi.yaml", "lang": "yaml",
        "brief": "An OpenAPI 3.0 YAML contract for the main functional capabilities, with schemas, error responses, "
                 "an OIDC security scheme for the identity provider and <PLACEHOLDER> server URLs.",
    },
    "iac": {
        "label": "IaC starter (Terraform)", "file": "03_main.tf", "lang": "hcl",
        "brief": "A Terraform starter for the target cloud covering the ADR's runtime, database, storage, secrets and "
                 "monitoring. All environment values are variables; secrets come from the cloud secret store.",
    },
    "diagram": {
        "label": "Diagram-as-code (Mermaid)", "file": "04_diagram.mmd", "lang": "text",
        "brief": "A valid Mermaid flowchart of the deployed components and integrations using the target cloud's "
                 "candidate services, consistent with the IaC.",
    },
    "readme": {
        "label": "README", "file": "05_README.md", "lang": "markdown",
        "brief": "A developer README: architecture intent and the ADR it implements, assumptions, local setup with "
                 "placeholders, how to deploy the IaC, and review notes / open questions.",
    },
    "checklist": {
        "label": "Compliance checklist", "file": "06_compliance_checklist.md", "lang": "markdown",
        "brief": "A Markdown checklist a reviewer ticks before use, grouped into ADR alignment, NFRs, security, "
                 "observability and safe AI usage, each item traceable to the ADR or a guardrail.",
    },
}

DEFAULT_GUARDRAILS = (
    "- No secrets in code or templates; use the cloud secret store and managed identity\n"
    "- Sign-in only through the existing identity provider (OIDC)\n"
    "- Data stays in US regions\n"
    "- Encrypt data at rest and in transit (TLS 1.2+)\n"
    "- Central logging and monitoring for every component\n"
    "- Every generated artifact is a draft until an architect reviews it"
)


# ---- demo data -------------------------------------------------------------
def demo_meta():
    return load_json("samples/handoff_demo/demo.json")


def demo_inputs():
    meta = demo_meta()
    return {"adr": load_json("samples/demo_run.json")["adr"]["markdown"], **meta["inputs"]}


def _demo_artifact(entry):
    return {**{k: v for k, v in entry.items() if k != "file"},
            "content": (DEMO_DIR / entry["file"]).read_text(encoding="utf-8")}


# ---- stages ----------------------------------------------------------------
def _ctx(ctx):
    return {"target_cloud": ctx["target_cloud"], "names": ctx["names"], "guardrails": ctx["guardrails"]}


def extract(mode, adr, target_cloud, names, guardrails):
    if mode == "demo":
        return demo_meta()["extract"]
    return run_stage("handoff/extract", mode, adr=adr, target_cloud=target_cloud, names=names, guardrails=guardrails)


def generate(mode, kind, ctx, comments=""):
    if mode == "demo":
        return _demo_artifact(demo_meta()["artifacts"][kind])
    return run_stage(
        "handoff/generate", mode, max_tokens=8000, kind=ARTIFACTS[kind]["label"],
        kind_instructions=ARTIFACTS[kind]["brief"], comments=comments or "(none)",
        context=ctx["extract"], **_ctx(ctx),
    )


def refine(mode, kind, artifact, instruction, ctx):
    """Return the revised artifact, or None when Demo mode has no saved refinement for this artifact."""
    if mode == "demo":
        saved = demo_meta()["refine"]
        return _demo_artifact(saved["result"]) if saved["kind"] == kind else None
    return run_stage(
        "handoff/refine", mode, max_tokens=8000, kind=ARTIFACTS[kind]["label"],
        instruction=instruction, artifact=artifact["content"], context=ctx["extract"], **_ctx(ctx),
    )


def review(mode, kind, artifact, ctx):
    """Self-review: the model's review plus deterministic checks that do not depend on the model."""
    if mode == "demo":
        meta = demo_meta()
        saved = meta["refine"]
        refined = saved["kind"] == kind and artifact.get("version", 1) > 1
        items = saved["review"] if refined else meta["review"][kind]
    else:
        items = run_stage(
            "handoff/review", mode, kind=ARTIFACTS[kind]["label"], artifact=artifact["content"],
            context=ctx["extract"], **_ctx(ctx),
        )["items"]
    checks = handoff_checks.run(kind, artifact["content"], ctx["target_cloud"], ctx["extract"].get("rejected_terms", []))
    return {"items": items, "checks": checks}


def worst_status(rev):
    statuses = [i["status"] for i in rev["items"]] + [c[1] for c in rev["checks"]]
    for s in ("Fail", "Warn"):
        if s in statuses:
            return s
    return "Pass"


# ---- packaging -------------------------------------------------------------
def handoff_md(ctx, artifacts, reviews):
    ex = ctx["extract"]
    out = [f"# Developer handoff: {ex.get('title', 'architecture')}\n",
           f"Generated {datetime.date.today().isoformat()} for target cloud **{ctx['target_cloud']}**. "
           f"ADR status: **{ex.get('status', 'unknown')}**.\n",
           "## Package contents\n", "| File | Artifact | Version | Self-review |", "|---|---|---|---|"]
    for kind, art in artifacts.items():
        a = ARTIFACTS[kind]
        out.append(f"| {a['file']} | {a['label']} | v{art.get('version', 1)} | {worst_status(reviews[kind])} |")
    out.append("\n## Approved decisions this package implements")
    out += [f"- {d}" for d in ex.get("decisions", [])]
    out.append("\n## Open findings to resolve before use")
    open_items = []
    for kind, rev in reviews.items():
        label = ARTIFACTS[kind]["label"]
        open_items += [f"- **{label}** ({i['status']}, {i['area']}): {i['finding']} Fix: {i['fix']}"
                       for i in rev["items"] if i["status"] != "Pass"]
        open_items += [f"- **{label}** ({status}, check): {name}. {detail}"
                       for name, status, detail in rev["checks"] if status != "Pass"]
    out += open_items or ["- None flagged. A human review is still required."]
    out.append("\n## Open questions from the ADR")
    out += [f"- {q}" for q in ex.get("open_questions", [])] or ["- None"]
    out.append("\n## How to review this package")
    out += [
        "1. Read the ADR first; every artifact must trace back to a decision listed above.",
        "2. Work through 06_compliance_checklist.md and tick each item only after checking it yourself.",
        "3. Replace every <PLACEHOLDER> and variable default with values from your approved configuration source. Never commit secrets.",
        "4. Validate candidate cloud services, SKUs and limits against your organisation's approved catalogue.",
        "5. Run `terraform validate` and `terraform plan` in a sandbox subscription/account, and lint the OpenAPI file, before any use.",
        "6. Resolve or accept every open finding above and record the outcome in the ADR review notes.",
    ]
    return "\n".join(out)


def package(ctx, artifacts, reviews, base=None):
    """Write the package to outputs/handoff_<timestamp>/ and return (folder, zip bytes)."""
    files = {ARTIFACTS[k]["file"]: handoff_checks.with_banner(k, a["content"]) for k, a in artifacts.items()}
    files["00_HANDOFF.md"] = handoff_checks.with_banner("readme", handoff_md(ctx, artifacts, reviews))
    files["07_self_review.json"] = json.dumps(
        {k: {"items": r["items"], "checks": [{"check": n, "status": s, "detail": d} for n, s, d in r["checks"]]}
         for k, r in reviews.items()}, indent=2)
    folder = pathlib.Path(base or ROOT / "outputs") / datetime.datetime.now().strftime("handoff_%Y%m%d_%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, body in sorted(files.items()):
            (folder / name).write_text(body, encoding="utf-8")
            zf.writestr(f"handoff/{name}", body)
    return folder, buf.getvalue()
