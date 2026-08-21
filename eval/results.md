# Resultados da avaliacao RAG

Relatorio gerado por `python eval/evaluate_rag.py`.

## Resumo

- Total de perguntas: 30
- Avaliadas automaticamente: 30
- Aprovadas totalmente (Checks + Juiz): 14
- Revisao manual: 0
- Recuperacao ok: 10/23 (43.5%)
- Geracao ok (Regras lexicas): 20/30 (66.7%)
- Recusa fora do acervo ok: 6/6 (100.0%)
- Latencia media: 1404 ms

## Metricas do LLM as a Judge

- Taxa de Fidelidade (Faithfulness): 86.7%
- Taxa de Relevancia (Answer Relevancy): 83.3%
- Taxa de Aderencia a Recusa (Refusal): 86.7%

## Metricas da camada de recuperacao

- Casos com chunks positivos anotados: 16
- Context Recall@2: 56.2%
- Context Precision@2: 34.4%
- Hit Rate@1: 50.0%
- Hit Rate@2: 62.5%
- Hit Rate@5: 87.5%
- Hit Rate@10: 87.5%
- MRR@10: 0.646

## Resultados por pergunta

| ID | Categoria | Status | Recuperacao | Geracao | Juiz (F/R/Ref) | Latencia | Fontes | Docs | Recusa | Checks com falha |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| bula_001 | bula | ok | ok | ok | 1/1/1 | 7446 ms | 2 | 2 | nao | - |
| bula_002 | bula | falha | falha | falha | 1/0/0 | 1894 ms | 2 | 2 | nao | termos_obrigatorios, fonte_chunk, fonte_pagina |
| bula_003 | bula | falha | falha | falha | 0/0/0 | 1762 ms | 2 | 2 | nao | termos_obrigatorios, fonte_chunk |
| bula_004 | bula | falha | falha | falha | 1/1/1 | 1471 ms | 2 | 2 | nao | termos_obrigatorios, fonte_chunk |
| bula_005 | bula | falha | ok | falha | 1/1/1 | 2243 ms | 2 | 2 | nao | termos_obrigatorios |
| bula_006 | bula | falha | falha | falha | 1/1/1 | 775 ms | 2 | 2 | nao | termos_obrigatorios, fonte_chunk, fonte_pagina |
| bula_007 | bula | falha | ok | falha | 1/1/1 | 1642 ms | 2 | 2 | nao | termos_obrigatorios |
| bula_008 | bula | ok | ok | ok | 1/1/1 | 1869 ms | 2 | 2 | nao | - |
| bula_009 | bula | falha | falha | falha | 0/0/0 | 1506 ms | 2 | 2 | nao | termos_obrigatorios, fonte_chunk, fonte_pagina |
| bula_010 | bula | ok | ok | ok | 1/1/1 | 1638 ms | 2 | 2 | nao | - |
| bula_011 | bula | ok | ok | ok | 1/1/1 | 2279 ms | 2 | 2 | nao | - |
| bula_012 | bula | falha | falha | falha | 0/0/1 | 751 ms | 2 | 2 | sim | recusa_esperada, termos_obrigatorios, fonte_chunk |
| bula_013 | bula | ok | ok | ok | 1/1/1 | 774 ms | 2 | 2 | nao | - |
| bula_014 | bula | ok | ok | ok | 1/1/1 | 1329 ms | 2 | 2 | nao | - |
| bula_015 | bula | ok | ok | ok | 1/1/1 | 897 ms | 2 | 2 | nao | - |
| bula_016 | bula | falha | ok | falha | 1/1/1 | 1140 ms | 2 | 2 | nao | termos_obrigatorios |
| paciente_001 | dados_paciente | falha | falha | ok | 1/1/1 | 1659 ms | 2 | 2 | nao | metadados_recuperados |
| paciente_002 | dados_paciente | falha | falha | ok | 1/1/1 | 1407 ms | 2 | 2 | nao | metadados_recuperados |
| paciente_003 | dados_paciente | falha | falha | ok | 1/1/1 | 407 ms | 2 | 2 | nao | metadados_recuperados |
| paciente_004 | dados_paciente | ok | ok | ok | 1/1/1 | 2198 ms | 2 | 2 | nao | - |
| paciente_005 | dados_paciente | falha | falha | ok | 1/1/1 | 721 ms | 2 | 2 | nao | metadados_recuperados |
| paciente_006 | dados_paciente | falha | falha | ok | 1/1/1 | 665 ms | 2 | 2 | nao | metadados_recuperados |
| paciente_007 | dados_paciente | falha | falha | falha | 0/0/0 | 757 ms | 2 | 2 | nao | termos_obrigatorios, metadados_recuperados |
| paciente_008 | dados_paciente | falha | falha | ok | 1/1/1 | 654 ms | 2 | 2 | nao | metadados_recuperados |
| fora_001 | fora_do_acervo | ok | ok | ok | 1/1/1 | 593 ms | 2 | 2 | sim | - |
| fora_002 | fora_do_acervo | ok | ok | ok | 1/1/1 | 725 ms | 2 | 2 | sim | - |
| fora_003 | fora_do_acervo | ok | ok | ok | 1/1/1 | 622 ms | 2 | 2 | sim | - |
| fora_004 | fora_do_acervo | ok | ok | ok | 1/1/1 | 783 ms | 2 | 2 | sim | - |
| fora_005 | fora_do_acervo | ok | ok | ok | 1/1/1 | 714 ms | 2 | 2 | sim | - |
| fora_006 | fora_do_acervo | ok | ok | ok | 1/1/1 | 812 ms | 2 | 2 | sim | - |

