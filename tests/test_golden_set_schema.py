import json
from collections import Counter
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_SET_PATH = PROJECT_ROOT / "eval" / "golden_set.json"

REQUIRED_FIELDS = {
    "id",
    "category",
    "question",
    "expected_scope",
    "expected_behavior",
    "expected_answer",
    "expected_keywords",
    "must_contain",
    "must_not_contain",
    "expected_source_hint",
    "expected_source_chunks",
    "expected_source_pages",
    "expected_metadata_fields",
    "evidence_quote",
    "atomic_claims",
    "should_refuse",
    "notes",
}

EXPECTED_CATEGORY_COUNTS = {
    "bula": 16,
    "dados_paciente": 8,
    "fora_do_acervo": 6,
}


def load_golden_set():
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


GOLDEN_SET = load_golden_set()


def golden_case_id(item):
    return item["id"]


def test_golden_set_size_ids_and_distribution():
    questions = GOLDEN_SET

    assert isinstance(questions, list)
    assert len(questions) == 30

    ids = [item["id"] for item in questions]
    assert len(ids) == len(set(ids))

    assert Counter(item["category"] for item in questions) == EXPECTED_CATEGORY_COUNTS


@pytest.mark.parametrize("item", GOLDEN_SET, ids=golden_case_id)
def test_golden_set_item_schema(item):
    assert REQUIRED_FIELDS.issubset(item)
    assert isinstance(item["id"], str)
    assert isinstance(item["category"], str)
    assert isinstance(item["question"], str)
    assert isinstance(item["expected_scope"], str)
    assert isinstance(item["expected_behavior"], str)
    assert isinstance(item["expected_answer"], str)
    assert isinstance(item["expected_keywords"], list)
    assert isinstance(item["must_contain"], list)
    assert isinstance(item["must_not_contain"], list)
    assert isinstance(item["expected_source_hint"], str)
    assert isinstance(item["expected_source_chunks"], list)
    assert isinstance(item["expected_source_pages"], list)
    assert isinstance(item["expected_metadata_fields"], list)
    assert isinstance(item["evidence_quote"], str)
    assert isinstance(item["atomic_claims"], list)
    assert isinstance(item["should_refuse"], bool)
    assert isinstance(item["notes"], str)
    assert item["question"].strip()
    assert item["expected_answer"].strip()

    if item["should_refuse"]:
        assert not item["expected_source_chunks"]
        assert not item["expected_source_pages"]
        assert not item["atomic_claims"]
    else:
        assert item["evidence_quote"].strip()
        assert item["atomic_claims"]


def test_patient_metadata_questions_have_metadata_evidence():
    patient_questions = [
        item for item in GOLDEN_SET if item["category"] == "dados_paciente"
    ]

    assert patient_questions
    for item in patient_questions:
        assert item["expected_behavior"] == "responder com base nos metadados recuperados"
        assert item["expected_source_hint"] == "metadata"
        assert item["expected_metadata_fields"]
        assert not item["should_refuse"]
