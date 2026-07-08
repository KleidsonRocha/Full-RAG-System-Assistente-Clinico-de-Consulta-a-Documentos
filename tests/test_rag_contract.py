import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_RAG_INTEGRATION") == "1",
    reason="Teste de integracao do RAG desativado por SKIP_RAG_INTEGRATION=1.",
)


def test_clinical_rag_ask_contract(clinical_rag_with_temp_vectorstore):
    rag = clinical_rag_with_temp_vectorstore
    result = rag.ask(
        "Quais sao as contraindicacoes da amoxicilina com clavulanato?"
    )

    assert isinstance(result, dict)
    assert {"question", "answer", "sources", "documents"}.issubset(result)
    assert result["question"]
    assert isinstance(result["answer"], str)
    assert isinstance(result["sources"], list)
    assert isinstance(result["documents"], list)
