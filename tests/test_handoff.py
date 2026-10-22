"""Use Case 2 tests: deterministic checks and the Demo-mode pipeline."""
import io
import zipfile

from pipeline import handoff, handoff_checks


def status(checks, name):
    return next(s for n, s, _ in checks if n.startswith(name))


def test_flags_hardcoded_secret_but_not_references():
    bad = handoff_checks.run("iac", 'administrator_login_password = "P@ssw0rd123!"', "Azure")
    good = handoff_checks.run("iac", 'administrator_login_password = random_password.sql.result\n'
                                     'DB_PASSWORD = "@Microsoft.KeyVault(SecretUri=${x.id})"\npassword = "<DB_PASSWORD>"', "Azure")
    assert status(bad, "No hardcoded secrets") == "Fail"
    assert status(good, "No hardcoded secrets") == "Pass"


def test_flags_known_key_formats():
    assert status(handoff_checks.run("readme", "key AKIAABCDEFGHIJKLMNOP", "AWS"), "No hardcoded secrets") == "Fail"


def test_private_hosts_and_urls():
    checks = handoff_checks.run("readme", "db at 10.1.2.3 and app.corp; see https://api.client.com and http://localhost:8000.", "Azure")
    assert status(checks, "No private hosts") == "Fail"
    assert status(checks, "URLs are placeholders") == "Warn"
    clean = handoff_checks.run("readme", "https://<API_HOST>/v1, vnet 10.0.0.0/16, http://localhost:8000", "Azure")
    assert status(clean, "No private hosts") == "Pass"
    assert status(clean, "URLs are placeholders") == "Pass"


def test_wrong_cloud_and_rejected_alternative():
    checks = handoff_checks.run("iac", 'resource "aws_s3_bucket" "x" {} # microservices', "Azure", ["microservice"])
    assert status(checks, "Matches target cloud") == "Fail"
    assert status(checks, "Does not reintroduce") == "Warn"


def test_banner_uses_artifact_comment_syntax():
    assert handoff_checks.with_banner("iac", "x").startswith("# AI-GENERATED DRAFT")
    assert handoff_checks.with_banner("diagram", "flowchart LR").startswith("%% AI-GENERATED DRAFT")
    assert handoff_checks.with_banner("readme", "x").startswith("> **AI-GENERATED DRAFT")


def _demo_ctx():
    i = handoff.demo_inputs()
    ctx = {"target_cloud": i["target_cloud"], "names": i["names"], "guardrails": handoff.DEFAULT_GUARDRAILS}
    ctx["extract"] = handoff.extract("demo", i["adr"], ctx["target_cloud"], ctx["names"], ctx["guardrails"])
    return ctx


def test_demo_pipeline_catches_then_fixes_secret(tmp_path):
    ctx = _demo_ctx()
    arts = {k: {**handoff.generate("demo", k, ctx), "version": 1} for k in handoff.ARTIFACTS}
    revs = {k: handoff.review("demo", k, arts[k], ctx) for k in arts}
    assert handoff.worst_status(revs["iac"]) == "Fail"
    assert all(s != "Fail" for k, r in revs.items() if k != "iac" for _, s, _ in r["checks"])

    new = handoff.refine("demo", "iac", arts["iac"], "use key vault", ctx)
    arts["iac"] = {**new, "version": 2}
    revs["iac"] = handoff.review("demo", "iac", arts["iac"], ctx)
    assert handoff.worst_status(revs["iac"]) == "Warn"
    assert handoff.refine("demo", "api", arts["api"], "x", ctx) is None

    folder, data = handoff.package(ctx, arts, revs, base=tmp_path)
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert "handoff/00_HANDOFF.md" in names and "handoff/03_main.tf" in names and len(names) == 8
    assert (folder / "03_main.tf").read_text().startswith("# AI-GENERATED DRAFT")
    assert "P@ssw0rd" not in (folder / "03_main.tf").read_text()
