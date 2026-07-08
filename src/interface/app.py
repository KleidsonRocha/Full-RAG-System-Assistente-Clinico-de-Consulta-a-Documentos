from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.interface.components.sidebar import render_sidebar
from src.interface.components.source_view import render_contexts, render_sources
from src.interface.services.rag_service import SAMPLE_QUESTIONS, ask_question


def main() -> None:
    st.set_page_config(
        page_title="Assistente Clínico RAG",
        page_icon="RAG",
        layout="wide",
    )

    _init_session_state()
    _apply_theme()
    settings = render_sidebar()

    _render_header()
    _render_chat(settings)
    _render_example_popover(settings)
    _render_chat_input(settings)


def _init_session_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("latest_result", None)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --primary-color: #1d75bd;
            --background-color: #f7fbff;
            --secondary-background-color: #ffffff;
            --text-color: #12324a;
        }

        html,
        body,
        .stApp,
        .stApp *,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] * {
            color: #12324a;
        }
        
        button[data-testid="stDeployButton"], 
        .stDeployButton,
        div[data-testid="stStatusWidget"] + div {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            padding: 0 !important;
        }
        
        header[data-testid="stHeader"] div:first-child {
            display: none !important;
        }
        
        [data-testid="stStatusWidget"], 
        [data-testid="stMainMenu"] {
            display: none !important;
        }
        
        [data-testid="stHeader"] {
            background: transparent !important;
        }

        .stApp {
            background: linear-gradient(180deg, #f7fbff 0%, #eef6ff 100%);
            color: #12324a;
        }

        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #f7fbff 0%, #eef6ff 100%);
        }

        [data-testid="stHeader"] {
            background: rgba(247, 251, 255, 0.92);
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #d7e7f7;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] div {
            color: #12324a !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #0b3a5b !important;
            font-weight: 700;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #476b86 !important;
        }

        [data-testid="stSidebar"] [data-testid="stAlert"] {
            background: #dff6e8 !important;
            border: 1px solid #9ad8b0 !important;
            color: #135c35 !important;
        }

        [data-testid="stSidebar"] [data-testid="stAlert"] * {
            color: #135c35 !important;
        }

        h1, h2, h3 {
            color: #0b3a5b !important;
        }

        p, label, span, small, figcaption {
            color: #12324a;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {
            color: #5d7890 !important;
        }

        [data-testid="stMarkdownContainer"] p {
            color: #12324a;
        }

        [data-testid="stAlert"] {
            border-radius: 8px;
        }

        div[data-testid="stChatMessage"] {
            background: #ffffff;
            border: 1px solid #d8e8f7;
            border-radius: 14px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.06);
            padding: 0.75rem;
        }

        div[data-testid="stChatMessage"] * {
            color: #12324a !important;
        }

        [data-testid="stBottomBlockContainer"],
        [data-testid="stBottom"] {
            background: #f7fbff !important;
            border-top: 1px solid #d7e7f7;
        }

        div[data-testid="stChatInput"],
        [data-testid="stChatInput"] {
            background: #ffffff !important;
            border: 1px solid #c9ddf0 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 18px rgba(11, 58, 91, 0.08);
        }

        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input {
            background: #ffffff !important;
            color: #12324a !important;
            caret-color: #1d75bd !important;
        }

        [data-testid="stChatInput"] textarea::placeholder,
        [data-testid="stChatInput"] input::placeholder {
            color: #6c879d !important;
            opacity: 1 !important;
        }

        [data-testid="stChatInput"] button {
            background: #1d75bd !important;
            color: #ffffff !important;
            border-radius: 8px !important;
        }

        [data-testid="stChatInput"] button svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }

        .stButton > button,
        .stPopover > button {
            background: #ffffff !important;
            border: 1px solid #2f80d1 !important;
            color: #135c9f !important;
            border-radius: 8px !important;
        }

        .stButton > button *,
        .stPopover > button * {
            color: #135c9f !important;
        }

        .stButton > button:hover,
        .stPopover > button:hover {
            border-color: #1769b3 !important;
            color: #0d477d !important;
            background: #eaf4ff !important;
        }

        .stButton > button:hover *,
        .stPopover > button:hover * {
            color: #0d477d !important;
        }

        [data-testid="stPopoverBody"] {
            background: #ffffff !important;
            border: 1px solid #c9ddf0 !important;
            border-radius: 10px !important;
            box-shadow: 0 8px 28px rgba(11, 58, 91, 0.14);
        }

        [data-testid="stPopoverBody"] * {
            color: #12324a !important;
        }

        [data-testid="stSlider"] * {
            color: #12324a !important;
        }

        [data-testid="stCheckbox"] label,
        [data-testid="stCheckbox"] label * {
            color: #12324a !important;
            opacity: 1 !important;
        }

        [data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid #d8e8f7 !important;
            border-radius: 10px !important;
        }

        [data-testid="stExpander"] * {
            color: #12324a !important;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 7rem;
            max-width: 1050px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.title("Assistente Clínico RAG")
    st.caption(
        "Chat local para consultar o acervo processado com FAISS, Ollama e o pipeline RAG existente do projeto."
    )


def _render_chat(settings: dict[str, object]) -> None:
    history = st.session_state.get("history") or []
    if not history:
        st.info(
            "Faça uma pergunta sobre a bula ou sobre os dados clínicos disponíveis para iniciar a conversa."
        )
        return

    for result in history:
        question = result.get("question") or "Pergunta sem texto"
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            _render_assistant_message(result, settings)


def _render_assistant_message(result: dict, settings: dict[str, object]) -> None:
    if not result.get("ok"):
        st.error(result.get("error") or "Erro ao consultar o pipeline RAG.")
        technical_details = result.get("technical_details")
        if technical_details and bool(settings["debug"]):
            with st.expander("Detalhes Técnicos de Debug (Exceção Completa)", expanded=True):
                st.caption("Abaixo está o rastro do erro (Traceback) gerado pelo Python:")
                st.code(technical_details, language="python")
        elif technical_details:
            st.caption("💡 Ative o 'Modo debug' na barra lateral para ver os detalhes técnicos deste erro.")
        return

    if result.get("is_out_of_scope"):
        st.warning("A pergunta foi tratada como fora do acervo disponível.")

    answer = result.get("answer") or ""
    if answer:
        st.markdown(answer)
    else:
        st.warning("O pipeline não retornou uma resposta textual.")

    latency_ms = result.get("latency_ms")
    source_count = len(result.get("sources") or [])
    context_count = len(result.get("retrieved_context") or [])
    elapsed = f"{latency_ms} ms" if latency_ms is not None else "tempo indisponível"
    st.caption(f"{elapsed} | {source_count} fonte(s) | {context_count} contexto(s)")

    for warning in result.get("warnings") or []:
        st.info(warning)

    if bool(settings["debug"]):
        with st.expander("Dados brutos do Pipeline (Debug)", expanded=False):
            st.json(result)

    with st.expander("Fontes e contexto recuperado"):
        render_sources(
            result.get("sources") or [],
            show_scores=bool(settings["show_scores"]),
        )
        render_contexts(
            result.get("retrieved_context") or [],
            show_context=bool(settings["show_context"]),
            show_scores=bool(settings["show_scores"]),
        )


def _render_example_popover(settings: dict[str, object]) -> None:
    with st.popover("^ Perguntas recomendadas"):
        st.caption("Clique em uma sugestão para consultar diretamente.")
        for index, question in enumerate(SAMPLE_QUESTIONS, start=1):
            if st.button(question, key=f"sample_question_{index}", use_container_width=True):
                _submit_question(question, settings)
                st.rerun()


def _render_chat_input(settings: dict[str, object]) -> None:
    question = st.chat_input(
        "Digite uma pergunta sobre a bula ou os dados clínicos disponíveis"
    )

    if question:
        _submit_question(question, settings)
        st.rerun()


def _submit_question(question: str, settings: dict[str, object]) -> None:
    if not question.strip():
        st.warning("Digite uma pergunta antes de consultar.")
        return

    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("Consultando pipeline RAG..."):
        result = ask_question(
            question=question,
            top_k=int(settings["top_k"]),
            debug=bool(settings["debug"]),
        )

    st.session_state.latest_result = result
    _add_to_history(result)


def _add_to_history(result: dict) -> None:
    history = list(st.session_state.get("history") or [])
    history.append(result)
    st.session_state.history = history[-10:]


if __name__ == "__main__":
    main()
