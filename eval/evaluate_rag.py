from __future__ import annotations

import json
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_SET_PATH = PROJECT_ROOT / "eval" / "golden_set.json"
RESULTS_PATH = PROJECT_ROOT / "eval" / "results.md"
CONTEXT_METRICS_K = 2
RETRIEVAL_METRICS_K = 10
HIT_RATE_KS = (1, 2, 5, 10)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REFUSAL_MARKERS = (
    "nao encontrei",
    "não encontrei",
    "nÃ£o encontrei",
    "documentos disponiveis",
    "documentos disponíveis",
    "documentos disponÃ­veis",
    "fora do acervo",
    "nao posso responder",
    "não posso responder",
    "nao ha informacao",
    "não há informação",
    "nÃ£o hÃ¡ informaÃ§Ã£o",
)


def load_golden_set() -> list[dict[str, Any]]:
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


def looks_like_refusal(answer: str) -> bool:
    normalized_answer = normalize_text(answer)
    return any(marker in normalized_answer for marker in REFUSAL_MARKERS)


def normalize_text(value: Any) -> str:
    text = " ".join(str(value or "").lower().split())
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def _chunk_key_from_identifier(value: Any) -> tuple[str | None, str] | None:
    identifier = str(value or "").strip()
    if not identifier:
        return None

    if "::" in identifier:
        patient_id, chunk_label = identifier.rsplit("::", 1)
    else:
        patient_id, chunk_label = None, identifier

    if not chunk_label.startswith("chunk_"):
        return None

    try:
        chunk_label = f"chunk_{int(chunk_label.removeprefix('chunk_')):03d}"
    except ValueError:
        pass

    return patient_id or None, chunk_label


def _document_chunk_key(document: Any) -> tuple[str | None, str] | None:
    metadata = getattr(document, "metadata", {}) or {}
    patient_id = metadata.get("patient_id")
    chunk_number = metadata.get("chunk_number")

    if chunk_number is not None:
        try:
            chunk_label = f"chunk_{int(chunk_number):03d}"
        except (TypeError, ValueError):
            chunk_label = str(chunk_number)
        return str(patient_id) if patient_id not in (None, "") else None, chunk_label

    return _chunk_key_from_identifier(metadata.get("chunk_id"))


def _chunk_keys_match(
    expected: tuple[str | None, str],
    returned: tuple[str | None, str],
) -> bool:
    expected_patient, expected_chunk = expected
    returned_patient, returned_chunk = returned
    same_patient = (
        expected_patient is None
        or returned_patient is None
        or expected_patient == returned_patient
    )
    return same_patient and expected_chunk == returned_chunk


def calculate_retrieval_metrics(
    expected_chunk_ids: list[str],
    context_documents: list[Any],
    ranked_documents: list[Any],
) -> dict[str, float] | None:
    expected_keys = {
        key
        for chunk_id in expected_chunk_ids
        if (key := _chunk_key_from_identifier(chunk_id)) is not None
    }
    if not expected_keys:
        return None

    context = list(context_documents[:CONTEXT_METRICS_K])
    context_keys = [
        key
        for document in context
        if (key := _document_chunk_key(document)) is not None
    ]
    ranking_keys = [
        _document_chunk_key(document)
        for document in ranked_documents[:RETRIEVAL_METRICS_K]
    ]

    found_expected = {
        expected
        for expected in expected_keys
        if any(_chunk_keys_match(expected, returned) for returned in context_keys)
    }
    relevant_context_count = sum(
        any(_chunk_keys_match(expected, returned) for expected in expected_keys)
        for returned in context_keys
    )
    context_precision = (
        relevant_context_count / len(context)
        if context
        else 0.0
    )

    first_relevant_rank = next(
        (
            rank
            for rank, returned in enumerate(ranking_keys, start=1)
            if returned is not None
            and any(
                _chunk_keys_match(expected, returned)
                for expected in expected_keys
            )
        ),
        None,
    )

    metrics = {
        "context_recall_at_2": len(found_expected) / len(expected_keys),
        "context_precision_at_2": context_precision,
        "mrr_at_10": 1.0 / first_relevant_rank if first_relevant_rank else 0.0,
    }
    for k in HIT_RATE_KS:
        metrics[f"hit_rate_at_{k}"] = float(
            any(
                any(
                    _chunk_keys_match(expected, returned)
                    for expected in expected_keys
                )
                for returned in ranking_keys[:k]
                if returned is not None
            )
        )

    return metrics


