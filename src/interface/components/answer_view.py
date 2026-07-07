from __future__ import annotations

import streamlit as st


def render_answer(result: dict | None) -> None:
    if not result:
        return

    if not result.get("ok"):
        st.error(result.get("error") or "Erro ao consultar o pipeline RAG.")
        technical_details = result.get("technical_details")
        if technical_details:
            with st.expander("Detalhes técnicos"):
                st.code(technical_details)
        return

    if result.get("is_out_of_scope"):
        st.warning("A pergunta foi tratada como fora do acervo disponível.")

    st.subheader("Resposta")
    answer = result.get("answer") or ""
    if answer:
        st.markdown(answer)
    else:
        st.warning("O pipeline não retornou uma resposta textual.")

    latency_ms = result.get("latency_ms")
    if latency_ms is not None:
        st.caption(f"Tempo de resposta: {latency_ms} ms")

    warnings = result.get("warnings") or []
    for warning in warnings:
        st.info(warning)
