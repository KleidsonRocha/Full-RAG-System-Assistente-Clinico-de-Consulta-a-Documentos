from dataclasses import dataclass, field
from typing import Any

from src.interface.services import rag_service


@dataclass
class FakeDocument:
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class FakeVectorStore:
    def __init__(self) -> None:
        self.last_search_kwargs: dict[str, Any] | None = None

    def as_retriever(self, search_type: str, search_kwargs: dict[str, Any]) -> object:
        self.last_search_kwargs = search_kwargs
        return {"search_type": search_type, "search_kwargs": search_kwargs}


class FakeRAG:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.vector_store = FakeVectorStore()
        self.retriever = None

    def ask(self, question: str) -> dict[str, Any]:
        return {
            "question": question,
            "answer": self.answer,
            "sources": [{"chunk": "chunk_001"}],
            "documents": [
                FakeDocument(
                    page_content="Trecho recuperado da bula.",
                    metadata={
                        "arquivo_origem": "bula_amoxicilina_clavulanato_paciente1.pdf",
                        "pagina_origem": 1,
                        "chunk_number": 1,
                        "medicamento_bula_alvo": "amoxicilina + clavulanato",
                    },
                )
            ],
        }


def _mock_ready_runtime(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_service,
        "get_runtime_status",
        lambda: {"vectorstore_ready": True},
    )


def test_ask_question_returns_normalized_success_payload(monkeypatch):
    fake_rag = FakeRAG("Resposta baseada no contexto recuperado.")
    _mock_ready_runtime(monkeypatch)
    monkeypatch.setattr(rag_service, "_get_rag", lambda: fake_rag)

    result = rag_service.ask_question("  Qual e a composicao do medicamento?  ", top_k=2)

    assert result["ok"] is True
    assert result["question"] == "Qual e a composicao do medicamento?"
    assert result["answer"] == "Resposta baseada no contexto recuperado."
    assert result["error"] is None
    assert result["top_k"] == 2
    assert result["is_out_of_scope"] is False
    assert isinstance(result["latency_ms"], int)
    assert len(result["sources"]) == 1
    assert len(result["retrieved_context"]) == 1
    assert fake_rag.vector_store.last_search_kwargs == {"k": 2}


def test_ask_question_rejects_empty_question():
    result = rag_service.ask_question("   ")

    assert result["ok"] is False
    assert result["error_code"] == "empty_question"
    assert result["answer"] == ""
    assert result["sources"] == []
    assert result["retrieved_context"] == []


def test_ask_question_marks_guardrail_answer_as_out_of_scope(monkeypatch):
    fake_rag = FakeRAG(rag_service.OUT_OF_SCOPE_MESSAGE)
    _mock_ready_runtime(monkeypatch)
    monkeypatch.setattr(rag_service, "_get_rag", lambda: fake_rag)

    result = rag_service.ask_question("Quem ganhou a Copa do Mundo de 2002?")

    assert result["ok"] is True
    assert result["answer"] == rag_service.OUT_OF_SCOPE_MESSAGE
    assert result["is_out_of_scope"] is True


def test_ask_question_reports_missing_vectorstore(monkeypatch):
    monkeypatch.setattr(
        rag_service,
        "get_runtime_status",
        lambda: {"vectorstore_ready": False},
    )

    result = rag_service.ask_question("Qual e a composicao do medicamento?")

    assert result["ok"] is False
    assert result["error_code"] == "vectorstore_not_found"
    assert result["technical_details"]
