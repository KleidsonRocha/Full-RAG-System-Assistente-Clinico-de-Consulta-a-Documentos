import os
from langchain_ollama import OllamaEmbeddings 
from langchain_chroma import Chroma
from langchain_core.documents import Document

VECTORSTORE = os.path.join(os.path.dirname(__file__), "..", "vectorstore")

def modelo_embedding(model_name: str = "nomic-embed-text") -> OllamaEmbeddings:
    print(f"-> Inicializando embeddings locais via Ollama ({model_name})...")
    return OllamaEmbeddings(
        model=model_name,
        base_url="http://localhost:11434"
    )

def Carregando_embeddings(chunks: list[Document], model_name: str = "nomic-embed-text") -> Chroma:
    """
    Recebe os chunks de texto, gera os embeddings e os persiste no ChromaDB local.
    """
    embedding_model = modelo_embedding(model_name=model_name)
    
    print(f"-> Vetorizando e salvando {len(chunks)} chunks no ChromaDB em: {VECTORSTORE}")
    
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=VECTORSTORE
    )
    
    print("Base vetorial criada com sucesso!")
    return vector_db

