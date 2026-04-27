# Model Card, PawPal+ AI Assistant

## Project Overview

**Base project:** PawPal+, a Streamlit pet care task scheduler  
**Extension:** Ask PawPal, a RAG-powered chat assistant that answers general pet care questions for dogs and cats

---

## 1. Model Details

| Field | Value |
|---|---|
| Model used | Claude Haiku (Anthropic) / Gemini 2.0 Flash (Google), switchable via `LLM_PROVIDER` in `assistant.py` |
| Retrieval method | TF-IDF keyword overlap, no external vector database |
| Knowledge base | 8 curated markdown files across nutrition, behavior, grooming, health basics, and safety (dogs and cats) |
| Triage outcomes | `ANSWER`, `IDK`, `VET` |
| Sources cited | AKC, Cornell Feline Health Center, Merck Veterinary Manual |

---

## 2. Intended Use

PawPal+ is intended for pet owners looking for general, non-medical guidance on dog and cat care. It is **not** a substitute for veterinary advice.

**In scope:**
- Nutrition and feeding schedules
- Grooming frequency and technique
- Behavioral basics and enrichment
- Common minor wellness care (e.g. upset stomach home care, hairball prevention)
- Toxic foods and plants to avoid

**Out of scope:**
- Any medical diagnosis or treatment
- Medication names, dosages, or interactions
- Injury assessment or wound care
- Exotic or uncommon species (reptiles, birds, fish, etc.)

---

## 3. AI Collaboration

### How AI was used

AI was used as a collaborative engineering partner across both the scheduler and the assistant extension, not as a code generator, but as a thinking tool. The most valuable interactions were design conversations: talking through tradeoffs before writing any code, challenging assumptions, and stress-testing logic.

For the scheduler: the category ranking (feed → meds → walk → grooming) came from a collaborative discussion about what "biology first" actually means in practice. The `auto_escalate` field was proposed as a global `Owner` setting by the AI, but pushed back on, everyday tasks like feeding shouldn't escalate, but periodic tasks like nail trimming should opt in. That correction came from thinking about the real user, not the data model.

For the assistant: the three-way triage router (VET / IDK / ANSWER) was designed collaboratively. The key insight, that the VET blocklist must run before retrieval, not after, came from asking "what's the failure mode if we let retrieval run first?" The answer was clear: a well-matched chunk of text about medication could trick a naive system into answering a dosage question.

### Judgment and verification

AI suggestions were reviewed and corrected throughout:
- A test that initially failed was diagnosed as a wrong test assumption, not a scheduler bug, the sort logic was correct and the test was fixed to match it
- The initial triage blocklist was too aggressive, routing common minor questions (upset stomach, occasional vomiting) to VET. After testing real queries, the patterns were narrowed to serious cases only
- Knowledge base facts were verified against named veterinary sources before inclusion

---

## 4. Bias and Limitations

### Species bias

The knowledge base only covers dogs and cats. Questions about any other species, rabbits, reptiles, birds, small mammals, route to IDK. This is an intentional, honest limitation, but it means the app is less useful for owners of non-traditional pets.

### Lexical retrieval bias

The TF-IDF retriever matches on word overlap, not meaning. A question phrased differently from the knowledge base wording (e.g. "What should my dog not eat?" vs. "toxic foods for dogs") may score low and fall through to IDK even when the answer exists. Owners who phrase questions conversationally may get more IDK responses than owners who use keyword-dense queries.

### Blocklist coverage gaps

The VET keyword blocklist covers known high-risk patterns but cannot anticipate every phrasing. A sufficiently indirect or rephrased medical question may not be caught. The system prompt instructs the LLM to refuse medical answers as a second line of defense, but this is not a guarantee.

### Source recency

Knowledge base facts were curated at the time of writing. Veterinary guidance evolves; the app has no mechanism to update facts automatically. Information should be verified against current veterinary sources for any health-adjacent decision.

### Breed and individual variation

Facts in the knowledge base reflect general guidance for the average dog or cat. Breed-specific needs (e.g. brachycephalic dogs, senior cats with kidney disease) are not accounted for. Owners of dogs or cats with known health conditions should consult a vet rather than relying on general care guidance.

---

## 5. Testing Results

### Scheduler (test_scheduler.py), 5/5 passing

| Test | What it verifies |
|---|---|
| `test_priority_ordering` | High priority tasks schedule before low priority |
| `test_time_constraint_skips_long_tasks` | Tasks exceeding remaining time are marked skipped |
| `test_fill_gaps_false_stops_scheduling` | Scheduling halts after first task that doesn't fit |
| `test_auto_escalate_bumps_priority` | Priority bumps up one level at reschedule threshold |
| `test_category_rank_tiebreaker` | Biological urgency breaks ties within same priority |

### Triage router (test_triage.py), 16/16 passing

| Category | Tests | Outcome verified |
|---|---|---|
| Normal care questions | 3 | `ANSWER` |
| Symptom questions | 2 | `VET` |
| Medication / dosage | 1 | `VET` |
| Injury | 1 | `VET` |
| Diagnosis questions | 1 | `VET` |
| Blocklist override (high retrieval score) | 1 | `VET` regardless of score |
| Exotic species | 2 | `IDK` |
| Low confidence retrieval | 2 | `IDK` |
| Edge cases (rephrasing, behavioral change, vaccines) | 3 | `VET` |

All triage tests run without a network connection or API key, triage logic is tested with simulated retrieval scores.

---

## 6. What Would Improve This Model

- **Vector embeddings**, replacing TF-IDF with a semantic embedding retriever would dramatically reduce IDK false negatives for conversationally phrased questions
- **Broader species coverage**, adding knowledge files for rabbits, guinea pigs, and birds would reduce the exotic species gap
- **Source freshness**, a mechanism to flag or update knowledge base facts that have become outdated
- **Breed-aware retrieval**, tagging facts by breed or size class so retrieval can weight results toward the owner's specific animal
