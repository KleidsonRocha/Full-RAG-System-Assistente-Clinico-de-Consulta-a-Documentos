## Conclusao e Decisao Arquitetural

A avaliacao sistematica isolou o impacto individual e combinado das camadas de recuperacao (embeddings) e geracao (LLM) sobre o `golden_set.json` completo:

### 1. Desempenho da Camada de Recuperacao (Embeddings)
- O modelo **`nomic-embed-text`** superou amplamente o **`all-minilm`** em todas as metricas de busca:
  * **Context Recall@2:** 56.2% contra 37.5% (+18.7 pp).
  * **Hit Rate@2:** 62.5% contra 37.5% (+25.0 pp).
  * **MRR@10:** 0.646 contra 0.426 (+0.220).
- **Impacto na Geracao:** A degradacao do retrieval no `all-minilm` causou efeito em cascata no gerador, derrubando a Fidelidade de 86.7% para 66.7% e a Relevancia de 83.3% para 63.3% devido a falta de contexto clinico relevante no `top_k=2`.

### 2. Desempenho da Camada de Geracao (Modelos LLM)
- Sob o mesmo contexto (`nomic-embed-text`), o **`qwen2.5:3b`** apresentou desempenho superior ao **`ministral-3:3b`**:
  * **Fidelidade:** 86.7% contra 83.3%.
  * **Relevancia:** 83.3% contra 80.0%.
  * **Latencia Media:** 1387 ms contra 3535 ms (2.5x mais rapido).
- O `ministral-3:3b` gerou respostas mais extensas e descritivas, aumentando o tempo de inferencia sem ganho de precisao factual.

### 3. Decisao Final
A **Configuração 1 (Baseline: nomic-embed-text + qwen2.5:3b)** e confirmada como a arquitetura ideal do pipeline, entregando o melhor equilibrio entre qualidade de recuperacao, aderencia factual nas respostas e viabilidade de latencia.