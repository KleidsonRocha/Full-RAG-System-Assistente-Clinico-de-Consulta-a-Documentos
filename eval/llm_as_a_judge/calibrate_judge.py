import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
 
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
 
from eval.llm_as_a_judge.judge import LLMJudge
from src.pipeline.rag_chain import ClinicalRAG
 
CALIBRATION_FILE = PROJECT_ROOT / "eval" / "llm_as_a_judge" / "calibration_set.json"
RESULTS_JSON = PROJECT_ROOT / "eval" / "llm_as_a_judge" / "calibration_results.json"
RESULTS_MD = PROJECT_ROOT / "eval" / "llm_as_a_judge" / "calibration_results.md"

JUDGE_RUNS_PER_CASE = 3
 
 
def majority_vote(scores: list[int]) -> int:
    """Voto majoritario entre as N rodadas do juiz para um mesmo score."""
    return 1 if sum(scores) > len(scores) / 2 else 0

def evaluate_retrieval(item: dict, rag_result: dict) -> dict[str, bool]:
    sources = rag_result.get("sources", [])
    documents = rag_result.get("documents", [])

    returned_chunks = {
        str(s.get("chunk")) for s in sources if isinstance(s, dict) and s.get("chunk")
    }
    returned_pages = {
        int(s.get("pagina")) for s in sources if isinstance(s, dict) and s.get("pagina") is not None
    }

    expected_chunks = set(item.get("expected_source_chunks", []))
    expected_pages = set(item.get("expected_source_pages", []))

    chunk_hit = bool(expected_chunks & returned_chunks) if expected_chunks else True
    page_hit = bool(expected_pages & returned_pages) if expected_pages else True

    return {
        "retrieval_chunk_hit": chunk_hit,
        "retrieval_page_hit": page_hit,
        "retrieval_ok": chunk_hit and page_hit,
    }

 
