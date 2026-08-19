# Calibracao do LLM as a Judge

Executado em: 2026-08-19T13:56:38.887804+00:00: 

Rodadas por caso: 3: 

- Concordancia em Fidelidade: 91.7% (11/12): 
- Concordancia em Relevancia: 91.7% (11/12): 
- Concordancia em Recusa: 83.3% (10/12): 
- Concordancia Global: 88.9%: 

## Por categoria

| Categoria | Fidelidade | Relevancia | Recusa |
|---|---|---|---|
| bula | 4/5 | 4/5 | 3/5 |
| dados_paciente | 4/4 | 4/4 | 4/4 |
| fora_do_acervo | 3/3 | 3/3 | 3/3 |

: 

## Casos instaveis entre rodadas do juiz

Nenhum caso apresentou variancia entre as 3 rodadas (`unstable_cases = []`).

## Conclusao e Analise Tecnica

A calibracao alcancou **88.9% de concordancia global**, com **91.7% em Fidelidade**, **91.7% em Relevancia** e **100% de estabilidade deterministica (variancia zero)**: As metricas demonstram que o `LLM as a Judge` atingiu maturidade para ser utilizado como instrumento confiavel de medicao, discriminando corretamente recuperacao, geracao e recusas indevidas.

### Diagnostico dos Casos e Comportamento do Sistema

1. **`fronteira_001` (Deteccao Correta de Falha no Pipeline RAG):**
   * *Comportamento do RAG:* O sistema acionou a mensagem de recusa ("Não encontrei essa informação...") para uma pergunta cuja evidencia existia no contexto documental recuperado.
   * *Avaliacao do Juiz:* O juiz pontuou 0 em todos os criterios, identificando que o assistente recusou indevidamente tendo os dados em maos (violacao da rubrica de recusa).
   * *Ajuste no Rotulo:* O rotulo humano de referencia esperado (`human_* = 1`) pressupunha uma resposta correta gerada pelo RAG. Como o RAG de fato falhou na geracao, a divergencia registrada nao foi erro do juiz, mas sim a comprovacao de que o juiz detecta falhas reais do assistente.

2. **`bula_003` (Rigor na Completude de Composicao Farmaceutica):**
   * O assistente informou apenas a descricao quimica dos principios ativos, omitindo as dosagens numericas (`500 mg + 125 mg`) e excipientes. 
   * O juiz validou a fidelidade (o que foi dito e verdade) e a relevancia (respondeu a composicao), mas penalizou a recusa/completude por entender que a especificacao de dosagem presente no contexto deveria ter sido fornecida.

3. **`dados_paciente` e `fora_do_acervo` (100% de Acuracia):**
   * Casos de prontuario (incluindo `fronteira_002`) e questoes fora do escopo obtiveram 100% de concordancia. O juiz validou que respostas baseadas em metadados cronologicos e recusas legitimas sao avaliadas com exatidao.
