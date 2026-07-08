import os
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

VECTORSTORE = os.path.join(os.path.dirname(__file__), "..", "vectorstore_faiss")

def modelo_embedding(model_name: str = "nomic-embed-text") -> OllamaEmbeddings:
    print(f"-> Inicializando embeddings locais via Ollama ({model_name})...")
    return OllamaEmbeddings(
        model=model_name,
        base_url="http://localhost:11434"
    )

def Carregando_embeddings(chunks: list[Document], model_name: str = "nomic-embed-text") -> FAISS:
    """
    Recebe os chunks de texto, gera os embeddings e os persiste no FAISS local.
    """
    embedding_model = modelo_embedding(model_name=model_name)

    print(f"-> Vetorizando e salvando {len(chunks)} chunks no FAISS em: {VECTORSTORE}")

    # Criando a base vetorial com FAISS na memória
    vector_db = FAISS.from_documents(
        documents=chunks,
        embedding=embedding_model
    )

    vector_db.save_local(VECTORSTORE)

    print("Base vetorial FAISS criada com sucesso!")
    return vector_db