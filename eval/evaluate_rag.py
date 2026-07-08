from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = PROJECT_ROOT / "eval" / "test_questions.json"
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


def load_questions() -> list[dict[str, Any]]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


def looks_like_refusal(answer: str) -> bool:
    normalized_answer = " ".join(str(answer or "").lower().split())
    return any(marker in normalized_answer for marker in REFUSAL_MARKERS)


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
    status = classify_status(item, answer, sources, documents, is_refusal, error)

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
        "error": error,
    }


def classify_status(
    item: dict[str, Any],
    answer: str,
    sources: list[Any],
    documents: list[Any],
    is_refusal: bool,
    error: str | None,
) -> str:
    if item["category"] == "paciente_metadados":
        return "avaliar manualmente"

    if error:
        return "falha"

    if item["category"] == "fora_do_acervo":
        return "ok" if is_refusal else "falha"

    has_grounding = bool(sources) or bool(documents)
    if answer and has_grounding and not is_refusal:
        return "ok"

    return "falha"


def build_report(rows: list[dict[str, Any]]) -> str:
    automatic_rows = [row for row in rows if row["status"] != "avaliar manualmente"]
    passed_rows = [row for row in automatic_rows if row["status"] == "ok"]
    manual_rows = [row for row in rows if row["status"] == "avaliar manualmente"]
    average_latency = (
        sum(row["latency_ms"] for row in rows) / len(rows)
        if rows
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
        f"- Revisao manual: {len(manual_rows)}",
        f"- Latencia media: {average_latency:.0f} ms",
        "",
        "Perguntas sobre paciente/metadados ficam fora da taxa automatica,",
        "pois dependem da recuperacao dos metadados do chunk.",
        "",
        "## Resultados por pergunta",
        "",
        "| ID | Categoria | Status | Latencia | Fontes | Docs | Recusa |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]

    for row in rows:
        refusal = "sim" if row["is_refusal"] else "nao"
        lines.append(
            "| {id} | {category} | {status} | {latency_ms} ms | "
            "{source_count} | {document_count} | {refusal} |".format(
                refusal=refusal,
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

    questions = load_questions()
    rag = ClinicalRAG()
    rows = [evaluate_row(rag, item) for item in questions]

    RESULTS_PATH.write_text(build_report(rows), encoding="utf-8")
    print(f"Relatorio gerado em {RESULTS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
