# Full RAG System - Assistente Clínico para Consulta a Documentos

Sistema de Recuperação Aumentada por Geração (RAG) desenvolvido como parte do desafio técnico, utilizando documentos clínicos para responder perguntas em linguagem natural por meio de modelos locais executados via Ollama.

---

# Tecnologias utilizadas

- Python 3.12+
- LangChain
- FAISS
- BM25 (`rank-bm25`)
- Ollama
- Streamlit
- Pandas

---

# Instalação

Clone o repositório:

```bash
git clone https://github.com/KleidsonRocha/Full-RAG-System-Assistente-Clinico-de-Consulta-a-Documentos.git
cd Full-RAG-System-Assistente-Clinico-de-Consulta-a-Documentos
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente:

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---


# Instalação do Ollama

Baixe e instale o Ollama:

https://ollama.com/download

Após a instalação, faça o download dos modelos utilizados pelo projeto.

Modelo responsável pelos embeddings:

```bash
ollama pull nomic-embed-text
```

Modelo responsável pelas respostas:

```bash
ollama pull qwen2.5:3b
```

Verifique se ambos foram instalados:

```bash
ollama list
```

A saída deverá conter algo semelhante a:

```text
NAME
qwen2.5:3b
nomic-embed-text
```

---

# Executando o projeto

Antes de executar qualquer módulo, certifique-se de que o Ollama esteja em execução.

Caso necessário:

```bash
ollama serve
```

---

## Gerar a base vetorial

Antes de testar o RAG, gere os arquivos processados, os chunks e a base vetorial:

```bash
python -m src.ingestion.ingest
python -m src.chunk.chunking
python ingest_pipeline.py
```

Esse processo realiza:

- leitura dos documentos brutos em `data/raw/`;
- geração do arquivo processado `data/processed/dados_paciente.json`;
- geração dos chunks em `data/processed/dados_paciente_chunk.json`;
- criação dos embeddings com Ollama;
- persistência da base vetorial no FAISS em `src/vectorstore_faiss/`.

O BM25 não cria uma segunda base persistida. Seu corpus é montado em memória
com os mesmos `Document` armazenados no docstore do FAISS.

---

## Recuperação híbrida com RRF

Para cada pergunta, o pipeline executa:

1. busca vetorial no FAISS;
2. busca lexical BM25 sobre os mesmos chunks do docstore FAISS;
3. fusão e deduplicação das duas listas com Reciprocal Rank Fusion (RRF);
4. seleção dos `top_k` documentos finais diretamente no ranking RRF.

Fluxo resumido:

`Pergunta → FAISS + BM25 → RRF → top_k → contexto → LLM`

Cada canal solicita até 10 candidatos por padrão. Quando `top_k` é maior que 10,
o número solicitado aos canais também aumenta, evitando um limite artificial
antes da fusão. O `top_k` representa somente a quantidade final de documentos
selecionados após o RRF.

Para o BM25, diferenças de caixa, acentos e pontuação são removidas apenas durante
a tokenização lexical. Documentos com score BM25 igual a zero não são adicionados
ao ranking lexical. O texto original dos chunks, seus metadados e os próprios
objetos `Document` são preservados durante toda a recuperação.

A lista final produzida pelo RRF é a única fonte usada pela `ClinicalRAG` para
construir o contexto, preencher `documents` e gerar `sources`.

O reranking com FlashRank foi implementado e avaliado experimentalmente, mas
reduziu a qualidade da recuperação neste corpus. Por isso, ele não faz parte do
pipeline padrão; a estratégia final usa FAISS + BM25 + RRF, que apresentou melhor
desempenho nas métricas avaliadas.

---

## Testar o pipeline RAG no terminal

Após gerar a base vetorial, execute o pipeline RAG diretamente pelo terminal:

```bash
python -m src.pipeline.rag_chain
```

Digite uma pergunta relacionada ao acervo carregado. Nesta versão, o RAG está mais focado na bula de **amoxicilina + clavulanato de potássio**, usando os dados do paciente como metadados associados aos chunks recuperados.

Exemplos de perguntas recomendadas:

```text
Quais são as contraindicações da amoxicilina + clavulanato de potássio?
```

```text
Quais reações adversas podem ocorrer com amoxicilina + clavulanato de potássio?
```

```text
Qual é a composição da amoxicilina + clavulanato de potássio?
```

Perguntas sobre o paciente também podem ser feitas, mas podem ter respostas limitadas, pois os dados clínicos do paciente estão armazenados principalmente nos metadados dos chunks e nem todos são enviados explicitamente ao modelo durante a geração da resposta.

Exemplos de perguntas sobre o paciente:

```text
O paciente já utilizou amoxicilina com clavulanato?
```

```text
Quais diagnósticos aparecem no histórico do paciente?
```

Para testar o comportamento fora do acervo, use uma pergunta não relacionada aos documentos:

```text
Quem ganhou a Copa do Mundo de 2002?
```

Para finalizar a execução:

```text
sair
```

---

## Executar a interface Streamlit

Após gerar a base vetorial, a interface pode ser executada com:

```bash
streamlit run src/interface/app.py
```

No Windows, caso o monitoramento automático de arquivos cause instabilidade, use:

```bash
streamlit run src/interface/app.py --server.fileWatcherType none
```

A interface chama o pipeline RAG existente, envia a pergunta para `ClinicalRAG.ask()`, exibe a resposta gerada, as fontes recuperadas, os chunks usados como contexto e os metadados disponíveis do paciente.

Também há uma barra lateral com:

- quantidade de chunks recuperados (`top_k`);
- opção para mostrar ou ocultar contexto recuperado;
- opção para mostrar scores, quando disponíveis;
- modo debug;
- limpeza do histórico da sessão.

Mais detalhes estão em `src/interface/README_INTERFACE.md`.

---


# Testes e avaliação

Execute a bateria completa de testes, incluindo integração com o RAG real, com:

### Windows PowerShell

```powershell
.venv\Scripts\python.exe -m pytest
```

### Linux/macOS

```bash
python -m pytest
```

Esse comando inclui os testes de integração com RAG real, então depende do Ollama em execução, dos modelos locais e da base vetorial gerada.

Para rodar somente os testes que não chamam o modelo:

### Windows PowerShell

```powershell
$env:SKIP_RAG_INTEGRATION='1'; .venv\Scripts\python.exe -m pytest
```

### Linux/macOS

```bash
SKIP_RAG_INTEGRATION=1 python -m pytest
```

Para rodar a bateria de avaliação com o gold set versionado em `eval/golden_set.json` e gerar o relatório em `eval/results.md`:

```bash
python eval/evaluate_rag.py
```

O gold set possui 30 casos versionados, distribuídos entre `bula`, `dados_paciente` e `fora_do_acervo`.
Cada item registra resposta esperada, termos obrigatórios/proibidos, fonte esperada, trecho de evidência e afirmações atômicas para avaliação de fidelidade.
O relatório separa checks de recuperação e geração para facilitar análise de erro.
Para os casos elegíveis, `eval/evaluate_rag.py` também calcula Context Recall@2,
Context Precision@2, Hit Rate@1, Hit Rate@2, Hit Rate@5, Hit Rate@10 e MRR@10.

No Windows PowerShell, também pode ser executado com:

```powershell
.venv\Scripts\python.exe eval\evaluate_rag.py
```

## Testes de regressão de configuração

Para validar que uma mudança de configuração não melhora uma métrica degradando
outra, execute o gate de regressão:

```bash
python eval/regression.py
```

No Windows PowerShell:

```powershell
.venv\Scripts\python.exe eval\regression.py
```

Esse comando roda o mesmo golden set versionado, calcula as métricas principais
de recuperação, geração e recusa, e compara o resultado com os limites definidos
em `eval/regression_config.json`. Se alguma métrica ficar abaixo do mínimo
configurado ou cair além da tolerância em relação ao baseline, o processo termina
com código `1`.

O resultado estruturado fica em `eval/regression_results.json` e o resumo em
`eval/regression_results.md`. Para reaproveitar uma execução já avaliada sem
chamar o Ollama/RAG novamente, use:

```bash
python eval/regression.py --rows-json caminho/para/rows.json
```

## Resultado atual da avaliação

A avaliação mais recente foi executada com o pipeline FAISS + BM25 + RRF. Os
resultados abaixo correspondem ao golden set atual do projeto:

| Indicador | Resultado |
|---|---:|
| Context Recall@2 | 56,2% |
| Context Precision@2 | 34,4% |
| Hit Rate@1 | 50,0% |
| Hit Rate@2 | 62,5% |
| Hit Rate@5 | 87,5% |
| Hit Rate@10 | 87,5% |
| MRR@10 | 0,646 |
| Recuperação geral | 18/24 (75,0%) |
| Recusas fora do acervo | 6/6 (100,0%) |

As métricas da camada de recuperação consideram os 16 casos `bula_*` que possuem
chunks positivos anotados no golden set. Context Precision@2 considera somente
esses chunks positivos; trechos relevantes não anotados são contabilizados como
não relevantes.

A suíte completa validada possui 62 testes aprovados e nenhum teste falho.

---


# Estrutura do projeto

```text
src/
│
├── chunk/
│   └── chunking.py
│
├── embedding/
│   └── embeddings.py
│
├── ingestion/
│   ├── ingest.py
│   ├── persistence.py
│   └── translation.py
│
├── interface/
│   ├── app.py
│   ├── README_INTERFACE.md
│   ├── components/
│   └── services/
│
├── pipeline/
│   ├── prompts.py
│   ├── rag_chain.py
│   └── retrieval.py
│
└── vectorstore_faiss/

eval/
├── evaluate_rag.py
├── golden_set.json
└── results.md
```

---

# Modelos utilizados

| Finalidade | Modelo |
|------------|--------|
| Embeddings | `nomic-embed-text` |
| LLM | `qwen2.5:3b` |

---

# Observações

- O projeto utiliza modelos locais por meio do Ollama.
- A base vetorial é persistida em `src/vectorstore_faiss/` e carregada pelo FAISS
  durante a inicialização do RAG.
- O pipeline RAG foi desenvolvido utilizando LCEL (LangChain Expression Language).
