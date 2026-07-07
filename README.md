# Full RAG System - Assistente Clínico para Consulta a Documentos

Sistema de Recuperação Aumentada por Geração (RAG) desenvolvido como parte do desafio técnico, utilizando documentos clínicos para responder perguntas em linguagem natural por meio de modelos locais executados via Ollama.

---

# Tecnologias utilizadas

- Python 3.12+
- LangChain
- ChromaDB
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
- persistência da base vetorial no ChromaDB em `src/vectorstore/`.

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
│   └── rag_chain.py
│
└── vectorstore/
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
- A base vetorial é persistida utilizando ChromaDB.
- O pipeline RAG foi desenvolvido utilizando LCEL (LangChain Expression Language).
