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
ollama pull gemma3:12b
```

Verifique se ambos foram instalados:

```bash
ollama list
```

A saída deverá conter algo semelhante a:

```text
NAME
gemma3:12b
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

Execute o pipeline de ingestão para criar a base vetorial:

```bash
python -m src.ingestion.ingest_pipeline
```

Esse processo realiza:

- leitura dos documentos;
- geração dos chunks;
- criação dos embeddings;
- persistência da base vetorial no ChromaDB.

---

## Testar o pipeline RAG

Para executar o pipeline diretamente pelo terminal:

```bash
python -m src.pipeline.rag_chain
```

Digite uma pergunta quando solicitado.

Para finalizar:

```text
sair
```

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
│   └── ingest_pipeline.py
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
| LLM | `gemma3:12b` |

---

# Observações

- O projeto utiliza modelos locais por meio do Ollama.
- A base vetorial é persistida utilizando ChromaDB.
- O pipeline RAG foi desenvolvido utilizando LCEL (LangChain Expression Language).