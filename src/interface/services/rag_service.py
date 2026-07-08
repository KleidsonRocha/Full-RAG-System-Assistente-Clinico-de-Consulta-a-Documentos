from __future__ import annotations

import sqlite3
import sys
import time
import traceback
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VECTORSTORE_DIR = PROJECT_ROOT / "src" / "vectorstore_faiss"
CHUNKS_JSON_PATH = PROJECT_ROOT / "data" / "processed" / "dados_paciente_chunk.json"
OUT_OF_SCOPE_MESSAGE = "Não encontrei essa informação nos documentos disponíveis."

SAMPLE_QUESTIONS = [
    "Quais são as contraindicações da amoxicilina + clavulanato de potássio?",
    "Quais reações adversas podem ocorrer com amoxicilina + clavulanato de potássio?",
    "Qual é a composição da amoxicilina + clavulanato de potássio?",
    "O paciente já utilizou amoxicilina com clavulanato?",
    "Quais diagnósticos aparecem no histórico do paciente?",
    "Quem ganhou a Copa do Mundo de 2002?",
]

def rebuild_vectorstore() -> dict[str, Any]:
    """
    Função que limpa os caches e dispara a recriação da base vetorial FAISS.
    """
    import time
    started_at = time.perf_counter()

    try:
        from ingest_pipeline import executar_ingestao
        executar_ingestao()
        _get_rag.cache_clear()
        return {
            "ok": True,
            "message": "Base vetorial FAISS recriada com sucesso!",
            "elapsed_ms": int((time.perf_counter() - started_at) * 1000)
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Erro ao recriar a base: {str(e)}",
            "elapsed_ms": int((time.perf_counter() - started_at) * 1000)
        }
def get_runtime_status() -> dict[str, Any]:
    faiss_path = VECTORSTORE_DIR / "index.faiss"
    pkl_path = VECTORSTORE_DIR / "index.pkl"
    status = {
        "vectorstore_dir": str(VECTORSTORE_DIR),
        "vectorstore_exists": VECTORSTORE_DIR.exists(),
        "sqlite_exists": faiss_path.exists(),
        "embedding_count": None,
        "chunks_json_exists": CHUNKS_JSON_PATH.exists(),
    }

    if faiss_path.exists() and pkl_path.exists():
        status["embedding_count"] = "Ativo (FAISS)"
    else:
        status["embedding_count"] = None

    return status


def ask_question(question: str, top_k: int = 2, debug: bool = False) -> dict[str, Any]:
    started_at = time.perf_counter()
    normalized_question = question.strip()

    if not normalized_question:
        return _error_response(
            message="Digite uma pergunta antes de consultar a RAG.",
            code="empty_question",
            started_at=started_at,
        )

    runtime_status = get_runtime_status()
    if not runtime_status["sqlite_exists"]:
        return _error_response(
            message=(
                "Base vetorial não encontrada. Gere a base antes de consultar a RAG."
            ),
            code="vectorstore_not_found",
            started_at=started_at,
            technical_details=f"Caminho esperado: {VECTORSTORE_DIR}",
        )

    try:
        rag = _get_rag()
        safe_top_k = max(1, min(int(top_k), 10))
        docs_and_scores = rag.vector_store.similarity_search_with_score(normalized_question, k=safe_top_k)
        documents = []
        for doc, score in docs_and_scores:
            assertividade = max(0.0, min(100.0, (1.0 - (score / 2.0)) * 100))
            doc.metadata["score_assertividade"] = round(assertividade, 2)
            documents.append(doc)
        raw_result = rag.ask(normalized_question)
        answer = str(raw_result.get("answer") or "").strip()
        sources = _normalize_sources(documents)
        retrieved_context = _normalize_context(documents)
        warnings = _build_warnings(answer, sources, retrieved_context)

        return {
            "ok": True,
            "question": normalized_question,
            "answer": answer,
            "sources": sources,
            "retrieved_context": retrieved_context,
            "is_out_of_scope": _is_out_of_scope(answer),
            "latency_ms": _elapsed_ms(started_at),
            "warnings": warnings,
            "error": None,
            "error_code": None,
            "technical_details": None,
            "top_k": top_k,
        }

    except Exception as exc:
        return _error_response(
            message=_friendly_error_message(exc),
            code=_classify_error(exc),
            started_at=started_at,
            technical_details=traceback.format_exc() if debug else str(exc),
        )


@lru_cache(maxsize=1)
def _get_rag() -> Any:
    from src.pipeline.rag_chain import ClinicalRAG

    return ClinicalRAG()


def _configure_top_k(rag: Any, top_k: int) -> None:
    safe_top_k = max(1, min(int(top_k), 10))
    rag.retriever = rag.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": safe_top_k},
    )


