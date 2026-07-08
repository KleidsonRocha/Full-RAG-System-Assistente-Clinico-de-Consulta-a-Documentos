from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.embedding.embeddings import VECTORSTORE, modelo_embedding
from src.pipeline.prompts import OUT_OF_SCOPE_MESSAGE, SYSTEM_PROMPT


MAX_METADATA_ITEMS = 6
MAX_METADATA_CHARS = 900
MAX_CONTEXT_CHARS_PER_DOC = 1800

PATIENT_METADATA_FIELDS = (
    ("paciente_nome", "Paciente"),
    ("paciente_genero", "Genero"),
    ("paciente_data_nascimento", "Data de nascimento"),
    ("paciente_historico_diagnosticos", "Diagnosticos registrados"),
    ("paciente_medicamentos_historico", "Medicamentos registrados"),
    ("paciente_historico_consultas", "Consultas registradas"),
    ("paciente_historico_procedimentos", "Procedimentos registrados"),
    ("paciente_historico_observacoes", "Observacoes recentes"),
    ("paciente_ultimo_peso_kg", "Ultimo peso"),
    ("paciente_ultima_altura_cm", "Ultima altura"),
)

MINIMAL_METADATA_FIELDS = (
    ("medicamento_bula_alvo", "Medicamento da bula"),
)

PATIENT_QUESTION_KEYWORDS = (
    "paciente",
    "historico",
    "histórico",
    "diagnostico",
    "diagnóstico",
    "diagnosticos",
    "diagnósticos",
    "consulta",
    "consultas",
    "peso",
    "altura",
    "utilizou",
    "usou",
    "usa",
    "alergia",
    "alergias",
    "exame",
    "exames",
)


class ClinicalRAG:

    def __init__(self):

        self.embedding_model = modelo_embedding()

        self.vector_store = Chroma(
            persist_directory=VECTORSTORE,
            embedding_function=self.embedding_model
        )

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2}
        )

        self.llm = ChatOllama(
            model="qwen2.5:3b",
            temperature=0,
            num_predict=256
        )

        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

        self.parser = StrOutputParser()

    def _retrieve_documents(self, question: str):
        return self.retriever.invoke(question)

    def _format_context(self, documents):

        context_blocks = []

        for index, doc in enumerate(documents, start=1):
            metadata = doc.metadata or {}
            text = self._truncate_text(doc.page_content or "", MAX_CONTEXT_CHARS_PER_DOC)
            context_blocks.append(
                "\n".join(
                    [
                        f"[Fonte {index}]",
                        f"pagina: {metadata.get('pagina_origem', 'N/A')}",
                        f"chunk: {self._chunk_id(metadata) or 'N/A'}",
                        text,
                    ]
                )
            )

        return "\n\n".join(context_blocks)

    def _format_patient_metadata(self, documents, question: str):

        merged_metadata = {}

        for doc in documents:
            for key, value in (doc.metadata or {}).items():
                if key not in merged_metadata and value not in (None, "", []):
                    merged_metadata[key] = value

        fields = (
            PATIENT_METADATA_FIELDS
            if self._is_patient_question(question)
            else MINIMAL_METADATA_FIELDS
        )

        metadata_lines = []
        for key, label in fields:
            value = merged_metadata.get(key)
            if value in (None, "", []):
                continue

            metadata_lines.append(f"{label}: {self._format_metadata_value(value)}")

        if not metadata_lines:
            return "Nenhum metadado relevante recuperado."

        return "\n".join(metadata_lines)

    def _get_sources(self, documents):

        sources = []

        for doc in documents:

            metadata = doc.metadata

            source = {
                "chunk": self._chunk_id(metadata),
                "pagina": metadata.get("pagina_origem"),
                "medicamento": metadata.get("medicamento_bula_alvo")
            }

            if source not in sources:
                sources.append(source)

        return sources

    def ask(self, question: str):

        documents = self._retrieve_documents(question)

        context = self._format_context(documents)
        patient_metadata = self._format_patient_metadata(documents, question)

        messages = self.prompt.invoke({
            "question": question,
            "context": context,
            "patient_metadata": patient_metadata
        })

        response = self.llm.invoke(messages)

        answer = self._normalize_answer(self.parser.invoke(response))

        return {
            "question": question,
            "answer": answer,
            "sources": self._get_sources(documents),
            "documents": documents
        }

    def stream(self, question: str):

        documents = self._retrieve_documents(question)
        context = self._format_context(documents)
        patient_metadata = self._format_patient_metadata(documents, question)

        messages = self.prompt.invoke({
            "question": question,
            "context": context,
            "patient_metadata": patient_metadata
        })

        for chunk in self.llm.stream(messages):

            if chunk.content:
                yield chunk.content

    def get_sources(self, question: str):

        documents = self._retrieve_documents(question)

        return self._get_sources(documents)

    def _is_patient_question(self, question: str) -> bool:
        normalized_question = str(question or "").lower()
        return any(keyword in normalized_question for keyword in PATIENT_QUESTION_KEYWORDS)

    def _format_metadata_value(self, value):
        if isinstance(value, list):
            items = [str(item) for item in value if item not in (None, "")]
            selected_items = items[-MAX_METADATA_ITEMS:]
            formatted_value = "; ".join(selected_items)
            if len(items) > len(selected_items):
                formatted_value += f"; ({len(items) - len(selected_items)} itens anteriores omitidos)"
            return self._truncate_text(formatted_value, MAX_METADATA_CHARS)

        if isinstance(value, dict):
            items = list(value.items())[:MAX_METADATA_ITEMS]
            formatted_value = "; ".join(f"{key}: {item}" for key, item in items)
            return self._truncate_text(formatted_value, MAX_METADATA_CHARS)

        formatted_value = str(value)
        if "; " in formatted_value:
            items = formatted_value.split("; ")
            selected_items = items[-MAX_METADATA_ITEMS:]
            formatted_value = "; ".join(selected_items)
            if len(items) > len(selected_items):
                formatted_value += f"; ({len(items) - len(selected_items)} itens anteriores omitidos)"

        return self._truncate_text(formatted_value, MAX_METADATA_CHARS)

    def _chunk_id(self, metadata):
        chunk_id = metadata.get("chunk_id")
        if chunk_id:
            return str(chunk_id)

        chunk_number = metadata.get("chunk_number")
        if chunk_number is None:
            return None

        try:
            return f"chunk_{int(chunk_number):03d}"
        except (TypeError, ValueError):
            return str(chunk_number)

    def _truncate_text(self, text: str, max_chars: int) -> str:
        clean_text = " ".join(str(text).split())
        if len(clean_text) <= max_chars:
            return clean_text

        return f"{clean_text[:max_chars].rstrip()}..."

    def _normalize_answer(self, answer: str) -> str:
        clean_answer = str(answer or "").strip()
        normalized_answer = " ".join(clean_answer.lower().split())
        fallback_markers = (
            "não encontrei",
            "nao encontrei",
            "não consegui encontrar",
            "nao consegui encontrar",
            "não há informação",
            "nao ha informacao",
        )

        if any(marker in normalized_answer for marker in fallback_markers):
            return OUT_OF_SCOPE_MESSAGE

        return clean_answer


if __name__ == "__main__":

    rag = ClinicalRAG()

    while True:

        pergunta = input("\nPergunta: ")

        if pergunta.lower() == "sair":
            break

        print("\nResposta:\n")

        for token in rag.stream(pergunta):
            print(token, end="", flush=True)

        print("\n\nFontes:")

        for source in rag.get_sources(pergunta):
            print(source)

        print()
