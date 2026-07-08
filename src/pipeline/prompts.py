"""
Todos os prompts utilizados pela aplicação.

Este arquivo centraliza:
- Prompt principal do sistema RAG;
- Mensagens de erro;
- Perguntas utilizadas para testes rápidos.

"""

SYSTEM_PROMPT = """
Você é um assistente clínico de consulta documental.
Use somente os METADADOS DO PACIENTE e o CONTEXTO recuperado.

REGRAS OBRIGATÓRIAS:

1. Não use conhecimento externo, memória do modelo ou suposições.

2. Não invente informações nem complete lacunas.

3. Se a resposta não estiver explicitamente apoiada nos dados recebidos, responda somente:

"Não encontrei essa informação nos documentos disponíveis."

4. Não responda perguntas fora do acervo documental.

5. Não faça diagnósticos, prescrições ou recomendações médicas próprias.

6. Para perguntas sobre bula, priorize o CONTEXTO.

7. Para perguntas sobre paciente, use apenas os METADADOS DO PACIENTE.

8. Quando responder, cite fonte, página ou chunk se estiverem disponíveis.

9. Seja direto e responda em no máximo 3 frases, exceto quando a pergunta pedir lista.

========================
METADADOS DO PACIENTE
========================

{patient_metadata}

========================
CONTEXTO
========================

{context}

========================
PERGUNTA
========================

{question}
...
"""


OUT_OF_SCOPE_MESSAGE = (
    "Não encontrei essa informação nos documentos disponíveis."
)


TEST_QUESTIONS = [
    # Protocolos Clínicos
    "Quais exames são recomendados para o diagnóstico da doença descrita no protocolo?",
    "Quais são os critérios para iniciar o tratamento?",
    "Quais contraindicações são apresentadas no protocolo?",
    "Qual é o tratamento de primeira escolha?",
    "Existe algum tratamento alternativo recomendado?",
    "Quais pacientes devem ser encaminhados para atendimento especializado?",
    "Quais sinais indicam agravamento da doença?",
    "Qual acompanhamento deve ser realizado após o tratamento?",

    # Bulas
    "Qual é a posologia recomendada do medicamento?",
    "Quais são os efeitos colaterais mais comuns?",
    "Quais são as contraindicações do medicamento?",
    "O medicamento pode ser utilizado durante a gestação?",
    "Existe interação medicamentosa importante?",
    "Qual é a dose máxima diária?",

    # Prontuários Sintéticos
    "Qual é o histórico clínico do paciente?",
    "Quais medicamentos o paciente utiliza atualmente?",
    "Quais exames laboratoriais foram realizados?",
    "Qual foi o diagnóstico registrado?",
    "Quais alergias o paciente possui?",
    "Qual foi a última consulta registrada?",

    # Casos Negativos
    "Quem ganhou a Copa do Mundo de 2002?",
    "Explique como funciona um motor a combustão.",
    "Quem foi Albert Einstein?",
    "Qual a capital da França?",
    "Como investir em ações?",
    "Escreva um poema sobre medicina."
]
