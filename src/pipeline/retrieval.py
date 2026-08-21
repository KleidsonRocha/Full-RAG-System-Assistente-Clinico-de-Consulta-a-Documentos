from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any, Sequence

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


RETRIEVAL_CANDIDATES = 10
RRF_RANK_CONSTANT = 60

def identify_document_type(question: str) -> str | None:
    """
    Identifica qual tipo de documento deve ser consultado
    com base na pergunta do usuário.

    Retorna:
        "bula"
        "prontuario"
        None
    """

    normalized = " ".join(normalize_for_bm25(question))

    prontuario_terms = (
        "paciente",
        "historico",
        "diagnostico",
        "consulta",
        "consultas",
        "procedimento",
        "procedimentos",
        "peso",
        "altura",
        "prontuario",
    )

    bula_terms = (
        "bula",
        "contraindicacao",
        "contraindicacoes",
        "reacao adversa",
        "reacoes adversas",
        "composicao",
        "posologia",
        "armazenamento",
        "armazenar",
        "superdose",
        "interacao medicamentosa",
        "interacoes medicamentosas",
        "mecanismo de acao",
    )

    if any(term in normalized for term in prontuario_terms):
        return "prontuario"

    if any(term in normalized for term in bula_terms):
        return "bula"

    return None

def filter_documents_by_type(
    documents: Sequence[Document],
    document_type: str | None,
) -> list[Document]:

    if document_type is None:
        return list(documents)

    return [
        document
        for document in documents
        if document.metadata.get("tipo_documento") == document_type
    ]

def documents_from_vectorstore(vector_store: Any) -> list[Document]:
    """Retorna os mesmos documentos associados ao índice FAISS carregado."""
    documents = []

    for position in sorted(vector_store.index_to_docstore_id):
        docstore_id = vector_store.index_to_docstore_id[position]
        document = vector_store.docstore.search(docstore_id)

        if not isinstance(document, Document):
            raise ValueError(
                f"Documento FAISS invalido na posicao {position}: {docstore_id}"
            )

        documents.append(document)

    return documents


def normalize_for_bm25(text: str) -> list[str]:
    """Normaliza apenas os tokens usados pelo BM25, preservando o texto original."""
    normalized = unicodedata.normalize("NFKD", str(text or "").lower())
    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return re.findall(r"[a-z0-9]+", without_accents)


def build_bm25_index(documents: Sequence[Document]) -> BM25Okapi:
    if not documents:
        raise ValueError("Nao ha documentos no FAISS para construir o indice BM25.")

    tokenized_corpus = [normalize_for_bm25(doc.page_content) for doc in documents]
    return BM25Okapi(tokenized_corpus)


# def retrieve_hybrid(
#     question: str,
#     vector_store: Any,
#     corpus_documents: Sequence[Document],
#     bm25_index: BM25Okapi,
#     top_k: int = 2,
# ) -> list[Document]:
#     final_count = int(top_k)
#     if final_count <= 0:
#         return []

#     candidate_count = max(RETRIEVAL_CANDIDATES, final_count)
#     vector_documents = vector_store.similarity_search(
#         question,
#         k=candidate_count,
#     )
#     lexical_documents = _bm25_search(
#         question,
#         corpus_documents,
#         bm25_index,
#         candidate_count,
#     )
#     fused_documents = reciprocal_rank_fusion(
#         [vector_documents, lexical_documents]
#     )
#     return fused_documents[:final_count]

def retrieve_hybrid(
    question: str,
    vector_store: Any,
    corpus_documents: Sequence[Document],
    bm25_index: BM25Okapi,
    top_k: int = 2,
) -> list[Document]:

    final_count = int(top_k)

    if final_count <= 0:
        return []

    candidate_count = max(
        RETRIEVAL_CANDIDATES,
        final_count
    )

  
    document_type = identify_document_type(question)


    if document_type:

        vector_documents = vector_store.similarity_search(
            question,
            k=candidate_count,
            filter={
                "tipo_documento": document_type
            },
        )

    else:

        vector_documents = vector_store.similarity_search(
            question,
            k=candidate_count,
        )


    filtered_corpus = filter_documents_by_type(
        corpus_documents,
        document_type
    )


    if filtered_corpus:

        filtered_bm25 = build_bm25_index(
            filtered_corpus
        )

        lexical_documents = _bm25_search(
            question,
            filtered_corpus,
            filtered_bm25,
            candidate_count,
        )

    else:

        lexical_documents = []

    fused_documents = reciprocal_rank_fusion(
        [
            vector_documents,
            lexical_documents
        ]
    )

    return fused_documents[:final_count]


def reciprocal_rank_fusion(
    ranked_document_lists: Sequence[Sequence[Document]],
) -> list[Document]:
    scores: dict[tuple[Any, Any], float] = defaultdict(float)
    documents_by_key: dict[tuple[Any, Any], Document] = {}

    for ranked_documents in ranked_document_lists:
        for rank, document in enumerate(ranked_documents, start=1):
            key = _document_key(document)
            documents_by_key.setdefault(key, document)
            scores[key] += 1.0 / (RRF_RANK_CONSTANT + rank)

    return sorted(
        documents_by_key.values(),
        key=lambda document: scores[_document_key(document)],
        reverse=True,
    )


def _bm25_search(
    question: str,
    documents: Sequence[Document],
    bm25_index: BM25Okapi,
    candidate_count: int,
) -> list[Document]:
    scores = bm25_index.get_scores(normalize_for_bm25(question))
    matching_positions = [
        position
        for position in range(len(documents))
        if scores[position] != 0
    ]
    ranked_positions = sorted(
        matching_positions,
        key=lambda position: scores[position],
        reverse=True,
    )
    return [documents[position] for position in ranked_positions[:candidate_count]]


def _document_key(
    document: Document
) -> tuple[Any, Any, Any]:

    metadata = document.metadata or {}

    patient_id = metadata.get("patient_id")
    document_type = metadata.get("tipo_documento")
    chunk_number = metadata.get("chunk_number")

    if (
        patient_id in (None, "")
        or document_type in (None, "")
        or chunk_number is None
    ):
        raise ValueError(
            "Documento sem patient_id, tipo_documento "
            "ou chunk_number para deduplicacao."
        )

    return (
        patient_id,
        document_type,
        chunk_number
    )

        

# def _document_key(document: Document) -> tuple[Any, Any]:
#     metadata = document.metadata or {}
#     patient_id = metadata.get("patient_id")
#     chunk_number = metadata.get("chunk_number")

#     if patient_id in (None, "") or chunk_number is None:
#         raise ValueError(
#             "Documento sem patient_id ou chunk_number para deduplicacao."
#         )

#     return patient_id, chunk_number
