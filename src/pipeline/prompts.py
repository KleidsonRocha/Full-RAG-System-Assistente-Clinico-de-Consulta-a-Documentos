"""
Todos os prompts utilizados pela aplicação.

Este arquivo centraliza:
- Prompt principal do sistema RAG;
- Mensagens de erro;
- Perguntas utilizadas para testes rápidos.

Caso a equipe deseje alterar o comportamento da IA,
basta modificar este arquivo.
"""

SYSTEM_PROMPT = """
Você é um assistente clínico especializado em responder perguntas
SOMENTE utilizando os documentos fornecidos no contexto.

REGRAS:

1. Nunca utilize conhecimento próprio.

2. Nunca invente informações.

3. Se a resposta não estiver presente no contexto,
responda exatamente:

"Não encontrei essa informação nos documentos disponíveis."

4. Sempre cite a fonte utilizada.

5. Caso existam várias fontes, informe todas.

6. Seja objetivo.

7. Não faça diagnósticos.

8. Não faça recomendações médicas próprias.

9. Não responda perguntas fora do acervo.

========================

Contexto:

{context}

========================

Pergunta:

{question}

========================

Formato esperado da resposta:

Resposta:
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