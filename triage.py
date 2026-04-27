import re

# Minimum retrieval score to attempt an answer.
_ANSWER_THRESHOLD = 0.08

# Species with knowledge coverage — anything else is IDK by default.
_COVERED_SPECIES = {"dog", "cat"}

# Blocklist checked before retrieval. Any match -> VET, no exceptions.
_VET_PATTERNS: list[str] = [
    # serious / emergency symptoms only — minor digestive issues are handled by knowledge base
    r"\bseizure",
    r"\bblood\b",
    r"\blimp",
    r"\bswollen",
    r"\blethargi",
    r"\bfever",
    r"\binfection",
    r"\binfected",
    r"\bwound",
    r"\binjur",
    r"\bpain\b",
    r"\bhurt\b",
    r"\bnot eating",
    r"\bhasn.t eaten",
    r"\brefusing (to eat|food|water)",
    r"\bnot drinking",
    r"\bhasn.t drunk",
    r"\bhasn.t drank",
    r"\bvomit(ing)?.{0,40}(blood|non.?stop|constant|for\s+(days|a\s+week|weeks))",
    r"(blood|non.?stop|constant).{0,20}vomit",
    r"\bdiarrhea.{0,30}(blood|for\s+(days|weeks))",
    r"\bdiagnos",
    r"\bdisease",
    r"\bdisorder",
    r"\billness",
    r"\bdiabet",
    r"\bcancer",
    r"\btumor",
    r"\bhave\b.{0,30}\b(diabetes|cancer|tumor|disease|infection)",
    r"\bdoes.{0,20}have\b",
    r"\bdehydrat",
    r"\bparasit",
    r"\bworm",
    r"\bflea.*(treat|medicat|pill)",
    # medication / dosage
    r"\bmedication",
    r"\bdosage",
    r"\bdose\b",
    r"\bprescri",
    r"\bantibiotic",
    r"\bvaccin",
    r"\bdrug\b",
    r"\bpill\b",
    r"\bointment",
    r"\btopical",
    # behavioral change as illness signal
    r"\bbehavior(al)? change",
    r"\bsuddenly (aggressive|biting|hiding|limping|lethargic)",
    r"\bacting (weird|strange|different|off)\b",
    # vet-context phrases
    r"\bveterinarian",
    r"\bemergency",
]

_VET_RE = re.compile("|".join(_VET_PATTERNS), re.IGNORECASE)


def _is_vet_question(query: str) -> bool:
    return bool(_VET_RE.search(query))


def triage(
    query: str,
    retrieval_results: list[dict],
    species: str,
) -> tuple[str, str, float]:
    """Classify a query into VET, IDK, or ANSWER.

    Parameters
    ----------
    query:             Raw user question.
    retrieval_results: Output of retriever.retrieve() — list of dicts with 'score'.
    species:           "dog", "cat", or anything else.

    Returns
    -------
    (outcome, reason, confidence)
      outcome    — "VET" | "IDK" | "ANSWER"
      reason     — human-readable explanation surfaced in the UI
      confidence — float 0–1 (top retrieval score, or 0 for VET/IDK)
    """
    # 1. VET blocklist runs first — no retrieval needed.
    if _is_vet_question(query):
        return (
            "VET",
            "This question involves symptoms, medication, injury, or a health change. "
            "Please consult a licensed veterinarian.",
            0.0,
        )

    # 2. Species coverage check.
    if species not in _COVERED_SPECIES:
        return (
            "IDK",
            f"PawPal currently covers dogs and cats. "
            f"I don't have reliable information for '{species}'.",
            0.0,
        )

    # 3. Retrieval confidence check.
    top_score = retrieval_results[0]["score"] if retrieval_results else 0.0
    if top_score < _ANSWER_THRESHOLD:
        return (
            "IDK",
            "I couldn't find enough relevant information in my knowledge base to answer confidently.",
            top_score,
        )

    # 4. All clear — safe to answer.
    return (
        "ANSWER",
        "Relevant information found in the knowledge base.",
        top_score,
    )