def _normalize_sources(documents: list[Any]) -> list[dict[str, Any]]:
    sources = []
    seen = set()

    for position, doc in enumerate(documents, start=1):
        metadata = _enrich_metadata(getattr(doc, "metadata", {}) or {})
        excerpt = _excerpt(getattr(doc, "page_content", "") or "")
        chunk_id = _chunk_id(metadata)
        document_name = metadata.get("arquivo_origem") or metadata.get(
            "medicamento_bula_alvo"
        ) or "Documento recuperado"
        page = metadata.get("pagina_origem")
        key = (document_name, page, chunk_id, excerpt)

        if key in seen:
            continue

        seen.add(key)
        sources.append(
            {
                "rank": position,
                "document": document_name,
                "page": page,
                "chunk_id": chunk_id,
                "score": metadata.get("score_assertividade"),
                "excerpt": excerpt,
                "metadata": metadata,
            }
        )

    return sources


def _normalize_context(documents: list[Any]) -> list[dict[str, Any]]:
    contexts = []

    for position, doc in enumerate(documents, start=1):
        metadata = _enrich_metadata(getattr(doc, "metadata", {}) or {})
        contexts.append(
            {
                "rank": position,
                "text": getattr(doc, "page_content", "") or "",
                "metadata": metadata,
                "source": metadata.get("arquivo_origem")
                          or metadata.get("medicamento_bula_alvo")
                          or "Documento recuperado",
                "page": metadata.get("pagina_origem"),
                "chunk_id": _chunk_id(metadata),
                "score": metadata.get("score_assertividade"),
            }
        )

    return contexts


@lru_cache(maxsize=1)
def _chunks_by_number() -> dict[int, dict[str, Any]]:
    if not CHUNKS_JSON_PATH.exists():
        return {}

    import json

    with CHUNKS_JSON_PATH.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    indexed_chunks = {}
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        chunk_number = metadata.get("chunk_number")
        if isinstance(chunk_number, int):
            indexed_chunks[chunk_number] = chunk

    return indexed_chunks


def _enrich_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(metadata)
    chunk_number = enriched.get("chunk_number")

    if isinstance(chunk_number, int):
        original_chunk = _chunks_by_number().get(chunk_number)
        if original_chunk:
            enriched.update(original_chunk.get("metadata") or {})
            enriched["chunk_id"] = original_chunk.get("chunk_id")

    return enriched


def _chunk_id(metadata: dict[str, Any]) -> str | None:
    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)

    chunk_number = metadata.get("chunk_number")
    if chunk_number is None:
        return None

    return f"chunk_{int(chunk_number):03d}"


def _build_warnings(
        answer: str,
        sources: list[dict[str, Any]],
        retrieved_context: list[dict[str, Any]],
) -> list[str]:
    warnings = []

    if not answer:
        warnings.append("O pipeline retornou uma resposta vazia.")

    if not sources:
        warnings.append("Nenhuma fonte foi retornada pelo pipeline.")

    if not retrieved_context:
        warnings.append("Nenhum contexto recuperado foi retornado pelo pipeline.")

    return warnings


def _is_out_of_scope(answer: str) -> bool:
    normalized_answer = " ".join(answer.lower().split())
    normalized_message = " ".join(OUT_OF_SCOPE_MESSAGE.lower().split())
    return normalized_message in normalized_answer


def _friendly_error_message(exc: Exception) -> str:
    error_text = str(exc).lower()

    if isinstance(exc, ImportError) or "no module named" in error_text:
        return "Dependências do projeto indisponíveis. Verifique o ambiente virtual e o requirements.txt."

    if "connection refused" in error_text or "11434" in error_text or "ollama" in error_text:
        return "Ollama ou modelo local indisponível. Verifique se o Ollama está em execução e se os modelos foram baixados."

    if "faiss" in error_text or "vector" in error_text or "chroma" in error_text:
        return "Falha ao acessar a base vetorial FAISS. Verifique se a base foi gerada corretamente."

    return "Não foi possível consultar o pipeline RAG."


def _classify_error(exc: Exception) -> str:
    error_text = str(exc).lower()

    if isinstance(exc, ImportError) or "no module named" in error_text:
        return "dependency_error"

    if "connection refused" in error_text or "11434" in error_text or "ollama" in error_text:
        return "ollama_unavailable"

    if "faiss" in error_text or "vector" in error_text or "chroma" in error_text:
        return "vectorstore_error"

    return "pipeline_error"


def _error_response(
        message: str,
        code: str,
        started_at: float,
        technical_details: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "question": "",
        "answer": "",
        "sources": [],
        "retrieved_context": [],
        "is_out_of_scope": False,
        "latency_ms": _elapsed_ms(started_at),
        "warnings": [],
        "error": message,
        "error_code": code,
        "technical_details": technical_details,
        "top_k": None,
    }


def _excerpt(text: str, max_chars: int = 600) -> str:
    clean_text = " ".join(text.split())
    if len(clean_text) <= max_chars:
        return clean_text

    return f"{clean_text[:max_chars].rstrip()}..."


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)