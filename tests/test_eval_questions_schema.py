import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = PROJECT_ROOT / "eval" / "test_questions.json"

REQUIRED_FIELDS = {
    "id",
    "category",
    "question",
    "expected_scope",
    "expected_behavior",
    "expected_keywords",
    "expected_source_hint",
    "notes",
}

EXPECTED_CATEGORY_COUNTS = {
    "bula_medicamento": 8,
    "paciente_metadados": 4,
    "fora_do_acervo": 4,
}


def test_eval_questions_json_schema_and_distribution():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    assert isinstance(questions, list)
    assert len(questions) == 16

    ids = [item["id"] for item in questions]
    assert len(ids) == len(set(ids))

    for item in questions:
        assert REQUIRED_FIELDS.issubset(item)
        assert isinstance(item["id"], str)
        assert isinstance(item["category"], str)
        assert isinstance(item["question"], str)
        assert isinstance(item["expected_scope"], str)
        assert isinstance(item["expected_behavior"], str)
        assert isinstance(item["expected_keywords"], list)
        assert isinstance(item["expected_source_hint"], str)
        assert isinstance(item["notes"], str)
        assert item["question"].strip()

    assert Counter(item["category"] for item in questions) == EXPECTED_CATEGORY_COUNTS


def test_patient_metadata_questions_are_manual_review():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    patient_questions = [
        item for item in questions if item["category"] == "paciente_metadados"
    ]

    assert patient_questions
    assert all(
        item["expected_behavior"] == "avaliar manualmente"
        for item in patient_questions
    )
