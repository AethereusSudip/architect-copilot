"""Input sanitization, deterministic output checks and the OWASP LLM review."""
import re

from .llm import load_json, run_stage

PII_PATTERNS = {
    "email address": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "phone number": r"\b(?:\+?\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b",
    "SSN-style number": r"\b\d{3}-\d{2}-\d{4}\b",
    "long digit string": r"\b\d{12,}\b",
    "IP address": r"\b\d{1,3}(?:\.\d{1,3}){3}\b",
    "secret/key": r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+",
}


def sanitize_check(text):
    """Return a list of findings. An empty list means the brief looks sanitized."""
    return [
        label for label, pattern in PII_PATTERNS.items() if re.search(pattern, text)
    ]


def owasp_review(mode, state):
    checklist = load_json("knowledge/owasp_llm_top10.json")
    return run_stage(
        "risk_review",
        mode,
        checklist=checklist,
        recommendation=state.get("recommendation", {}),
        adr=state.get("adr", {}),
    )


def static_checks(state):
    """Deterministic guardrails that do not depend on the model."""
    checks = []
    rec = state.get("recommendation", {})
    checks.append(("Confidence level shown", bool(rec.get("confidence"))))
    checks.append(("Assumptions listed", bool(state.get("intake", {}).get("assumptions"))))
    checks.append(("Review notes present", bool(rec.get("review_notes"))))
    checks.append(("Architect approved assumptions", bool(state.get("approved_assumptions"))))
    checks.append(("Architect approved option", bool(state.get("approved_option"))))
    checks.append(("Architect approved ADR", bool(state.get("approved_adr"))))
    text = str(state.get("adr", "")) + str(rec)
    checks.append(("No definitive vendor mandate", "must use" not in text.lower()))
    return checks
