"""Use Case 2: Architecture-to-Implementation AI Coding Assistant - Streamlit page."""
import html

import streamlit as st
import streamlit.components.v1 as components

from pipeline import handoff, safety
from pipeline.handoff import ARTIFACTS

st.set_page_config(page_title="Coding Assistant", layout="wide")

S = st.session_state
S.setdefault("handoff", {})
H = S["handoff"]
H.setdefault("artifacts", {})   # kind -> {content, assumptions, conflicts, review_notes, version}
H.setdefault("reviews", {})     # kind -> {items, checks}
H.setdefault("history", {})     # kind -> [(instruction, review_notes)]

ICON = {"Pass": "✅", "Warn": "⚠️", "Fail": "❌"}

st.title("Architecture-to-Implementation Coding Assistant")
st.warning("AI-generated drafts. Sanitized or simulated data only. Every artifact must be reviewed before use.")

with st.sidebar:
    mode_label = st.radio("Mode", ["Demo (cached run)", "Live (Anthropic API)"], key="handoff_mode")
    mode = "demo" if mode_label.startswith("Demo") else "live"
    st.caption("Demo replays a saved run for the sample ADR, so it works offline.")
    st.markdown("**Progress**")
    step = 0 if "ctx" not in H else 1 if not H["artifacts"] else 2
    for i, name in enumerate(["1 ADR intake", "2 Generate artifacts", "3 Review, refine and export"]):
        st.write(("✅ " if step > i else "▶️ " if step == i else "⬜ ") + name)
    if st.button("Reset", key="handoff_reset"):
        S["handoff"] = {}
        st.rerun()

# ---- Step 1: ADR intake ---------------------------------------------------
st.header("1. ADR and handoff inputs")
demo = handoff.demo_inputs()
uc1 = S.get("state", {})
sources = ["Sample ADR", "Paste my own ADR"]
if uc1.get("approved_adr"):
    sources.insert(0, "ADR approved in Use Case 1")
locked = "ctx" in H
source = st.radio("ADR source", sources, horizontal=True, disabled=locked)
default_adr = uc1["adr"]["markdown"] if source.startswith("ADR approved") else "" if source.startswith("Paste") else demo["adr"]
adr = st.text_area("Sanitized ADR or architecture brief", value=H.get("adr", default_adr), height=260, disabled=locked)
c1, c2 = st.columns(2)
with c1:
    clouds = ["Azure", "AWS"]
    target_cloud = st.selectbox("Target cloud", clouds, index=clouds.index(H.get("target_cloud", demo["target_cloud"])),
                                disabled=locked)
    names = st.text_input("Resource / API naming", value=H.get("names", demo["names"]), disabled=locked)
with c2:
    guardrails = st.text_area("Security guardrails", value=H.get("guardrails", handoff.DEFAULT_GUARDRAILS), height=150,
                              disabled=locked)

if not locked:
    findings = safety.sanitize_check(adr + "\n" + names)
    if mode == "demo" and (adr.strip() != demo["adr"].strip() or target_cloud != demo["target_cloud"]):
        st.info("Demo mode replays the saved run for the sample ADR on Azure. Switch to Live to use your own ADR or cloud.")
    if findings:
        st.error("Possible sensitive data found: " + ", ".join(findings) + ". Remove it before continuing.")
    elif st.button("Extract decisions", type="primary", disabled=not adr.strip()):
        with st.spinner("Extracting decisions, constraints and NFRs..."):
            H.update(adr=adr, target_cloud=target_cloud, names=names, guardrails=guardrails)
            H["ctx"] = {"target_cloud": target_cloud, "names": names, "guardrails": guardrails}
            H["ctx"]["extract"] = handoff.extract(mode, adr, target_cloud, names, guardrails)
        st.rerun()

if "ctx" in H:
    ctx = H["ctx"]
    ex = ctx["extract"]
    st.subheader(ex.get("title", "Extracted ADR context"))
    if "accepted" not in ex.get("status", "").lower() and "approved" not in ex.get("status", "").lower():
        st.warning(f"ADR status is **{ex.get('status', 'unknown')}**. Treat everything below as a draft until the ADR is approved.")
    for c in ex.get("conflicts", []):
        st.error("Conflict: " + c)
    cols = st.columns(3)
    groups = [("Decisions", "decisions"), ("Rejected alternatives", "rejected_alternatives"), ("Constraints", "constraints"),
              ("NFRs", "nfrs"), ("Components and integrations", None), ("Open questions", "open_questions")]
    for i, (title, key) in enumerate(groups):
        with cols[i % 3]:
            st.markdown(f"**{title}**")
            items = ex.get(key, []) if key else ex.get("components", []) + ex.get("integrations", [])
            for item in items:
                st.write("• " + item)

# ---- Step 2: generate -----------------------------------------------------
def _generate(kinds, comments=""):
    for kind in kinds:
        art = handoff.generate(mode, kind, ctx, comments)
        art["version"] = 1
        H["artifacts"][kind] = art
        H["reviews"][kind] = handoff.review(mode, kind, art, ctx)
        H["history"][kind] = []