def evaluate_row(rag: Any, item: dict[str, Any]) -> dict[str, Any]:
    started_at = time.perf_counter()
    error = None
    result: dict[str, Any] = {}

    try:
        result = rag.ask(item["question"])
    except Exception as exc:  # pragma: no cover - usado para relatorio manual.
        error = str(exc)

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    answer = str(result.get("answer") or "").strip()
    sources = result.get("sources") or []
    documents = result.get("documents") or []
    expected_chunk_ids = list(item.get("expected_source_chunks") or [])
    ranked_documents: list[Any] = []

    if expected_chunk_ids and error is None:
        try:
            ranked_documents = rag._retrieve_documents(
                item["question"],
                top_k=RETRIEVAL_METRICS_K,
            )
        except Exception as exc:  # pragma: no cover - usado para relatorio manual.
            error = str(exc)

    retrieval_metrics = calculate_retrieval_metrics(
        expected_chunk_ids,
        documents,
        ranked_documents,
    )
    is_refusal = looks_like_refusal(answer)
    checks = evaluate_checks(item, answer, sources, documents, is_refusal, error)
    retrieval_checks = {
        name: passed
        for name, passed in checks.items()
        if name in {"fonte_chunk", "fonte_pagina", "metadados_recuperados"}
    }
    generation_checks = {
        name: passed
        for name, passed in checks.items()
        if name
        in {
            "resposta_presente",
            "recusa_esperada",
            "termos_obrigatorios",
            "termos_proibidos",
        }
    }
    status = "ok" if all(checks.values()) else "falha"

    return {
        "id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "answer": answer,
        "source_count": len(sources),
        "document_count": len(documents),
        "latency_ms": latency_ms,
        "is_refusal": is_refusal,
        "status": status,
        "checks": checks,
        "retrieval_status": "ok" if all(retrieval_checks.values()) else "falha",
        "generation_status": "ok" if all(generation_checks.values()) else "falha",
        "retrieval_metrics": retrieval_metrics,
        "error": error,
    }


def evaluate_checks(
    item: dict[str, Any],
    answer: str,
    sources: list[Any],
    documents: list[Any],
    is_refusal: bool,
    error: str | None,
) -> dict[str, bool]:
    if error:
        return {"sem_erro": False}

    normalized_answer = normalize_text(answer)
    expected_refusal = bool(item.get("should_refuse"))
    required_terms = [normalize_text(term) for term in item.get("must_contain", [])]
    forbidden_terms = [normalize_text(term) for term in item.get("must_not_contain", [])]
    expected_chunks = set(item.get("expected_source_chunks") or [])
    expected_chunk_keys = {
        key
        for chunk_id in expected_chunks
        if (key := _chunk_key_from_identifier(chunk_id)) is not None
    }
    expected_pages = {str(page) for page in item.get("expected_source_pages") or []}

    returned_document_chunk_keys = {
        key
        for document in documents
        if (key := _document_chunk_key(document)) is not None
    }
    returned_source_chunk_keys = {
        key
        for source in sources
        if isinstance(source, dict)
        and (key := _chunk_key_from_identifier(source.get("chunk"))) is not None
    }
    returned_chunk_keys = (
        returned_document_chunk_keys
        if returned_document_chunk_keys
        else returned_source_chunk_keys
    )
    returned_pages = {
        str(source.get("pagina"))
        for source in sources
        if isinstance(source, dict) and source.get("pagina") is not None
    }

    metadata_fields = set(item.get("expected_metadata_fields") or [])
    returned_metadata_fields = set()
    for doc in documents:
        metadata = getattr(doc, "metadata", {}) or {}
        returned_metadata_fields.update(
            key for key in metadata_fields if metadata.get(key) not in (None, "", [])
        )

    checks = {
        "sem_erro": True,
        "resposta_presente": bool(answer),
        "recusa_esperada": is_refusal if expected_refusal else not is_refusal,
        "termos_obrigatorios": all(term in normalized_answer for term in required_terms),
        "termos_proibidos": not any(term in normalized_answer for term in forbidden_terms),
    }

    if expected_chunks:
        checks["fonte_chunk"] = any(
            _chunk_keys_match(expected, returned)
            for expected in expected_chunk_keys
            for returned in returned_chunk_keys
        )

    if expected_pages:
        checks["fonte_pagina"] = bool(expected_pages & returned_pages)

    if metadata_fields:
        checks["metadados_recuperados"] = metadata_fields.issubset(returned_metadata_fields)

    return checks


