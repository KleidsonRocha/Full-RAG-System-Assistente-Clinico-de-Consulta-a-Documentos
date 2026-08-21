import os
from ollama import Client
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

VECTORSTORE = os.path.join(os.path.dirname(__file__), "..", "vectorstore_faiss")
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


def _model_name_matches(installed_model: str, requested_model: str) -> bool:
    return installed_model in {
        requested_model,
        f"{requested_model}:latest",
    } or installed_model.split(":", 1)[0] == requested_model


def validar_modelo_ollama(model_name: str) -> None:
    try:
        response = Client(host=OLLAMA_BASE_URL).list()
    except Exception as exc:
        raise RuntimeError(
            "Nao foi possivel conectar ao Ollama em "
            f"{OLLAMA_BASE_URL}. Inicie o Ollama com: ollama serve"
        ) from exc

    installed_models = [model.model for model in response.models]

    if not any(_model_name_matches(model, model_name) for model in installed_models):
        installed = ", ".join(installed_models) or "nenhum modelo instalado"
        raise RuntimeError(
            f"Modelo Ollama '{model_name}' nao encontrado. "
            f"Modelos instalados: {installed}. "
            f"Instale com: ollama pull {model_name}"
        )

def modelo_embedding(model_name: str = "nomic-embed-text") -> OllamaEmbeddings:
    print(f"-> Inicializando embeddings locais via Ollama ({model_name})...")
    validar_modelo_ollama(model_name)
    return OllamaEmbeddings(
        model=model_name,
        base_url=OLLAMA_BASE_URL
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
