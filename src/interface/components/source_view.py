from __future__ import annotations

from typing import Any

import streamlit as st


def render_sources(sources: list[dict[str, Any]], show_scores: bool) -> None:
    st.subheader("Fontes recuperadas")

    if not sources:
        st.warning("Nenhuma fonte foi retornada.")
        return

    for source in sources:
        title = _source_title(source)
        with st.expander(title, expanded=source.get("rank") == 1):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Página", source.get("page") or "N/A")
            col_b.metric("Chunk", source.get("chunk_id") or "N/A")

            score = source.get("score")
            if show_scores:
                col_c.metric("Score", "N/A" if score is None else f"{score:.4f}")
            else:
                col_c.metric("Ordem", source.get("rank") or "N/A")

            if show_scores and score is None:
                st.caption("Score indisponível no contrato atual do pipeline.")

            st.markdown("**Trecho recuperado**")
            st.write(source.get("excerpt") or "Trecho não disponível.")

            _render_patient_summary(source.get("metadata") or {})


def render_contexts(
    contexts: list[dict[str, Any]],
    show_context: bool,
    show_scores: bool,
) -> None:
    if not show_context:
        return

    st.subheader("Chunks e contexto usados")

    if not contexts:
        st.warning("Nenhum contexto recuperado foi retornado.")
        return

    for context in contexts:
        label = _context_title(context)
        with st.expander(label):
            if show_scores:
                score = context.get("score")
                st.caption(
                    "Score: indisponível"
                    if score is None
                    else f"Score: {score:.4f}"
                )

            st.markdown("**Texto enviado como contexto recuperado**")
            st.write(context.get("text") or "Texto não disponível.")

            metadata = context.get("metadata") or {}
            if metadata:
                st.markdown("**Metadados do chunk**")
                st.json(metadata, expanded=False)


def _source_title(source: dict[str, Any]) -> str:
    rank = source.get("rank") or "?"
    document = source.get("document") or "Documento recuperado"
    page = source.get("page")
    page_label = f" - página {page}" if page else ""
    return f"Fonte {rank}: {document}{page_label}"


def _context_title(context: dict[str, Any]) -> str:
    rank = context.get("rank") or "?"
    source = context.get("source") or "Documento recuperado"
    page = context.get("page")
    chunk_id = context.get("chunk_id")
    details = []

    if page:
        details.append(f"página {page}")

    if chunk_id:
        details.append(str(chunk_id))

    suffix = f" ({', '.join(details)})" if details else ""
    return f"Contexto {rank}: {source}{suffix}"


def _render_patient_summary(metadata: dict[str, Any]) -> None:
    patient_fields = {
        "Paciente": metadata.get("paciente_nome"),
        "Nascimento": metadata.get("paciente_data_nascimento"),
        "Último peso": metadata.get("paciente_ultimo_peso_kg"),
        "Última altura": metadata.get("paciente_ultima_altura_cm"),
    }
    available_fields = {
        key: value for key, value in patient_fields.items() if value not in (None, "")
    }

    if not available_fields:
        return

    st.markdown("**Dados do paciente encontrados nos metadados**")
    st.table(available_fields)
