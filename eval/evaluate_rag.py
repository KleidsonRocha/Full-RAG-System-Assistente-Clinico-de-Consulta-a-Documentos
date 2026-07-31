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
    expected_pages = {str(page) for page in item.get("expected_source_pages") or []}

    returned_chunks = {
        str(source.get("chunk"))
        for source in sources
        if isinstance(source, dict) and source.get("chunk")
    }
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
        checks["fonte_chunk"] = bool(expected_chunks & returned_chunks)

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
