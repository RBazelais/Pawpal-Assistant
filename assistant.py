import os
from typing import Any

import anthropic

from retriever import retrieve
from triage import triage

_VET_RESPONSE = (
    "I'm not able to answer medical, symptom, or medication questions. "
    "Please contact a licensed veterinarian as soon as possible — "
    "they are the only appropriate source of advice for health concerns."
)

_IDK_RESPONSE = (
    "I don't have enough reliable information to answer that confidently. "
    "I currently cover general care topics (nutrition, behavior, grooming) "
    "for dogs and cats. For anything outside that scope, please consult a "
    "veterinarian or a breed-specific resource."
)

_SYSTEM_PROMPT = """\
You are PawPal, a pet care assistant. Your knowledge comes ONLY from the \
context passages provided in each message. You must follow these rules without exception:

1. NEVER answer questions about symptoms, diagnoses, medications, dosages, injuries, \
   or any health concern — these have already been filtered out before reaching you, \
   but if one slips through, respond only with: "Please consult a veterinarian."

2. NEVER speculate or make up facts. If the provided context does not contain a clear \
   answer, say "I don't have enough information to answer that."

3. Answer ONLY from the context below. Do not draw on general training knowledge.

4. Keep answers concise — 2 to 4 sentences unless more detail is clearly needed.

5. Do not suggest veterinary diagnoses or imply that any home observation replaces \
   professional veterinary assessment.
"""


def ask(
    query: str,
    species: str = "dog",
    top_k: int = 3,
) -> dict[str, Any]:
    """Orchestrate retrieval → triage → (optional) Anthropic API call.

    Returns a dict with keys:
        outcome    — "VET" | "IDK" | "ANSWER"
        response   — string to display to the user
        confidence — float 0–1
        sources    — list of source file paths (empty for VET/IDK)
    """
    results = retrieve(query, species=species, top_k=top_k)
    outcome, reason, confidence = triage(query, results, species)

    if outcome == "VET":
        return {
            "outcome": "VET",
            "response": _VET_RESPONSE,
            "confidence": 0.0,
            "sources": [],
        }

    if outcome == "IDK":
        return {
            "outcome": "IDK",
            "response": _IDK_RESPONSE,
            "confidence": confidence,
            "sources": [],
        }

    # ANSWER — build context block and call the API.
    context_block = "\n\n".join(
        f"[{r['source']}]\n{r['text']}" for r in results
    )
    user_message = (
        f"Context:\n{context_block}\n\n"
        f"The owner's pet is a {species}.\n\n"
        f"Question: {query}"
    )

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = message.content[0].text if message.content else _IDK_RESPONSE

    return {
        "outcome": "ANSWER",
        "response": response_text,
        "confidence": confidence,
        "sources": [r["source"] for r in results],
    }
