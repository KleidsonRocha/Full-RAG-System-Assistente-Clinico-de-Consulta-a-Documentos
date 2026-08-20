from typing import Any

from langchain_core.documents import Document

from src.pipeline.retrieval import (
    RETRIEVAL_CANDIDATES,
    build_bm25_index,
    documents_from_vectorstore,
    normalize_for_bm25,
    reciprocal_rank_fusion,
    retrieve_hybrid,
)
from src.pipeline.rag_chain import ClinicalRAG


def make_document(chunk_number: int, text: str) -> Document:
    return Document(
        page_content=text,
        metadata={
            "patient_id": "patient-1",
            "chunk_number": chunk_number,
            "pagina_origem": chunk_number,
        },
    )


class FakeDocstore:
    def __init__(self, documents: dict[str, Document]) -> None:
        self.documents = documents

    def search(self, docstore_id: str) -> Document:
        return self.documents[docstore_id]


class FakeVectorStore:
    def __init__(
        self,
        corpus_documents: list[Document],
        vector_results: list[Document] | None = None,
    ) -> None:
        self.index_to_docstore_id = {
            position: f"doc-{position}"
            for position in range(len(corpus_documents))
        }
        self.docstore = FakeDocstore(
            {
                f"doc-{position}": document
                for position, document in enumerate(corpus_documents)
            }
        )
        self.vector_results = vector_results or corpus_documents
        self.last_k: int | None = None

    def similarity_search(self, question: str, k: int) -> list[Document]:
        self.last_k = k
        return self.vector_results[:k]


class FakePrompt:
    def __init__(self) -> None:
        self.last_payload: dict[str, Any] | None = None

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_payload = payload
        return payload


class FakeLLM:
    def invoke(self, messages: Any) -> str:
        return "Resposta baseada no contexto final."


class FakeParser:
    def invoke(self, response: Any) -> str:
        return str(response)


def test_documents_from_vectorstore_returns_same_document_objects():
    documents = [
        make_document(1, "Primeiro chunk"),
        make_document(2, "Segundo chunk"),
    ]
    vector_store = FakeVectorStore(documents)

    loaded_documents = documents_from_vectorstore(vector_store)

    assert loaded_documents[0] is documents[0]
    assert loaded_documents[1] is documents[1]


def test_bm25_normalization_does_not_change_original_content():
    original_text = "REAÇÕES adversas: náusea, dor e febre."
    document = make_document(1, original_text)

    tokens = normalize_for_bm25(document.page_content)
    build_bm25_index([document])

    assert tokens == ["reacoes", "adversas", "nausea", "dor", "e", "febre"]
    assert document.page_content == original_text


def test_rrf_uses_equal_contributions_and_deduplicates_by_metadata():
    first = make_document(1, "Primeiro")
    second = make_document(2, "Segundo")
    duplicate_first = make_document(1, "Copia que nao deve substituir o original")
    original_metadata = [dict(first.metadata), dict(second.metadata)]

    fused = reciprocal_rank_fusion(
        [
            [first, second],
            [duplicate_first, second],
        ]
    )

    assert fused == [first, second]
    assert fused[0] is first
    assert [first.metadata, second.metadata] == original_metadata


def test_hybrid_retrieval_applies_top_k_after_rrf():
    documents = [
        make_document(1, "contraindicacao alergia penicilina"),
        make_document(2, "composicao do medicamento"),
        make_document(3, "reacoes adversas nausea"),
    ]
    vector_store = FakeVectorStore(
        documents,
        vector_results=[documents[1], documents[0], documents[2]],
    )
    bm25_index = build_bm25_index(documents)
    original_metadata = [dict(document.metadata) for document in documents]

    result = retrieve_hybrid(
        question="alergia a penicilina",
        vector_store=vector_store,
        corpus_documents=documents,
        bm25_index=bm25_index,
        top_k=2,
    )

    assert len(result) == 2
    assert result[0] is documents[0]
    assert result[1] is documents[1]
    assert vector_store.last_k == RETRIEVAL_CANDIDATES
    assert [document.metadata for document in documents] == original_metadata


