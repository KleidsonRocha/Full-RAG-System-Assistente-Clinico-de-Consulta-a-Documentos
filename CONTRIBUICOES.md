# Registro de Contribuições Individuais

## Tabela de Entregas

| Pessoa                        | O que construiu                                                                                                                                                                                                                                                            | Principais Commits                                |
|:------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------|
| **Gabriel Ferreira Oliveira** | Desenvolvi o pipeline de chunking por tokens (`src/chunk/chunking.py`). Realizei a limpeza dos ruídos que foram apresentados no PDF da bula do medicamento. Por fim, foi feita a organização e a modelagem dos metadados que serão utilizados como auxilio de informações. | `feat: implementa chunking semântico e metadados` |
---

## Reflexão Individual

### [Gabriel Ferreira]
Trabalhando com chunking, pude compreender que essa etapa vai muito além de apenas cortar o texto em partes, é preciso saber isolar e agrupar os contextos corretos. O meu maior desafio foi lidar com a "vida real" dos dados do prontuário: o JSON original veio com várias informações flutuantes e valores nulos nas consultas de rotina, além de exames e pesos antigos misturados com os mais recentes. A divisão dos chunks, sem um tratamento prévio desses dados, trariam problemas futuros.

A solução encontrada para isso foi a organização da linha do tempo cronológica do paciente (juntando consultas, condições, exames e procedimentos) direto nos metadados de cada pedaço da bula. Essa amarração garante que, não importa qual bloco da bula seja retornada, a LLM sempre terá o histórico correto do paciente para cruzar as informações, evitando alucinações e mistura de prontuários. Por fim, configurar o Splitter por tokens e usar Regex para limpar a "sujeira" visual do PDF da bula garantiu um fatiamento limpo, sem quebra de frases e otimizado o resultado final.