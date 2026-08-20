# Resultados da avaliacao RAG

Relatorio gerado por `python eval/evaluate_rag.py`.

## Resumo

- Total de perguntas: 30
- Avaliadas automaticamente: 30
- Aprovadas automaticamente: 17
- Revisao manual: 0
- Recuperacao ok: 18/24 (75.0%)
- Geracao ok: 17/30 (56.7%)
- Recusa fora do acervo ok: 6/6 (100.0%)
- Latencia media: 16226 ms

A avaliacao usa gold set versionado com resposta esperada, termos
obrigatorios/proibidos, fonte esperada e comportamento de recusa.

## Metricas da camada de recuperacao

- Casos com chunks positivos anotados: 16
- Context Recall@2: 56.2%
- Context Precision@2: 34.4%
- Hit Rate@1: 50.0%
- Hit Rate@2: 62.5%
- Hit Rate@5: 87.5%
- Hit Rate@10: 87.5%
- MRR@10: 0.646

Context Precision@2 considera somente os chunks positivos anotados
no golden set; chunks relevantes nao anotados sao contabilizados como
nao relevantes.

## Resultados por pergunta

| ID           | Categoria      | Status | Recuperacao | Geracao | Latencia | Fontes | Docs | Recusa | Checks com falha                                                |
| ------------ | -------------- | ------ | ----------- | ------- | -------: | -----: | ---: | ------ | --------------------------------------------------------------- |
| bula_001     | bula           | ok     | ok          | ok      | 33802 ms |      2 |    2 | nao    | -                                                               |
| bula_002     | bula           | falha  | falha       | falha   | 21635 ms |      2 |    2 | nao    | termos_obrigatorios, fonte_chunk, fonte_pagina                  |
| bula_003     | bula           | falha  | falha       | falha   | 22453 ms |      2 |    2 | nao    | termos_obrigatorios, fonte_chunk                                |
| bula_004     | bula           | falha  | falha       | falha   | 20301 ms |      2 |    2 | nao    | termos_obrigatorios, fonte_chunk                                |
| bula_005     | bula           | ok     | ok          | ok      | 23005 ms |      2 |    2 | nao    | -                                                               |
| bula_006     | bula           | falha  | falha       | falha   | 11256 ms |      2 |    2 | nao    | termos_obrigatorios, fonte_chunk, fonte_pagina                  |
| bula_007     | bula           | falha  | ok          | falha   | 18669 ms |      2 |    2 | nao    | termos_obrigatorios                                             |
| bula_008     | bula           | ok     | ok          | ok      | 22183 ms |      2 |    2 | nao    | -                                                               |
| bula_009     | bula           | falha  | falha       | falha   |  2032 ms |      2 |    2 | sim    | recusa_esperada, termos_obrigatorios, fonte_chunk, fonte_pagina |
| bula_010     | bula           | falha  | ok          | falha   | 18838 ms |      2 |    2 | nao    | termos_obrigatorios                                             |
| bula_011     | bula           | ok     | ok          | ok      | 22728 ms |      2 |    2 | nao    | -                                                               |
| bula_012     | bula           | falha  | falha       | falha   | 13303 ms |      2 |    2 | sim    | recusa_esperada, termos_obrigatorios, fonte_chunk               |
| bula_013     | bula           | ok     | ok          | ok      | 14758 ms |      2 |    2 | nao    | -                                                               |
| bula_014     | bula           | falha  | ok          | falha   | 17390 ms |      2 |    2 | nao    | termos_obrigatorios                                             |
| bula_015     | bula           | ok     | ok          | ok      | 13219 ms |      2 |    2 | nao    | -                                                               |
| bula_016     | bula           | falha  | ok          | falha   | 16573 ms |      2 |    2 | nao    | termos_obrigatorios                                             |
| paciente_001 | dados_paciente | ok     | ok          | ok      | 29096 ms |      2 |    2 | nao    | -                                                               |
| paciente_002 | dados_paciente | ok     | ok          | ok      | 20258 ms |      2 |    2 | nao    | -                                                               |
| paciente_003 | dados_paciente | falha  | ok          | falha   | 10397 ms |      2 |    2 | nao    | termos_obrigatorios                                             |
| paciente_004 | dados_paciente | ok     | ok          | ok      | 23026 ms |      2 |    2 | nao    | -                                                               |
| paciente_005 | dados_paciente | ok     | ok          | ok      | 15426 ms |      2 |    2 | nao    | -                                                               |
| paciente_006 | dados_paciente | falha  | ok          | falha   |  8514 ms |      2 |    2 | nao    | termos_obrigatorios                                             |
| paciente_007 | dados_paciente | ok     | ok          | ok      | 24305 ms |      2 |    2 | nao    | -                                                               |
| paciente_008 | dados_paciente | falha  | ok          | falha   | 13896 ms |      2 |    2 | sim    | recusa_esperada, termos_obrigatorios                            |
| fora_001     | fora_do_acervo | ok     | ok          | ok      |  6429 ms |      2 |    2 | sim    | -                                                               |
| fora_002     | fora_do_acervo | ok     | ok          | ok      |  7546 ms |      2 |    2 | sim    | -                                                               |
| fora_003     | fora_do_acervo | ok     | ok          | ok      |  4496 ms |      2 |    2 | sim    | -                                                               |
| fora_004     | fora_do_acervo | ok     | ok          | ok      |  9311 ms |      2 |    2 | sim    | -                                                               |
| fora_005     | fora_do_acervo | ok     | ok          | ok      | 14090 ms |      2 |    2 | sim    | -                                                               |
| fora_006     | fora_do_acervo | ok     | ok          | ok      |  7860 ms |      2 |    2 | sim    | -                                                               |

