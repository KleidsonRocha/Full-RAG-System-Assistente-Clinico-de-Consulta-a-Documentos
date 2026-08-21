# Benchmark Comparativo de Configuracoes RAG

## Tabela Consolidada de Resultados

| Configuracao | Embedding | LLM | Recall@2 | Hit Rate@2 | MRR@10 | Fidelidade | Relevancia | Recusa | Latencia Media |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Configuração 1 | nomic-embed-text | qwen2.5:3b | 56.2% | 62.5% | 0.646 | 86.7% | 83.3% | 86.7% | 1387 ms |
| Configuração 2 | all-minilm | qwen2.5:3b | 37.5% | 37.5% | 0.426 | 66.7% | 63.3% | 66.7% | 1145 ms |
| Configuração 3 | nomic-embed-text | ministral-3:3b | 56.2% | 62.5% | 0.646 | 83.3% | 80.0% | 83.3% | 3535 ms |
| Configuração 4 | all-minilm | ministral-3:3b | 37.5% | 37.5% | 0.426 | 66.7% | 66.7% | 76.7% | 5106 ms |
 