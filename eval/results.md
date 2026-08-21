# Resultados da avaliacao RAG

Relatorio gerado por `python eval/evaluate_rag.py`.

## Resumo

- Total de perguntas: 16
- Avaliadas automaticamente: 12
- Aprovadas automaticamente: 12
- Fidelidade Média (Claim-level):** 70.8%
- Revisao manual: 4
- Latencia media: 13704 ms

Perguntas sobre paciente/metadados ficam fora da taxa automatica,
pois dependem da recuperacao dos metadados do chunk.

## Resultados por pergunta

| ID | Categoria | Status | Latencia | Fontes | Docs | Recusa |
| --- | --- | --- | ---: | ---: | ---: | --- |
| bula_001 | ok | 20448 ms | 2/2 | 100.0% | sim | nao |
| bula_002 | ok | 17662 ms | 3/3 | 100.0% | sim | nao |
| bula_003 | ok | 13400 ms | 1/1 | 100.0% | sim | nao |
| bula_004 | ok | 16139 ms | 3/3 | 100.0% | sim | nao |
| bula_005 | ok | 16284 ms | 2/2 | 100.0% | sim | nao |
| bula_006 | ok | 9508 ms | 1/2 | 50.0% | sim | nao |
| bula_007 | ok | 15523 ms | 2/2 | 100.0% | sim | nao |
| bula_008 | ok | 15876 ms | 6/6 | 100.0% | sim | nao |
| paciente_001 | avaliar manualmente | 21012 ms | 0/1 | 0.0% | sim | nao |
| paciente_002 | avaliar manualmente | 17097 ms | 0/4 | 0.0% | sim | nao |
| paciente_003 | avaliar manualmente | 9182 ms | 1/1 | 100.0% | sim | nao |
| paciente_004 | avaliar manualmente | 18415 ms | 0/7 | 0.0% | sim | nao |
| fora_001 | ok | 10301 ms | 0/0 | 0.0% | sim | sim |
| fora_002 | ok | 8542 ms | 0/0 | 0.0% | sim | sim |
| fora_003 | ok | 6336 ms | 0/0 | 0.0% | sim | sim |
| fora_004 | ok | 3533 ms | 0/0 | 0.0% | sim | sim |

## Observacoes


## Melhoria futura

- Mutation testing nao foi implementado nesta rodada; pode ser avaliado
  depois que a suite base estiver estavel.