## Metricas de recuperacao por pergunta

| ID       | Context Recall@2 | Context Precision@2 | Hit Rate@1 | Hit Rate@2 | Hit Rate@5 | Hit Rate@10 | MRR@10 |
| -------- | ---------------: | ------------------: | ---------: | ---------: | ---------: | ----------: | -----: |
| bula_001 |           100.0% |               50.0% |          1 |          1 |          1 |           1 |  1.000 |
| bula_002 |             0.0% |                0.0% |          0 |          0 |          0 |           0 |  0.000 |
| bula_003 |             0.0% |                0.0% |          0 |          0 |          1 |           1 |  0.333 |
| bula_004 |             0.0% |                0.0% |          0 |          0 |          1 |           1 |  0.333 |
| bula_005 |           100.0% |              100.0% |          1 |          1 |          1 |           1 |  1.000 |
| bula_006 |             0.0% |                0.0% |          0 |          0 |          0 |           0 |  0.000 |
| bula_007 |            50.0% |               50.0% |          1 |          1 |          1 |           1 |  1.000 |
| bula_008 |            50.0% |               50.0% |          1 |          1 |          1 |           1 |  1.000 |
| bula_009 |             0.0% |                0.0% |          0 |          0 |          1 |           1 |  0.333 |
| bula_010 |           100.0% |               50.0% |          1 |          1 |          1 |           1 |  1.000 |
| bula_011 |           100.0% |               50.0% |          1 |          1 |          1 |           1 |  1.000 |
| bula_012 |             0.0% |                0.0% |          0 |          0 |          1 |           1 |  0.333 |
| bula_013 |           100.0% |               50.0% |          0 |          1 |          1 |           1 |  0.500 |
| bula_014 |           100.0% |               50.0% |          0 |          1 |          1 |           1 |  0.500 |
| bula_015 |           100.0% |               50.0% |          1 |          1 |          1 |           1 |  1.000 |
| bula_016 |           100.0% |               50.0% |          1 |          1 |          1 |           1 |  1.000 |

## Observacoes

- bula_002: revisar resposta manualmente; criterio automatico marcou falha.
- bula_003: revisar resposta manualmente; criterio automatico marcou falha.
- bula_004: revisar resposta manualmente; criterio automatico marcou falha.
- bula_006: revisar resposta manualmente; criterio automatico marcou falha.
- bula_007: revisar resposta manualmente; criterio automatico marcou falha.
- bula_009: revisar resposta manualmente; criterio automatico marcou falha.
- bula_010: revisar resposta manualmente; criterio automatico marcou falha.
- bula_012: revisar resposta manualmente; criterio automatico marcou falha.
- bula_014: revisar resposta manualmente; criterio automatico marcou falha.
- bula_016: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_003: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_006: revisar resposta manualmente; criterio automatico marcou falha.
- paciente_008: revisar resposta manualmente; criterio automatico marcou falha.

## Matriz de Recusa

A matriz compara o comportamento esperado com o comportamentoobservado do sistema, permitindo identificar recusas corretas,respostas indevidas e recusas indevidas.Partindo dos testes do golden set com 30, foi feito um plot da imagem com a matriz de recusa com o casos.
| Esperado / Observado | Respondeu | Recusou |
| --- | ---: | ---: |
| Deveria responder | 21 | 3 |
| Deveria recusar | 0 | 6 |

![Matriz de Recusa](matriz_recusa.png)

## Melhoria futura

- Mutation testing nao foi implementado nesta rodada; pode ser avaliado
  depois que a suite base estiver estavel.
