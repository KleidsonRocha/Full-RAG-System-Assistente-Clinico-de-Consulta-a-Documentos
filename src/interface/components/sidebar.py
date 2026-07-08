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
        help="Controla quantos documentos o retriever busca no Chroma.",
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

    if status["sqlite_exists"]:
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

    if st.sidebar.button("Recriar Base Vetorial", use_container_width=True):
        with st.sidebar.spinner("Gerando embeddings no FAISS..."):
            res = rebuild_vectorstore()
            if res["ok"]:
                st.session_state.history = []
                st.session_state.latest_result = None
                st.sidebar.success("Base recriada com sucesso!")
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


