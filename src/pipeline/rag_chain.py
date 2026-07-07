from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

from src.embedding.embeddings import VECTORSTORE, modelo_embedding
from src.pipeline.prompts import SYSTEM_PROMPT


class ClinicalRAG:

    def __init__(self):

        self.embedding_model = modelo_embedding()

        self.vector_store = Chroma(
            persist_directory=VECTORSTORE,
            embedding_function=self.embedding_model,
        )

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4},
        )

        self.llm = ChatOllama(
            model="gemma3:12b",
            temperature=0,
            num_predict=1024,
        )

        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

        self.chain = (
            RunnablePassthrough.assign(
                context=lambda x: self._format_context(
                    self.retriever.invoke(x["question"])
                )
            )
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _format_context(self, documents):

        return "\n\n".join(doc.page_content for doc in documents)

    def _get_documents(self, question: str):

        return self.retriever.invoke(question)

    def _get_sources(self, documents):

        sources = []

        for doc in documents:

            metadata = doc.metadata

            source = {
                "chunk": metadata.get("chunk_id"),
                "pagina": metadata.get("pagina_origem"),
                "medicamento": metadata.get("medicamento_bula_alvo"),
            }

            if source not in sources:
                sources.append(source)

        return sources

    def ask(self, question: str):

        documents = self._get_documents(question)

        answer = self.chain.invoke(
            {
                "question": question,
            }
        )

        return {
            "question": question,
            "answer": answer,
            "sources": self._get_sources(documents),
            "documents": documents,
        }

    def stream(self, question: str):

        documents = self._get_documents(question)

        answer = ""

        for chunk in self.chain.stream(
            {
                "question": question,
            }
        ):

            answer += chunk
            yield chunk

        return {
            "question": question,
            "answer": answer,
            "sources": self._get_sources(documents),
            "documents": documents,
        }


if __name__ == "__main__":

    rag = ClinicalRAG()

    while True:

        pergunta = input("\nPergunta: ")

        if pergunta.lower() == "sair":
            break

        documents = rag._get_documents(pergunta)

        for token in rag.stream(pergunta):
            print(token, end="", flush=True)

        print("\nDocumentos recuperados: ")

        for i, doc in enumerate(documents, start=1):

            print(f"\nDocumento {i}")
            print("-" * 80)
            print(doc.page_content)
            print()

        print("\n")

        print("Fontes: ")

        for source in rag._get_sources(documents):
            print(source)