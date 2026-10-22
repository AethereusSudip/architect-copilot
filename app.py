"""Architecture Decision & Risk Review Agent - Streamlit demo."""
import html
import pathlib

import streamlit as st
import streamlit.components.v1 as components

from pipeline import render, safety, stages

ROOT = pathlib.Path(__file__).parent
st.set_page_config(page_title="Architect Co-pilot", layout="wide")

S = st.session_state
S.setdefault("step", 0)
S.setdefault("state", {})
state = S["state"]

st.title("Architecture Decision & Risk Review Agent")
st.warning("AI-generated drafts. Sanitized or simulated data only. The architect makes every final decision.")

with st.sidebar:
    mode_label = st.radio("Mode", ["Demo (cached run)", "Live (Anthropic API)"])
    mode = "demo" if mode_label.startswith("Demo") else "live"
    st.caption("Demo replays a saved run, so it works offline.")
    st.markdown("**Progress**")
    for i, name in enumerate(["1 Intake", "2 Clarify", "3 Options & recommendation", "4 ADR, diagram, risk review", "5 Export"]):
        st.write(("✅ " if S["step"] > i else "▶️ " if S["step"] == i else "⬜ ") + name)
    if st.button("Reset"):
        S["step"], S["state"] = 0, {}
        st.rerun()

# ---- Step 0: intake -------------------------------------------------------
st.header("1. Requirement intake")
sample = (ROOT / "samples" / "brief.md").read_text(encoding="utf-8")
brief = st.text_area("Sanitized requirement brief", value=state.get("brief", sample), height=260, disabled=S["step"] > 0)
if S["step"] == 0:
    findings = safety.sanitize_check(brief)
    if findings:
        st.error("Possible sensitive data found: " + ", ".join(findings) + ". Remove it before continuing.")
    elif st.button("Analyse brief", type="primary"):
        with st.spinner("Extracting requirements..."):
            state["brief"] = brief
            state["intake"] = stages.intake(mode, brief)
            state["clarify"] = stages.clarify(mode, state["intake"])
        S["step"] = 1
        st.rerun()

# ---- Step 1: clarify + approve assumptions --------------------------------
if S["step"] >= 1:
    intake = state["intake"]
    cols = st.columns(5)
    for col, key in zip(cols, ["functional", "nfrs", "constraints", "assumptions", "unknowns"]):
        with col:
            st.subheader(key.title())
            for item in intake[key]:
                st.write("• " + item)
    st.header("2. Clarifying questions")
    answers = {}
    for i, q in enumerate(state["clarify"]["questions"]):
        answers[q["q"]] = st.text_input(q["q"], key=f"ans{i}", help=q["why"], disabled=S["step"] > 1)
    if S["step"] == 1:
        ok = st.checkbox("I approve the extracted assumptions (answers may be left blank in the demo).")
        if st.button("Approve assumptions and generate options", type="primary", disabled=not ok):
            state["approved_assumptions"] = True
            state["answers"] = answers
            with st.spinner("Generating options, trade-offs and recommendation..."):
                state["options"] = stages.options(mode, intake, answers)
                state["tradeoff"] = stages.tradeoff(mode, state["options"])
                state["recommendation"] = stages.recommend(mode, state["options"], state["tradeoff"])
            S["step"] = 2
            st.rerun()

# ---- Step 2: options + approve option -------------------------------------
if S["step"] >= 2:
    st.header("3. Options, trade-offs and recommendation")
    for opt in state["options"]["options"]:
        with st.expander(f"Option {opt['id']}: {opt['name']}", expanded=True):
            st.write(opt["summary"])
            st.caption("Candidate services (to validate) - Azure: " + ", ".join(opt["candidate_services"]["azure"])
                       + " | AWS: " + ", ".join(opt["candidate_services"]["aws"]))
    st.markdown(render.comparison_md(state))
    rec = state["recommendation"]
    st.success(f"Recommended: Option {rec['recommended_id']} (candidate) - confidence: {rec['confidence']}")
    st.write(rec["rationale"])
    st.write("**Risks:** " + "; ".join(rec["risks"]))
    st.caption("Review notes: " + rec["review_notes"])
    ids = [o["id"] for o in state["options"]["options"]]
    choice = st.selectbox("Selected option", ids, index=ids.index(rec["recommended_id"]), disabled=S["step"] > 2)
    if S["step"] == 2 and st.button("Approve selected option", type="primary"):
        state["approved_option"] = choice
        with st.spinner("Drafting ADR, diagram, summary and risk review..."):
            state["adr"] = stages.adr(mode, state["intake"], state["options"], rec, choice)
            state["diagram"] = stages.diagram(mode, state["options"], choice)
            state["summary"] = stages.summary(mode, rec, choice)
            state["risk"] = safety.owasp_review(mode, state)
        S["step"] = 3
        st.rerun()

# ---- Step 3: artifacts + approve ADR --------------------------------------
if S["step"] >= 3:
    st.header("4. Draft artifacts")
    t1, t2, t3, t4 = st.tabs(["ADR", "Diagram", "OWASP LLM risk review", "Client summary"])
    with t1:
        st.markdown(state["adr"]["markdown"])
    with t2:
        mermaid = state["diagram"]["mermaid"]
        components.html(
            f'<pre class="mermaid">{html.escape(mermaid)}</pre>'
            '<script type="module">import m from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";m.initialize({startOnLoad:true});</script>',
            height=420, scrolling=True)
        st.code(mermaid, language="text")
        st.caption("Diagram prompt for Eraser / draw.io:")
        st.write(state["diagram"]["prompt"])
    with t3:
        st.markdown(render.risk_md(state))
        st.markdown("**Guardrail checks**")
        for label, ok in safety.static_checks(state):
            st.write(("✅ " if ok else "⏳ ") + label)
    with t4:
        st.markdown(render.summary_md(state))
    if S["step"] == 3:
        if st.checkbox("I have reviewed and approve this ADR.") and st.button("Approve ADR and export", type="primary"):
            state["approved_adr"] = True
            state["export_dir"] = str(render.export(state, str(ROOT / "outputs")))
            S["step"] = 4
            st.rerun()

if S["step"] >= 4:
    st.header("5. Exported")
    st.success(f"Saved to {state['export_dir']}")
    st.write(sorted(p.name for p in pathlib.Path(state["export_dir"]).iterdir()))
    st.info("Next: open **Coding Assistant** in the sidebar to turn this approved ADR into a developer handoff package.")
