"""Offline legal-term glossary (demo mode, no API key needed)."""

from __future__ import annotations

GLOSSARY: dict[str, str] = {
    "indemnify": "To compensate someone for loss or damage — e.g., agreeing to cover costs if something goes wrong. Check who pays, for what, and whether there is a cap.",
    "indemnification": "An obligation to cover another party's losses or legal costs. Check whether it applies both ways and whether liability is limited.",
    "liability": "Legal responsibility for harm, loss, or contractual failure. Look for caps, exclusions, and carve-outs.",
    "arbitration": "Resolving disputes through a private arbitrator instead of a court. Often faster but can limit appeals and class actions.",
    "jurisdiction": "Which state or country's laws apply, and where disputes must be heard.",
    "termination": "How the agreement can be ended, by whom, with what notice, and with what consequences.",
    "renewal": "Whether the agreement extends automatically and how to opt out before the deadline.",
    "force majeure": "A clause excusing performance when extraordinary events (natural disasters, war, pandemics) make it impossible.",
    "confidentiality": "Duties to keep shared information private, including exceptions and how long the duty lasts.",
    "warranty": "A promise that something is true or will work as described, plus what happens if it isn't.",
    "assignment": "Whether rights or duties under the agreement can be transferred to someone else.",
    "severability": "If one clause is found unenforceable, the rest of the agreement still stands.",
    "governing law": "Which jurisdiction's laws interpret the agreement.",
    "notice": "How formal communications (termination, renewal, breach) must be delivered to count.",
    "breach": "Failing to do what the agreement requires, and the remedies the other side gets.",
    "cure period": "Extra time allowed to fix a breach before the other side can terminate or penalize.",
    "liquidated damages": "A pre-agreed amount payable on breach, instead of proving actual loss.",
    "non-compete": "A restriction on working with competitors after the agreement ends. Scope and duration matter greatly.",
    "escalation": "Steps for raising disputes (negotiation, mediation) before formal proceedings.",
}


def explain_term_offline(term: str, context: str = "") -> dict[str, object]:
    key = term.strip().lower()
    if key in GLOSSARY:
        return {"term": term.strip(), "definition": GLOSSARY[key], "demo": True}
    # Partial match fallback.
    for name, definition in GLOSSARY.items():
        if name in key or key in name:
            return {"term": term.strip(), "definition": definition, "demo": True}
    return {
        "term": term.strip(),
        "definition": (
            "No offline definition available for this term in demo mode. "
            "Connect an Anthropic API key for AI-powered definitions, or ask a licensed attorney."
        ),
        "demo": True,
    }
