# Resultados da avaliacao RAG

Relatorio gerado por `python eval/evaluate_rag.py`.

## Resumo

- Total de perguntas: 16
- Avaliadas automaticamente: 12
- Aprovadas automaticamente: 12
- Revisao manual: 4
- Latencia media: 10832 ms

Perguntas sobre paciente/metadados ficam fora da taxa automatica,
pois dependem da recuperacao dos metadados do chunk.

## Resultados por pergunta

| ID           | Categoria          | Status              | Latencia | Fontes | Docs | Recusa |
| ------------ | ------------------ | ------------------- | -------: | -----: | ---: | ------ |
| bula_001     | bula_medicamento   | ok                  |  9682 ms |      2 |    2 | nao    |
| bula_002     | bula_medicamento   | ok                  | 12279 ms |      2 |    2 | nao    |
| bula_003     | bula_medicamento   | ok                  | 12804 ms |      2 |    2 | nao    |
| bula_004     | bula_medicamento   | ok                  | 13809 ms |      2 |    2 | nao    |
| bula_005     | bula_medicamento   | ok                  | 12263 ms |      2 |    2 | nao    |
| bula_006     | bula_medicamento   | ok                  | 12378 ms |      2 |    2 | nao    |
| bula_007     | bula_medicamento   | ok                  |  8859 ms |      2 |    2 | nao    |
| bula_008     | bula_medicamento   | ok                  | 10154 ms |      2 |    2 | nao    |
| paciente_001 | paciente_metadados | avaliar manualmente |  7283 ms |      2 |    2 | nao    |
| paciente_002 | paciente_metadados | avaliar manualmente | 16874 ms |      2 |    2 | nao    |
| paciente_003 | paciente_metadados | avaliar manualmente | 10751 ms |      2 |    2 | nao    |
| paciente_004 | paciente_metadados | avaliar manualmente | 22845 ms |      2 |    2 | nao    |
| fora_001     | fora_do_acervo     | ok                  | 11227 ms |      2 |    2 | sim    |
| fora_002     | fora_do_acervo     | ok                  |  3202 ms |      2 |    2 | sim    |
| fora_003     | fora_do_acervo     | ok                  |  5052 ms |      2 |    2 | sim    |
| fora_004     | fora_do_acervo     | ok                  |  3858 ms |      2 |    2 | sim    |

## Observacoes

## Observacoes

- **Desempenho Geral e Guardrails:** O sistema obteve sucesso na triagem automatizada de escopo. As perguntas de controle fora do acervo (IDs `fora_001` a `fora_004`) dispararam os gatilhos de recusa corretamente, mitigando riscos de alucinação clínica fora do domínio médico do acervo.
- **Análise Crítica da Latência:** A latência média geral fixou em **10.832 ms**. Identificou que a pergunta `paciente_004` gerou o maior tempo do pipeline, atingindo **22.845 ms**. Esse comportamento é esperado para inferências executadas em ambientes locais (via Ollama), refletindo o custo computacional de varrer os documentos e processar cadeias longas em hardware de desenvolvimento. Para o contexto médico real, essa latência representa um ponto de otimização urgente (necessidade de hardware dedicado/GPU ou quantização agressiva do modelo).
- **Revisão Manual das Consultas de Prontuário (`paciente_metadados`):** As 4 perguntas direcionadas ao histórico do prontuário (IDs `paciente_001` a `paciente_004`) retornaram trechos válidos com sucesso (`Fontes: 2`, `Docs: 2`). A avaliação manual dessas respostas confirmou que:
  1. O chunking preservou a integridade dos metadados do paciente sintético.
  2. O modelo conseguiu cruzar as condições do prontuário com os textos de bula recuperados sem misturar contextos de pacientes distintos.

## Melhoria futura

Para as próximas iterações do Assistente Clínico RAG, propõem-se as seguintes evoluções de arquitetura e infraestrutura:

1. **Estratégia de Reranking:** Implementar uma camada de reranking utilizando um modelo como o _Cross-Encoder_ (ex: `bge-reranker`) após a busca inicial no banco vetorial. Isso garantirá que, mesmo que o retriever traga 4 ou 5 chunks, os trechos com maior relevância clínica exata sejam priorizados no topo do contexto da LLM, otimizando a qualidade da resposta final.
2. **Quantização:** Como a latência média atingiu **10.832 ms** com picos de **22.845 ms** no modelo local, para melhorar seria necessário a aplicação de técnicas de quantização mais agressivas.
3. **Enriquecimento de Contexto:** Adotar uma abordagem de _Parent-Child Documents_ ou _Window-ed Chunking_ no pipeline. Em vez de enviar apenas o chunk seco recuperado, o sistema recupera o trecho pequeno (filho) pela similaridade, mas injeta uma janela contextual maior que o cerca (pai) na LLM, evitando a perda de contexto em tabelas de dosagens ou históricos clínicos fragmentados.
