from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.evaluate_rag import build_report, evaluate_row, load_golden_set

CONFIG_PATH = PROJECT_ROOT / "eval" / "regression_config.json"
OUTPUT_JSON_PATH = PROJECT_ROOT / "eval" / "regression_results.json"
OUTPUT_MD_PATH = PROJECT_ROOT / "eval" / "regression_results.md"


def _rate(part: int, total: int) -> float:
    return part / total if total else 0.0


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    automatic_rows = [row for row in rows if row["status"] != "avaliar manualmente"]
    passed_rows = [row for row in automatic_rows if row["status"] == "ok"]
    retrieval_rows = [
        row
        for row in rows
        if row["checks"].keys()
        & {"fonte_chunk", "fonte_pagina", "metadados_recuperados", "tipo_documento_correto"}
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
        return sum(row["retrieval_metrics"][name] for row in metric_rows) / len(metric_rows)

    return {
        "total_questions": len(rows),
        "automatic_questions": len(automatic_rows),
        "automatic_passed": len(passed_rows),
        "automatic_success_rate": _rate(len(passed_rows), len(automatic_rows)),
        "retrieval_cases": len(retrieval_rows),
        "retrieval_passed": len(retrieval_passed_rows),
        "retrieval_success_rate": _rate(len(retrieval_passed_rows), len(retrieval_rows)),
        "generation_passed": len(generation_passed_rows),
        "generation_success_rate": _rate(len(generation_passed_rows), len(rows)),
        "refusal_cases": len(refusal_rows),
        "refusal_passed": len(refusal_passed_rows),
        "refusal_success_rate": _rate(len(refusal_passed_rows), len(refusal_rows)),
        "context_recall_at_2": average_metric("context_recall_at_2"),
        "context_precision_at_2": average_metric("context_precision_at_2"),
        "hit_rate_at_1": average_metric("hit_rate_at_1"),
        "hit_rate_at_2": average_metric("hit_rate_at_2"),
        "hit_rate_at_5": average_metric("hit_rate_at_5"),
        "hit_rate_at_10": average_metric("hit_rate_at_10"),
        "mrr_at_10": average_metric("mrr_at_10"),
        "avg_latency_ms": (
            sum(row["latency_ms"] for row in rows) / len(rows) if rows else 0.0
        ),
    }


def evaluate_regression(
    summary: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    failures = []
    baseline = config.get("baseline", {})
    thresholds = config.get("thresholds", {})

    for metric, rule in thresholds.items():
        current = float(summary.get(metric, 0.0))
        minimum = float(rule.get("min", float("-inf")))
        baseline_value = baseline.get(metric)
        max_drop = float(rule.get("max_drop", 0.0))
        allowed_from_baseline = (
            float(baseline_value) - max_drop
            if baseline_value is not None
            else float("-inf")
        )
        effective_min = max(minimum, allowed_from_baseline)

        if current < effective_min:
            failures.append(
                {
                    "metric": metric,
                    "current": current,
                    "required": effective_min,
                    "baseline": baseline_value,
                    "min": minimum,
                    "max_drop": max_drop,
                }
            )

    return failures


def build_regression_report(
    summary: dict[str, Any],
    failures: list[dict[str, Any]],
) -> str:
    status = "falhou" if failures else "aprovado"
    lines = [
        "# Regressao de configuracao RAG",
        "",
        f"- Status: {status}",
        f"- Perguntas: {summary['total_questions']}",
        f"- Aprovacao automatica: {summary['automatic_passed']}/{summary['automatic_questions']} ({summary['automatic_success_rate'] * 100:.1f}%)",
        f"- Recuperacao: {summary['retrieval_passed']}/{summary['retrieval_cases']} ({summary['retrieval_success_rate'] * 100:.1f}%)",
        f"- Geracao: {summary['generation_passed']}/{summary['total_questions']} ({summary['generation_success_rate'] * 100:.1f}%)",
        f"- Recusa fora do acervo: {summary['refusal_passed']}/{summary['refusal_cases']} ({summary['refusal_success_rate'] * 100:.1f}%)",
        f"- Context Recall@2: {summary['context_recall_at_2'] * 100:.1f}%",
        f"- Context Precision@2: {summary['context_precision_at_2'] * 100:.1f}%",
        f"- Hit Rate@2: {summary['hit_rate_at_2'] * 100:.1f}%",
        f"- Hit Rate@5: {summary['hit_rate_at_5'] * 100:.1f}%",
        f"- Hit Rate@10: {summary['hit_rate_at_10'] * 100:.1f}%",
        f"- MRR@10: {summary['mrr_at_10']:.3f}",
        f"- Latencia media: {summary['avg_latency_ms']:.0f} ms",
        "",
    ]

    if failures:
        lines.extend(
            [
                "## Falhas",
                "",
                "| Metrica | Atual | Minimo exigido | Baseline |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for failure in failures:
            baseline = failure["baseline"]
            baseline_text = "-" if baseline is None else f"{float(baseline):.4f}"
            lines.append(
                f"| {failure['metric']} | {failure['current']:.4f} | "
                f"{failure['required']:.4f} | {baseline_text} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Como usar",
            "",
            "Execute este arquivo em toda alteracao de configuracao do RAG:",
            "",
            "```bash",
            "python eval/regression.py",
            "```",
            "",
            "O comando roda o mesmo golden set versionado e falha com codigo 1 se alguma metrica cair abaixo do limite configurado.",
        ]
    )
    return "\n".join(lines)


def load_rows_from_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    raise ValueError(f"Formato de rows invalido em {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa a suite de avaliacao e aplica o gate de regressao."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Arquivo JSON com baseline e thresholds.",
    )
    parser.add_argument(
        "--rows-json",
        type=Path,
        default=None,
        help="Opcional: reutiliza rows ja avaliadas, sem chamar Ollama/RAG.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=OUTPUT_JSON_PATH,
        help="Destino do resultado estruturado.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=OUTPUT_MD_PATH,
        help="Destino do relatorio markdown de regressao.",
    )
    parser.add_argument(
        "--full-report",
        type=Path,
        default=None,
        help="Opcional: grava tambem o relatorio completo da avaliacao.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))

    if args.rows_json:
        print(f"Carregando rows avaliadas de {args.rows_json}", flush=True)
        rows = load_rows_from_json(args.rows_json)
    else:
        from eval.llm_as_a_judge.judge import LLMJudge
        from src.pipeline.rag_chain import ClinicalRAG

        print("Carregando golden set...", flush=True)
        questions = load_golden_set()
        print("Inicializando ClinicalRAG...", flush=True)
        rag = ClinicalRAG()
        print("Inicializando LLMJudge...", flush=True)
        judge = LLMJudge()
        rows = []
        for index, item in enumerate(questions, start=1):
            print(
                f"Avaliando {index}/{len(questions)}: {item['id']}",
                flush=True,
            )
            rows.append(evaluate_row(rag, item, judge))
        if len(rows) != len(questions):
            raise RuntimeError("A avaliacao nao retornou todas as perguntas do golden set.")

    summary = summarize_rows(rows)
    failures = evaluate_regression(summary, config)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed" if failures else "passed",
        "summary": summary,
        "failures": failures,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.output_md.write_text(
        build_regression_report(summary, failures),
        encoding="utf-8",
    )

    if args.full_report:
        args.full_report.parent.mkdir(parents=True, exist_ok=True)
        args.full_report.write_text(build_report(rows), encoding="utf-8")

    print(f"Regressao: {result['status']}")
    print(f"Resumo JSON: {args.output_json}")
    print(f"Relatorio: {args.output_md}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
