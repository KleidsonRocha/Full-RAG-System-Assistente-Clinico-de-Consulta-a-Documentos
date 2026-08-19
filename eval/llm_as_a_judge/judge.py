import json
import re
from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.embedding.embeddings import OLLAMA_BASE_URL


class JudgeEvaluation(BaseModel):
    faithfulness_score: int = Field(
        description="1 se a resposta for suportada pelo contexto/metadados fornecidos sem inventar dados, 0 caso haja alucinacao."
    )
    relevance_score: int = Field(
        description="1 se a resposta atende diretamente ao que foi perguntado pelo usuario, 0 se fugir ao tema."
    )
    refusal_score: int = Field(
        description="1 se o assistente agiu corretamente (respondeu quando havia dados ou recusou quando nao havia), 0 caso contrario."
    )
    justification: str = Field(
        description="Justificativa concisa da pontuacao atribuida com base na rubrica."
    )


JUDGE_SYSTEM_PROMPT = """Você é um avaliador técnico e equilibrado de respostas de um sistema RAG clínico.
Seu objetivo é verificar se o assistente respondeu corretamente à dúvida do usuário com base nos dados disponíveis.

RUBRICA DE AVALIAÇÃO:

1. FIDELIDADE (faithfulness_score):
- Nota 1: Todas as afirmações contidas na resposta gerada são diretamente comprovadas pelo contexto recuperado ou pelos metadados do paciente.
- Nota 0: A resposta inventa dados, assume premissas não presentes no contexto (alucinação) ou utiliza conhecimento prévio externo aos documentos fornecidos.

2. RELEVÂNCIA (relevance_score):
- Nota 1: A resposta atende à PERGUNTA DO USUÁRIO de forma direta, clara e compreensível. Omissão de fatos secundários do gabarito que o usuário não perguntou explicitamente não deve ser penalizada.
- Nota 0: A resposta não responde ao que foi perguntado, foge do tema ou é totalmente vaga.

3. CORREÇÃO DE RECUSA (refusal_score):
- Nota 1: O assistente agiu certo: forneceu a resposta quando havia dados no contexto/metadados OU recusou quando a pergunta estava fora do acervo/sem dados.
- Nota 0: O assistente inventou resposta para algo fora do acervo OU recusou responder tendo os dados necessários no contexto.

Retorne SEMPRE e EXCLUSIVAMENTE um objeto JSON válido no seguinte formato:
{{
  "faithfulness_score": 1,
  "relevance_score": 1,
  "refusal_score": 1,
  "justification": "Justificativa concisa da pontuacao."
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