def test_bm25_without_match_does_not_inject_arbitrary_documents():
    documents = [
        make_document(1, "alergia a penicilina"),
        make_document(2, "reacoes adversas"),
        make_document(3, "composicao do medicamento"),
    ]
    vector_store = FakeVectorStore(documents, vector_results=[documents[0]])
    bm25_index = build_bm25_index(documents)

    result = retrieve_hybrid(
        question="termo lexical inexistente",
        vector_store=vector_store,
        corpus_documents=documents,
        bm25_index=bm25_index,
        top_k=2,
    )

    assert result == [documents[0]]
    assert result[0] is documents[0]


def test_hybrid_retrieval_is_faiss_plus_bm25_then_rrf_then_top_k():
    vector_documents = [
        make_document(position, f"conteudo vetorial {position}")
        for position in range(1, RETRIEVAL_CANDIDATES + 1)
    ]
    lexical_documents = [
        make_document(position, f"termolexical conteudo {position}")
        for position in range(
            RETRIEVAL_CANDIDATES + 1,
            (RETRIEVAL_CANDIDATES * 2) + 1,
        )
    ]
    neutral_document = make_document(
        (RETRIEVAL_CANDIDATES * 2) + 1,
        "conteudo neutro",
    )
    documents = vector_documents + lexical_documents + [neutral_document]
    vector_store = FakeVectorStore(
        documents,
        vector_results=vector_documents,
    )
    bm25_index = build_bm25_index(documents)

    result = retrieve_hybrid(
        question="termolexical",
        vector_store=vector_store,
        corpus_documents=documents,
        bm25_index=bm25_index,
        top_k=2,
    )

    assert vector_store.last_k == RETRIEVAL_CANDIDATES
    assert result == [vector_documents[0], lexical_documents[0]]
    assert result[0] is vector_documents[0]
    assert result[1] is lexical_documents[0]


def test_top_k_larger_than_retrieval_candidates_is_not_artificially_limited():
    requested_count = RETRIEVAL_CANDIDATES + 2
    documents = [
        make_document(position, "termocomum documento")
        for position in range(1, requested_count + 1)
    ]
    vector_store = FakeVectorStore(documents)
    bm25_index = build_bm25_index(documents)

    result = retrieve_hybrid(
        question="termocomum",
        vector_store=vector_store,
        corpus_documents=documents,
        bm25_index=bm25_index,
        top_k=requested_count,
    )

    assert vector_store.last_k == requested_count
    assert len(result) == requested_count
    assert all(actual is expected for actual, expected in zip(result, documents))


def test_ask_uses_final_documents_for_context_documents_and_sources():
    selected_documents = [
        make_document(2, "Contexto final mais relevante"),
        make_document(1, "Segundo contexto final"),
    ]
    retrieval_call: dict[str, Any] = {}

    def fake_retrieve(question: str, top_k: int = 2) -> list[Document]:
        retrieval_call.update({"question": question, "top_k": top_k})
        return selected_documents[:top_k]

    rag = ClinicalRAG.__new__(ClinicalRAG)
    rag._retrieve_documents = fake_retrieve
    rag.prompt = FakePrompt()
    rag.llm = FakeLLM()
    rag.parser = FakeParser()

    result = rag.ask("Qual e o contexto?", top_k=1)

    assert retrieval_call == {"question": "Qual e o contexto?", "top_k": 1}
    assert result["documents"] == [selected_documents[0]]
    assert result["documents"][0] is selected_documents[0]
    assert result["sources"] == [
        {
            "chunk": "chunk_002",
            "pagina": 2,
            "medicamento": None,
        }
    ]
    assert rag.prompt.last_payload is not None
    assert "Contexto final mais relevante" in rag.prompt.last_payload["context"]
    assert "Segundo contexto final" not in rag.prompt.last_payload["context"]