def build_report(rows: list[dict[str, Any]]) -> str:
    automatic_rows = rows
    passed_rows = [row for row in automatic_rows if row["status"] == "ok"]
    retrieval_rows = [
        row for row in rows if row["checks"].keys() & {"fonte_chunk", "fonte_pagina", "metadados_recuperados"}
    ]
    retrieval_passed_rows = [
        row for row in retrieval_rows if row["retrieval_status"] == "ok"
    ]
    generation_passed_rows = [
        row for row in rows if row["generation_status"] == "ok"
    ]
    refusal_rows = [row for row in rows if row["category"] == "fora_do_acervo"]
    refusal_passed_rows = [
        row for row in refusal_rows if row["checks"].get("recusa_esperada")
    ]
    metric_rows = [
        row for row in rows if row.get("retrieval_metrics") is not None
    ]

    def average_metric(name: str) -> float:
        if not metric_rows:
            return 0.0
        return sum(row["retrieval_metrics"][name] for row in metric_rows) / len(
            metric_rows
        )

    average_latency = (
        sum(row["latency_ms"] for row in rows) / len(rows)
        if rows
        else 0
    )
    retrieval_rate = (
        len(retrieval_passed_rows) / len(retrieval_rows) * 100
        if retrieval_rows
        else 0
    )
    generation_rate = (
        len(generation_passed_rows) / len(rows) * 100
        if rows
        else 0
    )
    refusal_rate = (
        len(refusal_passed_rows) / len(refusal_rows) * 100
        if refusal_rows
        else 0
    )

    lines = [
        "# Resultados da avaliacao RAG",
        "",
        "Relatorio gerado por `python eval/evaluate_rag.py`.",
        "",
        "## Resumo",
        "",
        f"- Total de perguntas: {len(rows)}",
        f"- Avaliadas automaticamente: {len(automatic_rows)}",
        f"- Aprovadas automaticamente: {len(passed_rows)}",
        "- Revisao manual: 0",
        f"- Recuperacao ok: {len(retrieval_passed_rows)}/{len(retrieval_rows)} ({retrieval_rate:.1f}%)",
        f"- Geracao ok: {len(generation_passed_rows)}/{len(rows)} ({generation_rate:.1f}%)",
        f"- Recusa fora do acervo ok: {len(refusal_passed_rows)}/{len(refusal_rows)} ({refusal_rate:.1f}%)",
        f"- Latencia media: {average_latency:.0f} ms",
        "",
        "A avaliacao usa gold set versionado com resposta esperada, termos",
        "obrigatorios/proibidos, fonte esperada e comportamento de recusa.",
        "",
        "## Metricas da camada de recuperacao",
        "",
        f"- Casos com chunks positivos anotados: {len(metric_rows)}",
        f"- Context Recall@2: {average_metric('context_recall_at_2') * 100:.1f}%",
        f"- Context Precision@2: {average_metric('context_precision_at_2') * 100:.1f}%",
        f"- Hit Rate@1: {average_metric('hit_rate_at_1') * 100:.1f}%",
        f"- Hit Rate@2: {average_metric('hit_rate_at_2') * 100:.1f}%",
        f"- Hit Rate@5: {average_metric('hit_rate_at_5') * 100:.1f}%",
        f"- Hit Rate@10: {average_metric('hit_rate_at_10') * 100:.1f}%",
        f"- MRR@10: {average_metric('mrr_at_10'):.3f}",
        "",
        "Context Precision@2 considera somente os chunks positivos anotados",
        "no golden set; chunks relevantes nao anotados sao contabilizados como",
        "nao relevantes.",
        "",
        "## Resultados por pergunta",
        "",
        "| ID | Categoria | Status | Recuperacao | Geracao | Latencia | Fontes | Docs | Recusa | Checks com falha |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]

    for row in rows:
        refusal = "sim" if row["is_refusal"] else "nao"
        failed_checks = [
            check_name
            for check_name, passed in row["checks"].items()
            if not passed
        ]
        failed_checks_text = ", ".join(failed_checks) if failed_checks else "-"
        lines.append(
            "| {id} | {category} | {status} | {retrieval_status} | "
            "{generation_status} | {latency_ms} ms | {source_count} | "
            "{document_count} | {refusal} | {failed_checks} |".format(
                refusal=refusal,
                failed_checks=failed_checks_text,
                **row,
            )
        )

    lines.extend(
        [
            "",
            "## Metricas de recuperacao por pergunta",
            "",
            "| ID | Context Recall@2 | Context Precision@2 | Hit Rate@1 | Hit Rate@2 | Hit Rate@5 | Hit Rate@10 | MRR@10 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in metric_rows:
        metrics = row["retrieval_metrics"]
        lines.append(
            f"| {row['id']} | "
            f"{metrics['context_recall_at_2'] * 100:.1f}% | "
            f"{metrics['context_precision_at_2'] * 100:.1f}% | "
            f"{metrics['hit_rate_at_1']:.0f} | "
            f"{metrics['hit_rate_at_2']:.0f} | "
            f"{metrics['hit_rate_at_5']:.0f} | "
            f"{metrics['hit_rate_at_10']:.0f} | "
            f"{metrics['mrr_at_10']:.3f} |"
        )

    lines.extend(["", "## Observacoes", ""])
    for row in rows:
        if row["error"]:
            lines.append(f"- {row['id']}: erro durante avaliacao: {row['error']}")
        elif row["status"] == "falha":
            lines.append(
                f"- {row['id']}: revisar resposta manualmente; "
                "criterio automatico marcou falha."
            )

    lines.extend(
        [
            "",
            "## Melhoria futura",
            "",
            "- Mutation testing nao foi implementado nesta rodada; pode ser avaliado",
            "  depois que a suite base estiver estavel.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    from src.pipeline.rag_chain import ClinicalRAG

    questions = load_golden_set()
    rag = ClinicalRAG()
    rows = [evaluate_row(rag, item) for item in questions]

    RESULTS_PATH.write_text(build_report(rows), encoding="utf-8")
    print(f"Relatorio gerado em {RESULTS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
