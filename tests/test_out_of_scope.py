import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_RAG_INTEGRATION") == "1",
    reason="Teste de integracao do RAG desativado por SKIP_RAG_INTEGRATION=1.",
)

REFUSAL_MARKERS = (
    "nao encontrei",
    "não encontrei",
    "nÃ£o encontrei",
    "documentos disponiveis",
    "documentos disponíveis",
    "documentos disponÃ­veis",
    "fora do acervo",
    "nao posso responder",
    "não posso responder",
    "nao ha informacao",
    "não há informação",
    "nÃ£o hÃ¡ informaÃ§Ã£o",
)


def _looks_like_refusal(answer: str) -> bool:
    normalized_answer = " ".join(str(answer or "").lower().split())
    return any(marker in normalized_answer for marker in REFUSAL_MARKERS)


@pytest.mark.parametrize(
    "question",
    [
        "Quem ganhou a Copa do Mundo de 2002?",
        "Explique como funciona um motor a combustao.",
        "Qual e a capital da Franca?",
        "Como investir em acoes?",
    ],
)
def test_out_of_scope_questions_are_refused(question, clinical_rag_with_temp_vectorstore):
    rag = clinical_rag_with_temp_vectorstore
    result = rag.ask(question)

    assert isinstance(result.get("answer"), str)
    assert _looks_like_refusal(result["answer"])