if "ctx" in H:
    st.header("2. Generate artifacts")
    c1, c2 = st.columns([1, 2])
    with c1:
        kind = st.selectbox("Artifact", list(ARTIFACTS), format_func=lambda k: ARTIFACTS[k]["label"])
        st.caption(ARTIFACTS[kind]["brief"])
    with c2:
        comments = st.text_area(
            "Guidance comments (optional, comment-driven generation)",
            placeholder="# endpoint: GET /applications/{id}/status returns status and last update\n"
                        "# resource: storage container for scanned migration files, private",
            height=110)
    b1, b2 = st.columns(2)
    if b1.button(f"Generate {ARTIFACTS[kind]['label']}", type="primary"):
        with st.spinner("Generating and self-reviewing..."):
            _generate([kind], comments)
        st.rerun()
    if b2.button("Generate all six"):
        with st.spinner("Generating and self-reviewing all artifacts..."):
            _generate(list(ARTIFACTS), comments)
        st.rerun()

# ---- Step 3: review, refine, export ---------------------------------------
if H["artifacts"]:
    st.header("3. Review and refine")
    kinds = [k for k in ARTIFACTS if k in H["artifacts"]]
    tabs = st.tabs([f"{ICON[handoff.worst_status(H['reviews'][k])]} {ARTIFACTS[k]['label']}" for k in kinds])
    for tab, kind in zip(tabs, kinds):
        art, rev = H["artifacts"][kind], H["reviews"][kind]
        with tab:
            st.caption(f"Draft v{art['version']} - {ARTIFACTS[kind]['file']} - AI-generated, review required")
            left, right = st.columns([3, 2])
            with left:
                if kind == "diagram":
                    components.html(
                        f'<pre class="mermaid">{html.escape(art["content"])}</pre>'
                        '<script type="module">import m from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";'
                        'm.initialize({startOnLoad:true});</script>', height=420, scrolling=True)
                if ARTIFACTS[kind]["lang"] == "markdown":
                    with st.expander("Rendered", expanded=True):
                        st.markdown(art["content"])
                st.code(art["content"], language=ARTIFACTS[kind]["lang"])
            with right:
                st.markdown("**Self-review (model)**")
                for item in rev["items"]:
                    st.write(f"{ICON.get(item['status'], '•')} **{item['area']}**: {item['finding']}")
                    if item["status"] != "Pass":
                        st.caption("Fix: " + item["fix"])
                st.markdown("**Deterministic checks**")
                for name, status, detail in rev["checks"]:
                    st.write(f"{ICON[status]} {name}")
                    if detail:
                        st.caption(detail)
                for c in art.get("conflicts", []):
                    st.error("ADR conflict surfaced: " + c)
                if art.get("assumptions"):
                    st.markdown("**Assumptions**")
                    for a in art["assumptions"]:
                        st.write("• " + a)
                st.caption("Review notes: " + art.get("review_notes", ""))

            st.markdown("**Refine**")
            for n, (instr, notes) in enumerate(H["history"][kind], start=2):
                st.chat_message("user").write(instr)
                st.chat_message("assistant").write(f"v{n}: {notes}")
            demo_refine = handoff.demo_meta()["refine"]
            hint = demo_refine["instruction"] if mode == "demo" and demo_refine["kind"] == kind else ""
            instruction = st.text_input("Ask for a change", value=hint, key=f"refine_{kind}",
                                        placeholder="e.g. add a health check endpoint, use private endpoints for storage")
            if st.button("Apply change", key=f"apply_{kind}", disabled=not instruction.strip()):
                with st.spinner("Refining and re-running the self-review..."):
                    new = handoff.refine(mode, kind, art, instruction, ctx)
                if new is None:
                    st.info("Demo mode has a saved refinement only for the Terraform starter. Switch to Live to refine this artifact.")
                else:
                    new["version"] = art["version"] + 1
                    H["artifacts"][kind] = new
                    H["reviews"][kind] = handoff.review(mode, kind, new, ctx)
                    H["history"][kind].append((instruction, new.get("review_notes", "")))
                    st.rerun()

    st.header("4. Handoff package")
    missing = [ARTIFACTS[k]["label"] for k in ARTIFACTS if k not in H["artifacts"]]
    if missing:
        st.info("Not generated yet: " + ", ".join(missing) + ". You can still export what you have.")
    statuses = {k: handoff.worst_status(r) for k, r in H["reviews"].items()}
    fails = [ARTIFACTS[k]["label"] for k, s in statuses.items() if s == "Fail"]
    if fails:
        st.error("Failing checks in: " + ", ".join(fails) + ". Refine them, or export and resolve them before use.")
    reviewed = st.checkbox("I have reviewed these drafts and understand they are not approved for use.")
    if st.button("Build handoff package", type="primary", disabled=not reviewed):
        folder, data = handoff.package(ctx, H["artifacts"], H["reviews"])
        H["package"] = (folder.name, data)
    if H.get("package"):
        name, data = H["package"]
        st.success(f"Package ready: {name}.zip (also saved under outputs/)")
        st.download_button("Download handoff package (.zip)", data, file_name=f"{name}.zip", mime="application/zip")
