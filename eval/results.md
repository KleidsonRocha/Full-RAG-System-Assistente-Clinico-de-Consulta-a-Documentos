# Resultados da avaliacao RAG

Relatorio gerado por `python eval/evaluate_rag.py`.

## Resumo

- Total de perguntas: 16
- Avaliadas automaticamente: 12
- Aprovadas automaticamente: 12
- Revisao manual: 4
- Latencia media: 9946 ms

Perguntas sobre paciente/metadados ficam fora da taxa automatica,
pois dependem da recuperacao dos metadados do chunk.

## Resultados por pergunta

| ID | Categoria | Status | Latencia | Fontes | Docs | Recusa |
| --- | --- | --- | ---: | ---: | ---: | --- |
| bula_001 | bula_medicamento | ok | 9091 ms | 2 | 2 | nao |
| bula_002 | bula_medicamento | ok | 9464 ms | 2 | 2 | nao |
| bula_003 | bula_medicamento | ok | 12235 ms | 2 | 2 | nao |
| bula_004 | bula_medicamento | ok | 22229 ms | 2 | 2 | nao |
| bula_005 | bula_medicamento | ok | 7513 ms | 2 | 2 | nao |
| bula_006 | bula_medicamento | ok | 2981 ms | 2 | 2 | nao |
| bula_007 | bula_medicamento | ok | 6786 ms | 2 | 2 | nao |
| bula_008 | bula_medicamento | ok | 7710 ms | 2 | 2 | nao |
| paciente_001 | paciente_metadados | avaliar manualmente | 7739 ms | 2 | 2 | nao |
| paciente_002 | paciente_metadados | avaliar manualmente | 16440 ms | 2 | 2 | nao |
| paciente_003 | paciente_metadados | avaliar manualmente | 10301 ms | 2 | 2 | nao |
| paciente_004 | paciente_metadados | avaliar manualmente | 24757 ms | 2 | 2 | nao |
| fora_001 | fora_do_acervo | ok | 1119 ms | 2 | 2 | sim |
| fora_002 | fora_do_acervo | ok | 9391 ms | 2 | 2 | sim |
| fora_003 | fora_do_acervo | ok | 6566 ms | 2 | 2 | sim |
| fora_004 | fora_do_acervo | ok | 4816 ms | 2 | 2 | sim |

## Melhoria futura

- Mutation testing nao foi implementado nesta rodada; pode ser avaliado
  depois que a suite base estiver estavel.
