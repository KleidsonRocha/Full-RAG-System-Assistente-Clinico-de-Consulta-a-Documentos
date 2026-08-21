import json
import sys
import time
from pathlib import Path
from typing import Any
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.evaluate_rag import calculate_retrieval_metrics, evaluate_checks, looks_like_refusal
from eval.llm_as_a_judge.judge import LLMJudge
from src.pipeline.rag_chain import ClinicalRAG
from src.embedding.embeddings import OLLAMA_BASE_URL

GOLDEN_SET_PATH = PROJECT_ROOT / "eval" / "golden_set.json"
BENCHMARK_JSON = PROJECT_ROOT / "eval" / "benchmark" / "benchmark_results.json"
BENCHMARK_MD = PROJECT_ROOT / "eval" / "benchmark" / "benchmark_results.md"

CONFIGURATIONS = [
    {
        "name": "Configuração 1",
        "embedding_model": "nomic-embed-text",
        "llm_model": "qwen2.5:3b",
        "description": "Baseline padrão do projeto",
    },
    {
        "name": "Configuração 2",
        "embedding_model": "all-minilm",
        "llm_model": "qwen2.5:3b",
        "description": "Avaliação do retriever com all-minilm",
    },
    {
        "name": "Configuração 3",
        "embedding_model": "nomic-embed-text",
        "llm_model": "ministral-3:3b",
        "description": "Avaliação do gerador com ministral-3:3b",
    },
    {
        "name": "Configuração 4",
        "embedding_model": "all-minilm",
        "llm_model": "ministral-3:3b",
        "description": "Combinação de all-minilm com ministral-3:3b",
    },
]


def get_rag_for_config(config: dict[str, Any], base_rag: ClinicalRAG) -> ClinicalRAG:
    rag = ClinicalRAG()
    
    rag.llm = ChatOllama(
        model=config["llm_model"],
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )
    if hasattr(rag, "chain") and hasattr(rag, "prompt"):
        rag.chain = rag.prompt | rag.llm

    if config["embedding_model"] != "nomic-embed-text":
        new_embeddings = OllamaEmbeddings(
            model=config["embedding_model"],
            base_url=OLLAMA_BASE_URL,
        )
        existing_docs = list(base_rag.vector_store.docstore._dict.values())
        rag.embeddings = new_embeddings
        rag.vector_store = FAISS.from_documents(existing_docs, new_embeddings)
        rag.retriever = rag.vector_store.as_retriever(search_kwargs={"k": 2})

    return rag


def run_benchmark_for_config(
    config: dict[str, Any], 
    questions: list[dict[str, Any]], 
    judge: LLMJudge, 
    base_rag: ClinicalRAG
) -> dict[str, Any]:
    print(f"--> Executando: {config['name']} (Embedding: {config['embedding_model']}, LLM: {config['llm_model']})...")
    
    rag = get_rag_for_config(config, base_rag)
    
    rows = []
    latencies = []
    
    for item in questions:
        started_at = time.perf_counter()
        error = None
        result = {}
        try:
            result = rag.ask(item["question"])
        except Exception as exc:
            error = str(exc)
        
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        latencies.append(latency_ms)
        
        answer = str(result.get("answer") or "").strip()
        sources = result.get("sources") or []
        documents = result.get("documents") or []
        expected_chunk_ids = list(item.get("expected_source_chunks") or [])
        ranked_documents = []
        
        if expected_chunk_ids and error is None:
            try:
                ranked_documents = rag._retrieve_documents(item["question"], top_k=10)
            except Exception as exc:
                error = str(exc)
        
        retrieval_metrics = calculate_retrieval_metrics(expected_chunk_ids, documents, ranked_documents)
        is_refusal = looks_like_refusal(answer)
        checks = evaluate_checks(item, answer, sources, documents, is_refusal, error)
        
        judge_eval = {"faithfulness_score": 0, "relevance_score": 0, "refusal_score": 0, "justification": ""}
        if error is None:
            try:
                rag_context = rag._format_context(documents)
                rag_metadata = rag._format_patient_metadata(documents, item["question"])
                full_context = f"{rag_metadata}\n\n{rag_context}".strip()
                
                judge_eval = judge.evaluate(
                    question=item["question"],
                    context=full_context,
                    expected_answer=item.get("expected_answer", ""),
                    atomic_claims=item.get("atomic_claims", []),
                    generated_answer=answer,
                )
            except Exception as exc:
                judge_eval["justification"] = f"Erro no juiz: {str(exc)}"
        
        rows.append({
            "id": item["id"],
            "checks": checks,
            "retrieval_metrics": retrieval_metrics,
            "judge_eval": judge_eval,
            "latency_ms": latency_ms,
        })
        
    metric_rows = [r for r in rows if r.get("retrieval_metrics") is not None]
    
    def avg_retrieval(metric_name: str) -> float:
        if not metric_rows:
            return 0.0
        return sum(r["retrieval_metrics"][metric_name] for r in metric_rows) / len(metric_rows)
    
    total = len(rows)
    return {
        "config": config,
        "summary": {
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "context_recall_at_2": avg_retrieval("context_recall_at_2") * 100,
            "context_precision_at_2": avg_retrieval("context_precision_at_2") * 100,
            "hit_rate_at_2": avg_retrieval("hit_rate_at_2") * 100,
            "mrr_at_10": avg_retrieval("mrr_at_10"),
            "judge_faithfulness": sum(r["judge_eval"]["faithfulness_score"] for r in rows) / total * 100,
            "judge_relevance": sum(r["judge_eval"]["relevance_score"] for r in rows) / total * 100,
            "judge_refusal": sum(r["judge_eval"]["refusal_score"] for r in rows) / total * 100,
        },
        "rows": rows,
    }


def main():
    if not GOLDEN_SET_PATH.exists():
        raise FileNotFoundError(f"Golden set nao encontrado: {GOLDEN_SET_PATH}")
        
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    judge = LLMJudge()
    base_rag = ClinicalRAG()
    benchmark_outputs = []
    
    BENCHMARK_JSON.parent.mkdir(parents=True, exist_ok=True)
    
    for cfg in CONFIGURATIONS:
        res = run_benchmark_for_config(cfg, questions, judge, base_rag)
        benchmark_outputs.append(res)
        
    with open(BENCHMARK_JSON, "w", encoding="utf-8") as f:
        json.dump(benchmark_outputs, f, ensure_ascii=False, indent=2)
        
    md_lines = [
        "# Benchmark Comparativo de Configuracoes RAG",
        "",
        "## Tabela Consolidada de Resultados",
        "",
        "| Configuracao | Embedding | LLM | Recall@2 | Hit Rate@2 | MRR@10 | Fidelidade | Relevancia | Recusa | Latencia Media |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    
    for out in benchmark_outputs:
        cfg = out["config"]
        s = out["summary"]
        md_lines.append(
            f"| {cfg['name']} | {cfg['embedding_model']} | {cfg['llm_model']} | "
            f"{s['context_recall_at_2']:.1f}% | {s['hit_rate_at_2']:.1f}% | {s['mrr_at_10']:.3f} | "
            f"{s['judge_faithfulness']:.1f}% | {s['judge_relevance']:.1f}% | {s['judge_refusal']:.1f}% | "
            f"{s['avg_latency_ms']:.0f} ms |"
        )
        
    BENCHMARK_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nBenchmark finalizado com sucesso! Relatorios em:\n- {BENCHMARK_JSON}\n- {BENCHMARK_MD}")


if __name__ == "__main__":
    main()