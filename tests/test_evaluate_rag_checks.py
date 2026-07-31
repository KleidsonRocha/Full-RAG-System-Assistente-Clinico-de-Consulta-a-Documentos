from types import SimpleNamespace

from eval.evaluate_rag import evaluate_checks


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
