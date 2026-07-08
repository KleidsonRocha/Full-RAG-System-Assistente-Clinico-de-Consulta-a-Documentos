import os
import json
from langchain_core.documents import Document
from src.embedding.embeddings import Carregando_embeddings

# Define o caminho do JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "dados_paciente_chunk.json")


def ler_chunks_do_json(caminho_json: str) -> list[Document]:
    """
    Lê o arquivo Json estruturado e converte para o langchain
    """
    if not os.path.exists(caminho_json):
        raise FileNotFoundError(f"Arquivo Json não encontrado em: {caminho_json}")

    print(f"-> Carregando dados de: {caminho_json}")
    with open(caminho_json, "r", encoding="utf-8") as f:
        dados_json = json.load(f)

    chunks_langchain = []

    for item in dados_json:
        texto = item.get("page_content", item.get("text", ""))
        metadados = item.get("metadata", {})

        if texto:
            doc = Document(page_content=texto, metadata=metadados)
            chunks_langchain.append(doc)

    print(f"{len(chunks_langchain)} chunks prontos.")
    return chunks_langchain


def executar_ingestao(caminho_json: str = None) -> None:
    """
    Função principal para ser chamada externamente pelo Streamlit
    para recriar a base vetorial baseada em um arquivo JSON.
    """
    path_to_use = caminho_json if caminho_json else JSON_PATH

    lista_de_chunks = ler_chunks_do_json(path_to_use)

    if lista_de_chunks:
        db_local = Carregando_embeddings(
            chunks=lista_de_chunks, model_name="nomic-embed-text"
        )
        print("\n Vetores foram persistidos com sucesso!")

        return len(lista_de_chunks)
    else:
        raise ValueError("O arquivo JSON não contém chunks válidos para processamento.")


if __name__ == "__main__":
    try:
        executar_ingestao(JSON_PATH)
    except Exception as e:
        print(f"\n Falha ao executar o processamento: {e}")