## Metricas de recuperacao por pergunta

| ID | Context Recall@2 | Context Precision@2 | Hit Rate@1 | Hit Rate@2 | Hit Rate@5 | Hit Rate@10 | MRR@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bula_001 | 100.0% | 50.0% | 1 | 1 | 1 | 1 | 1.000 |
| bula_002 | 0.0% | 0.0% | 0 | 0 | 0 | 0 | 0.000 |
| bula_003 | 0.0% | 0.0% | 0 | 0 | 1 | 1 | 0.333 |
| bula_004 | 0.0% | 0.0% | 0 | 0 | 1 | 1 | 0.333 |
| bula_005 | 100.0% | 100.0% | 1 | 1 | 1 | 1 | 1.000 |
| bula_006 | 0.0% | 0.0% | 0 | 0 | 0 | 0 | 0.000 |
| bula_007 | 50.0% | 50.0% | 1 | 1 | 1 | 1 | 1.000 |
| bula_008 | 50.0% | 50.0% | 1 | 1 | 1 | 1 | 1.000 |
| bula_009 | 0.0% | 0.0% | 0 | 0 | 1 | 1 | 0.333 |
| bula_010 | 100.0% | 50.0% | 1 | 1 | 1 | 1 | 1.000 |
| bula_011 | 100.0% | 50.0% | 1 | 1 | 1 | 1 | 1.000 |
| bula_012 | 0.0% | 0.0% | 0 | 0 | 1 | 1 | 0.333 |
| bula_013 | 100.0% | 50.0% | 0 | 1 | 1 | 1 | 0.500 |
| bula_014 | 100.0% | 50.0% | 0 | 1 | 1 | 1 | 0.500 |
| bula_015 | 100.0% | 50.0% | 1 | 1 | 1 | 1 | 1.000 |
| bula_016 | 100.0% | 50.0% | 1 | 1 | 1 | 1 | 1.000 |

## Observacoes

- bula_002: revisar resposta manualmente; criterio automatico marcou falha.
- bula_003: revisar resposta manualmente; criterio automatico marcou falha.
- bula_004: revisar resposta manualmente; criterio automatico marcou falha.
- bula_005: revisar resposta manualmente; criterio automatico marcou falha.
- bula_006: revisar resposta manualmente; criterio automatico marcou falha.
- bula_007: revisar resposta manualmente; criterio automatico marcou falha.
- bula_009: revisar resposta manualmente; criterio automatico marcou falha.
- bula_012: revisar resposta manualmente; criterio automatico marcou falha.
- bula_016: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_001: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_002: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_003: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_005: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_006: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_007: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_008: revisar resposta manualmente; criterio automatico marcou falha.

## Matriz de Recusa

A matriz compara o comportamento esperado com o comportamentoobservado do sistema, permitindo identificar recusas corretas,respostas indevidas e recusas indevidas.Partindo dos testes do golden set com 30, foi feito um plot da imagem com a matriz de recusa com o casos.
| Esperado / Observado | Respondeu | Recusou |
| --- | ---: | ---: |
| Deveria responder | 23 | 1 |
| Deveria recusar | 0 | 6 |

![Matriz de Recusa](matriz_recusa.png)


## Melhoria futura

- Mutation testing nao foi implementado nesta rodada; pode ser avaliado
  depois que a suite base estiver estavel.
