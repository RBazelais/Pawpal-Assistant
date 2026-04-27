"""Eval harness for the triage router.

Each test calls triage() directly with realistic retrieval scores
so the suite runs without an API key or network access.
"""

import pytest

from triage import triage

# Simulated retrieval results — score is all that matters for triage logic.
_STRONG = [{"score": 0.25}, {"score": 0.18}, {"score": 0.12}]
_WEAK   = [{"score": 0.03}, {"score": 0.01}]
_EMPTY  = []


# ---------------------------------------------------------------------------
# ANSWER cases — routine care questions with strong retrieval
# ---------------------------------------------------------------------------

def test_normal_grooming_question_answers():
    outcome, _, conf = triage("how often should I brush my dog", _STRONG, "dog")
    assert outcome == "ANSWER"
    assert conf > 0


def test_normal_nutrition_question_answers():
    outcome, _, _ = triage("what should I feed my cat", _STRONG, "cat")
    assert outcome == "ANSWER"


def test_normal_behavior_question_answers():
    outcome, _, _ = triage("why does my dog bark so much", _STRONG, "dog")
    assert outcome == "ANSWER"


# ---------------------------------------------------------------------------
# VET cases — blocked by keyword list regardless of retrieval score
# ---------------------------------------------------------------------------

def test_symptom_question_routes_to_vet():
    outcome, reason, conf = triage("my dog is vomiting and lethargic", _STRONG, "dog")
    assert outcome == "VET"
    assert conf == 0.0
    assert "veterinarian" in reason.lower()


def test_medication_question_routes_to_vet():
    outcome, _, _ = triage("what medication dosage should I give my cat", _STRONG, "cat")
    assert outcome == "VET"


def test_injury_question_routes_to_vet():
    outcome, _, _ = triage("my dog has a wound on its leg", _STRONG, "dog")
    assert outcome == "VET"


def test_not_eating_routes_to_vet():
    outcome, _, _ = triage("my cat hasn't eaten in two days", _STRONG, "cat")
    assert outcome == "VET"


def test_diagnosis_question_routes_to_vet():
    outcome, _, _ = triage("does my dog have diabetes", _STRONG, "dog")
    assert outcome == "VET"


def test_vet_blocklist_overrides_strong_retrieval():
    # Even with a near-perfect retrieval score, VET wins.
    outcome, _, _ = triage("my cat is sick and has diarrhea", [{"score": 0.99}], "cat")
    assert outcome == "VET"


# ---------------------------------------------------------------------------
# IDK cases — exotic species or low-confidence retrieval
# ---------------------------------------------------------------------------

def test_exotic_species_routes_to_idk():
    outcome, reason, _ = triage("how do I feed my iguana", _STRONG, "iguana")
    assert outcome == "IDK"
    assert "iguana" in reason


def test_other_species_routes_to_idk():
    outcome, _, _ = triage("best diet for my parrot", _STRONG, "other")
    assert outcome == "IDK"


def test_low_confidence_retrieval_routes_to_idk():
    outcome, _, conf = triage("tell me about grooming a dog", _WEAK, "dog")
    assert outcome == "IDK"
    assert conf < 0.08


def test_empty_retrieval_routes_to_idk():
    outcome, _, _ = triage("asdfghjkl nonsense question", _EMPTY, "dog")
    assert outcome == "IDK"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_rephrased_medical_question_still_vet():
    # "pill" is in the blocklist even without "medication" keyword.
    outcome, _, _ = triage("can I give my dog an aspirin pill for its pain", _STRONG, "dog")
    assert outcome == "VET"


def test_behavioral_change_phrase_routes_to_vet():
    # Sudden behavioral change is a clinical red flag.
    outcome, _, _ = triage("my dog is suddenly aggressive — behavior change overnight", _STRONG, "dog")
    assert outcome == "VET"


def test_vaccine_question_routes_to_vet():
    outcome, _, _ = triage("which vaccines does my puppy need", _STRONG, "dog")
    assert outcome == "VET"
