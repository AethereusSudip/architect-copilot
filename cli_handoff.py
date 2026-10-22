"""Headless run of the Use Case 2 handoff pipeline (auto-reviews; for testing only)."""
import sys

from pipeline import handoff

mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
inputs = handoff.demo_inputs()
ctx = {"target_cloud": inputs["target_cloud"], "names": inputs["names"], "guardrails": handoff.DEFAULT_GUARDRAILS}
ctx["extract"] = handoff.extract(mode, inputs["adr"], ctx["target_cloud"], ctx["names"], ctx["guardrails"])
artifacts, reviews = {}, {}
for kind in handoff.ARTIFACTS:
    artifacts[kind] = {**handoff.generate(mode, kind, ctx), "version": 1}
    reviews[kind] = handoff.review(mode, kind, artifacts[kind], ctx)
    print(f"{kind:10} v1 {handoff.worst_status(reviews[kind])}")

saved = handoff.demo_meta()["refine"]
new = handoff.refine(mode, saved["kind"], artifacts[saved["kind"]], saved["instruction"], ctx)
artifacts[saved["kind"]] = {**new, "version": 2}
reviews[saved["kind"]] = handoff.review(mode, saved["kind"], artifacts[saved["kind"]], ctx)
print(f"{saved['kind']:10} v2 {handoff.worst_status(reviews[saved['kind']])} (after: {saved['instruction']})")

folder, _ = handoff.package(ctx, artifacts, reviews)
print("Exported to", folder)
