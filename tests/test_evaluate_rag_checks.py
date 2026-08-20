from types import SimpleNamespace

import pytest

from eval.evaluate_rag import (
    build_report,
    calculate_retrieval_metrics,
    evaluate_checks,
    evaluate_row,
)


PATIENT_ID = "1d604da9-9a81-4ba9-80c2-de3375d59b40"


def make_document(chunk_number: int, **metadata):
    return SimpleNamespace(
        metadata={
            "patient_id": PATIENT_ID,
            "chunk_number": chunk_number,
            **metadata,
        }
    )


def expected_chunk(chunk_number: int) -> str:
    return f"{PATIENT_ID}::chunk_{chunk_number:03d}"


def test_evaluate_checks_accepts_grounded_answer_with_expected_source():
    item = {
        "should_refuse": False,
        "must_contain": ["hipersensibilidade", "penicilinas"],
        "must_not_contain": ["prescricao"],
        "expected_source_chunks": ["chunk_016"],
        "expected_source_pages": [5],
    }
    answer = "Contraindicada em caso de hipersensibilidade a penicilinas."
    sources = [{"chunk": "chunk_016", "pagina": 5}]

    checks = evaluate_checks(item, answer, sources, [], False, None)

    assert all(checks.values())


def test_evaluate_checks_rejects_missing_required_term():
    item = {
        "should_refuse": False,
        "must_contain": ["hipersensibilidade", "ictericia"],
        "must_not_contain": [],
        "expected_source_chunks": ["chunk_016"],
        "expected_source_pages": [5],
    }
    answer = "Contraindicada em caso de hipersensibilidade."
    sources = [{"chunk": "chunk_016", "pagina": 5}]

    checks = evaluate_checks(item, answer, sources, [], False, None)

    assert checks["termos_obrigatorios"] is False


def test_evaluate_checks_accepts_expected_refusal():
    item = {
        "should_refuse": True,
        "must_contain": ["nao encontrei", "documentos disponiveis"],
        "must_not_contain": ["paris"],
        "expected_source_chunks": [],
        "expected_source_pages": [],
    }
    answer = "Nao encontrei essa informacao nos documentos disponiveis."

    checks = evaluate_checks(item, answer, [], [], True, None)

    assert all(checks.values())


def test_evaluate_checks_validates_expected_metadata_fields():
    item = {
        "should_refuse": False,
        "must_contain": ["75", "kg"],
        "must_not_contain": ["nao registrado"],
        "expected_source_chunks": [],
        "expected_source_pages": [],
        "expected_metadata_fields": ["paciente_ultimo_peso_kg"],
    }
    answer = "O ultimo peso registrado foi 75,6 kg."
    documents = [
        SimpleNamespace(metadata={"paciente_ultimo_peso_kg": "75.6"}),
    ]

    checks = evaluate_checks(item, answer, [], documents, False, None)

    assert all(checks.values())


def test_evaluate_checks_matches_composite_chunk_id_using_document_metadata():
    item = {
        "should_refuse": False,
        "must_contain": ["hipersensibilidade"],
        "must_not_contain": [],
        "expected_source_chunks": [expected_chunk(16)],
        "expected_source_pages": [5],
    }
    documents = [make_document(16)]
    sources = [{"chunk": "chunk_016", "pagina": 5}]

    checks = evaluate_checks(
        item,
        "Hipersensibilidade.",
        sources,
        documents,
        False,
        None,
    )

    assert all(checks.values())


def test_retrieval_metrics_use_all_annotated_chunks_for_recall():
    irrelevant = make_document(1)
    first_relevant = make_document(2)
    second_relevant = make_document(3)
    metrics = calculate_retrieval_metrics(
        [expected_chunk(2), expected_chunk(3)],
        [irrelevant, first_relevant],
        [irrelevant, first_relevant, make_document(4), second_relevant],
    )

    assert metrics is not None
    assert metrics["context_recall_at_2"] == pytest.approx(0.5)
    assert metrics["context_precision_at_2"] == pytest.approx(0.5)
    assert metrics["hit_rate_at_1"] == 0.0
    assert metrics["hit_rate_at_2"] == 1.0
    assert metrics["hit_rate_at_5"] == 1.0
    assert metrics["hit_rate_at_10"] == 1.0
    assert metrics["mrr_at_10"] == pytest.approx(0.5)


def test_retrieval_metrics_respect_hit_rate_cutoffs_and_reciprocal_rank():
    first = SimpleNamespace(metadata={})
    second = make_document(2)
    relevant = make_document(3)
    metrics = calculate_retrieval_metrics(
        [expected_chunk(3)],
        [first, second],
        [first, second, relevant],
    )

    assert metrics is not None
    assert metrics["context_recall_at_2"] == 0.0
    assert metrics["context_precision_at_2"] == 0.0
    assert metrics["hit_rate_at_1"] == 0.0
    assert metrics["hit_rate_at_2"] == 0.0
    assert metrics["hit_rate_at_5"] == 1.0
    assert metrics["hit_rate_at_10"] == 1.0
    assert metrics["mrr_at_10"] == pytest.approx(1 / 3)


def test_retrieval_metrics_return_zero_when_relevant_chunk_is_absent():
    documents = [make_document(1), make_document(2)]
    metrics = calculate_retrieval_metrics(
        [expected_chunk(3)],
        documents,
        documents,
    )

    assert metrics is not None
    assert all(value == 0.0 for value in metrics.values())


def test_retrieval_metrics_ignore_rows_without_annotated_chunks():
    assert calculate_retrieval_metrics([], [], []) is None


class FakeEvaluationRAG:
    def __init__(self):
        self.context_documents = [make_document(1), make_document(2)]
        self.ranking = self.context_documents + [make_document(3)]
        self.retrieval_calls = []

    def ask(self, question):
        return {
            "answer": "Resposta encontrada.",
            "sources": [
                {"chunk": "chunk_001", "pagina": 1},
                {"chunk": "chunk_002", "pagina": 2},
            ],
            "documents": self.context_documents,
        }

    def _retrieve_documents(self, question, top_k):
        self.retrieval_calls.append((question, top_k))
        return self.ranking[:top_k]


def test_evaluate_row_uses_top_2_context_and_top_10_final_ranking():
    rag = FakeEvaluationRAG()
    item = {
        "id": "bula_teste",
        "category": "bula",
        "question": "Pergunta de teste?",
        "should_refuse": False,
        "must_contain": ["resposta"],
        "must_not_contain": [],
        "expected_source_chunks": [expected_chunk(3)],
        "expected_source_pages": [],
        "expected_metadata_fields": [],
    }

    row = evaluate_row(rag, item)

    assert row["document_count"] == 2
    assert rag.retrieval_calls == [("Pergunta de teste?", 10)]
    assert row["retrieval_metrics"]["context_recall_at_2"] == 0.0
    assert row["retrieval_metrics"]["hit_rate_at_2"] == 0.0
    assert row["retrieval_metrics"]["hit_rate_at_5"] == 1.0
    assert row["retrieval_metrics"]["mrr_at_10"] == pytest.approx(1 / 3)

    report = build_report([row])
    for label in (
        "Context Recall@2",
        "Context Precision@2",
        "Hit Rate@1",
        "Hit Rate@2",
        "Hit Rate@5",
        "Hit Rate@10",
        "MRR@10",
    ):
        assert label in report
    assert "somente os chunks positivos anotados" in report
