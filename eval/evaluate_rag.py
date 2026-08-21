from __future__ import annotations

import json
import re
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

def extract_claims(text: str) -> list[str]:
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    claims = [s.strip() for s in raw_sentences if len(s.strip()) > 15]
    return claims


def evaluate_claim_faithfulness(
    claims: list[str],
    retrieved_texts: list[str],
    sources: list[Any],
) -> dict[str, Any]:
    if not claims:
        return {
            "total_claims": 0,
            "supported_claims": 0,
            "faithfulness_score": 0.0,
            "has_citation": bool(sources),
        }

    full_context = " ".join(retrieved_texts).lower()
    supported = 0

    for claim in claims:
        words = [w.lower() for w in re.findall(r"\b\w{4,}\b", claim)]
        if not words:
            continue

        matches = sum(1 for word in words if word in full_context)
        match_ratio = matches / len(words)

        if match_ratio >= 0.5:
            supported += 1

    score = round((supported / len(claims)) * 100, 1)
    return {
        "total_claims": len(claims),
        "supported_claims": supported,
        "faithfulness_score": score,
        "has_citation": bool(sources),
    }

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

    retrieved_texts = []
    for doc in documents:
        if isinstance(doc, dict):
            retrieved_texts.append(doc.get("page_content") or doc.get("text") or "")
        elif hasattr(doc, "page_content"):
            retrieved_texts.append(doc.page_content)

    is_refusal = looks_like_refusal(answer)
    status = classify_status(item, answer, sources, documents, is_refusal, error)
    claims = extract_claims(answer) if not is_refusal else []
    faith_metrics = evaluate_claim_faithfulness(claims, retrieved_texts, sources)

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
        "total_claims": faith_metrics["total_claims"],
        "supported_claims": faith_metrics["supported_claims"],
        "faithfulness_score": faith_metrics["faithfulness_score"],
        "has_citation": faith_metrics["has_citation"],
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
    valid_faith_rows = [r for r in rows if not r["is_refusal"] and r["total_claims"] > 0]
    avg_faithfulness = (
        sum(r["faithfulness_score"] for r in valid_faith_rows) / len(valid_faith_rows)
        if valid_faith_rows else 0.0
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
        f"- Fidelidade Média (Claim-level):** {avg_faithfulness:.1f}%",
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
        citation = "sim" if row["has_citation"] else "nao"
        claims_fmt = f"{row['supported_claims']}/{row['total_claims']}"
        lines.append(
            f"| {row['id']} | {row['status']} | {row['latency_ms']} ms | "
            f"{claims_fmt} | {row['faithfulness_score']}% | {citation} | {refusal} |"
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
