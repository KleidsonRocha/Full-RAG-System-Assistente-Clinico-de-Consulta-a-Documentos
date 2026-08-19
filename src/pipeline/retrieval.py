from __future__ import annotations

import os
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

from flashrank import Ranker, RerankRequest
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


RETRIEVAL_CANDIDATES = 10
RRF_RANK_CONSTANT = 60
RERANKER_MODEL = "ms-marco-MultiBERT-L-12"


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


def build_reranker() -> Ranker:
    cache_dir = _reranker_cache_dir()
    return Ranker(model_name=RERANKER_MODEL, cache_dir=str(cache_dir))


def retrieve_and_rerank(
    question: str,
    vector_store: Any,
    corpus_documents: Sequence[Document],
    bm25_index: BM25Okapi,
    reranker: Any,
    top_k: int = 2,
) -> list[Document]:
    final_count = int(top_k)
    if final_count <= 0:
        return []

    candidate_count = RETRIEVAL_CANDIDATES
    vector_documents = vector_store.similarity_search(
        question,
        k=candidate_count,
    )
    lexical_documents = _bm25_search(
        question,
        corpus_documents,
        bm25_index,
        candidate_count,
    )
    fused_documents = reciprocal_rank_fusion(
        [vector_documents, lexical_documents]
    )

    return rerank_documents(
        question,
        fused_documents,
        reranker,
        final_count,
    )


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


def rerank_documents(
    question: str,
    documents: Sequence[Document],
    reranker: Any,
    top_k: int,
) -> list[Document]:
    if top_k <= 0 or not documents:
        return []

    passages = [
        {
            "id": position,
            "text": document.page_content,
        }
        for position, document in enumerate(documents)
    ]
    response = reranker.rerank(
        RerankRequest(query=question, passages=passages)
    )

    reranked_documents = []
    seen_positions = set()
    for result in response:
        position = int(result["id"])
        if position in seen_positions or not 0 <= position < len(documents):
            continue

        seen_positions.add(position)
        reranked_documents.append(documents[position])

    for position, document in enumerate(documents):
        if position not in seen_positions:
            reranked_documents.append(document)

    return reranked_documents[:top_k]


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


def _document_key(document: Document) -> tuple[Any, Any]:
    metadata = document.metadata or {}
    patient_id = metadata.get("patient_id")
    chunk_number = metadata.get("chunk_number")

    if patient_id in (None, "") or chunk_number is None:
        raise ValueError(
            "Documento sem patient_id ou chunk_number para deduplicacao."
        )

    return patient_id, chunk_number


def _reranker_cache_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "flashrank"
    return Path.home() / ".cache" / "flashrank"
