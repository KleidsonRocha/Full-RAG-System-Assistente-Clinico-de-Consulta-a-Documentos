from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.embedding.embeddings import VECTORSTORE, modelo_embedding
from src.pipeline.prompts import SYSTEM_PROMPT


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
            num_predict=1024
        )

        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

        self.parser = StrOutputParser()

    def _retrieve_documents(self, question: str):
        return self.retriever.invoke(question)

    def _format_context(self, documents):

        return "\n\n".join(
            doc.page_content
            for doc in documents
        )

    def _format_patient_metadata(self, documents):

        metadata_blocks = []

        for doc in documents:

            if not doc.metadata:
                continue

            metadata_blocks.append(
                "\n".join(
                    f"{key}: {value}"
                    for key, value in doc.metadata.items()
                )
            )

        return "\n\n".join(metadata_blocks)

    def _get_sources(self, documents):

        sources = []

        for doc in documents:

            metadata = doc.metadata

            source = {
                "chunk": metadata.get("chunk_id"),
                "pagina": metadata.get("pagina_origem"),
                "medicamento": metadata.get("medicamento_bula_alvo")
            }

            if source not in sources:
                sources.append(source)

        return sources

    def ask(self, question: str):

        documents = self._retrieve_documents(question)

        context = self._format_context(documents)
        patient_metadata = self._format_patient_metadata(documents)

        messages = self.prompt.invoke({
            "question": question,
            "context": context,
            "patient_metadata": patient_metadata
        })

        response = self.llm.invoke(messages)

        answer = self.parser.invoke(response)

        return {
            "question": question,
            "answer": answer,
            "sources": self._get_sources(documents),
            "documents": documents
        }

    def stream(self, question: str):

        documents = self._retrieve_documents(question)
        context = self._format_context(documents)
        patient_metadata = self._format_patient_metadata(documents)

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