def main():
    if not CALIBRATION_FILE.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {CALIBRATION_FILE}")
 
    with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)
 
    if not cases:
        raise ValueError("calibration_set.json esta vazio -- nada para calibrar.")
 
    rag = ClinicalRAG()
    judge = LLMJudge()
 
    results = []
    skipped_unlabeled = []
    errored_cases = []
 
    print(f"Iniciando calibracao do LLM as a Judge com {len(cases)} casos "
          f"({JUDGE_RUNS_PER_CASE}x por caso)...\n")
 
    for index, item in enumerate(cases, start=1):
        question = item["question"]
        print(f"[{index}/{len(cases)}] Avaliando caso '{item['id']}' ({item['category']})...")

        human_labels = (item.get("human_faithfulness"), item.get("human_relevance"), item.get("human_refusal"))
        if any(v is None for v in human_labels):
            print(f"  - PULADO: rotulo humano ausente (human_* = null). "
                  f"Preencha apos revisao manual antes de incluir na calibracao.\n")
            skipped_unlabeled.append(item["id"])
            continue
 
        try:
            rag_result = rag.ask(question)
            generated_answer = rag_result["answer"]
            documents = rag_result.get("documents", [])
 
            context_parts = []
            for doc in documents:
                context_parts.append(doc.page_content or "")
                meta = doc.metadata or {}
                for k in ("paciente_nome", "paciente_ultimo_peso_kg", "paciente_medicamentos_historico"):
                    if k in meta:
                        context_parts.append(f"{k}: {meta[k]}")
            full_context = "\n\n".join(context_parts)

            run_scores = {"faithfulness_score": [], "relevance_score": [], "refusal_score": []}
            justifications = []
            for _ in range(JUDGE_RUNS_PER_CASE):
                judge_eval = judge.evaluate(
                    question=question,
                    context=full_context,
                    expected_answer=item["expected_answer"],
                    atomic_claims=item["atomic_claims"],
                    generated_answer=generated_answer,
                )
                for key in run_scores:
                    run_scores[key].append(judge_eval[key])
                justifications.append(judge_eval["justification"])
 
            final_scores = {key: majority_vote(vals) for key, vals in run_scores.items()}
            variance = {key: len(set(vals)) > 1 for key, vals in run_scores.items()}
 
        except Exception as exc:
            print(f"  - ERRO ao avaliar este caso, pulando: {exc}\n")
            errored_cases.append({"id": item["id"], "error": str(exc)})
            continue
 
        f_match = final_scores["faithfulness_score"] == item["human_faithfulness"]
        r_match = final_scores["relevance_score"] == item["human_relevance"]
        ref_match = final_scores["refusal_score"] == item["human_refusal"]
 
        retrieval_eval = evaluate_retrieval(item=item, rag_result=rag_result)

        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": question,
            "generated_answer": generated_answer,
            "retrieval": retrieval_eval,
            "judge_runs": run_scores,
            "judge_final": final_scores,
            "judge_variance": variance,
            "human": {
                "faithfulness": item["human_faithfulness"],
                "relevance": item["human_relevance"],
                "refusal": item["human_refusal"],
            },
            "match": {"faithfulness": f_match, "relevance": r_match, "refusal": ref_match},
            "justifications": justifications,
        })
 
        preview = generated_answer if len(generated_answer) <= 200 else generated_answer[:200] + "..."
        print(f"  - Pergunta: {question}")
        print(f"  - Resposta RAG: {preview}")
        print(f"  - Juiz (voto majoritario, {JUDGE_RUNS_PER_CASE}x): "
              f"F={final_scores['faithfulness_score']}, R={final_scores['relevance_score']}, "
              f"Ref={final_scores['refusal_score']}")
        if any(variance.values()):
            print(f"  - AVISO: juiz instavel entre as {JUDGE_RUNS_PER_CASE} rodadas em: "
                  f"{[k for k, v in variance.items() if v]}")
        print(f"  - Humano: F={item['human_faithfulness']}, R={item['human_relevance']}, "
              f"Ref={item['human_refusal']}\n")
 
    if not results:
        print("Nenhum caso rotulado foi avaliado. Nada para reportar.")
        return
 
    total_cases = len(results)
    faithfulness_matches = sum(r["match"]["faithfulness"] for r in results)
    relevance_matches = sum(r["match"]["relevance"] for r in results)
    refusal_matches = sum(r["match"]["refusal"] for r in results)
 
    f_rate = (faithfulness_matches / total_cases) * 100
    r_rate = (relevance_matches / total_cases) * 100
    ref_rate = (refusal_matches / total_cases) * 100
    overall_rate = ((faithfulness_matches + relevance_matches + refusal_matches) / (total_cases * 3)) * 100
 
    by_category = defaultdict(lambda: {"n": 0, "f": 0, "r": 0, "ref": 0})
    for r in results:
        c = by_category[r["category"]]
        c["n"] += 1
        c["f"] += r["match"]["faithfulness"]
        c["r"] += r["match"]["relevance"]
        c["ref"] += r["match"]["refusal"]
 
    unstable_cases = [r["id"] for r in results if any(r["judge_variance"].values())]
 
    print("=" * 50)
    print("RESULTADOS DA CALIBRACAO")
    print("=" * 50)
    print(f"Casos avaliados:            {total_cases}")
    if skipped_unlabeled:
        print(f"Casos pulados (sem rotulo humano): {len(skipped_unlabeled)} -> {skipped_unlabeled}")
    if errored_cases:
        print(f"Casos com erro tecnico:     {len(errored_cases)} -> {[c['id'] for c in errored_cases]}")
    print(f"Concordancia em Fidelidade: {f_rate:.1f}% ({faithfulness_matches}/{total_cases})")
    print(f"Concordancia em Relevancia: {r_rate:.1f}% ({relevance_matches}/{total_cases})")
    print(f"Concordancia em Recusa:     {ref_rate:.1f}% ({refusal_matches}/{total_cases})")
    print(f"Concordancia Global:        {overall_rate:.1f}%")
    print("-" * 50)
    print("Por categoria:")
    for cat, c in by_category.items():
        print(f"  {cat}: F={c['f']}/{c['n']} R={c['r']}/{c['n']} Ref={c['ref']}/{c['n']}")
    if unstable_cases:
        print("-" * 50)
        print(f"Casos com variancia entre as {JUDGE_RUNS_PER_CASE} rodadas do juiz "
              f"(revisar prompt antes de confiar): {unstable_cases}")
    print("=" * 50)

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "run_at": datetime.now(timezone.utc).isoformat(),
            "judge_runs_per_case": JUDGE_RUNS_PER_CASE,
            "summary": {
                "total_cases": total_cases,
                "skipped_unlabeled": skipped_unlabeled,
                "errored_cases": errored_cases,
                "faithfulness_rate": f_rate,
                "relevance_rate": r_rate,
                "refusal_rate": ref_rate,
                "overall_rate": overall_rate,
                "by_category": by_category,
                "unstable_cases": unstable_cases,
            },
            "results": results,
        }, f, ensure_ascii=False, indent=2, default=str)
 
    with open(RESULTS_MD, "w", encoding="utf-8") as f:
        f.write("# Calibracao do LLM as a Judge\n\n")
        f.write(f"Executado em: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"Rodadas por caso: {JUDGE_RUNS_PER_CASE}\n\n")
        f.write(f"- Concordancia em Fidelidade: {f_rate:.1f}% ({faithfulness_matches}/{total_cases})\n")
        f.write(f"- Concordancia em Relevancia: {r_rate:.1f}% ({relevance_matches}/{total_cases})\n")
        f.write(f"- Concordancia em Recusa: {ref_rate:.1f}% ({refusal_matches}/{total_cases})\n")
        f.write(f"- Concordancia Global: {overall_rate:.1f}%\n\n")
        if skipped_unlabeled:
            f.write(f"Casos pulados (sem rotulo humano): {skipped_unlabeled}\n\n")
        f.write("## Por categoria\n\n")
        f.write("| Categoria | Fidelidade | Relevancia | Recusa |\n|---|---|---|---|\n")
        for cat, c in by_category.items():
            f.write(f"| {cat} | {c['f']}/{c['n']} | {c['r']}/{c['n']} | {c['ref']}/{c['n']} |\n")
        if unstable_cases:
            f.write(f"\n## Casos instaveis entre rodadas do juiz\n\n{unstable_cases}\n")
    print(f"\nResultados salvos em:\n  {RESULTS_JSON}\n  {RESULTS_MD}")
 
 
if __name__ == "__main__":
    main()