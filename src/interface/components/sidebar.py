from __future__ import annotations

import streamlit as st
import time

from src.interface.services.rag_service import rebuild_vectorstore
from src.interface.services.rag_service import get_runtime_status


def render_sidebar() -> dict[str, object]:
    st.sidebar.header("Configuração")

    top_k = st.sidebar.slider(
        "Chunks recuperados",
        min_value=1,
        max_value=10,
        value=2,
        help="Controla quantos documentos o retriever busca no FAISS.",
    )
    show_context = st.sidebar.checkbox("Mostrar contexto recuperado", value=True)
    show_scores = st.sidebar.checkbox(
        "Mostrar scores",
        value=False,
        help="Exibe as porcentagens de relação entre os documentos exibidos",
    )
    debug = st.sidebar.checkbox(
        "Modo debug",
        value=False,
        help="Exibe detalhes técnicos de exceções do pipeline.",
    )

    if st.sidebar.button("Limpar histórico da sessão", use_container_width=True):
        st.session_state.history = []
        st.session_state.latest_result = None
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Estado local")
    status = get_runtime_status()

    if status["vectorstore_ready"]:
        st.sidebar.success("Vectorstore encontrado")
    else:
        st.sidebar.error("Vectorstore não encontrado")

    embedding_count = status.get("embedding_count")
    if embedding_count is not None:
        st.sidebar.caption(f"Embeddings persistidos: {embedding_count}")

    if status["chunks_json_exists"]:
        st.sidebar.caption("Chunks processados encontrados")
    else:
        st.sidebar.caption("Chunks processados não encontrados")

    st.sidebar.divider()
    st.sidebar.subheader("Manutenção")

    chunk_size = st.sidebar.slider(
        "Tamanho do Chunk",
        min_value=100,
        max_value=1000,
        value=400,
        step=50,
        help="Quantidade de tokens por pedaço de documento."
    )
    
    chunk_overlap = st.sidebar.slider(
        "Overlap do Chunk",
        min_value=0,
        max_value=300,
        value=80,
        step=10,
        help="Quantidade de tokens que se sobrepõem entre os pedaços."
    )

    if st.sidebar.button("Recriar Base Vetorial", use_container_width=True):
        with st.sidebar.spinner("Fatiando documentos e gerando embeddings..."):
            res = rebuild_vectorstore(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        if res["ok"]:
            st.session_state.history = []
            st.session_state.latest_result = None
            
            st.sidebar.success(f"Base recriada com sucesso! ({res.get('chunk_count', '')} chunks gerados)")
            
            time.sleep(1.5)
            st.rerun()
        else:
            st.sidebar.error(res["message"])

    st.sidebar.divider()
    st.sidebar.caption(
        "Nesta versão, o texto recuperado é focado na bula. Dados do paciente são exibidos pela interface quando aparecem nos metadados."
    )

    return {
        "top_k": top_k,
        "show_context": show_context,
        "show_scores": show_scores,
        "debug": debug,
    }


