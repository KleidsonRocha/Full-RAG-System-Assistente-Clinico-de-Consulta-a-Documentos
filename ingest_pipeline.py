import os
import json
from langchain_core.documents import Document
from src.embedding.embeddings import Carregando_embeddings

# Define o caminho do JSON 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

if __name__ == "__main__":
    try:
        
        lista_de_chunks = ler_chunks_do_json(JSON_PATH)
        
        if lista_de_chunks:
            db_local = Carregando_embeddings(chunks=lista_de_chunks, model_name="nomic-embed-text")
            print("\n vetores foram persistidos!")
        else:
            print("Erro, Json não tem chunks")
            
    except Exception as e:
        print(f"\n Falha ao executar o processamento: {e}")