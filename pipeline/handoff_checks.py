"""Deterministic checks on generated handoff artifacts. They do not depend on the model."""
import re

from .safety import PII_PATTERNS

DRAFT = "AI-GENERATED DRAFT - REVIEW REQUIRED. Not approved for use until an architect has reviewed it."

SECRET_PATTERNS = {
    "cloud access key": r"\bAKIA[0-9A-Z]{16}\b",
    "private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "storage account key": r"(?i)AccountKey=[A-Za-z0-9+/=]{20,}",
    "API token": r"\b(sk-[A-Za-z0-9-]{16,}|ghp_[A-Za-z0-9]{20,}|xox[bp]-[A-Za-z0-9-]{10,})",
}
# A quoted literal assigned to a secret-looking key, e.g. password = "abc123"
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b\w*(password|passwd|secret|api_?key|access_?key|token|conn(?:ection)?_?string)\w*[\"']?\s*[:=]\s*[\"']([^\"'\n]+)[\"']")
PLACEHOLDER = re.compile(r"(?i)(<[A-Z0-9_ -]+>|\$\{|\{\{|var\.|CHANGE_?ME|REPLACE|@Microsoft\.KeyVault|example|placeholder)")
PRIVATE_IP = re.compile(r"\b(10\.\d{1,3}|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b(?!/)")
INTERNAL_HOST = re.compile(r"(?i)\b[\w-]+\.(internal|corp|lan|intranet)\b")
URL = re.compile(r"https?://([^/\s\"'<>)]+)")
ALLOWED_HOSTS = re.compile(r"(?i)^(localhost|127\.0\.0\.1|[\w.-]*example\.(com|org|net)|registry\.terraform\.io|spec\.openapis\.org)(:\d+)?$")
OTHER_CLOUD = {
    "Azure": re.compile(r"provider\s+\"aws\"|resource\s+\"aws_"),
    "AWS": re.compile(r"provider\s+\"azurerm\"|resource\s+\"azurerm_"),
}


def run(kind, content, target_cloud, rejected_terms=()):
    """Return [(check, status, detail)] with status Pass, Warn or Fail."""
    checks = []

    hits = [label for label, pattern in SECRET_PATTERNS.items() if re.search(pattern, content)]
    hits += [f"literal value for '{m.group(0).split('=')[0].split(':')[0].strip()}'"
             for m in SECRET_ASSIGNMENT.finditer(content) if not PLACEHOLDER.search(m.group(2))]
    checks.append(("No hardcoded secrets", "Fail" if hits else "Pass",
                   "Found " + "; ".join(hits) + ". Move it to the secret store or a variable." if hits else ""))

    private = PRIVATE_IP.findall(content) and ["private IP address"] or []
    private += [m.group(0) for m in INTERNAL_HOST.finditer(content)]
    checks.append(("No private hosts or IP addresses", "Fail" if private else "Pass",
                   "Found: " + ", ".join(sorted(set(private))) + ". Replace with <PLACEHOLDER>." if private else ""))

    urls = sorted({h for h in (u.rstrip(".,;:") for u in URL.findall(content)) if not ALLOWED_HOSTS.match(h)})
    checks.append(("URLs are placeholders or configuration", "Warn" if urls else "Pass",
                   "Hardcoded host(s): " + ", ".join(urls) + ". Use <PLACEHOLDER> or a config key unless it is a public reference."
                   if urls else ""))

    pii = [label for label, pattern in PII_PATTERNS.items()
           if label in ("email address", "SSN-style number") and re.search(pattern, content)]
    checks.append(("No personal data", "Fail" if pii else "Pass", ", ".join(pii)))

    if kind in ("iac", "api", "scaffold"):
        uses = bool(PLACEHOLDER.search(content))
        checks.append(("Environment values are variables or placeholders", "Pass" if uses else "Warn",
                       "" if uses else "No variables or <PLACEHOLDER> values found; check for hardcoded environment values."))

    if kind == "iac":
        wrong = OTHER_CLOUD.get(target_cloud)
        bad = bool(wrong and wrong.search(content))
        checks.append((f"Matches target cloud ({target_cloud})", "Fail" if bad else "Pass",
                       "Resources for a different cloud were generated." if bad else ""))

    lower = content.lower()
    found = [t for t in rejected_terms if re.search(r"\b" + re.escape(t.lower()), lower)]
    checks.append(("Does not reintroduce a rejected ADR alternative", "Warn" if found else "Pass",
                   "Mentions " + ", ".join(found) + ". Confirm it does not override the ADR, or raise an ADR change."
                   if found else ""))
    return checks


def with_banner(kind, content):
    """Prefix the draft label in the artifact's own comment syntax."""
    if kind in ("iac", "api"):
        return f"# {DRAFT}\n\n{content}"
    if kind == "diagram":
        return f"%% {DRAFT}\n{content}"
    return f"> **{DRAFT}**\n\n{content}"
