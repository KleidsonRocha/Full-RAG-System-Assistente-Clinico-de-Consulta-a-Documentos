import json
import re
from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.embedding.embeddings import OLLAMA_BASE_URL


class JudgeEvaluation(BaseModel):
    faithfulness_score: int = Field(
        description="1 se a resposta for 100% suportada pelo contexto/metadados fornecidos, 0 caso haja extrapolacao ou alucinacao."
    )
    relevance_score: int = Field(
        description="1 se a resposta atende diretamente a pergunta feita, 0 se for evasiva, incorreta ou incompleta."
    )
    refusal_score: int = Field(
        description="1 se a acao de recusar ou responder estiver correta conforme o escopo e contexto, 0 caso contrario."
    )
    justification: str = Field(
        description="Justificativa concisa da pontuacao atribuida com base na rubrica."
    )


JUDGE_SYSTEM_PROMPT = """Você é um juiz avaliador técnico e imparcial de sistemas RAG clínicos.
Sua função é avaliar com rigor a resposta gerada por um assistente em relação ao contexto recuperado, metadados do paciente, pergunta do usuário e resposta esperada (gabarito).

RUBRICA DE AVALIAÇÃO:

1. FIDELIDADE (faithfulness_score):
- Nota 1: Todas as afirmações contidas na resposta gerada são diretamente comprovadas pelo contexto recuperado ou pelos metadados do paciente.
- Nota 0: A resposta inventa dados, assume premissas não presentes no contexto (alucinação) ou utiliza conhecimento prévio externo aos documentos fornecidos.

2. RELEVÂNCIA (relevance_score):
- Nota 1: A resposta aborda diretamente a intenção da pergunta do usuário com clareza e precisão.
- Nota 0: A resposta foge ao tema, responde algo diferente do solicitado ou omite o ponto central da questão.

3. CORREÇÃO DE RECUSA (refusal_score):
- Para perguntas fora do acervo ou sem evidência no contexto: Nota 1 se o assistente recusou conforme instruído ("Não encontrei essa informação nos documentos disponíveis"), e Nota 0 se respondeu usando memória própria.
- Para perguntas com evidência suficiente: Nota 1 se o assistente respondeu com os dados, e Nota 0 se recusou indevidamente.

Retorne SEMPRE e EXCLUSIVAMENTE um objeto JSON válido no seguinte formato:
{{
  "faithfulness_score": 1,
  "relevance_score": 1,
  "refusal_score": 1,
  "justification": "Justificativa da pontuacao."
}}
"""

JUDGE_USER_PROMPT = """Avalie a execução do sistema RAG abaixo:

[PERGUNTA DO USUÁRIO]
{question}

[CONTEXTO RECUPERADO E METADADOS]
{context}

[RESPOSTA ESPERADA (GABARITO)]
{expected_answer}

[AFIRMAÇÕES ATÔMICAS ESPERADAS]
{atomic_claims}

[RESPOSTA GERADA PELO ASSISTENTE]
{generated_answer}

JSON:"""


class LLMJudge:
    def __init__(self, model_name: str = "qwen2.5:3b", base_url: str = OLLAMA_BASE_URL):
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", JUDGE_SYSTEM_PROMPT),
                ("user", JUDGE_USER_PROMPT),
            ]
        )
        self.llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0,
            format="json",
        )
        self.chain = self.prompt | self.llm

    def _extract_json(self, raw_content: str) -> Dict[str, Any]:
        text = raw_content.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        return json.loads(text)

    def evaluate(
        self,
        question: str,
        context: str,
        expected_answer: str,
        atomic_claims: list[str],
        generated_answer: str,
    ) -> Dict[str, Any]:
        formatted_claims = "\n- ".join(atomic_claims) if atomic_claims else "Nenhuma (caso de recusa)"
        formatted_context = context.strip() if context.strip() else "Nenhum contexto recuperado."

        try:
            response = self.chain.invoke(
                {
                    "question": question,
                    "context": formatted_context,
                    "expected_answer": expected_answer,
                    "atomic_claims": formatted_claims,
                    "generated_answer": generated_answer,
                }
            )
            raw_text = response.content if hasattr(response, "content") else str(response)
            parsed = self._extract_json(raw_text)

            return {
                "faithfulness_score": int(parsed.get("faithfulness_score", 0)),
                "relevance_score": int(parsed.get("relevance_score", 0)),
                "refusal_score": int(parsed.get("refusal_score", 0)),
                "justification": str(parsed.get("justification", "Sem justificativa informada.")),
            }
        except Exception as exc:
            return {
                "faithfulness_score": 0,
                "relevance_score": 0,
                "refusal_score": 0,
                "justification": f"Falha ao interpretar saída JSON do juiz: {str(exc)}",
            }